"""GE v2 Lab 2 (프롬프트로 답 얻기 · 마케팅) — REAL UI recordings:
  ge2a_vague    : 막연한 질문 -> 일반적인 답
  ge2b_good     : 소스(Google 검색) 확인 -> 4요소 프롬프트 -> 출처 포함 답변 -> 출처 열기
  ge2c_followup : 이어서 질문(광고 카피 3안) -> 프롬프트 수정 아이콘 확인
  ge2d_share    : 작업 메뉴 -> 이름 바꾸기 -> 공유(링크 복사)
Run: python3 ge2.py [a b c d]
"""
import asyncio
import json
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from ge import GE, APP_HOME  # noqa: E402
from helpers import DUMP_JS  # noqa: E402

HOME = APP_HOME + '?hl=ko'
CHAT_TITLE_HINT = '1인 가구 트렌드 분석'
VAGUE = "1인 가구 트렌드 알려줘"
GOOD = ("당신은 Cymbal 마케팅팀의 시장 분석 담당자입니다. "
        "국내 1인 가구의 최근 1년 소비·생활 트렌드를 웹에서 찾아, 다음 주 신제품 출시 전략 회의에 쓸 수 있도록 정리해 주세요. "
        "핵심 트렌드 5가지를 표(트렌드 | 근거 | Cymbal에 주는 시사점)로 만들고, 각 근거에 출처를 달아 주세요. "
        "특정 기업이나 브랜드 이름은 쓰지 말아 주세요.")
FOLLOW = ("이 중 20~30대 1인 가구에게 가장 중요한 트렌드 2개를 골라, "
          "신제품 공기청정기 'Cymbal AirPole Pro'의 SNS 광고 카피 3안을 써 주세요. 각 안은 한 줄 헤드라인과 두 줄 본문으로요.")
LEAKS = []


async def guard(ge, where):
    hits = await ge.brand_scan()
    if hits:
        LEAKS.append((where, hits))
        print('BRAND LEAK', where, hits[:8])


async def hover(ge, loc, label, dwell=1200):
    box = await ge.move_to(loc, steps=18, pause=200)
    ge.mark("hover", label=label, box=box)
    await ge.page.wait_for_timeout(dwell)


async def ask(ge, text, label, delay=26, timeout=240):
    p = ge.page
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await ge.type_text(text, delay=delay, label=label)
    await p.wait_for_timeout(700)
    ge.mark('submit', label='전송')
    await p.keyboard.press('Enter')
    await ge.wait_answer_done(timeout=timeout, label=label)
    await p.wait_for_timeout(1000)


async def clip_vague(ge):
    p = ge.page
    await ge.goto(HOME, wait=4500)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ask(ge, VAGUE, '막연한 질문', delay=70)
    await ge.shot('ge_2_01_vague_answer')
    await p.mouse.move(1100, 500, steps=12)
    await p.mouse.wheel(0, 500)
    await p.wait_for_timeout(1800)
    await p.mouse.wheel(0, 900)
    await p.wait_for_timeout(1800)
    print(await ge.stop_recording('ge2a_vague'))
    await guard(ge, 'vague')


async def rename_current(ge, title):
    """Unrecorded rename of the open chat (auto titles vary run to run)."""
    p = ge.page
    await ge.click(await ge.vis('[aria-label="작업 메뉴"]'), steps=4)
    await p.wait_for_timeout(900)
    await ge.click(await ge.vis_text('이름 바꾸기'), steps=4)
    await p.wait_for_timeout(900)
    await p.keyboard.press('Meta+A')
    await p.keyboard.type(title, delay=10)
    await p.keyboard.press('Enter')
    await p.wait_for_timeout(1500)


async def clip_vague_clean(ge, tries=4):
    from chats import delete_current
    for i in range(tries):
        n = len(LEAKS)
        await clip_vague(ge)
        if len(LEAKS) == n:
            await rename_current(ge, '1인 가구 트렌드')
            return
        LEAKS.pop()
        print('vague answer named brands -> delete + retry', i + 1)
        await delete_current(ge)
    LEAKS.append(('vague', 'still leaking after retries'))


async def clip_good(ge):
    p = ge.page
    await ge.goto(HOME, wait=4500)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis('[aria-label="소스"]'), label='소스')
    await p.wait_for_timeout(1700)
    await ge.shot('ge_2_10_sources_menu')
    await p.keyboard.press('Escape')
    await p.wait_for_timeout(700)
    await ask(ge, GOOD, '4요소 프롬프트', delay=16, timeout=300)
    await ge.shot('ge_2_11_good_answer_top')
    await p.mouse.move(1100, 450, steps=12)
    for _ in range(3):
        await p.mouse.wheel(0, 450)
        await p.wait_for_timeout(1600)
    await ge.shot('ge_2_12_good_table')
    # citation chips / source links inside the answer
    items = await p.evaluate(DUMP_JS)
    cands = [it for it in items if it['x'] > 420 and 60 < it['y'] < 680 and it['w'] < 220 and
             (it['al'].find('출처') >= 0 or it['al'].find('소스') >= 0 or it['txt'].isdigit() or 'http' in it['al'])]
    print('citation candidates:', json.dumps(cands[:12], ensure_ascii=False))
    if cands:
        c = cands[0]
        await p.mouse.move(c['x'] + c['w'] / 2, c['y'] + c['h'] / 2, steps=18)
        ge.mark('hover', label='출처', box={'x': c['x'], 'y': c['y'], 'width': c['w'], 'height': c['h']})
        await p.wait_for_timeout(1800)
        await ge.shot('ge_2_13_citation_hover')
        await ge.click(p.locator(f'[aria-label="{c["al"]}"]').first if c['al'] else
                       p.get_by_text(c['txt'], exact=True).first, label='출처 열기')
        await p.wait_for_timeout(2500)
        await ge.shot('ge_2_14_sources_panel')
        items = await p.evaluate(DUMP_JS)
        print('after citation click:', json.dumps([it for it in items if it['x'] > 900][:20], ensure_ascii=False))
    await p.wait_for_timeout(1500)
    print(await ge.stop_recording('ge2b_good'))
    await guard(ge, 'good')
    await rename_current(ge, CHAT_TITLE_HINT)


async def open_latest_chat(ge, hint):
    p = ge.page
    await ge.goto(HOME, wait=4500)
    for h in (hint, 'AirPole Pro 출시'):
        try:
            await (await ge.vis_text(h, exact=False, timeout=6000)).click()
            break
        except RuntimeError:
            continue
    await p.wait_for_timeout(3500)


async def clip_followup(ge):
    p = ge.page
    await open_latest_chat(ge, CHAT_TITLE_HINT)
    await p.mouse.move(1100, 500)
    await p.mouse.wheel(0, 5000)
    await p.wait_for_timeout(1200)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ask(ge, FOLLOW, '이어서 질문', delay=24, timeout=200)
    await ge.shot('ge_2_20_followup_answer')
    await p.mouse.move(1100, 450, steps=10)
    await p.mouse.wheel(0, 700)
    await p.wait_for_timeout(1800)
    # user prompt bubble actions (edit / copy) appear on hover
    await p.mouse.wheel(0, -1400)
    await p.wait_for_timeout(1000)
    items = await p.evaluate(DUMP_JS)
    edits = [it for it in items if any(k in it['al'] for k in ('수정', '프롬프트 복사', '편집'))]
    print('prompt actions:', json.dumps(edits[:6], ensure_ascii=False))
    for it in edits[:2]:
        await p.mouse.move(it['x'] + it['w'] / 2, it['y'] + it['h'] / 2, steps=16)
        ge.mark('hover', label=it['al'], box={'x': it['x'], 'y': it['y'], 'width': it['w'], 'height': it['h']})
        await p.wait_for_timeout(1500)
    await ge.shot('ge_2_21_prompt_actions')
    await p.wait_for_timeout(800)
    print(await ge.stop_recording('ge2c_followup'))
    await guard(ge, 'followup')


async def clip_share(ge):
    p = ge.page
    await open_latest_chat(ge, CHAT_TITLE_HINT)
    await p.mouse.move(1000, 500)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis('[aria-label="작업 메뉴"]'), label='작업 메뉴')
    await p.wait_for_timeout(1200)
    await ge.click(p.get_by_text('이름 바꾸기', exact=True).first, label='이름 바꾸기')
    await p.wait_for_timeout(1300)
    await p.keyboard.press('Meta+A')
    await ge.type_text('AirPole Pro 출시 — 1인 가구 트렌드·광고 카피', delay=45, label='새 이름')
    await p.wait_for_timeout(500)
    await ge.shot('ge_2_30_rename')
    await p.keyboard.press('Enter')
    await p.wait_for_timeout(1500)
    await ge.click(await ge.vis('[aria-label="작업 메뉴"]'), label='작업 메뉴')
    await p.wait_for_timeout(1200)
    await ge.click(p.get_by_text('공유', exact=True).first, label='공유')
    await p.wait_for_timeout(2500)
    await ge.shot('ge_2_31_share_dialog')
    items = await p.evaluate(DUMP_JS)
    print('share dialog:', json.dumps([it for it in items if 300 < it['x'] < 1200 and 100 < it['y'] < 700][:20],
                                      ensure_ascii=False))
    btn = None
    for txt in ('링크 생성', '링크 만들기', '링크 복사', '공유 링크 만들기', '만들기', '복사'):
        loc = p.get_by_text(txt, exact=True)
        if await loc.count():
            btn = (txt, loc.first)
            break
    if btn:
        await ge.click(btn[1], label=btn[0])
        await p.wait_for_timeout(2500)
        await ge.shot('ge_2_32_share_link')
        items = await p.evaluate(DUMP_JS)
        print('after share click:', json.dumps([it for it in items if 300 < it['x'] < 1200 and 100 < it['y'] < 700][:20],
                                               ensure_ascii=False))
    await p.wait_for_timeout(1500)
    await p.keyboard.press('Escape')
    await p.wait_for_timeout(1200)
    print(await ge.stop_recording('ge2d_share'))


async def clip_sources(ge):
    """ge2e_sources: 추론 과정 표시 열고 닫기 -> 출처 칩에 마우스 -> 소스 카드 -> 다른 칩."""
    p = ge.page
    await open_latest_chat(ge, CHAT_TITLE_HINT)
    await p.mouse.move(1300, 400)
    await p.mouse.wheel(0, -30000)
    await p.wait_for_timeout(1500)
    await ge.start_recording()
    await p.wait_for_timeout(1200)
    try:
        rs = await ge.vis_text('추론 과정 표시', exact=False, timeout=4000)
        await ge.click(rs, label='추론 과정 표시')
        await p.wait_for_timeout(2600)
        await ge.shot('ge_2_15_reasoning')
        await ge.click(await ge.vis_text('추론 과정', exact=False, timeout=4000), label='추론 과정 닫기')
        await p.wait_for_timeout(1200)
    except Exception as e:  # noqa: BLE001
        print('reasoning toggle skipped:', e)
    chips = p.locator('md-assist-chip.domain-chip')
    n = await chips.count()
    print('chips:', n)
    for i in (0, 1):
        if i >= n:
            break
        c = chips.nth(i)
        await c.scroll_into_view_if_needed()
        await p.wait_for_timeout(500)
        b = await c.bounding_box()
        await p.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2, steps=20)
        ge.mark('hover', label=f'출처 칩 {i + 1}', box=b)
        await p.wait_for_timeout(2600)
        await ge.shot(f'ge_2_1{3 + i}_source_card')
        await p.mouse.move(1300, b['y'] + 160, steps=14)
        await p.wait_for_timeout(900)
    await p.wait_for_timeout(800)
    print(await ge.stop_recording('ge2e_sources'))


async def main(which):
    async with GE() as ge:
        for k, fn in (('a', clip_vague_clean), ('b', clip_good), ('e', clip_sources), ('c', clip_followup), ('d', clip_share)):
            if k in which:
                await fn(ge)
    if LEAKS:
        print('LEAKS:', LEAKS)
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ['a', 'b', 'e', 'c', 'd']))
