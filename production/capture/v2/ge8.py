"""GE v2 Lab 8 (워크플로 심화 — Cymbal 고객 문의 자동 분류 · 답변 초안) — REAL UI recordings.
  ge8a_build  : 새 에이전트 > 워크플로 -> 자연어 설명으로 워크플로 생성
  ge8b_edit   : 왼쪽 대화창에서 긴급도 분류 단계 추가 요청 -> 트리거 · 단계 세부 설정 확인
  ge8c_test   : 테스트 탭 -> 테스트 실행 시작 -> 단계별 실행 결과 및 답변 초안 확인 -> 사용 설정
Run: python3 ge8.py [a b c]
"""
import asyncio
import json
import re
import sys
import time

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME, RECS, SHOTS  # noqa: E402
from helpers import type_prompt, click_xy, smooth_scroll, FIND_TEXT_JS, DUMP_JS  # noqa: E402

HOME = APP_HOME + '?hl=ko'
WF_URL_FILE = RECS / 'ge8_workflow_url.txt'
WF_INPUT = 'textarea[placeholder="워크플로에 어떤 일을 맡길지 설명해 주세요"]'

DESC = (
    "매일 오전 9시에 실행되는 'Cymbal 고객 문의 일일 브리핑 및 답변 초안' 워크플로를 만들어 주세요.\n"
    "1단계: Cymbal 스마트 공기청정기 AirPole Pro의 주요 고객 문의 유형 3가지(필터 교체·소음·앱 연결)를 정리합니다.\n"
    "2단계: 각 문의 유형별로 CS 상담원이 바로 복사해 쓸 수 있는 친절한 표준 답변 초안을 작성합니다.\n"
    "3단계: '오늘의 핵심 요약 3줄 + 문의 유형별 답변 표 + CS팀 체크포인트' 형식의 일일 브리핑으로 정리합니다."
)
CHANGE = (
    "1단계와 2단계 사이에 문의 유형별 긴급도(상·중·하)와 담당 부서(CS팀·품질보증팀·앱개발팀)를 분류하는 단계를 추가해 주세요."
)

NODES_JS = r"""
([x0, x1, y0, y1]) => {
  const res = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      const t = (n.nodeValue || '').trim();
      if (t.length < 2) continue;
      const el = n.parentElement; if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.width > 4 && r.height > 4 && r.height <= 34 && r.x >= x0 && r.x + r.width <= x1 && r.y >= y0 && r.y <= y1)
        res.push({t, x: r.x, y: r.y, w: r.width, h: r.height});
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  res.sort((a, b) => a.y - b.y);
  return res;
}
"""
ICON = re.compile(r'^[a-z0-9_]+$')


async def nodes(ge):
    raw = await ge.page.evaluate(NODES_JS, [470, 1100, 140, 760])
    return [n for n in raw if not ICON.match(n['t'])]


async def left_input(ge):
    loc = ge.page.locator('[contenteditable="true"]')
    for i in range(await loc.count()):
        b = await loc.nth(i).bounding_box()
        if b and b['x'] < 470 and b['y'] > 560 and b['width'] > 50:
            return loc.nth(i)
    raise RuntimeError('left chat input not found')


async def textarea_value(ge):
    return await ge.page.evaluate(r"""(sel) => {
      function find(root) {
        const e = root.querySelector(sel); if (e) return e;
        for (const x of root.querySelectorAll('*')) if (x.shadowRoot) { const r = find(x.shadowRoot); if (r) return r; }
        return null;
      }
      const t = find(document); return t ? t.value : null;
    }""", WF_INPUT)


async def clip_a(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis_label('새 에이전트'), label='새 에이전트')
    await p.wait_for_timeout(900)
    chat = (await p.evaluate(FIND_TEXT_JS, ['채팅 에이전트', 300, 60, 0]))[-1]
    wf = (await p.evaluate(FIND_TEXT_JS, ['워크플로', 300, 60, 0]))[-1]
    await p.mouse.move(chat['x'] + 30, chat['y'] + chat['h'] / 2, steps=12)
    await p.wait_for_timeout(250)
    await click_xy(ge, wf, '워크플로')
    await p.wait_for_timeout(4500)
    await ge.install_cursor()
    await ge.shot('ge_8_01_workflow_start')
    await ge.click(await ge.vis(WF_INPUT), label='워크플로 설명 입력')
    await type_prompt(ge, DESC, delay=15)
    await p.wait_for_timeout(700)
    await ge.shot('ge_8_02_workflow_description')
    await p.keyboard.press('Enter'); ge.mark('submit', label='workflow_desc')
    await p.wait_for_timeout(3500)
    v = await textarea_value(ge)
    if v and len(v) > 20:
        for lab in ('제출', '보내기', '전송', 'Submit', 'Send'):
            loc = p.locator(f'[aria-label="{lab}"]')
            if await loc.count():
                try:
                    await ge.click(await ge.vis(f'[aria-label="{lab}"]', timeout=2000), label=lab)
                    break
                except Exception:
                    pass
    await ge.set_rate(3)
    ge.mark('wait_start', label='workflow_build')
    t0 = time.monotonic()
    last_n, last_change = -1, time.monotonic()
    while time.monotonic() - t0 < 480:
        st = await p.evaluate(ge.PROBE_JS)
        now = time.monotonic()
        if st['n'] != last_n:
            last_n, last_change = st['n'], now
        el = now - t0
        if el > 35 and not st['busy'] and now - last_change >= 20:
            break
        await p.wait_for_timeout(1000)
    ge.mark('wait_end', label='workflow_build', secs=round(time.monotonic() - t0, 1))
    await ge.set_rate(1)
    await p.wait_for_timeout(2500)
    await ge.shot('ge_8_03_workflow_generated')
    WF_URL_FILE.write_text(p.url)
    print(await ge.stop_recording('ge8a_build'), flush=True)


async def clip_b(ge):
    p = ge.page
    url = WF_URL_FILE.read_text().strip()
    if p.url.split('?')[0] != url.split('?')[0]:
        await ge.goto(url, wait=5000, sidebar=False)
    await ge.install_cursor()
    await p.mouse.move(760, 720)
    await p.mouse.click(760, 720)
    await p.wait_for_timeout(1200)
    ns = await nodes(ge)
    n_before = len(ns)
    print('nodes before', [n['t'] for n in ns], flush=True)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await left_input(ge), label='변경 요청 입력')
    await type_prompt(ge, CHANGE, delay=16)
    await p.wait_for_timeout(600)
    await ge.shot('ge_8_04_change_request')
    await p.keyboard.press('Enter'); ge.mark('submit', label='change_request')
    await ge.set_rate(3)
    ge.mark('wait_start', label='wf_change')
    t0 = time.monotonic()
    state = {'sig': None, 't': time.monotonic()}
    while time.monotonic() - t0 < 300:
        cur = await nodes(ge)
        sig = tuple(n['t'] for n in cur)
        now = time.monotonic()
        if sig != state['sig']:
            state['sig'], state['t'] = sig, now
        st = await p.evaluate(ge.PROBE_JS)
        if len(cur) > n_before and not st['busy'] and now - state['t'] >= 6:
            break
        await p.wait_for_timeout(1000)
    ge.mark('wait_end', label='wf_change', secs=round(time.monotonic() - t0, 1))
    await ge.set_rate(1)
    await p.wait_for_timeout(2500)
    ns = await nodes(ge)
    print('nodes after', [n['t'] for n in ns], flush=True)
    await ge.shot('ge_8_05_changed_flow')
    if ns:
        await click_xy(ge, ns[0], '트리거 노드')
        await p.wait_for_timeout(2200)
    await ge.shot('ge_8_06_trigger_schedule')
    ns = await nodes(ge)
    if len(ns) > 1:
        await click_xy(ge, ns[1], '1단계 노드')
        await p.wait_for_timeout(2200)
    await ge.shot('ge_8_07_step_detail')
    print(await ge.stop_recording('ge8b_edit'), flush=True)


async def clip_c(ge):
    p = ge.page
    url = WF_URL_FILE.read_text().strip()
    if p.url.split('?')[0] != url.split('?')[0]:
        await ge.goto(url, wait=5000, sidebar=False)
    await ge.install_cursor()
    await ge.start_recording()
    await p.wait_for_timeout(800)
    tab = await p.evaluate(FIND_TEXT_JS, ['테스트', 120, 50, 0])
    if tab:
        await click_xy(ge, tab[0], '테스트 탭')
        await p.wait_for_timeout(2500)
    await ge.shot('ge_8_08_test_tab')
    start = await p.evaluate(FIND_TEXT_JS, ['테스트 실행 시작', 300, 60, 0])
    if start:
        await click_xy(ge, start[0], '테스트 실행 시작')
        await p.wait_for_timeout(6000)
    await ge.shot('ge_8_09_test_running')
    await ge.set_rate(4)
    ge.mark('wait_start', label='wf_test')
    t0 = time.monotonic()
    last = {'n': -1, 't': time.monotonic()}
    while time.monotonic() - t0 < 480:
        st = await p.evaluate(ge.PROBE_JS)
        now = time.monotonic()
        if st['n'] != last['n']:
            last['n'], last['t'] = st['n'], now
        if (not st['busy']) and now - last['t'] >= 22 and (now - t0) > 25:
            break
        await p.wait_for_timeout(1500)
    ge.mark('wait_end', label='wf_test', secs=round(time.monotonic() - t0, 1))
    await ge.set_rate(1)
    await p.wait_for_timeout(2000)
    await ge.shot('ge_8_11_test_done')
    # expand the last step's output
    rows = await p.evaluate(r"""() => {
      const out = [];
      function scan(root) {
        const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = tw.nextNode())) {
          const t = (n.nodeValue || '').trim();
          if (!t) continue;
          const el = n.parentElement; if (!el) continue;
          const r = el.getBoundingClientRect();
          if (r.x > 840 && r.y > 100 && r.y < 760 && r.width > 20 && /에이전트|브리핑|작성|정리/.test(t))
            out.push({x: r.x, y: r.y, w: r.width, h: r.height, t});
        }
        for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
      }
      scan(document); return out;
    }""")
    if rows:
        await click_xy(ge, rows[-1], '결과 펼치기')
        await p.wait_for_timeout(2500)
    await ge.shot('ge_8_12_briefing_output')
    await p.mouse.move(1150, 500, steps=12)
    await smooth_scroll(ge, 700, step=100, pause=130)
    await p.wait_for_timeout(1200)
    await ge.shot('ge_8_13_briefing_output_more')
    en = await p.evaluate(FIND_TEXT_JS, ['사용 설정', 200, 50, 0])
    if en:
        await click_xy(ge, en[0], '사용 설정')
        await p.wait_for_timeout(3000)
    await ge.shot('ge_8_15_enable_clicked')
    print(await ge.stop_recording('ge8c_test'), flush=True)


async def main(which):
    async with GE() as ge:
        for k, fn in (('a', clip_a), ('b', clip_b), ('c', clip_c)):
            if k in which:
                await fn(ge)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or ['a', 'b', 'c']))
