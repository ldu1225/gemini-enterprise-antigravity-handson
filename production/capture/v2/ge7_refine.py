# -*- coding: utf-8 -*-
"""GE v2 Lab 7 Part 2 — refine the 'Cymbal 사내 지원 데스크' chat agent in its node panel.

Parts (run in order, each one a separate recording under production/assets/recordings/):
  open      ge7e_open_edit         에이전트 페이지 → ⋮ → 수정 → 에이전트 노드 열기 (세부정보 패널)
  instr     ge7f_node_instructions 요청 사항에 답변 규칙 한 줄 추가
  model     ge7f2_model_menu       모델 목록(Gemini 4 Argon / 3.8 Flash / 3.5 Flash / 2.5 Pro) 확인
  know      ge7g_node_knowledge    커넥터(Google 검색) 제거 · 지식에 규정 PDF 업로드
  starter   ge7g2_starter_prompt   시작 질문 3번을 정산 마감일 날짜 계산 질문으로 바꾸기
  sub       ge7h_subagent          하위 에이전트 추가 → 이름·설명·요청 사항 · 커넥터 제거 → 화면에 맞추기
  preview   ge7i_preview_update    미리보기에서 새 시작 질문 테스트 → 업데이트
Usage: python3 production/capture/v2/ge7_refine.py [open|instr|model|know|starter|sub|preview]
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import APP_HOME, GE, ROOT, RECS  # noqa: E402
from helpers import FIND_TEXT_JS, DUMP_JS, click_xy  # noqa: E402

AGENT = "Cymbal 사내 지원 데스크"
AGENTS_URL = APP_HOME + "/r/agents?hl=ko"
URL_FILE = RECS / "ge7_agent_url.txt"
PDF = ROOT / "production" / "samples" / "v2" / "build" / "Cymbal_출장비_및_경비처리_규정_가상.pdf"
PDF_LEAVE = ROOT / "production" / "samples" / "v2" / "build" / "Cymbal_휴가_및_근무제도_규정_가상.pdf"
PDF_SEC = ROOT / "production" / "samples" / "v2" / "build" / "Cymbal_IT보안_및_생성형AI_가이드_가상.pdf"
RULE = "답변의 첫 줄에는 '결론:'으로 시작하는 한 줄 요약을 먼저 적어 주세요."
NEW_PROMPT = "10월 23일(금) 귀국 시 출장비 정산 마감일은 언제인가요?"
COMPOUND_PROMPT = "10월 23일(금) 귀국 시 출장비 정산 마감일은 언제이고, 귀국 다음 주 월요일 오전 반차를 쓰면 몇 시까지 출근해야 하나요?"
SUB_NAME = "정산 기한 계산 도우미"
SUB_DESC = "귀국일을 받아 출장비 정산 마감일(7영업일)을 계산합니다."
SUB_INSTR = (
    "사용자가 귀국일을 알려 주면, 귀국 다음 날부터 주말을 뺀 7영업일째 날을 정산 마감일로 계산하세요. "
    "날짜는 'M월 D일(요일)' 형식으로 쓰고, 기한을 넘기면 받는 조치(7·15·30영업일 초과)를 표로 함께 안내하세요."
)
SUB2_NAME = "휴가·근무제도 및 보안 상담 도우미"
SUB2_DESC = "연차·반차·반반차·경조사 휴가와 선택적 근로시간제 코어타임 및 생성형 AI 보안 규정을 안내합니다."
SUB2_INSTR = (
    "첨부된 「휴가 및 근무제도 규정」과 「IT 보안 및 생성형 AI 가이드」 문서를 근거로 장 번호와 함께 답변하세요. "
    "오전 반차(09:00~14:00, 0.5일 차감)·오후 반차(14:00~18:00)·반반차(2시간, 0.25일 차감), "
    "코어타임(10:00~15:00), 대외비·개인정보 AI 입력 금지 기준을 표로 정리하세요."
)
SCHED_PROMPT = "이번 주 귀국 예정자의 7영업일 출장비 정산 마감일 계산 기준과 반차·반반차 사용 시 코어타임 주의사항을 요약해 주세요."

PANEL_SCROLL_JS = r"""
(dy) => {
  function find(root) {
    for (const e of root.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      if (r.x > 960 && r.width > 380 && r.height > 300 && /(auto|scroll)/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 20) return e;
      if (e.shadowRoot) { const f = find(e.shadowRoot); if (f) return f; }
    }
    return null;
  }
  const el = find(document);
  if (!el) return null;
  el.scrollBy({top: dy, behavior: 'smooth'});
  return el.scrollTop;
}
"""

CARET_JS = r"""
(needle) => {
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if ((n.nodeValue || '').includes(needle)) return n;
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) { const f = scan(e.shadowRoot); if (f) return f; }
    return null;
  }
  let t = scan(document);
  if (!t) {
    // Fallback: pick first text node inside contenteditable in right panel (x > 960)
    function findEd(root) {
      for (const e of root.querySelectorAll('[contenteditable="true"], [aria-label="에이전트 요청 사항"]')) {
        const r = e.getBoundingClientRect();
        if (r.x > 950 && r.width > 200 && r.height > 40) return e;
      }
      for (const e of root.querySelectorAll('*')) if (e.shadowRoot) { const f = findEd(e.shadowRoot); if (f) return f; }
      return null;
    }
    const ed = findEd(document);
    if (!ed) return false;
    const tw = document.createTreeWalker(ed, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if ((n.nodeValue || '').trim().length > 10) { t = n; break; }
    }
    if (!t) return false;
  }
  const editable = t.parentElement.closest('[contenteditable="true"]');
  if (editable) editable.focus();
  const sel = t.getRootNode().getSelection ? t.getRootNode().getSelection() : window.getSelection();
  const range = document.createRange();
  range.setStart(t, t.nodeValue.length);
  range.collapse(true);
  (sel || window.getSelection()).removeAllRanges();
  (sel || window.getSelection()).addRange(range);
  const r = t.parentElement.getBoundingClientRect();
  return {x: r.x, y: r.y, w: r.width, h: r.height};
}
"""

PANEL_JS = r"""
() => {
  function find(root) {
    for (const e of root.querySelectorAll('[aria-label="에이전트 모델"], input[aria-label="에이전트 이름"]')) {
      const r = e.getBoundingClientRect();
      if (r.width > 50 && r.x > 900) return true;
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot && find(e.shadowRoot)) return true;
    return false;
  }
  return find(document);
}
"""

SET_SCROLL_JS = r"""
(top) => {
  function find(root) {
    for (const e of root.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      if (r.x > 960 && r.width > 380 && r.height > 300 && /(auto|scroll)/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 20) return e;
      if (e.shadowRoot) { const f = find(e.shadowRoot); if (f) return f; }
    }
    return null;
  }
  const el = find(document);
  if (!el) return null;
  if (top !== null) el.scrollTop = top;
  return el.scrollTop;
}
"""

CONTAINS_JS = r"""
([needle, minX]) => {
  const res = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeValue && n.nodeValue.includes(needle)) {
        const el = n.parentElement;
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 4 && r.height > 4 && r.x >= minX && r.y > 40 && r.y < 800)
          res.push({x: r.x, y: r.y, w: r.width, h: r.height, t: n.nodeValue.trim().slice(0, 80)});
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return res;
}
"""

DEEP_BLUR_JS = r"""
() => {
  let a = document.activeElement;
  while (a && a.shadowRoot && a.shadowRoot.activeElement) a = a.shadowRoot.activeElement;
  if (a && a.blur) a.blur();
  return a ? a.tagName : null;
}
"""


async def find_text(ge, text, minx=0, maxw=700, maxh=90, miny=40):
    hits = await ge.page.evaluate(FIND_TEXT_JS, [text, maxw, maxh, miny])
    return [h for h in hits if h["x"] >= minx]


async def click_text(ge, text, label, minx=0, wait=1200, maxw=700, maxh=90, miny=40, last=False):
    hits = await find_text(ge, text, minx, maxw, maxh, miny)
    if not hits:
        raise RuntimeError(f"text not found: {text}")
    await click_xy(ge, hits[-1] if last else hits[0], label)
    await ge.page.wait_for_timeout(wait)
    return hits[0]


async def scroll_panel(ge, dy, settle=900):
    await ge.page.evaluate(PANEL_SCROLL_JS, dy)
    await ge.page.wait_for_timeout(settle)


async def panel_open(ge):
    return bool(await ge.page.evaluate(PANEL_JS))


async def set_panel_scroll(ge, top):
    return await ge.page.evaluate(SET_SCROLL_JS, top)


async def panel_box(ge, selector, minx=900, timeout=15):
    loc = ge.page.locator(selector)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        for i in range(await loc.count()):
            try:
                b = await loc.nth(i).bounding_box()
            except Exception:
                b = None
            if b and b["width"] > 2 and b["height"] > 2 and b["x"] >= minx:
                return {"x": b["x"], "y": b["y"], "w": b["width"], "h": b["height"]}
        await ge.page.wait_for_timeout(250)
    raise RuntimeError(f"no visible panel element for {selector}")


async def open_node(ge, name=AGENT, label="에이전트 노드"):
    hits = [h for h in await find_text(ge, name, 480, 340, 70, 140) if h["x"] < 1100]
    if not hits:
        hits = [h for h in await ge.page.evaluate(CONTAINS_JS, ["사내 지원", 480]) if h["x"] < 1100 and h["w"] < 360]
    if not hits:
        raise RuntimeError(f"node {name} not found")
    await click_xy(ge, hits[0], label)
    await ge.page.wait_for_timeout(1600)


async def ensure_builder(ge):
    if "agent-builder" not in ge.page.url:
        if URL_FILE.exists():
            await ge.goto(URL_FILE.read_text().strip(), wait=5500)
        else:
            raise RuntimeError("not on the agent builder page: " + ge.page.url)
    await ge.install_cursor()


# ----------------------------------------------------------------------------- parts
async def part_open(ge):
    p = ge.page
    await ge.goto(AGENTS_URL, wait=4500)
    await ge.start_recording()
    await p.mouse.move(700, 420, steps=8)
    await p.wait_for_timeout(1000)
    for _ in range(3):
        await p.mouse.wheel(0, 80)
        await p.wait_for_timeout(120)
    await p.wait_for_timeout(800)
    try:
        menu = await ge.vis_label(f"{AGENT} 에이전트")
        await ge.click(menu, label="에이전트 메뉴")
    except Exception:
        # fallback: find kebab on Cymbal 사내 지원 데스크 card
        hits = await p.evaluate(CONTAINS_JS, ["사내 지원 데스크", 260])
        if hits:
            c = hits[0]
            items = await p.evaluate(DUMP_JS)
            kebabs = [i for i in items if i["x"] > c["x"] + 80 and abs(i["y"] - c["y"]) < 60 and i["w"] <= 48]
            if kebabs:
                k = kebabs[0]
                await click_xy(ge, {"x": k["x"], "y": k["y"], "w": k["w"], "h": k["h"]}, "에이전트 메뉴")
    await p.wait_for_timeout(900)
    await click_text(ge, "수정", "수정", wait=600, maxw=260, maxh=48)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 40:
        if "agent-builder" in p.url and await find_text(ge, "플로우", 800, 120, 40, 10):
            break
        await p.wait_for_timeout(500)
    await p.wait_for_timeout(2500)
    await ge.install_cursor()
    if "agent-builder" in p.url:
        URL_FILE.write_text(p.url)
    banner = p.locator('[aria-label="배너 닫기"]')
    if await banner.count():
        b = await banner.first.bounding_box()
        if b and b["width"] > 2:
            await ge.click(banner.first, label="배너 닫기")
            await p.wait_for_timeout(800)
    # Switch to 플로우 tab if not active
    fl = await find_text(ge, "플로우", 750, 120, 44, 10)
    if fl and not await find_text(ge, AGENT, 480, 340, 70, 140):
        await click_xy(ge, fl[0], "플로우 탭")
        await p.wait_for_timeout(1500)
    await open_node(ge)
    await p.wait_for_timeout(1500)
    await ge.shot("ge_7_20_node_panel")
    await p.mouse.move(1180, 520, steps=12)
    await p.wait_for_timeout(1500)
    out, n = await ge.stop_recording("ge7e_open_edit")
    print("saved", out, n, p.url)


async def part_instr(ge):
    p = ge.page
    await ensure_builder(ge)
    if not await panel_open(ge):
        await open_node(ge)
    await set_panel_scroll(ge, 0)
    await p.wait_for_timeout(600)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    box = await p.evaluate(CARET_JS, "답변해야 합니다.")
    if not box:
        box = await p.evaluate(CARET_JS, "근거로")
    if not box:
        raise RuntimeError("Role paragraph not found")
    await p.mouse.move(min(box["x"] + box["w"] - 8, 1380), box["y"] + box["h"] - 8, steps=18)
    await p.wait_for_timeout(300)
    ge.mark("click", label="요청 사항 끝", box={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]})
    await p.evaluate(CARET_JS, "답변해야 합니다.")
    await p.wait_for_timeout(500)
    await p.keyboard.press("Enter")
    ge.mark("type_start", label="규칙", chars=len(RULE))
    await p.keyboard.type(RULE, delay=38)
    ge.mark("type_end", label="규칙")
    await p.wait_for_timeout(1500)
    await ge.shot("ge_7_21_rule_added")
    out, n = await ge.stop_recording("ge7f_node_instructions")
    print("saved", out, n)


async def part_model(ge):
    p = ge.page
    await ensure_builder(ge)
    if not await panel_open(ge):
        await open_node(ge)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    sel = await ge.vis('[aria-label="에이전트 모델"]')
    b = await sel.bounding_box()
    if b["y"] > 640:
        await scroll_panel(ge, 300)
        sel = await ge.vis('[aria-label="에이전트 모델"]')
        b = await sel.bounding_box()
    await ge.click(sel, label="모델 선택")
    await p.wait_for_timeout(2000)
    await ge.shot("ge_7_22_model_menu")
    opts = await find_text(ge, "Gemini 3.8 Flash", 600, 700, 80, 60)
    picked = False
    for o in reversed(opts):
        if o["y"] > b["y"] - 400:
            await click_xy(ge, o, "Gemini 3.8 Flash 유지")
            picked = True
            break
    if not picked:
        await p.keyboard.press("Escape")
    await p.wait_for_timeout(1500)
    out, n = await ge.stop_recording("ge7f2_model_menu")
    print("saved", out, n)


async def pick_file(ge, box, label, path):
    from playwright.async_api import TimeoutError as PWTimeout
    p = ge.page
    try:
        async with p.expect_file_chooser(timeout=3000) as fc:
            await click_xy(ge, box, label)
        chooser = await fc.value
    except PWTimeout:
        return False
    await chooser.set_files(str(path))
    return True


async def part_know(ge):
    p = ge.page
    await ensure_builder(ge)
    if not await panel_open(ge):
        await open_node(ge)
        await p.wait_for_timeout(800)
    await set_panel_scroll(ge, 300)
    await p.mouse.move(1180, 520, steps=6)
    await p.wait_for_timeout(900)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    # 1) connector chip "Google 검색" → its 삭제 (x) button
    chip = await find_text(ge, "Google 검색", 960, 200, 40, 100)
    if not chip:
        await scroll_panel(ge, 250)
        chip = await find_text(ge, "Google 검색", 960, 200, 40, 100)
    if chip:
        c = chip[0]
        closes = [h for h in await find_text(ge, "close", 960, 40, 40, 100) if abs(h["y"] - c["y"]) < 14 and h["x"] > c["x"]]
        if closes:
            await p.mouse.move(c["x"] + 30, c["y"] + 8, steps=16)
            await p.wait_for_timeout(700)
            await click_xy(ge, closes[0], "Google 검색 제거")
            await p.wait_for_timeout(1600)
    # 2) knowledge: 파일 추가 (+) → upload the travel-policy PDF (or leave-policy PDF if travel already attached)
    b = await panel_box(ge, '[aria-label="파일 추가"]')
    if b["y"] > 700:
        await scroll_panel(ge, 160)
        b = await panel_box(ge, '[aria-label="파일 추가"]')
    already_has_travel = bool(await p.evaluate(CONTAINS_JS, ["출장비_및_경비처리", 960]))
    target_pdf = PDF_LEAVE if already_has_travel else PDF
    needle = "휴가_및_근무제도" if already_has_travel else "출장비_및_경비처리"
    ok = await pick_file(ge, b, "파일 추가", target_pdf)
    if not ok:
        await p.wait_for_timeout(900)
        await ge.shot("ge_7_23a_knowledge_menu")
        up = await find_text(ge, "파일 업로드", 500, 320, 60, 60)
        if not up:
            raise RuntimeError("knowledge menu: 파일 업로드 not found")
        if not await pick_file(ge, up[0], "파일 업로드", target_pdf):
            raise RuntimeError("file chooser did not open")
    ge.mark("upload", label="규정 PDF")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 90:
        if await p.evaluate(CONTAINS_JS, [needle, 960]):
            break
        await p.wait_for_timeout(600)
    await p.wait_for_timeout(2500)
    await ge.shot("ge_7_23_knowledge_added")
    out, n = await ge.stop_recording("ge7g_node_knowledge")
    print("saved", out, n)


async def starter_field(ge):
    ta = ge.page.locator('textarea[aria-label^="시작 프롬프트"]')
    n = await ta.count()
    for i in range(n):
        v = await ta.nth(i).input_value()
        if "정산" in v or "마감일" in v or "기한" in v:
            return ta.nth(i)
    return ta.nth(n - 1)


async def part_starter(ge):
    p = ge.page
    await ensure_builder(ge)
    cont = await find_text(ge, "계속 수정", 200, 200, 60, 100)
    if cont:
        await click_xy(ge, cont[0], "계속 수정")
        await p.wait_for_timeout(1000)
    fl = await find_text(ge, "플로우", 600, 120, 50, 10)
    if fl:
        await click_xy(ge, fl[0], "플로우 탭")
        await p.wait_for_timeout(1200)
    if not await panel_open(ge):
        await open_node(ge)
        await p.wait_for_timeout(800)
    await set_panel_scroll(ge, 100000)
    await p.wait_for_timeout(600)
    target = await starter_field(ge)
    await p.evaluate(DEEP_BLUR_JS)
    await p.mouse.move(1272, 607, steps=4)
    await p.wait_for_timeout(1200)
    await ge.start_recording()
    await p.wait_for_timeout(700)
    await ge.click(target, label="시작 질문 3")
    await p.keyboard.press("Meta+A")
    await p.wait_for_timeout(500)
    short_prompt = "10월 23일(금) 귀국 시 정산 마감일은 언제인가요?"
    ge.mark("type_start", label="시작 질문", chars=len(short_prompt))
    await p.keyboard.type(short_prompt, delay=40)
    ge.mark("type_end", label="시작 질문")
    await p.wait_for_timeout(800)
    await p.evaluate("""() => {
      for (const t of document.querySelectorAll('textarea')) t.scrollTop = 0;
    }""")
    await p.evaluate(DEEP_BLUR_JS)
    await p.wait_for_timeout(900)
    await ge.shot("ge_7_24_starter_prompt")
    await p.wait_for_timeout(600)
    out, n = await ge.stop_recording("ge7g2_starter_prompt")
    print("saved", out, n)


async def part_sub(ge):
    p = ge.page
    await ensure_builder(ge)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    # ⊕ on the bottom edge of the agent node = 하위 에이전트 추가
    plus = await find_text(ge, "add_circle", 500, 60, 60, 120)
    if not plus:
        raise RuntimeError("add_circle (하위 에이전트 추가) not found")
    await click_xy(ge, plus[0], "하위 에이전트 추가")
    await p.wait_for_timeout(2400)
    if not await panel_open(ge):
        raise RuntimeError("sub-agent panel did not open")
    await scroll_panel(ge, -3000, settle=1300)
    b = await panel_box(ge, '[aria-label="에이전트 이름"]')
    await click_xy(ge, b, "이름")
    await p.wait_for_timeout(300)
    await p.keyboard.press("Meta+A")
    ge.mark("type_start", label="이름", chars=len(SUB_NAME))
    await p.keyboard.type(SUB_NAME, delay=55)
    ge.mark("type_end", label="이름")
    await p.wait_for_timeout(600)
    b = await panel_box(ge, '[aria-label="에이전트 설명"]')
    await click_xy(ge, b, "설명")
    await p.wait_for_timeout(300)
    await p.keyboard.press("Meta+A")
    ge.mark("type_start", label="설명", chars=len(SUB_DESC))
    await p.keyboard.type(SUB_DESC, delay=38)
    ge.mark("type_end", label="설명")
    await p.wait_for_timeout(600)
    b = await panel_box(ge, '[aria-label="에이전트 요청 사항"]')
    if b["y"] + 60 > 760:
        await scroll_panel(ge, int(b["y"]) - 300, settle=1000)
        b = await panel_box(ge, '[aria-label="에이전트 요청 사항"]')
    await click_xy(ge, {"x": b["x"] + 20, "y": b["y"] + 14, "w": 200, "h": 30}, "요청 사항")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="요청 사항", chars=len(SUB_INSTR))
    await p.keyboard.type(SUB_INSTR, delay=16)
    ge.mark("type_end", label="요청 사항")
    await p.wait_for_timeout(1500)
    await ge.shot("ge_7_25_subagent_config")
    # remove the default web-search connector from sub-agent
    await scroll_panel(ge, 420, settle=1200)
    chip = await find_text(ge, "Google 검색", 960, 200, 40, 100)
    if chip:
        c = chip[0]
        closes = [h for h in await find_text(ge, "close", 960, 40, 40, 100) if abs(h["y"] - c["y"]) < 14 and h["x"] > c["x"]]
        if closes:
            await p.mouse.move(c["x"] + 30, c["y"] + 8, steps=14)
            await p.wait_for_timeout(500)
            await click_xy(ge, closes[0], "Google 검색 제거")
            await p.wait_for_timeout(1500)
    await ge.shot("ge_7_25b_subagent_connector")
    # close the panel (click empty canvas) and fit the canvas so both nodes are visible
    await click_xy(ge, {"x": 640, "y": 180, "w": 10, "h": 10}, "캔버스")
    await p.wait_for_timeout(1200)
    if await panel_open(ge):
        hits = [h for h in await find_text(ge, SUB_NAME, 500, 300, 60, 100) if h["x"] < 960]
        if hits:
            await click_xy(ge, hits[0], "하위 에이전트 노드")
            await p.wait_for_timeout(1200)
    fit = await panel_box(ge, '[aria-label="화면에 맞추기"]', minx=450)
    await click_xy(ge, fit, "화면에 맞추기")
    await p.wait_for_timeout(1800)
    await p.mouse.move(760, 560, steps=14)
    await p.wait_for_timeout(1200)
    await ge.shot("ge_7_26_two_nodes")
    await p.wait_for_timeout(1200)
    out, n = await ge.stop_recording("ge7h_subagent")
    print("saved", out, n)


async def close_panel_clean(ge):
    p = ge.page
    if not await panel_open(ge):
        return
    await set_panel_scroll(ge, 0)
    await p.wait_for_timeout(500)
    try:
        cb = await panel_box(ge, '[aria-label="패널 닫기"]', minx=960)
        await click_xy(ge, cb, "패널 닫기")
        await p.wait_for_timeout(1200)
    except Exception:
        pass


async def part_sub2(ge):
    p = ge.page
    await ensure_builder(ge)
    cont = await find_text(ge, "계속 수정", 300, 200, 60, 100)
    if cont:
        await click_xy(ge, cont[0], "계속 수정")
        await p.wait_for_timeout(1200)
    fl = await find_text(ge, "플로우", 600, 120, 50, 10)
    if fl:
        await click_xy(ge, fl[0], "플로우 탭")
        await p.wait_for_timeout(1200)
    await close_panel_clean(ge)
    fit = await panel_box(ge, '[aria-label="화면에 맞추기"]', minx=450)
    await click_xy(ge, fit, "화면에 맞추기")
    await p.wait_for_timeout(1000)

    await ge.start_recording()
    await p.wait_for_timeout(900)
    # 1) Click root agent node on canvas and ensure PDF_LEAVE is attached to 지식
    roots = await find_text(ge, AGENT, 500, 400, 50, 80)
    if roots:
        await click_xy(ge, roots[0], "메인 에이전트 노드 선택")
        await p.wait_for_timeout(1400)
    else:
        await open_node(ge)
        await p.wait_for_timeout(1400)

    await set_panel_scroll(ge, 420)
    await p.wait_for_timeout(800)
    if not await p.evaluate(CONTAINS_JS, ["휴가_및_근무제도", 960]):
        b = await panel_box(ge, '[aria-label="파일 추가"]')
        if b["y"] > 700:
            await scroll_panel(ge, 160)
            b = await panel_box(ge, '[aria-label="파일 추가"]')
        ok = await pick_file(ge, b, "다중 규정 파일 추가", PDF_LEAVE)
        if not ok:
            await p.wait_for_timeout(900)
            up = await find_text(ge, "파일 업로드", 500, 320, 60, 60)
            if not up:
                raise RuntimeError("knowledge menu: 파일 업로드 not found")
            if not await pick_file(ge, up[0], "파일 업로드", PDF_LEAVE):
                raise RuntimeError("file chooser did not open")
        ge.mark("upload", label="휴가 및 근무제도 규정 PDF")
        t0 = time.monotonic()
        while time.monotonic() - t0 < 90:
            if await p.evaluate(CONTAINS_JS, ["휴가_및_근무제도", 960]):
                break
            await p.wait_for_timeout(600)
        await p.wait_for_timeout(1800)
    await ge.shot("ge_7_26b_subagent2_knowledge")

    # 2) Click add_circle on root agent to create 2nd parallel Sub-agent
    pluses = await find_text(ge, "add_circle", 500, 60, 60, 120)
    if pluses:
        pluses.sort(key=lambda h: h["y"])
        ac = pluses[0]
        await p.mouse.move(ac["x"] + ac["w"] / 2, ac["y"] + ac["h"] / 2, steps=16)
        await p.wait_for_timeout(400)
        ge.mark("click", label="2번째 하위 에이전트 추가", box={"x": ac["x"], "y": ac["y"], "width": ac["w"], "height": ac["h"]})
    clicked = await p.evaluate("""() => {
      function scan(root) {
        const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = tw.nextNode())) {
          if ((n.nodeValue || '').trim() === 'add_circle' && n.parentElement) {
            const btn = n.parentElement.closest('button, [role=button]') || n.parentElement;
            btn.click();
            return true;
          }
        }
        for (const e of root.querySelectorAll('*')) if (e.shadowRoot) {
          if (scan(e.shadowRoot)) return true;
        }
        return false;
      }
      return scan(document);
    }""")
    if not clicked:
        raise RuntimeError("add_circle button click failed")
    await p.wait_for_timeout(2400)
    await set_panel_scroll(ge, 0)
    await p.wait_for_timeout(600)
    b = await panel_box(ge, '[aria-label="에이전트 이름"]')
    await click_xy(ge, b, "하위 에이전트 2 이름")
    await p.wait_for_timeout(300)
    await p.keyboard.press("Meta+A")
    ge.mark("type_start", label="이름", chars=len(SUB2_NAME))
    await p.keyboard.type(SUB2_NAME, delay=50)
    ge.mark("type_end", label="이름")
    await p.wait_for_timeout(600)

    b = await panel_box(ge, '[aria-label="에이전트 설명"]')
    await click_xy(ge, b, "하위 에이전트 2 설명")
    await p.wait_for_timeout(300)
    await p.keyboard.press("Meta+A")
    ge.mark("type_start", label="설명", chars=len(SUB2_DESC))
    await p.keyboard.type(SUB2_DESC, delay=35)
    ge.mark("type_end", label="설명")
    await p.wait_for_timeout(600)

    b = await panel_box(ge, '[aria-label="에이전트 요청 사항"]')
    if b["y"] + 60 > 760:
        await scroll_panel(ge, int(b["y"]) - 300, settle=1000)
        b = await panel_box(ge, '[aria-label="에이전트 요청 사항"]')
    await click_xy(ge, {"x": b["x"] + 20, "y": b["y"] + 14, "w": 200, "h": 30}, "하위 에이전트 2 요청 사항")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="요청 사항", chars=len(SUB2_INSTR))
    await p.keyboard.type(SUB2_INSTR, delay=14)
    ge.mark("type_end", label="요청 사항")
    await p.wait_for_timeout(1200)

    # Scroll down to 커넥터
    await scroll_panel(ge, 460, settle=1200)
    chip = await find_text(ge, "Google 검색", 960, 200, 40, 100)
    if chip:
        c = chip[0]
        closes = [h for h in await find_text(ge, "close", 960, 40, 40, 100) if abs(h["y"] - c["y"]) < 14 and h["x"] > c["x"]]
        if closes:
            await p.mouse.move(c["x"] + 30, c["y"] + 8, steps=14)
            await p.wait_for_timeout(500)
            await click_xy(ge, closes[0], "Google 검색 제거")
            await p.wait_for_timeout(1200)

    # Open + 커넥터 추가 modal to showcase enterprise connector binding
    conn_btn = await panel_box(ge, '[aria-label="커넥터 추가"]')
    await click_xy(ge, conn_btn, "커넥터 추가 모달 열기")
    await p.wait_for_timeout(1800)
    await ge.shot("ge_7_26a_connector_modal")
    await p.keyboard.press("Escape")
    await p.wait_for_timeout(1200)

    # Close panel via 패널 닫기 and fit 3-node multi-agent hierarchy on canvas
    await close_panel_clean(ge)
    fit = await panel_box(ge, '[aria-label="화면에 맞추기"]', minx=450)
    await click_xy(ge, fit, "화면에 맞추기")
    await p.wait_for_timeout(1800)
    await p.mouse.move(760, 560, steps=14)
    await p.wait_for_timeout(1200)
    await ge.shot("ge_7_26c_three_nodes")
    out, n = await ge.stop_recording("ge7h2_subagent2")
    print("saved", out, n)


async def part_schedule(ge):
    p = ge.page
    await ensure_builder(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    # Click top 일정 tab
    await click_text(ge, "일정", "일정 탭", minx=880, maxw=120, maxh=50, miny=10, wait=2200)
    await ge.shot("ge_7_26d_schedule_tab")
    # Click 일정 추가
    add_btn = await find_text(ge, "일정 추가", 700, 200, 60, 180)
    if add_btn:
        await click_xy(ge, add_btn[0], "일정 추가")
        await p.wait_for_timeout(1800)
    # Click 매주 frequency chip
    weekly = await find_text(ge, "매주", 500, 120, 50, 120)
    if weekly:
        await click_xy(ge, weekly[0], "반복 빈도: 매주")
        await p.wait_for_timeout(900)
    # Type into 트리거 프롬프트 textarea
    ta = p.locator('textarea[aria-label="트리거 프롬프트"]')
    if await ta.count():
        await ge.click(ta.first, label="트리거 프롬프트")
        await p.wait_for_timeout(400)
        ge.mark("type_start", label="트리거 프롬프트", chars=len(SCHED_PROMPT))
        await p.keyboard.type(SCHED_PROMPT, delay=22)
        ge.mark("type_end", label="트리거 프롬프트")
        await p.wait_for_timeout(1500)
    await ge.shot("ge_7_26e_schedule_form")
    # Click 취소 to return cleanly without leaving an active cron spam
    cancel_btn = await find_text(ge, "취소", 480, 140, 50, 480)
    if cancel_btn:
        await click_xy(ge, cancel_btn[0], "취소")
        await p.wait_for_timeout(1200)
    # Switch back to 플로우 tab briefly
    await click_text(ge, "플로우", "플로우 탭", minx=780, maxw=120, maxh=50, miny=10, wait=1500)
    out, n = await ge.stop_recording("ge7h3_schedule")
    print("saved", out, n)


async def preview_input(ge):
    loc = ge.page.locator('[contenteditable="true"]')
    best = None
    for i in range(await loc.count()):
        b = await loc.nth(i).bounding_box()
        if b and b["width"] > 50 and b["x"] > 560 and b["y"] > 300:
            best = loc.nth(i)
    return best


async def part_preview(ge):
    p = ge.page
    await ensure_builder(ge)
    await p.mouse.move(1180, 400, steps=4)
    await p.wait_for_timeout(500)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await click_text(ge, "미리보기", "미리보기 탭", minx=850, maxw=160, maxh=50, miny=10, wait=2800)
    # Only click reset if a reset/new chat button is present (never click 공유)
    items = await p.evaluate(DUMP_JS)
    reset = [
        i for i in items
        if 600 < i["x"] < 1340 and i["y"] < 80 and i["w"] <= 48
        and ("초기화" in (i["al"] or "") or "새" in (i["al"] or "") or "재설정" in (i["al"] or "") or "refresh" in (i["txt"] or ""))
    ]
    if reset:
        r = reset[0]
        await click_xy(ge, {"x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"]}, "미리보기 초기화")
        await p.wait_for_timeout(2500)
    box = await preview_input(ge)
    await ge.click(box, label="미리보기 입력창")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="멀티 에이전트 복합 질문", chars=len(COMPOUND_PROMPT))
    await p.keyboard.type(COMPOUND_PROMPT, delay=24)
    ge.mark("type_end", label="멀티 에이전트 복합 질문")
    await p.wait_for_timeout(500)
    await p.keyboard.press("Enter")
    ge.mark("submit", label="멀티 에이전트 복합 질문")
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=240, stable=5.0, label="preview")
    await ge.set_rate(1)
    await p.wait_for_timeout(1500)
    await ge.shot("ge_7_27_preview_answer")
    ok = bool(await p.evaluate(CONTAINS_JS, ["11월 3일", 520]))
    concl = bool(await p.evaluate(CONTAINS_JS, ["결론", 520]))
    half = bool(await p.evaluate(CONTAINS_JS, ["반차", 520])) or bool(await p.evaluate(CONTAINS_JS, ["14:00", 520])) or bool(await p.evaluate(CONTAINS_JS, ["오후", 520]))
    print("answer has 11월 3일:", ok, "| 결론:", concl, "| 반차:", half, flush=True)
    await p.mouse.move(980, 420, steps=10)
    for _ in range(4):
        await p.mouse.wheel(0, 120)
        await p.wait_for_timeout(250)
    await p.wait_for_timeout(1800)
    await ge.shot("ge_7_28_preview_answer_more")
    await click_text(ge, "업데이트", "업데이트", minx=1200, maxw=160, maxh=60, miny=10, wait=2200)
    await ge.shot("ge_7_29a_update_dialog")
    for word in ("업데이트", "확인", "게시"):
        btns = [h for h in await find_text(ge, word, 300, 200, 50, 100) if h["y"] > 150]
        if btns:
            await click_xy(ge, btns[-1], "업데이트 확인")
            await p.wait_for_timeout(3000)
            break
    await ge.shot("ge_7_29_updated")
    await p.wait_for_timeout(2000)
    out, n = await ge.stop_recording("ge7i_preview_update")
    print("saved", out, n, p.url)


PARTS = {
    "open": part_open,
    "instr": part_instr,
    "model": part_model,
    "know": part_know,
    "starter": part_starter,
    "sub": part_sub,
    "sub2": part_sub2,
    "schedule": part_schedule,
    "preview": part_preview,
}


async def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(PARTS)
    async with GE() as ge:
        for n in names:
            print("== part", n, flush=True)
            await PARTS[n](ge)


if __name__ == "__main__":
    asyncio.run(main())
