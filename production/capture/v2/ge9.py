"""GE v2 Lab 9 (에이전트 공유 · 갤러리 · 관리) — REAL UI recordings.
  ge9a_gallery : 사이드바 에이전트 갤러리(Google 제공 · 조직 공유 · 내가 만든 에이전트) 살펴보기 & 고정
  ge9b_manage  : 내 에이전트('Cymbal 사내 지원 데스크') ⋮ 메뉴 -> 수정/버전 관리 -> 홈에서 @멘션 호출
Run: python3 ge9.py [a b]
"""
import asyncio
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME  # noqa: E402
from helpers import click_xy, smooth_scroll, type_prompt, FIND_TEXT_JS  # noqa: E402

HOME = APP_HOME + '?hl=ko'
AGENTS_URL = APP_HOME + '/r/agents?hl=ko'
Q = "반차와 반반차는 몇 시간 단위로 쓸 수 있나요?"


async def find_word(ge, word, maxw=460, maxh=70, miny=0):
    hits = await ge.page.evaluate(FIND_TEXT_JS, [word, maxw, maxh, miny])
    return [h for h in hits if h['x'] < 1440]


async def clip_a(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis_label('에이전트'), label='에이전트')
    await p.wait_for_timeout(3500)
    await ge.shot('ge_9_01_gallery_top')
    await p.mouse.move(860, 420, steps=12)
    await smooth_scroll(ge, 420, step=100, pause=120)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_9_02_gallery_custom')
    # open ⋮ menu on custom agent card if visible
    menus = await p.evaluate(r"""() => {
      const out = [];
      function scan(root) {
        for (const b of root.querySelectorAll('button[aria-label*="작업"], button[aria-label*="더보기"], button[aria-label*="메뉴"]')) {
          const r = b.getBoundingClientRect();
          if (r.x > 300 && r.y > 160 && r.width > 16) out.push({x: r.x, y: r.y, w: r.width, h: r.height});
        }
        for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
      }
      scan(document); return out;
    }""")
    if menus:
        await click_xy(ge, menus[0], '에이전트 작업 메뉴')
        await p.wait_for_timeout(1500)
        await ge.shot('ge_9_03_agent_card_menu')
        await p.keyboard.press('Escape')
        await p.wait_for_timeout(800)
    else:
        await ge.shot('ge_9_03_agent_card_menu')
    print(await ge.stop_recording('ge9a_gallery'), flush=True)


async def clip_b(ge):
    p = ge.page
    await ge.goto(HOME, wait=4500)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.shot('ge_9_04_sidebar_pinned')
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await p.keyboard.type('@', delay=80)
    await p.wait_for_timeout(1200)
    await ge.shot('ge_9_05_mention_popup')
    hits = await find_word(ge, '사내 지원', 420, 60)
    if hits:
        await click_xy(ge, hits[-1], '@Cymbal 사내 지원 데스크')
        await p.wait_for_timeout(800)
    else:
        await p.keyboard.press('Enter')
    await type_prompt(ge, ' ' + Q, delay=22)
    await p.wait_for_timeout(500)
    await ge.shot('ge_9_06_mention_question')
    await p.keyboard.press('Enter'); ge.mark('submit', label='lab9_mention')
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=180, stable=4, label='lab9_mention')
    await ge.set_rate(1)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_9_07_mention_answer')
    print(await ge.stop_recording('ge9b_manage'), flush=True)


Q_ADK = "이번 달 예정된 사내 행사 목록과 참가 신청 방법을 알려주세요."
Q_SKILL = "방금 Cymbal 행사 안내 에이전트가 조회한 이번 달 사내 행사 일정을 신입사원 온보딩 공지용 1페이지 요약 보고서로 정리해 주세요."


async def clip_c(ge):
    p = ge.page
    await ge.goto(HOME, wait=4500)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await p.keyboard.type('@Cymbal 행사', delay=70)
    await p.wait_for_timeout(1200)
    hits = await find_word(ge, '행사 안내', 420, 60)
    if hits:
        await click_xy(ge, hits[-1], '@Cymbal 행사 안내(ADK)')
        await p.wait_for_timeout(800)
    else:
        await p.keyboard.press('Enter')
        await p.wait_for_timeout(800)
    await type_prompt(ge, ' ' + Q_ADK, delay=22)
    await p.wait_for_timeout(600)
    await ge.shot('ge_9_08_adk_mention_question')
    await p.keyboard.press('Enter')
    ge.mark('submit', label='lab9_adk_mention')
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=180, stable=5, label='lab9_adk_mention')
    await ge.set_rate(1)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_9_09_adk_mention_answer')

    # Unpin active sub-agent chip (click close X in input banner) so /cymbal-report-style runs in main Gemini chat
    close_btns = await p.evaluate(r"""() => {
      const out = [];
      function scan(root) {
        const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = tw.nextNode())) {
          if (n.nodeValue && n.nodeValue.trim() === 'close') {
            const el = n.parentElement;
            if (!el) continue;
            const r = el.getBoundingClientRect();
            if (r.x > 800 && r.y > 550 && r.width > 8) out.push({x: r.x, y: r.y, w: r.width, h: r.height});
          }
        }
        for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
      }
      scan(document);
      return out;
    }""")
    if close_btns:
        await click_xy(ge, close_btns[-1], '에이전트 대화 고정 해제')
        await p.wait_for_timeout(900)

    # Follow-up in the same thread using /cymbal-report-style skill
    await ge.click(await ge.vis('[contenteditable="true"]'), label='후속 질문 입력창')
    await p.keyboard.type('/', delay=80)
    await p.wait_for_timeout(1200)
    sk_hits = await find_word(ge, 'cymbal-report-style', 420, 60)
    if sk_hits:
        await click_xy(ge, sk_hits[-1], '/cymbal-report-style 스킬 선택')
        await p.wait_for_timeout(800)
    else:
        await p.keyboard.type('cymbal-report-style ', delay=40)
        await p.wait_for_timeout(600)
    await type_prompt(ge, ' ' + Q_SKILL, delay=22)
    await p.wait_for_timeout(600)
    await ge.shot('ge_9_10_skill_combo_prompt')
    await p.keyboard.press('Enter')
    ge.mark('submit', label='lab9_skill_combo')
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=180, stable=5, label='lab9_skill_combo')
    await ge.set_rate(1)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_9_11_skill_combo_answer')
    print(await ge.stop_recording('ge9c_combo'), flush=True)



async def main(which):
    async with GE() as ge:
        for k, fn in (('a', clip_a), ('b', clip_b), ('c', clip_c)):
            if k in which:
                await fn(ge)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or ['a', 'b', 'c']))

