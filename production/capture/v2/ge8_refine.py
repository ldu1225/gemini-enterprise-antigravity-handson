# -*- coding: utf-8 -*-
"""GE v2 Lab 8 Part 2 — refine the 'Cymbal 고객 문의 일일 브리핑 및 답변 초안' workflow node by node.

Parts (run in order; each is a separate recording under production/assets/recordings/):
  enable    ge8c2_enable       사용 설정 → 권한 승인 → 워크플로 사용 설정(버전 1 게시)
  trigger   ge8d_trigger       에이전트 목록 → ⋮ → 수정 → 트리거 노드: 트리거 유형 확인 · 시작 시간 08:30 변경
  step      ge8e_step          1단계 분류 에이전트 노드: 요청 사항 한 줄 추가 · 연결된 앱 · 더보기(모델 Gemini 3.8 Flash · 출력 형식)
  approval  ge8f_approval      마지막 ＋ → 인간 참여형 → 승인 노드 추가 → 검토 메시지 + 브리핑 output 변수 삽입
  branch    ge8g_branch        '승인됨' 갈래 ＋ → Gemini Agent → CS팀 공지 3줄 요약 요청 사항 + 변수 삽입 → 이름 바꾸기('CS팀 공지 요약 에이전트')
  test      ge8h_test_approval 테스트 탭 → 재설정 → 테스트 실행 시작 → 승인 요청에 [승인] → 최종 요약 결과 확인
  update    ge8i_update        수정 탭 → 업데이트 → 새 버전(버전 2) 게시
Usage: python3 production/capture/v2/ge8_refine.py [enable|trigger|step|approval|branch|test|update]
"""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import APP_HOME, GE, RECS, SHOTS  # noqa: E402
from helpers import DUMP_JS, FIND_TEXT_JS, click_xy  # noqa: E402

WF_NAME = "Cymbal 고객 문의 일일 브리핑 및 답변 초안"
AGENTS_URL = APP_HOME + "/r/agents?hl=ko"
URL_FILE = RECS / "ge8_workflow_url.txt"
STEP1_SUB = "Classify Inquiries"
BRIEF_SUB = "Generate CS Daily Briefing"
STEP_ADD = "특히 영유아·반려동물 가구의 야간 저소음 모드 문의와 Wi-Fi 초기 페어링 실패 사례를 우선 분류하세요."
APPROVAL_MSG = "오늘의 Cymbal 고객 문의 일일 브리핑 및 표준 답변 초안입니다. 내용을 확인하고 CS팀 공지를 승인해 주세요."
BRANCH_INSTR = "승인된 일일 브리핑과 표준 답변 초안을 CS 상담원 전체 공지 채널에 바로 올릴 수 있도록, 핵심 요약 3줄과 오늘의 응대 주의사항 1개로 짧게 정리해 주세요."
BRANCH_NAME = "CS팀 공지 요약 에이전트"
REJECT_INSTR = "승인권자가 일일 브리핑 초안을 반려했습니다. 반려 코멘트를 반영해 긴급도 분류 근거와 표준 답변 톤앤매너를 보완한 재검토용 브리핑 수정본을 작성해 주세요."
REJECT_NAME = "반려 보완 초안 에이전트"
PDF_AIRPOLE = Path(__file__).resolve().parents[2] / "samples" / "v2" / "build" / "Cymbal_신제품_브리프_에어폴_프로_가상.pdf"
PROG = SHOTS / "_ge8_progress"

CONTAINS_JS = r"""
([needle, minX, maxX]) => {
  const res = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeValue && n.nodeValue.includes(needle)) {
        const el = n.parentElement;
        if (!el) continue;
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        if (r.width > 4 && r.height > 4 && r.x >= minX && r.x <= maxX && r.y > 40 && r.y < 800 && cs.visibility !== 'hidden')
          res.push({x: r.x, y: r.y, w: r.width, h: r.height, t: n.nodeValue.trim().slice(0, 80)});
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return res;
}
"""

VIS_TEXT_JS = r"""
([needle, minX, maxW, maxH, minY]) => {
  if (minY === undefined || minY === null) minY = 40;
  const res = [];
  function hidden(el) {
    for (let e = el; e; e = e.parentElement || (e.getRootNode && e.getRootNode().host)) {
      const cs = getComputedStyle(e);
      if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) return true;
      if (e === document.documentElement) break;
    }
    return false;
  }
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeValue && n.nodeValue.trim() === needle) {
        const el = n.parentElement;
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 4 && r.height > 4 && r.width <= maxW && r.height <= maxH && r.x >= minX && r.y > minY && r.y < 800 && !hidden(el))
          res.push({x: r.x, y: r.y, w: r.width, h: r.height});
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return res;
}
"""

PANEL_SCROLL_JS = r"""
(dy) => {
  function find(root) {
    for (const e of root.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      if (r.x > 1000 && r.width > 300 && r.height > 600 && /(auto|scroll)/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 20) return e;
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
    while ((n = tw.nextNode())) if ((n.nodeValue || '').includes(needle)) return n;
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) { const f = scan(e.shadowRoot); if (f) return f; }
    return null;
  }
  let t = scan(document);
  if (!t) {
    function findEd(root) {
      for (const e of root.querySelectorAll('[contenteditable="true"]')) {
        const r = e.getBoundingClientRect();
        if (r.x > 1000 && r.width > 200 && r.height > 20) return e;
      }
      for (const e of root.querySelectorAll('*')) if (e.shadowRoot) { const f = findEd(e.shadowRoot); if (f) return f; }
      return null;
    }
    const ed = findEd(document);
    if (!ed) return false;
    const tw = document.createTreeWalker(ed, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if ((n.nodeValue || '').trim().length > 8) { t = n; break; }
    }
    if (!t) return false;
  }
  const editable = t.parentElement.closest('[contenteditable="true"]');
  if (editable) editable.focus();
  const root = t.getRootNode();
  const sel = (root.getSelection && root.getSelection()) || window.getSelection();
  const range = document.createRange();
  range.setStart(t, t.nodeValue.length);
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
  const r = t.parentElement.getBoundingClientRect();
  return {x: r.x, y: r.y, w: r.width, h: r.height};
}
"""

ICON_JS = r"""
(name) => {
  const res = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeValue && n.nodeValue.trim() === name) {
        const el = n.parentElement; const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        if (r.width > 0) res.push({x: r.x, y: r.y, w: r.width, h: r.height, vis: cs.visibility});
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return res;
}
"""

HIT_JS = r"""
([x, y, needle]) => {
  let el = document.elementFromPoint(x, y);
  while (el && el.shadowRoot) {
    const inner = el.shadowRoot.elementFromPoint(x, y);
    if (!inner || inner === el) break;
    el = inner;
  }
  for (let e = el, i = 0; e && i < 5; i++, e = e.parentElement || (e.getRootNode && e.getRootNode().host)) {
    const t = e.textContent || '';
    if (t.includes(needle) && t.length < needle.length + 160) return true;
  }
  return false;
}
"""

EDITOR_JS = r"""
() => {
  function deepAt(x, y) {
    let el = document.elementFromPoint(x, y);
    while (el && el.shadowRoot) { const i = el.shadowRoot.elementFromPoint(x, y); if (!i || i === el) break; el = i; }
    return el;
  }
  const out = [];
  function walk(root) {
    for (const e of root.querySelectorAll('[contenteditable="true"]')) {
      const r = e.getBoundingClientRect();
      if (r.x < 1040 || r.width < 200 || r.height < 16 || r.y < 60 || r.y > 760) continue;
      const hit = deepAt(r.x + Math.min(40, r.width / 2), r.y + Math.min(12, r.height / 2));
      if (hit && (hit === e || e.contains(hit))) out.push({x: r.x, y: r.y, w: r.width, h: r.height});
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) walk(e.shadowRoot);
  }
  walk(document);
  return out;
}
"""


async def vtext(ge, text, minx=0, maxw=700, maxh=90, hit=True, miny=40):
    hits = await ge.page.evaluate(VIS_TEXT_JS, [text, minx, maxw, maxh, miny])
    if not hit:
        return hits
    out = []
    for h in hits:
        if await ge.page.evaluate(HIT_JS, [h["x"] + h["w"] / 2, h["y"] + h["h"] / 2, text]):
            out.append(h)
    return out


async def click_vtext(ge, text, label, minx=0, maxw=700, maxh=90, wait=1200, last=False, miny=40):
    hits = await vtext(ge, text, minx, maxw, maxh, miny=miny)
    if not hits:
        raise RuntimeError(f"visible text not found: {text}")
    await click_xy(ge, hits[-1] if last else hits[0], label)
    await ge.page.wait_for_timeout(wait)
    return hits[-1] if last else hits[0]


async def label_box(ge, label, minx=0, maxx=1440, timeout=12):
    loc = ge.page.locator(f'[aria-label="{label}"]')
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        for i in range(await loc.count()):
            try:
                b = await loc.nth(i).bounding_box()
            except Exception:
                b = None
            if b and b["width"] > 2 and b["height"] > 2 and minx <= b["x"] <= maxx and 0 < b["y"] < 800:
                return {"x": b["x"], "y": b["y"], "w": b["width"], "h": b["height"]}
        await ge.page.wait_for_timeout(250)
    raise RuntimeError(f"no visible element with aria-label {label}")


async def scroll_panel(ge, dy, settle=900):
    await ge.page.evaluate(PANEL_SCROLL_JS, dy)
    await ge.page.wait_for_timeout(settle)


async def ensure_builder(ge):
    if "agent-flow-builder" not in ge.page.url:
        if URL_FILE.exists():
            await ge.goto(URL_FILE.read_text().strip(), wait=5500, sidebar=False)
        else:
            raise RuntimeError("not on the workflow builder: " + ge.page.url)
    await ge.install_cursor()


async def node_box(ge, sub):
    hits = await ge.page.evaluate(CONTAINS_JS, [sub, 470, 1030])
    if not hits:
        raise RuntimeError(f"node not found: {sub}")
    return hits[0]


async def deselect(ge):
    await ge.page.mouse.click(600, 760)
    await ge.page.wait_for_timeout(900)


async def menu_item(ge, text, minx=0):
    for it in await ge.page.evaluate(DUMP_JS):
        if it["role"] in ("menuitem", "option") and text in it["txt"] and it["x"] >= minx:
            return {"x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"]}
    return None


# ----------------------------------------------------------------------------- parts
async def part_enable(ge):
    """Complete Version 1 enablement (consent + enable dialog) so subsequent edits become Version 2 update."""
    p = ge.page
    await ensure_builder(ge)
    await ge.start_recording()
    await p.wait_for_timeout(700)
    # Check if consent dialog is already open or if we need to click 사용 설정
    consent_btn = await vtext(ge, "승인", 300, 200, 60, hit=False)
    if not consent_btn:
        en_btn = await vtext(ge, "사용 설정", 1150, 200, 50, miny=0, hit=False)
        if en_btn:
            await click_xy(ge, en_btn[0], "사용 설정")
            await p.wait_for_timeout(2200)
            consent_btn = await vtext(ge, "승인", 300, 200, 60, hit=False)
    if consent_btn:
        await click_xy(ge, consent_btn[-1], "승인")
        await p.wait_for_timeout(2500)
        # Click 사용 설정 again if needed to open the 워크플로 사용 설정 modal
        en_dialogs = [h for h in await vtext(ge, "사용 설정", 300, 220, 60, hit=False) if h["y"] > 150]
        if not en_dialogs:
            en_top = await vtext(ge, "사용 설정", 1150, 200, 50, miny=0, hit=False)
            if en_top:
                await click_xy(ge, en_top[0], "사용 설정")
                await p.wait_for_timeout(2200)
    await ge.shot("ge_8_16_enable_dialog")
    en_confirm = [h for h in await vtext(ge, "사용 설정", 300, 220, 60, hit=False) if h["y"] > 150]
    if en_confirm:
        await click_xy(ge, en_confirm[-1], "사용 설정(확인)")
        await p.wait_for_timeout(3500)
    await ge.shot("ge_8_17_enabled")
    out, n = await ge.stop_recording("ge8c2_enable")
    print("saved", out, n, flush=True)


async def part_trigger(ge):
    p = ge.page
    await ge.goto(AGENTS_URL, wait=4500)
    await ge.start_recording()
    await p.mouse.move(760, 420, steps=8)
    await p.wait_for_timeout(1000)
    for _ in range(3):
        await p.mouse.wheel(0, 80)
        await p.wait_for_timeout(120)
    await p.wait_for_timeout(800)
    try:
        kebab = await ge.vis_label(f"{WF_NAME} 에이전트")
        await ge.click(kebab, label="워크플로 메뉴")
    except Exception:
        hits = await p.evaluate(CONTAINS_JS, ["고객 문의 일일 브리핑", 260, 1400])
        if hits:
            c = hits[0]
            items = await p.evaluate(DUMP_JS)
            kebabs = [i for i in items if i["x"] > c["x"] + 80 and abs(i["y"] - c["y"]) < 60 and i["w"] <= 48]
            if kebabs:
                k = kebabs[0]
                await click_xy(ge, {"x": k["x"], "y": k["y"], "w": k["w"], "h": k["h"]}, "워크플로 메뉴")
    await p.wait_for_timeout(900)
    await click_vtext(ge, "수정", "수정", maxw=260, maxh=48, wait=600)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 45:
        if "agent-flow-builder" in p.url and (
            await p.evaluate(CONTAINS_JS, ["Daily at", 470, 1030])
            or await p.evaluate(CONTAINS_JS, ["AM", 470, 1030])
        ):
            break
        await p.wait_for_timeout(500)
    await p.wait_for_timeout(2500)
    await ge.install_cursor()
    if "agent-flow-builder" in p.url:
        URL_FILE.write_text(p.url)

    # Click trigger node
    trig = await p.evaluate(CONTAINS_JS, ["AM", 470, 1030])
    if not trig:
        trig = await p.evaluate(CONTAINS_JS, ["Trigger", 470, 1030])
    await click_xy(ge, trig[0], "트리거 노드")
    await p.wait_for_timeout(1800)

    # Show trigger types accordion
    hdr = await p.evaluate(CONTAINS_JS, ["트리거:", 1040, 1440])
    if hdr:
        await click_xy(ge, hdr[0], "트리거 유형")
        await p.wait_for_timeout(2200)
        await ge.shot("ge_8_20_trigger_types")
        # Re-open schedule accordion
        sched = [h for h in await p.evaluate(CONTAINS_JS, ["Trigger", 1040, 1440]) if h["y"] > 140]
        if sched:
            await click_xy(ge, sched[-1], "일정 설정")
            await p.wait_for_timeout(1600)

    # Change start time 09:00 → 08:30
    tb = await label_box(ge, "시작 시간", 1040)
    await click_xy(ge, {"x": tb["x"] + 2, "y": tb["y"], "w": 16, "h": tb["h"]}, "시작 시간")
    await p.wait_for_timeout(400)
    ge.mark("type_start", label="시작 시간", chars=4)
    await p.keyboard.type("0830", delay=160)
    ge.mark("type_end", label="시작 시간")
    await p.wait_for_timeout(500)
    await p.keyboard.press("Tab")
    await p.wait_for_timeout(1500)
    try:
        tz = await label_box(ge, "시간대", 1040, timeout=4)
        await p.mouse.move(tz["x"] + tz["w"] / 2, tz["y"] + tz["h"] / 2, steps=14)
    except Exception:
        await p.mouse.move(1200, 480, steps=14)
    await p.wait_for_timeout(1500)
    await ge.shot("ge_8_21_trigger_edited")
    await p.mouse.move(800, 300, steps=12)
    await p.wait_for_timeout(1200)
    out, n = await ge.stop_recording("ge8d_trigger")
    print("saved", out, n, p.url, flush=True)


async def part_step(ge):
    p = ge.page
    await ensure_builder(ge)
    await deselect(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await click_xy(ge, await node_box(ge, STEP1_SUB), "1단계 분류 에이전트")
    await p.wait_for_timeout(2000)

    # 1) 요청 사항: add one line after first paragraph
    if not await p.evaluate(CONTAINS_JS, ["분류하세요", 1040, 1440]):
        try:
            await click_xy(ge, await label_box(ge, "요청 사항", 1040, timeout=5), "요청 사항 펼치기")
            await p.wait_for_timeout(1000)
        except Exception:
            pass
    box = await p.evaluate(CARET_JS, "분류하세요.")
    if not box:
        box = await p.evaluate(CARET_JS, "AirPole Pro")
    if not box:
        raise RuntimeError("first paragraph not found in step 1")
    await p.mouse.move(min(box["x"] + box["w"] - 10, 1390), box["y"] + box["h"] - 8, steps=16)
    await p.wait_for_timeout(300)
    ge.mark("click", label="요청 사항 끝", box={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]})
    await p.evaluate(CARET_JS, "분류하세요.")
    await p.wait_for_timeout(400)
    await p.keyboard.press("Enter")
    ge.mark("type_start", label="요청 사항 추가", chars=len(STEP_ADD))
    await p.keyboard.type(STEP_ADD, delay=34)
    ge.mark("type_end", label="요청 사항 추가")
    await p.wait_for_timeout(1500)
    await ge.shot("ge_8_22_step_instruction")

    # 2) 연결된 앱 펼치기
    try:
        app_b = await label_box(ge, "연결된 앱 펼치기", 1040, timeout=6)
        await click_xy(ge, app_b, "연결된 앱 펼치기")
        await p.wait_for_timeout(1600)
    except Exception:
        apps_txt = await p.evaluate(CONTAINS_JS, ["연결된 앱", 1040, 1440])
        if apps_txt:
            await click_xy(ge, apps_txt[0], "연결된 앱 펼치기")
            await p.wait_for_timeout(1600)
    await ge.shot("ge_8_23_step_apps")

    # 3) 더보기 → 모델 선택 / 출력 형식 선택
    more = await label_box(ge, "더보기", 1040)
    if more["y"] > 640:
        await scroll_panel(ge, int(more["y"]) - 360, settle=1100)
        more = await label_box(ge, "더보기", 1040)
    await click_xy(ge, more, "더보기")
    await p.wait_for_timeout(1500)
    mb = await label_box(ge, "모델 선택", 1040)
    if mb["y"] > 640:
        await scroll_panel(ge, int(mb["y"]) - 420, settle=1100)
        mb = await label_box(ge, "모델 선택", 1040)
    await click_xy(ge, mb, "모델 선택")
    await p.wait_for_timeout(1500)
    await ge.shot("ge_8_24_step_models")
    opt = await vtext(ge, "Gemini 3.8 Flash", 900, 400, 50)
    if not opt:
        opt = [h for h in await p.evaluate(CONTAINS_JS, ["3.8 Flash", 900, 1440])]
    if opt:
        await click_xy(ge, opt[-1], "Gemini 3.8 Flash")
    else:
        await p.keyboard.press("Escape")
    await p.wait_for_timeout(1500)
    ob = await label_box(ge, "출력 형식 선택", 1040)
    await click_xy(ge, ob, "출력 형식 선택")
    await p.wait_for_timeout(1600)
    await ge.shot("ge_8_25_step_output")
    plain = await vtext(ge, "일반 텍스트", 900, 300, 50)
    if len(plain) > 1:
        await click_xy(ge, plain[-1], "일반 텍스트 유지")
    else:
        await p.keyboard.press("Escape")
    await p.wait_for_timeout(1600)
    await ge.shot("ge_8_26_step_done")
    out, n = await ge.stop_recording("ge8e_step")
    print("saved", out, n, flush=True)


async def end_plus(ge):
    icons = [h for h in await ge.page.evaluate(ICON_JS, "add_2") if 480 < h["x"] < 1030 and h["vis"] != "hidden"]
    icons.sort(key=lambda h: h["y"])
    return icons[-1] if icons else None


async def part_approval(ge):
    p = ge.page
    await ensure_builder(ge)
    await deselect(ge)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    plus = await end_plus(ge)
    if not plus:
        raise RuntimeError("end + not found")
    await click_xy(ge, plus, "단계 추가")
    await p.wait_for_timeout(1600)
    await ge.shot("ge_8_27_add_panel")
    await click_vtext(ge, "인간 참여형(Human In The Loop)", "인간 참여형", minx=1040, maxw=400, maxh=40, wait=1200)
    appr = [h for h in await p.evaluate(ICON_JS, "person_raised_hand") if h["x"] > 1040 and h["vis"] != "hidden"]
    if not appr:
        raise RuntimeError("승인 item not found")
    await click_xy(ge, {"x": appr[0]["x"], "y": appr[0]["y"], "w": 80, "h": appr[0]["h"]}, "승인")
    await p.wait_for_timeout(2200)

    ph = await p.evaluate(CONTAINS_JS, ["검토자를 위한 메시지 추가", 1040, 1440])
    if not ph:
        raise RuntimeError("approval message editor not found")
    await click_xy(ge, {"x": ph[0]["x"], "y": ph[0]["y"], "w": 120, "h": ph[0]["h"]}, "메시지")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="메시지", chars=len(APPROVAL_MSG))
    await p.keyboard.type(APPROVAL_MSG, delay=28)
    ge.mark("type_end", label="메시지")
    await p.keyboard.press("Enter")
    await p.wait_for_timeout(600)
    await click_xy(ge, await label_box(ge, "변수 삽입", 1040), "변수 삽입")
    await p.wait_for_timeout(1500)
    await ge.shot("ge_8_28_variable_menu")
    var = await p.evaluate(CONTAINS_JS, [": output", 900, 1440])
    if not var:
        var = await p.evaluate(CONTAINS_JS, [BRIEF_SUB, 900, 1440])
    if not var:
        raise RuntimeError("briefing output variable not found")
    await click_xy(ge, var[-1], "브리핑 결과 변수")
    await p.wait_for_timeout(1200)
    doc = await p.evaluate(CONTAINS_JS, ["daily_briefing_document", 900, 1440])
    if doc:
        await click_xy(ge, doc[-1], "daily_briefing_document")
        await p.wait_for_timeout(1500)
    else:
        await p.wait_for_timeout(600)
    await ge.shot("ge_8_29_approval_message")
    out, n = await ge.stop_recording("ge8f_approval")
    print("saved", out, n, flush=True)


async def part_branch(ge):
    p = ge.page
    await ensure_builder(ge)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    lab = [h for h in await p.evaluate(CONTAINS_JS, ["승인됨", 470, 1030])]
    icons = [h for h in await p.evaluate(ICON_JS, "add_2") if 470 < h["x"] < 1030 and h["vis"] != "hidden"]
    if not lab:
        raise RuntimeError("승인됨 label not found")
    L = min(lab, key=lambda h: h["x"])
    below = [h for h in icons if h["y"] > L["y"] and abs((h["x"] + h["w"] / 2) - (L["x"] + L["w"] / 2)) < 60]
    below.sort(key=lambda h: h["y"])
    await click_xy(ge, below[-1], "승인됨 단계 추가")
    await p.wait_for_timeout(1600)
    await click_vtext(ge, "Gemini Agent", "Gemini Agent", minx=1040, maxw=300, maxh=40, wait=2200)
    await ge.shot("ge_8_30_branch_agent")

    eds = await p.evaluate(EDITOR_JS)
    if not eds:
        await click_xy(ge, await label_box(ge, "요청 사항", 1040), "요청 사항 펼치기")
        await p.wait_for_timeout(1300)
        eds = await p.evaluate(EDITOR_JS)
    if not eds:
        raise RuntimeError("instruction editor not visible")
    target = eds[0]
    await click_xy(ge, {"x": target["x"] + 10, "y": target["y"] + 6, "w": 160, "h": 24}, "요청 사항")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="요청 사항", chars=len(BRANCH_INSTR))
    await p.keyboard.type(BRANCH_INSTR, delay=22)
    ge.mark("type_end", label="요청 사항")
    await p.keyboard.press("Enter")
    await p.wait_for_timeout(500)
    await click_xy(ge, await label_box(ge, "변수 삽입", 1040), "변수 삽입")
    await p.wait_for_timeout(1300)
    sub = await vtext(ge, "변수", 1040, 200, 40)
    if sub:
        await click_xy(ge, sub[0], "변수")
        await p.wait_for_timeout(1300)
    await ge.shot("ge_8_31a_branch_variables")
    var = await p.evaluate(CONTAINS_JS, [f"{BRIEF_SUB}: output", 600, 1440])
    if not var:
        var = await p.evaluate(CONTAINS_JS, [BRIEF_SUB, 800, 1440])
    if not var:
        var = await p.evaluate(CONTAINS_JS, [": output", 600, 1440])
    if not var:
        raise RuntimeError("briefing output variable not found")
    await click_xy(ge, var[-1], "브리핑 결과 변수")
    await p.wait_for_timeout(1200)
    doc = await p.evaluate(CONTAINS_JS, ["daily_briefing_document", 800, 1440])
    if doc:
        await click_xy(ge, doc[-1], "daily_briefing_document")
        await p.wait_for_timeout(1500)
    else:
        await p.wait_for_timeout(600)
    await ge.shot("ge_8_31_branch_instruction")

    # Rename new node: hover → ⋮ → 이름 바꾸기
    new_nodes = [h for h in await p.evaluate(ICON_JS, "spark") if 470 < h["x"] < 1030]
    new_nodes.sort(key=lambda h: h["y"])
    nb = new_nodes[-1]
    await p.mouse.move(nb["x"] + 60, nb["y"] + 10, steps=14)
    await p.wait_for_timeout(900)
    ks = [k for k in await p.evaluate(ICON_JS, "more_vert") if k["vis"] == "visible" and 470 < k["x"] < 1030 and abs(k["y"] - nb["y"]) < 30]
    if not ks:
        raise RuntimeError("node kebab not visible")
    await click_xy(ge, ks[0], "노드 메뉴")
    await p.wait_for_timeout(900)
    mi = await menu_item(ge, "이름 바꾸기")
    if not mi:
        rn = await p.evaluate(CONTAINS_JS, ["이름 바꾸기", 470, 1100])
        if rn:
            mi = rn[-1]
    await click_xy(ge, mi, "이름 바꾸기")
    await p.wait_for_timeout(900)
    await p.keyboard.press("Meta+A")
    ge.mark("type_start", label="이름", chars=len(BRANCH_NAME))
    await p.keyboard.type(BRANCH_NAME, delay=55)
    ge.mark("type_end", label="이름")
    await p.keyboard.press("Enter")
    await p.wait_for_timeout(1800)
    await ge.shot("ge_8_32_branch_named")
    out, n = await ge.stop_recording("ge8g_branch")
    print("saved", out, n, flush=True)


async def wait_until(ge, cond, timeout, label):
    p = ge.page
    t0 = time.monotonic()
    ge.mark("wait_start", label=label)
    while time.monotonic() - t0 < timeout:
        if await cond():
            break
        await p.wait_for_timeout(1000)
    secs = round(time.monotonic() - t0, 1)
    ge.mark("wait_end", label=label, secs=secs)
    print(label, "done in", secs, flush=True)
    return secs


APPROVE_BTN_JS = r"""
(doScroll) => {
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      const t = (n.nodeValue || '').trim();
      if (t === '승인' || t === '승인하기') {
        const el = n.parentElement;
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.x > 1050 && r.width > 20 && r.width < 220 && r.y > 140) {
          if (doScroll) el.scrollIntoView({block: 'center', behavior: 'smooth'});
          const r2 = el.getBoundingClientRect();
          return {x: Math.round(r2.x), y: Math.round(r2.y), w: Math.round(r2.width), h: Math.round(r2.height)};
        }
      }
    }
    for (const e of root.querySelectorAll('*')) {
      if (e.shadowRoot) { const f = scan(e.shadowRoot); if (f) return f; }
    }
    return null;
  }
  return scan(document);
}
"""


async def approve_button(ge, scroll=False):
    box = await ge.page.evaluate(APPROVE_BTN_JS, scroll)
    if scroll and box:
        await ge.page.wait_for_timeout(1200)
        box = await ge.page.evaluate(APPROVE_BTN_JS, False)
    return box


async def part_test(ge):
    p = ge.page
    PROG.mkdir(exist_ok=True)
    await ensure_builder(ge)
    if "/preview" in p.url:
        await click_vtext(ge, "수정", "수정 탭", maxw=120, maxh=50, wait=2500, miny=0)
        await deselect(ge)
    await p.mouse.move(900, 300, steps=4)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await click_vtext(ge, "테스트", "테스트 탭", maxw=120, maxh=50, wait=2500, miny=0)
    if not await vtext(ge, "테스트 실행 시작", 0, 300, 60):
        await click_xy(ge, await label_box(ge, "재설정", 1200), "재설정")
        await p.wait_for_timeout(2500)
        for word in ("재설정", "확인"):
            btns = [h for h in await vtext(ge, word, 300, 200, 50) if h["y"] > 150]
            if btns:
                await click_xy(ge, btns[-1], "재설정 확인")
                await p.wait_for_timeout(2000)
                break
    await ge.shot("ge_8_33_test_tab")
    await click_vtext(ge, "테스트 실행 시작", "테스트 실행 시작", maxw=300, maxh=60, wait=5000)
    await ge.set_rate(4)

    async def approval_ready():
        return await approve_button(ge, scroll=False) is not None
    await wait_until(ge, approval_ready, 600, "wf_until_approval")
    await ge.set_rate(1)
    await p.wait_for_timeout(2000)
    await ge.shot("ge_8_34_approval_request")
    btn = await approve_button(ge, scroll=True)
    if not btn:
        out, n = await ge.stop_recording("ge8h_test_noapproval")
        print("NO approval button — saved", out, n, flush=True)
        return
    await ge.shot("ge_8_34b_approval_buttons")
    await click_xy(ge, btn, "승인")
    await p.wait_for_timeout(2500)
    await ge.shot("ge_8_35_approved")
    await ge.set_rate(4)
    last = {"n": -1, "t": time.monotonic()}

    async def run_done():
        st = await p.evaluate(ge.PROBE_JS)
        now = time.monotonic()
        if st["n"] != last["n"]:
            last["n"], last["t"] = st["n"], now
        return (not st["busy"]) and now - last["t"] >= 20
    await wait_until(ge, run_done, 480, "wf_after_approval")
    await ge.set_rate(1)
    await p.wait_for_timeout(2000)

    # Scroll the test panel to show the final branch output
    await p.evaluate("""() => {
      function scan(root) {
        const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = tw.nextNode())) {
          if ((n.nodeValue || '').includes('CS팀 공지 요약 에이전트')) {
            const el = n.parentElement;
            if (el && el.getBoundingClientRect().x > 840) {
              el.scrollIntoView({block: 'start', behavior: 'smooth'});
              return true;
            }
          }
        }
        for (const e of root.querySelectorAll('*')) if (e.shadowRoot) { const f = scan(e.shadowRoot); if (f) return f; }
        return false;
      }
      return scan(document);
    }""")
    await p.wait_for_timeout(1500)
    branch_row = await p.evaluate(CONTAINS_JS, [BRANCH_NAME, 840, 1440])
    if branch_row:
        await click_xy(ge, branch_row[-1], "CS팀 공지 요약 결과 펼치기")
        await p.wait_for_timeout(2000)
    await ge.shot("ge_8_36_test_done")
    out, n = await ge.stop_recording("ge8h_test_approval")
    print("saved", out, n, flush=True)


async def part_update(ge):
    p = ge.page
    await ensure_builder(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await click_vtext(ge, "수정", "수정 탭", maxw=120, maxh=50, wait=2200, miny=0)
    await deselect(ge)
    await p.wait_for_timeout(600)
    upd = await vtext(ge, "업데이트", 1150, 180, 50, miny=0, hit=False)
    if not upd:
        upd = await vtext(ge, "사용 설정", 1150, 180, 50, miny=0, hit=False)
    if upd:
        await click_xy(ge, upd[0], "업데이트")
        await p.wait_for_timeout(2200)
    for word in ("업데이트", "승인", "확인"):
        btns = [h for h in await vtext(ge, word, 300, 220, 60, hit=False) if h["y"] > 120]
        if btns:
            b = btns[-1]
            await p.mouse.move(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2, steps=16)
            await p.wait_for_timeout(900)
            break
    await ge.shot("ge_8_37_update_dialog")
    cancel = [h for h in await vtext(ge, "취소", 300, 220, 60, hit=False) if h["y"] > 120]
    if cancel:
        await p.mouse.click(cancel[-1]["x"] + cancel[-1]["w"] / 2, cancel[-1]["y"] + cancel[-1]["h"] / 2)
        await p.wait_for_timeout(1200)
    else:
        await p.keyboard.press("Escape")
        await p.wait_for_timeout(1200)
    await p.mouse.move(720, 260, steps=10)
    await p.wait_for_timeout(600)
    await ge.shot("ge_8_38_updated")
    out, n = await ge.stop_recording("ge8i_update")
    print("saved", out, n, flush=True)


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


SCROLL_INTO_VIEW_JS = r"""
([needle, minX]) => {
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeValue && n.nodeValue.includes(needle)) {
        const el = n.parentElement;
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.x >= minX && r.width > 4) {
          el.scrollIntoView({block: 'center', behavior: 'instant'});
          const r2 = el.getBoundingClientRect();
          return {x: r2.x, y: r2.y, w: r2.width, h: r2.height};
        }
      }
    }
    for (const e of root.querySelectorAll('*')) {
      if (e.shadowRoot) { const f = scan(e.shadowRoot); if (f) return f; }
    }
    return null;
  }
  return scan(document);
}
"""


async def part_step_file_schema(ge):
    p = ge.page
    await ensure_builder(ge)
    if "/preview" in p.url:
        await click_vtext(ge, "수정", "수정 탭", maxw=120, maxh=50, wait=2200, miny=0)
    await deselect(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await click_xy(ge, await node_box(ge, STEP1_SUB), "1단계 분류 에이전트")
    await p.wait_for_timeout(2000)

    # 1) Upload file if not attached, then click 파일 header to expand and show attached PDF
    fb = await label_box(ge, "파일 추가", 1040, timeout=8)
    has_file_1 = bool([h for h in await vtext(ge, "1", 1040, 40, 30, hit=False) if abs(h["y"] - fb["y"]) < 24])
    if not has_file_1:
        ok = await pick_file(ge, fb, "파일 추가", PDF_AIRPOLE)
        if not ok:
            await p.wait_for_timeout(1000)
            await ge.shot("ge_8_23b_step_file_menu")
            up = await vtext(ge, "파일 업로드", 900, 300, 50, hit=False)
            if not up:
                up = await p.evaluate(CONTAINS_JS, ["파일 업로드", 900, 1440])
            if not up:
                raise RuntimeError("step file menu: 파일 업로드 not found")
            if not await pick_file(ge, up[0], "파일 업로드", PDF_AIRPOLE):
                raise RuntimeError("step file chooser did not open")
        ge.mark("upload", label="신제품 브리프 PDF")
        await p.wait_for_timeout(4500)

    fb = await label_box(ge, "파일 추가", 1040, timeout=6)
    await click_xy(ge, {"x": fb["x"] - 220, "y": fb["y"], "w": 80, "h": fb["h"]}, "파일 섹션 펼치기")
    await p.wait_for_timeout(1500)
    await p.mouse.move(1200, 680, steps=6)
    for _ in range(4):
        await p.mouse.wheel(0, 90)
        await p.wait_for_timeout(100)
    await p.wait_for_timeout(900)
    await ge.shot("ge_8_23c_step_file_attached")

    # 2) Click 더보기 header to expand it, then scroll down to 출력 (classified_inquiries)
    more_hits = [h for h in await vtext(ge, "더보기", 1040, 140, 44, hit=False) if h["y"] > 200]
    if not more_hits:
        try:
            more_hits = [await label_box(ge, "더보기", 1040, timeout=4)]
        except Exception:
            more_hits = []
    if more_hits:
        await click_xy(ge, more_hits[0], "더보기 펼치기")
        await p.wait_for_timeout(1600)

    await p.mouse.move(1200, 680, steps=6)
    for _ in range(8):
        await p.mouse.wheel(0, 110)
        await p.wait_for_timeout(100)
    await p.wait_for_timeout(1000)

    # Expand classified_inquiries row
    ci = [h for h in await p.evaluate(CONTAINS_JS, ["classified_inquiries", 1040, 1440]) if 120 < h["y"] < 760]
    if ci:
        await click_xy(ge, ci[0], "classified_inquiries 스키마 펼치기")
        await p.wait_for_timeout(1500)
    await p.mouse.move(1200, 680, steps=6)
    for _ in range(4):
        await p.mouse.wheel(0, 90)
        await p.wait_for_timeout(100)
    await p.wait_for_timeout(900)
    await ge.shot("ge_8_25b_schema_fields")

    # Click edit icon next to 구조화된 출력 to open Visual Schema Editor modal
    so_box = [h for h in await p.evaluate(CONTAINS_JS, ["구조화된 출력", 1040, 1440]) if 80 < h["y"] < 760]
    edits = [h for h in await p.evaluate(ICON_JS, "edit") if h["x"] > 1250 and 80 < h["y"] < 760 and h["vis"] != "hidden"]
    if so_box and edits:
        edits.sort(key=lambda h: abs(h["y"] - so_box[-1]["y"]))
    if edits:
        await click_xy(ge, edits[0], "스키마 편집 모달 열기")
        await p.wait_for_timeout(2000)
        await ge.shot("ge_8_25c_schema_modal")
        apply_btn = await vtext(ge, "스키마 적용", 400, 220, 60, hit=False)
        if apply_btn:
            await click_xy(ge, apply_btn[-1], "스키마 적용")
            await p.wait_for_timeout(1500)
        else:
            await p.keyboard.press("Escape")
            await p.wait_for_timeout(1200)
    out, n = await ge.stop_recording("ge8e2_step_file_schema")
    print("saved", out, n, flush=True)


async def delete_canvas_node(ge, sub):
    p = ge.page
    await deselect(ge)
    hits = await p.evaluate(CONTAINS_JS, [sub, 400, 1300])
    if not hits:
        return
    nb = hits[-1]
    await p.mouse.move(nb["x"] + 20, nb["y"] + 8, steps=12)
    await p.wait_for_timeout(800)
    ks = [
        k for k in await p.evaluate(ICON_JS, "more_vert")
        if k["vis"] == "visible" and 400 < k["x"] < 1350 and abs(k["y"] - nb["y"]) < 35 and k["x"] > nb["x"]
    ]
    if ks:
        await click_xy(ge, ks[0], "노드 메뉴")
        await p.wait_for_timeout(800)
        mi = await menu_item(ge, "삭제")
        if not mi:
            dl = await p.evaluate(CONTAINS_JS, ["삭제", 400, 1350])
            if dl:
                mi = dl[-1]
        if mi:
            await click_xy(ge, mi, "삭제")
            await p.wait_for_timeout(1800)


async def part_flow_menu(ge):
    p = ge.page
    await ensure_builder(ge)
    if "/preview" in p.url:
        await click_vtext(ge, "수정", "수정 탭", maxw=120, maxh=50, wait=2200, miny=0)
    await deselect(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    icons = [h for h in await p.evaluate(ICON_JS, "add_2") if 470 < h["x"] < 1030 and h["vis"] != "hidden"]
    icons.sort(key=lambda h: (h["y"], h["x"]))
    plus = icons[-1] if icons else await end_plus(ge)
    if not plus:
        raise RuntimeError("end + not found")
    await click_xy(ge, plus, "단계 추가 패널 열기")
    await p.wait_for_timeout(1600)
    # 1) Expand 흐름 제어(Flow Control): 조건 · 루프 · 필터
    await click_vtext(ge, "흐름 제어", "흐름 제어(조건·루프·필터)", minx=1040, maxw=400, maxh=40, wait=1400)
    await ge.shot("ge_8_27b_flow_control_items")
    # 2) Click 조건(alt_route) to actually add the If/Else Condition node onto the canvas
    cond_icon = [h for h in await p.evaluate(ICON_JS, "alt_route") if h["x"] > 1040 and h["y"] > 230 and h["vis"] != "hidden"]
    if cond_icon:
        await click_xy(ge, {"x": cond_icon[0]["x"], "y": cond_icon[0]["y"], "w": 80, "h": cond_icon[0]["h"]}, "조건(If/Else) 노드 추가")
        await p.wait_for_timeout(2200)
    # 3) Open 변수 dropdown inside If condition panel to show upstream variables
    var_dd = [h for h in await p.evaluate(CONTAINS_JS, ["변수", 1050, 1300]) if 140 < h["y"] < 210]
    if var_dd:
        await click_xy(ge, var_dd[0], "조건 비교 변수 선택")
        await p.wait_for_timeout(1400)
        var_opt = await p.evaluate(CONTAINS_JS, [BRIEF_SUB, 800, 1440])
        if var_opt:
            await click_xy(ge, var_opt[-1], "브리핑 결과 변수")
            await p.wait_for_timeout(1200)
            doc = await p.evaluate(CONTAINS_JS, ["daily_briefing_document", 800, 1440])
            if doc:
                await click_xy(ge, doc[-1], "daily_briefing_document")
                await p.wait_for_timeout(1200)
        else:
            await p.keyboard.press("Escape")
            await p.wait_for_timeout(800)
    await ge.shot("ge_8_27c_all_step_categories")
    # Clean up temporary 조건 node so the main approval flow remains intact
    await delete_canvas_node(ge, "조건")
    await deselect(ge)
    out, n = await ge.stop_recording("ge8f0_flow_menu")
    print("saved", out, n, flush=True)


ADK_PROMPT = "이번 달 예정된 Cymbal AirPole Pro 고객 체험 행사 및 CS 교육 일정을 조회해 공지 하단에 함께 안내해 주세요."
REQ_INFO_MSG = "반려된 일일 브리핑 초안에서 보완이 필요한 항목을 입력해 주세요."
REQ_INFO_Q1 = "긴급도 분류 기준, 표준 답변 문구, 수치 근거 중 어떤 항목을 우선 수정해야 하나요?"


async def part_reject_branch(ge):
    p = ge.page
    await ensure_builder(ge)
    if "/preview" in p.url:
        await click_vtext(ge, "수정", "수정 탭", maxw=120, maxh=50, wait=2200, miny=0)
    # Ensure clean state if re-running
    await delete_canvas_node(ge, "Cymbal 행사 안내")
    await delete_canvas_node(ge, "요청 정보")
    await deselect(ge)
    await ge.start_recording()
    await p.wait_for_timeout(900)

    # Part A: Under '승인됨' (after CS팀 공지 요약 에이전트), add '기존 에이전트 -> Cymbal 행사 안내 (ADK 에이전트)'
    cs_node = await p.evaluate(CONTAINS_JS, [BRANCH_NAME, 400, 1000])
    icons = [h for h in await p.evaluate(ICON_JS, "add_2") if 450 < h["x"] < 1150 and h["vis"] != "hidden"]
    if cs_node:
        cx = cs_node[0]["x"] + cs_node[0]["w"] / 2
        left_plus = [h for h in icons if h["y"] > cs_node[0]["y"] and abs((h["x"] + h["w"] / 2) - cx) < 90]
    else:
        icons.sort(key=lambda h: h["x"])
        left_plus = [icons[0]]
    left_plus.sort(key=lambda h: h["y"])
    await click_xy(ge, left_plus[-1], "승인됨 후속 단계 추가")
    await p.wait_for_timeout(1600)
    await click_vtext(ge, "기존 에이전트", "기존 에이전트(ADK/A2A)", minx=1040, maxw=400, maxh=40, wait=1400)
    adk_note = await p.evaluate(CONTAINS_JS, ["ADK 및 A2A", 1000, 1440])
    if adk_note:
        await click_xy(
            ge,
            {"x": 1080, "y": adk_note[0]["y"] + 85, "w": 220, "h": 36},
            "Cymbal 행사 안내(ADK 에이전트) 선택",
        )
        await p.wait_for_timeout(2400)

    # Fill 프롬프트 * and attach variable in Cymbal 행사 안내 ADK agent panel
    eds = await p.evaluate(EDITOR_JS)
    if eds:
        target = eds[0]
        await click_xy(ge, {"x": target["x"] + 12, "y": target["y"] + 8, "w": 160, "h": 24}, "ADK 에이전트 프롬프트")
    else:
        await click_xy(ge, {"x": 1085, "y": 241, "w": 180, "h": 28}, "ADK 에이전트 프롬프트")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="ADK 에이전트 프롬프트", chars=len(ADK_PROMPT))
    await p.keyboard.type(ADK_PROMPT, delay=22)
    ge.mark("type_end", label="ADK 에이전트 프롬프트")
    await p.keyboard.press("Enter")
    await p.wait_for_timeout(500)
    try:
        vb = await label_box(ge, "변수 삽입", 1040, timeout=4)
        await click_xy(ge, vb, "변수 삽입")
    except Exception:
        plus_in_panel = [h for h in await p.evaluate(ICON_JS, "add_2") if h["x"] > 1300 and 240 < h["y"] < 360 and h["vis"] != "hidden"]
        if plus_in_panel:
            await click_xy(ge, plus_in_panel[0], "변수 삽입")
    await p.wait_for_timeout(1200)
    var = await p.evaluate(CONTAINS_JS, [BRANCH_NAME, 800, 1440])
    if not var:
        var = await p.evaluate(CONTAINS_JS, [BRIEF_SUB, 800, 1440])
    if var:
        await click_xy(ge, var[-1], "이전 단계 출력 변수")
        await p.wait_for_timeout(1200)
        doc = await p.evaluate(CONTAINS_JS, ["daily_briefing_document", 800, 1440])
        if doc:
            await click_xy(ge, doc[-1], "daily_briefing_document")
            await p.wait_for_timeout(1200)
    await ge.shot("ge_8_32b_reject_branch_agent")

    # Part B: Under '거부됨' branch, add '인간 참여형 -> 요청 정보(Request Info)'
    await deselect(ge)
    await p.wait_for_timeout(800)
    icons2 = [h for h in await p.evaluate(ICON_JS, "add_2") if 450 < h["x"] < 1250 and h["vis"] != "hidden" and h["y"] > 450]
    icons2.sort(key=lambda h: h["x"])
    if not icons2:
        raise RuntimeError("add_2 under 거부됨 not found")
    await click_xy(ge, icons2[-1], "거부됨 갈래 단계 추가")
    await p.wait_for_timeout(1600)
    await click_vtext(ge, "인간 참여형(Human In The Loop)", "인간 참여형", minx=1040, maxw=400, maxh=40, wait=1300)
    req = [h for h in await p.evaluate(ICON_JS, "assignment") if h["x"] > 1040 and h["vis"] != "hidden"]
    if not req:
        raise RuntimeError("요청 정보 icon not found")
    await click_xy(ge, {"x": req[0]["x"], "y": req[0]["y"], "w": 90, "h": req[0]["h"]}, "요청 정보(Request Info)")
    await p.wait_for_timeout(2200)

    # Fill 메시지 in 요청 정보 panel
    msg_ph = await p.evaluate(CONTAINS_JS, ["사용자에게 표시할 메시지", 1040, 1440])
    if msg_ph:
        await click_xy(ge, {"x": msg_ph[0]["x"], "y": msg_ph[0]["y"], "w": 160, "h": msg_ph[0]["h"]}, "요청 정보 메시지")
    else:
        eds = await p.evaluate(EDITOR_JS)
        if eds:
            await click_xy(ge, {"x": eds[0]["x"] + 12, "y": eds[0]["y"] + 8, "w": 160, "h": 24}, "요청 정보 메시지")
    await p.wait_for_timeout(500)
    ge.mark("type_start", label="요청 정보 메시지", chars=len(REQ_INFO_MSG))
    await p.keyboard.type(REQ_INFO_MSG, delay=22)
    ge.mark("type_end", label="요청 정보 메시지")
    await p.keyboard.press("Enter")
    await p.wait_for_timeout(500)
    try:
        vb = await label_box(ge, "변수 삽입", 1040, timeout=4)
        await click_xy(ge, vb, "변수 삽입")
    except Exception:
        plus_in_panel = [h for h in await p.evaluate(ICON_JS, "add_2") if h["x"] > 1300 and 240 < h["y"] < 360 and h["vis"] != "hidden"]
        if plus_in_panel:
            await click_xy(ge, plus_in_panel[0], "변수 삽입")
    await p.wait_for_timeout(1200)
    var = await p.evaluate(CONTAINS_JS, [BRIEF_SUB, 800, 1440])
    if var:
        await click_xy(ge, var[-1], "브리핑 결과 변수")
        await p.wait_for_timeout(1200)
        doc = await p.evaluate(CONTAINS_JS, ["daily_briefing_document", 800, 1440])
        if doc:
            await click_xy(ge, doc[-1], "daily_briefing_document")
            await p.wait_for_timeout(1200)

    # Expand 질문 1 accordion and fill its question input
    q1_hdr = await p.evaluate(CONTAINS_JS, ["질문 1", 1060, 1250])
    if q1_hdr:
        await click_xy(ge, q1_hdr[0], "질문 1 펼치기")
        await p.wait_for_timeout(1000)
        q_in = await label_box(ge, "질문", 1040, timeout=4)
        await click_xy(ge, {"x": q_in["x"] + 12, "y": q_in["y"] + 8, "w": 160, "h": 24}, "질문 1 입력")
        await p.wait_for_timeout(400)
        await p.keyboard.press("Meta+A")
        ge.mark("type_start", label="질문 1 입력", chars=len(REQ_INFO_Q1))
        await p.keyboard.type(REQ_INFO_Q1, delay=22)
        ge.mark("type_end", label="질문 1 입력")
        await p.wait_for_timeout(1000)
        # Also re-open 메시지 header so both 메시지 and 질문 1 are visible if possible
        msg_hdr = await p.evaluate(CONTAINS_JS, ["메시지", 1060, 1250])
        if msg_hdr:
            await click_xy(ge, msg_hdr[0], "메시지 확인")
            await p.wait_for_timeout(1000)

    await ge.shot("ge_8_32c_both_branches_named")
    out, n = await ge.stop_recording("ge8g2_reject_branch")
    print("saved", out, n, flush=True)




PARTS = {
    "enable": part_enable,
    "trigger": part_trigger,
    "step": part_step,
    "step_file_schema": part_step_file_schema,
    "flow_menu": part_flow_menu,
    "approval": part_approval,
    "branch": part_branch,
    "reject_branch": part_reject_branch,
    "test": part_test,
    "update": part_update,
}


async def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(PARTS)
    async with GE() as ge:
        for n in names:
            print("== part", n, flush=True)
            await PARTS[n](ge)


if __name__ == "__main__":
    asyncio.run(main())
