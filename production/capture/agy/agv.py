"""AG track — 'cymbal-voc' storyline recordings (REAL Antigravity desktop app UI, driven over CDP).

Instance: production/capture/agy/launch_ag_rec_voc.sh  (CDP :9334, HOME $AG_REC_HOME/home,
workspace $AG_REC_HOME/work/cymbal-voc; AG_REC_HOME defaults to ~/ag-rec-voc). Every still writes <stem>.boxes.json (DOM boxes) and key moments are marked
as `target` events — callouts MUST be authored from these measurements (AGENTS.md §1).

Usage: python3 agv.py <step> [<step> ...]     e.g.  python3 agv.py l3_open
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agrec import AGRec  # noqa: E402
import os  # noqa: E402

AG_REC_HOME = Path(os.environ.get("AG_REC_HOME", str(Path.home() / "ag-rec-voc")))
WORK = AG_REC_HOME / "work" / "cymbal-voc"  # the recording workspace
# lab.env values typed on camera in Lab 6 (use your own lab project; never a real customer project)
LAB_PROJECT_ID = os.environ.get("LAB_PROJECT_ID", "your-project-id")
LAB_PROJECT_NUMBER = os.environ.get("LAB_PROJECT_NUMBER", "123456789012")
LAB_GE_APP_ID = os.environ.get("LAB_GE_APP_ID", "your-ge-app-id")

# ------------------------------------------------------------------------------------------------ prompts (exact)
L3_ASK_REST = (" 를 읽고 CX팀이 원하는 것을 3줄로 요약해 주세요. "
               "그리고 data/voc_tickets.csv의 열 구성과 주별 문의 건수를 알려 주세요.")
L3_PLAN = ("/plan 요청서 1번 VOC 대시보드를 만들 계획을 세워 주세요. HTML·CSS·JavaScript만 쓰고 외부 CDN은 쓰지 마세요. "
           "안전 이슈 긴급 문의는 맨 위에 보여 주세요.")
L3_FEEDBACK = "좋아요. 주간 추이는 4주 막대 차트로, 긴급 문의 목록에는 접수 일시와 상태도 넣어 주세요."
L4_BROWSE = ("/browser 로컬 서버를 띄우고 대시보드를 열어서, 주간 건수·제품별·분류별 차트와 긴급 문의 목록이 "
             "제대로 보이는지 확인해 주세요. 확인한 화면은 스크린샷으로 남겨 주세요.")
L4_ITER = ("대시보드에 제품 선택 필터와 '긴급만 보기' 토글을 추가해 주세요. "
           "필터를 바꾸면 차트와 목록이 함께 바뀌어야 하고, 안전 이슈는 항상 맨 위에 보여야 해요.")
L4_VERIFY = "/browser 제품을 '공기청정기'로 바꾸고 '긴급만 보기'를 켰을 때 목록과 차트가 맞게 바뀌는지 확인해 주세요."
L3_VERIFY = "표의 숫자는 눈으로 세지 말고, 터미널에서 python으로 다시 계산해서 검증해 주세요."


# ------------------------------------------------------------------------------------------------ helpers
async def settle(j, ms=900):
    await j.page.wait_for_timeout(ms)


async def clear_input(j):
    b = await j.input_box()
    await b.click()
    await j.page.keyboard.press("Meta+a")
    await j.page.keyboard.press("Backspace")
    return b


async def header_icon(j, tip):
    """Agent-panel header icon (24x24 anchors without aria-label). Hover candidates left→right until the tooltip
    contains `tip` ('New Conversation', 'Past Conversations', 'Additional Options', 'Close Agent View')."""
    p = j.page
    cands = await p.evaluate("""() => [...document.querySelectorAll('a')].map(a => { const r = a.getBoundingClientRect();
        return [r.left, r.top, r.width, r.height]; })
        .filter(([x, y, w, h]) => w >= 20 && w <= 28 && h >= 20 && h <= 28 && y >= 28 && y <= 64 && x > 700)""")
    for x, y, w, h in sorted(cands):
        await p.mouse.move(x + w / 2, y + h / 2, steps=4)
        await p.wait_for_timeout(1000)
        tips = await p.evaluate("""() => [...document.querySelectorAll('[role=tooltip],[class*=tooltip],[class*=Tooltip]')]
            .map(e => e.innerText || '').join('|')""")
        if tip in tips:
            return {"x": x, "y": y, "width": w, "height": h}
    return None


async def new_chat(j, record=True):
    """Agent panel header '+' (tooltip 'New Conversation ⌘⇧L')."""
    b = await header_icon(j, "New Conversation")
    if not b:
        print("WARNING: New Conversation button not found", flush=True)
        return False
    cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    if record:
        await j.click_xy(cx, cy, label="새 대화", box=b)
    else:
        await j.page.mouse.click(cx, cy)
    await settle(j, 900)
    return True


async def prep_editor(j, open_name=None):
    """Off-camera: close all editor tabs (⌘K ⌘W), optionally open one file from the explorer."""
    p = j.page
    await p.keyboard.press("Escape")
    await p.mouse.click(330, 400)
    await p.keyboard.press("Meta+k")
    await p.keyboard.press("Meta+w")
    await settle(j, 700)
    if open_name:
        await open_file(j, open_name)


async def prep(j):
    await prep_editor(j)


async def prep_index(j):
    await prep_editor(j, "index.html")


async def tree_item(j, name):
    loc = j.page.locator(f'[role="treeitem"][aria-label="{name}"]')
    for i in range(await loc.count()):
        b = await loc.nth(i).bounding_box()
        if b and b["width"] > 2:
            return loc.nth(i)
    return None


async def root_tree_item(j, name):
    """Visible explorer item `name` at the shallowest tree level (workspace root file, not e.g. cymbal-voc-agent/README.md)."""
    loc = j.page.locator(f'[role="treeitem"][aria-label="{name}"]')
    best, best_lv = None, 99
    for i in range(await loc.count()):
        el = loc.nth(i)
        b = await el.bounding_box()
        if not b or b["width"] <= 2:
            continue
        lv = int(await el.get_attribute("aria-level") or 99)
        if lv < best_lv:
            best, best_lv = el, lv
    return best


async def type_prompt(j, text, label, delay=26):
    inp = await j.input_box()
    await j.click(inp, label="입력창")
    await j.type_text(text, delay=delay, label=label + " 입력")
    await settle(j, 500)


async def wait_done(j, label, timeout=900, stable=10, on_tick=None, approve=True, proceed=False):
    base = j.auto(commands=approve, proceed=proceed)

    async def tick():
        if on_tick:
            r = await on_tick()
            if r == "done":
                return "done"
        await base()
    return await j.wait_agent(timeout=timeout, stable=stable, label=label, on_tick=tick)


# ------------------------------------------------------------------------------------------------ Lab 3
async def l3_open(j):
    """Trust dialog → Yes → explorer → 요청서 → data/voc_tickets.csv."""
    p = j.page
    await settle(j, 1200)
    await j.start_recording()
    await settle(j, 1500)
    yes = await j.find_text("Yes, I trust the authors", exact=True)
    if yes:
        dlg = await j.find_text("Do you trust the authors of the files in this folder?", exact=True)
        if dlg:
            await j.mark_target("신뢰 확인", dlg)
        await j.shot("ag_3v_01_trust", targets={"Yes, I trust the authors": yes,
                                                "Do you trust the authors": "Do you trust the authors of the files in this folder?"})
        await j.hover(yes, label="Yes, I trust the authors", pause=900)
        await j.click(yes, label="Yes, I trust the authors")
        await settle(j, 1500)
    req = await tree_item(j, "요청서_CX팀.md")
    await j.hover(req, label="탐색기", pause=700)
    await j.click(req, label="요청서_CX팀.md")
    await settle(j, 1800)
    await j.mark_target("요청 사항", "## 요청 사항")
    await j.mark_target("지켜야 할 것", "## 지켜야 할 것")
    await j.shot("ag_3v_02_request", targets={"요청 사항": "## 요청 사항", "지켜야 할 것": "## 지켜야 할 것"})
    await p.mouse.move(520, 420, steps=14)
    for _ in range(3):
        await p.mouse.wheel(0, 160)
        await settle(j, 420)
    await settle(j, 800)
    data = await tree_item(j, "data")
    await j.click(data, label="data 폴더")
    await settle(j, 900)
    csv = await tree_item(j, "voc_tickets.csv")
    await j.click(csv, label="voc_tickets.csv")
    await settle(j, 2200)
    await j.mark_target("CSV 머리글", "ticket_id,created_at")
    await j.shot("ag_3v_03_data", targets={"voc_tickets.csv": csv, "열 이름": "ticket_id,created_at"})
    await settle(j, 1200)
    print(await j.stop_recording("ag3v_open"))


async def row_control(j, row_text, ctl_texts=("Always Proceed", "Request Review", "Agent Decides", "Turbo")):
    """The dropdown control on the same row as a settings label (custom select in the agent settings popover)."""
    row = await j.find_text(row_text, exact=True)
    if row is None:
        return None, None
    rb = await row.bounding_box()
    for t in ctl_texts:
        loc = j.page.get_by_text(t, exact=True)
        for i in range(await loc.count()):
            b = await loc.nth(i).bounding_box()
            if b and abs((b["y"] + b["height"] / 2) - (rb["y"] + rb["height"] / 2)) < 12 and b["x"] > rb["x"]:
                return row, loc.nth(i)
    return row, None


async def set_policy(j, row_text, value, label):
    row, ctl = await row_control(j, row_text)
    if row is None or ctl is None:
        print(f"WARNING: settings row {row_text!r} or its control not found", flush=True)
        return False
    await j.hover(row, label=row_text, pause=700)
    if (await ctl.inner_text()).strip() == value:
        await j.hover(ctl, label=label, pause=900)
        return True
    await j.click(ctl, label=label)
    await settle(j, 700)
    opt = await j.find_text(value, exact=True)
    if opt:
        await j.hover(opt, label=value, pause=500)
        await j.click(opt, label=value)
        await settle(j, 700)
        return True
    print(f"WARNING: option {value!r} not found", flush=True)
    return False


async def l3_setup(j):
    """Agent settings → Auto Execution / Review Policy = Request Review; widen the agent panel; pick Gemini 4 Argon."""
    p = j.page
    await p.keyboard.press("Escape")
    await p.mouse.move(700, 420, steps=6)
    await j.start_recording()
    await settle(j, 1200)
    st = await j.vis('[aria-label*=" - Settings"]', timeout=8000)
    await j.click(st, label="에이전트 설정")
    await settle(j, 1300)
    await set_policy(j, "Auto Execution", "Request Review", "Auto Execution 선택")
    await set_policy(j, "Review Policy", "Request Review", "Review Policy 선택")
    await settle(j, 600)
    await j.mark_target("Auto Execution", "Auto Execution")
    await j.mark_target("Review Policy", "Review Policy")
    await j.shot("ag_3v_04_settings", targets={"Auto Execution": "Auto Execution", "Review Policy": "Review Policy",
                                               "Customizations": "Customizations"})
    await j.click(st, label="설정 닫기")
    await settle(j, 900)
    # widen the agent panel: drag the sash between the editor and the agent panel
    sash = await p.evaluate("""() => { const s = Array.from(document.querySelectorAll('.monaco-sash.vertical'))
        .map(e => e.getBoundingClientRect()).filter(r => r.height > 300 && r.x > 800 && r.x < 1300)[0];
        return s ? [s.x + s.width / 2, s.y + s.height / 2] : null; }""")
    if sash:
        sx, sy = sash
        await p.mouse.move(sx, sy, steps=16)
        await settle(j, 300)
        j.mark("hover", label="패널 경계", box={"x": sx - 6, "y": 35, "width": 12, "height": 753})
        await p.mouse.down()
        await p.mouse.move(sx - 160, sy, steps=12)
        await p.mouse.move(700, sy, steps=20)
        await p.mouse.up()
        await settle(j, 900)
    region = j.page.locator('[aria-label="Agent Conversation"]')
    await j.mark_target("에이전트 패널", region)
    # model picker
    model = await j.vis('[aria-label^="Select model"]', timeout=8000)
    await j.click(model, label="모델 선택")
    await settle(j, 900)
    argon = await j.find_text("Gemini 4 Argon Medium", exact=True)
    await j.shot("ag_3v_05_models", targets={"Gemini 4 Argon Medium": argon} if argon else None)
    if argon:
        await j.hover(argon, label="Gemini 4 Argon Medium", pause=600)
        await j.click(argon, label="Gemini 4 Argon Medium")
    else:
        await p.keyboard.press("Escape")
    await settle(j, 1000)
    model = await j.vis('[aria-label^="Select model"]', timeout=8000)
    await j.mark_target("선택된 모델", model)
    await settle(j, 800)
    print(await j.stop_recording("ag3v_setup"))


async def l3_ask(j):
    """@요청서 mention → question about the request + data → terminal command approval → answer."""
    p = j.page
    await p.keyboard.press("Escape")
    await clear_input(j)
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 1000)
    inp = await j.input_box()
    await j.click(inp, label="입력창")
    await j.type_text("@요청서", delay=90, label="@ 멘션")
    await settle(j, 1300)
    item = await j.find_text("요청서_CX팀.md", exact=False)
    await j.shot("ag_3v_06_mention", targets={"요청서_CX팀.md": item} if item else None)
    if item:
        await j.mark_target("멘션 후보", item)
    await p.keyboard.press("Enter")
    await settle(j, 700)
    await j.type_text(L3_ASK_REST, delay=24, label="질문 입력")
    await settle(j, 600)
    await j.mark_target("입력한 질문", await j.input_box())
    await j.submit(label="질문 전송")
    shot_done = False

    async def tick():
        nonlocal shot_done
        if not shot_done and await j.find_text("Allow running this command?"):
            await settle(j, 1500)
            card = await j.find_text("Allow running this command?")
            await j.mark_target("명령 실행 승인", card)
            await j.shot("ag_3v_07_allow", targets={"Allow running this command?": card,
                                                   "Yes, allow this time": "Yes, allow this time"})
            shot_done = True
            await settle(j, 1500)
        await j.approve_command()
    await j.wait_agent(timeout=600, stable=10, label="답변", on_tick=tick)
    await settle(j, 1500)
    await p.mouse.move(1000, 200, steps=8)
    await j.shot("ag_3v_08_answer")
    print(await j.stop_recording("ag3v_ask"))


async def l3_verify(j):
    """Same chat: recompute with a terminal command → 'Allow running this command?' card → approve → corrected table."""
    p = j.page
    await p.keyboard.press("Escape")
    await clear_input(j)
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 1000)
    await type_prompt(j, L3_VERIFY, "검증 요청", delay=24)
    await j.mark_target("검증 요청", await j.input_box())
    await j.submit(label="검증 전송")
    shot_done = False

    async def tick():
        nonlocal shot_done
        if not shot_done and await j.find_text("Allow running this command?"):
            await settle(j, 1800)
            card = await j.find_text("Allow running this command?")
            await j.mark_target("명령 실행 승인", card)
            yes = await j.find_text("Yes, allow this time", exact=True)
            if yes:
                await j.mark_target("Yes, allow this time", yes)
            await j.shot("ag_3v_07_allow", targets={"Allow running this command?": card,
                                                   **({"Yes, allow this time": yes} if yes else {})})
            shot_done = True
            await settle(j, 1500)
        await j.approve_command()
    await j.wait_agent(timeout=600, stable=10, label="검증", on_tick=tick)
    await settle(j, 1500)
    await p.mouse.move(1000, 200, steps=8)
    await j.shot("ag_3v_08b_verified")
    print(await j.stop_recording("ag3v_verify"))


async def idle(j):
    return not (await j.page.evaluate(j.BUSY_JS))["busy"]


async def proceed_button(j):
    """Prefer the Proceed button of the plan artifact (editor), else the one in the chat."""
    btns = j.page.get_by_role("button", name="Proceed", exact=True)
    best = None
    for i in range(await btns.count()):
        b = await btns.nth(i).bounding_box()
        if b and b["width"] > 2:
            best = btns.nth(i)
    return best or await j.find_text("Proceed", exact=True, tag="button")


async def toggle_sidebar(j, show: bool):
    tg = j.page.locator('[aria-label^="Toggle Primary Side Bar"]')
    if await tg.count():
        checked = await tg.first.get_attribute("aria-checked")
        if (checked == "true") != show:
            await tg.first.click()
            await settle(j, 600)


async def l3_plan(j):
    """/plan → Implementation Plan artifact → read → feedback in chat → updated plan (Proceed is Lab 4)."""
    p = j.page
    await p.keyboard.press("Escape")
    await toggle_sidebar(j, False)
    await clear_input(j)
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 1000)
    await type_prompt(j, L3_PLAN, "plan 요청", delay=22)
    await j.mark_target("plan 요청", await j.input_box())
    await j.submit(label="plan 전송")

    async def until_plan():
        await j.approve_command()
        if await j.find_text("Proceed", exact=True, tag="button") and await idle(j):
            return "done"
    await j.wait_agent(timeout=600, stable=6, label="계획 작성", on_tick=until_plan)
    await settle(j, 1500)
    pr = await proceed_button(j)
    if pr:
        await j.mark_target("Proceed", pr)
    title = await j.find_text("Implementation Plan", exact=False)
    if title:
        await j.mark_target("Implementation Plan", title)
    await j.shot("ag_3v_09_plan", targets={"Proceed": pr} if pr else None)
    # read the plan in the editor
    await p.mouse.move(380, 430, steps=14)
    ed = p.locator(".editor-group-container").first
    if await ed.count():
        await j.mark_target("계획서", ed)
    for _ in range(5):
        await p.mouse.wheel(0, 260)
        await settle(j, 500)
    await settle(j, 700)
    await p.mouse.wheel(0, -5000)
    await settle(j, 900)
    await type_prompt(j, L3_FEEDBACK, "피드백", delay=24)
    await j.submit(label="피드백 전송")
    await settle(j, 4000)
    await j.wait_agent(timeout=600, stable=6, label="계획 수정", on_tick=until_plan)
    await settle(j, 1500)
    pr = await proceed_button(j)
    if pr:
        await j.mark_target("Proceed", pr)
    await j.shot("ag_3v_10_plan_updated", targets={"Proceed": pr} if pr else None)
    print(await j.stop_recording("ag3v_plan"))


async def l3_plandoc(j):
    """Open the Implementation Plan artifact (chat card / editor tab) and read it in the editor."""
    p = j.page
    await p.keyboard.press("Escape")
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 1000)
    tab = p.get_by_role("tab").filter(has_text="Implementation Plan")
    target = None
    if await tab.count():
        target = tab.first
    else:
        card = await j.find_text("Implementation Plan", exact=True)
        target = card
    await j.hover(target, label="Implementation Plan", pause=700)
    await j.click(target, label="Implementation Plan 열기")
    await settle(j, 2200)
    ed = p.locator(".editor-group-container").first
    await j.mark_target("계획서", ed)
    await j.shot("ag_3v_11_plan_doc", targets={"계획서": ed})
    await p.mouse.move(380, 430, steps=14)
    for _ in range(6):
        await p.mouse.wheel(0, 220)
        await settle(j, 650)
    await settle(j, 800)
    await j.shot("ag_3v_12_plan_doc_more")
    await p.mouse.wheel(0, -5000)
    await settle(j, 900)
    print(await j.stop_recording("ag3v_plandoc"))


# ------------------------------------------------------------------------------------------------ Lab 4
async def l4_build(j):
    """Proceed → implementation (Request Review: command approvals + file review) → Accept all → open index.html."""
    p = j.page
    await p.keyboard.press("Escape")
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 1000)
    pr = await proceed_button(j)
    await j.hover(pr, label="Proceed", pause=900)
    await j.click(pr, label="Proceed")
    await settle(j, 2000)
    took = {"mid": False, "allow": False}
    t0 = time.monotonic()

    async def tick():
        if not took["mid"] and time.monotonic() - t0 > 45:
            await j.shot("ag_4v_01_working")
            took["mid"] = True
        if not took["allow"] and await j.find_text("Allow running this command?"):
            await settle(j, 1200)
            card = await j.find_text("Allow running this command?")
            await j.mark_target("명령 승인", card)
            took["allow"] = True
        await j.approve_command()
    await j.wait_agent(timeout=1200, stable=10, label="구현", on_tick=tick)
    await settle(j, 1500)
    acc = await j.find_text("Accept all", exact=True)
    files = await j.find_text("Files With Changes", exact=False)
    if files:
        await j.mark_target("변경된 파일", files)
    if acc:
        await j.mark_target("Accept all", acc)
    await j.shot("ag_4v_02_changes", targets={k: v for k, v in (("Accept all", acc), ("Files With Changes", files)) if v})
    rv = await j.find_text("Review Changes", exact=False)
    if rv:
        await j.click(rv, label="Review Changes")
        await settle(j, 2500)
        await j.shot("ag_4v_03_diff")
        await p.keyboard.press("Escape")
        await settle(j, 800)
    acc = await j.find_text("Accept all", exact=True)
    if acc:
        await j.click(acc, label="Accept all")
        await settle(j, 1800)
    print(await j.stop_recording("ag4v_build"))


async def l4_settings(j):
    """Practice folder only: Auto Execution / Review Policy → Always Proceed (faster loop from here on)."""
    p = j.page
    await p.keyboard.press("Escape")
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 900)
    st = await j.vis('[aria-label*=" - Settings"]', timeout=8000)
    await j.click(st, label="에이전트 설정")
    await settle(j, 1200)
    await set_policy(j, "Auto Execution", "Always Proceed", "Auto Execution 선택")
    await set_policy(j, "Review Policy", "Always Proceed", "Review Policy 선택")
    await settle(j, 600)
    await j.mark_target("Auto Execution", "Auto Execution")
    await j.mark_target("Review Policy", "Review Policy")
    await j.shot("ag_4v_04_always", targets={"Auto Execution": "Auto Execution", "Review Policy": "Review Policy"})
    await j.click(st, label="설정 닫기")
    await settle(j, 900)
    print(await j.stop_recording("ag4v_settings"))


CARD_JS = r"""() => { const out = [];
  for (const e of document.querySelectorAll('div')) {
    const r = e.getBoundingClientRect();
    if (r.left < 700 || r.width < 300 || r.height < 36 || r.height > 140 || r.top < 60 || r.bottom > 800) continue;
    if (getComputedStyle(e).cursor !== 'pointer') continue;
    if (!/rounded-xl/.test(String(e.className))) continue;
    const t = (e.innerText || '').trim(); if (!t || t.split('\n').length < 2) continue;
    if (/^\d+ files? changed/i.test(t)) continue;          // change-summary card, not an artifact
    out.push({x: r.left, y: r.top, width: r.width, height: r.height, title: t.split('\n')[0].trim()}); }
  return out; }"""


async def open_newest_artifact(j, shot=None, scroll=0, shot2=None):
    """Click the newest artifact card in the chat (e.g. 'Browser Verification' report) → opens in the editor."""
    cards = await j.page.evaluate(CARD_JS)
    if not cards:
        print("WARNING: no artifact card in the chat", flush=True)
        return None
    c = max(cards, key=lambda c: c["y"])
    box = {k: round(c[k], 1) for k in ("x", "y", "width", "height")}
    cx, cy = c["x"] + 140, c["y"] + c["height"] / 2
    j.mark("target", label="아티팩트 카드", box=box)
    await j.hover_xy(cx, cy, label=c["title"], box=box, pause=800)
    await j.click_xy(cx, cy, label=c["title"], box=box)
    await settle(j, 2600)
    if shot:
        await j.shot(shot)
    if scroll:
        await j.page.mouse.move(600, 430, steps=12)      # over the editor, not the explorer (path tooltips)
        for _ in range(scroll):
            await j.page.mouse.wheel(0, 260)
            await settle(j, 600)
        await settle(j, 900)
        if shot2:
            await j.shot(shot2)
    print("artifact:", c["title"], flush=True)
    return c


async def ask_and_wait(j, prompt, label, rec, mid_shot=None, mid_at=40, end_shot=None, timeout=1200, stable=10, new=False,
                       after=None):
    await j.page.keyboard.press("Escape")
    await j.page.mouse.move(1000, 300, steps=6)
    await j.start_recording(name=rec)
    await settle(j, 1000)
    if new:
        await new_chat(j, record=True)
    await clear_input(j)
    await type_prompt(j, prompt, label, delay=22)
    await j.mark_target(label + " 프롬프트", await j.input_box())
    await j.submit(label=label)
    t0 = time.monotonic()
    took = False

    async def tick():
        nonlocal took
        if mid_shot and not took and time.monotonic() - t0 > mid_at:
            await j.shot(mid_shot)
            took = True
        await j.approve_command()
        if time.monotonic() - t0 > 25 and await j.page.evaluate("() => /Queued Messages/.test(document.body.innerText)"):
            raise RuntimeError("prompt is queued behind a background task in this conversation — use new=True")
    await j.wait_agent(timeout=timeout, stable=stable, label=label, on_tick=tick)
    await settle(j, 1500)
    if end_shot:
        await j.page.mouse.move(1000, 200, steps=8)
        await j.shot(end_shot)
    acc = await j.find_text("Accept all", exact=True)
    if acc:
        await j.click(acc, label="Accept all")
        await settle(j, 1500)
    if after:
        await after(j)
    print(await j.stop_recording(rec))


async def l4_browse(j):
    async def after(j):
        await open_newest_artifact(j, shot="ag_4v_06b_report", scroll=4, shot2="ag_4v_06c_report_more")
    await ask_and_wait(j, L4_BROWSE, "브라우저 확인", "ag4v_browse", mid_shot="ag_4v_05_browsing", mid_at=50,
                       end_shot="ag_4v_06_browser_result", new=True, after=after)


async def l4_iterate(j):
    await ask_and_wait(j, L4_ITER, "기능 추가", "ag4v_iterate", end_shot="ag_4v_07_iterated", new=True)


async def l4_verify(j):
    async def after(j):
        await open_newest_artifact(j, shot="ag_4v_09b_report", scroll=4, shot2="ag_4v_09c_report_more")
    await ask_and_wait(j, L4_VERIFY, "필터 검증", "ag4v_verify", mid_shot="ag_4v_08_verifying", mid_at=45,
                       end_shot="ag_4v_09_verified", after=after, new=True)


# ------------------------------------------------------------------------------------------------ Lab 5
L5_RULES = ("이 프로젝트의 팀 규칙 파일 AGENTS.md를 만들어 주세요. 1) 화면과 문서는 한국어 "
            "2) 고객 이름은 가운데 글자, 연락처는 가운데 4자리를 *로 가려서 표시 3) 외부 CDN·외부 스크립트 금지 "
            "4) 날짜는 YYYY-MM-DD 5) 안전 이슈는 항상 맨 위에, 빨간색으로 강조 "
            "6) 모든 화면과 보고서 맨 아래에 데이터 출처와 기준일 표시.")
L5_CHECK = "AGENTS.md 규칙에 맞는지 대시보드 코드를 점검하고, 어긋난 곳이 있으면 고쳐 주세요."
L5_SKILL = ("주간 VOC 보고서를 만드는 스킬을 만들어 주세요. 위치는 .agents/skills/voc-weekly-report/ 입니다. "
            "SKILL.md에는 지난주와 그 전주를 비교해 '핵심 3줄 → 분류별 표 → 원인 추정 → 다음 할 일' 형식으로 쓰라는 지침을 넣고, "
            "scripts/weekly_stats.py에는 CSV에서 주별·분류별·제품별 건수와 긴급 건을 계산하는 코드를 넣어 주세요.")
L5_USE = "지난주(2026-10-19 ~ 2026-10-25) VOC 주간 보고서를 만들어서 reports/ 폴더에 저장해 주세요."
L5_SLASH_REST = " 2026-10-12 주간 보고서도 같은 형식으로 만들어 주세요."


async def open_file(j, name, label=None):
    await toggle_sidebar(j, True)
    loc = await tree_item(j, name)
    if loc:
        await j.click(loc, label=label or name)
        await settle(j, 1500)
        return loc
    # tree item not rendered (long, virtualized explorer) → Quick Open (⌘P)
    await j.page.keyboard.press("Meta+p")
    await settle(j, 600)
    await j.page.keyboard.type(name, delay=25)
    await settle(j, 900)
    await j.page.keyboard.press("Enter")
    await settle(j, 1500)
    return None


async def l5_rules(j):
    await ask_and_wait(j, L5_RULES, "규칙 만들기", "ag5v_rules", end_shot="ag_5v_01_rules", new=True)
    await j.page.wait_for_timeout(500)


async def l5_rules_file(j):
    """Show AGENTS.md in the editor (short clip)."""
    p = j.page
    await p.keyboard.press("Escape")
    await j.start_recording()
    await settle(j, 900)
    await open_file(j, "AGENTS.md", "AGENTS.md")
    ed = p.locator(".editor-group-container").first
    await j.mark_target("AGENTS.md 내용", ed)
    await j.shot("ag_5v_02_agents_md", targets={"AGENTS.md": ed})
    await settle(j, 1500)
    print(await j.stop_recording("ag5v_rules_file"))


async def l5_check(j):
    await ask_and_wait(j, L5_CHECK, "규칙 점검", "ag5v_check", mid_shot="ag_5v_03_checking", mid_at=40,
                       end_shot="ag_5v_04_checked")


async def l5_skill(j):
    await ask_and_wait(j, L5_SKILL, "스킬 만들기", "ag5v_skill", end_shot="ag_5v_05_skill", new=True)


async def l5_skill_file(j):
    p = j.page
    await p.keyboard.press("Escape")
    await j.start_recording()
    await settle(j, 900)
    await toggle_sidebar(j, True)
    for name in (".agents", "skills", "voc-weekly-report"):
        loc = await tree_item(j, name)
        if loc:
            exp = await loc.get_attribute("aria-expanded")
            if exp != "true":
                await j.click(loc, label=name)
                await settle(j, 700)
    await open_file(j, "SKILL.md", "SKILL.md")
    ed = p.locator(".editor-group-container").first
    await j.mark_target("SKILL.md 내용", ed)
    await j.shot("ag_5v_06_skill_md", targets={"SKILL.md": ed})
    await settle(j, 1500)
    print(await j.stop_recording("ag5v_skill_file"))


async def l5_use(j):
    await ask_and_wait(j, L5_USE, "보고서 요청", "ag5v_use", mid_shot="ag_5v_07_using", mid_at=25,
                       end_shot="ag_5v_08_report", new=True)


async def l5_slash(j):
    """New chat: '/voc' → slash menu shows the skill → pick it → rest of the prompt."""
    p = j.page
    await p.keyboard.press("Escape")
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording()
    await settle(j, 1000)
    await new_chat(j, record=True)
    await clear_input(j)
    inp = await j.input_box()
    await j.click(inp, label="입력창")
    await j.type_text("/voc", delay=110, label="슬래시")
    await settle(j, 1300)
    item = await j.find_text("voc-weekly-report", exact=False)
    if item:
        await j.mark_target("voc-weekly-report", item)
    await j.shot("ag_5v_09_slash", targets={"voc-weekly-report": item} if item else None)
    await p.keyboard.press("Enter")
    await settle(j, 700)
    await j.type_text(L5_SLASH_REST, delay=24, label="요청 입력")
    await settle(j, 500)
    await j.submit(label="슬래시 실행")
    await j.wait_agent(timeout=900, stable=10, label="스킬 실행", on_tick=j.auto(commands=True))
    await settle(j, 1500)
    await p.mouse.move(1000, 200, steps=8)
    await j.shot("ag_5v_10_slash_done")
    print(await j.stop_recording("ag5v_slash"))


async def l5_custom(j):
    """Agent settings → Customizations: Manage → rules and skills of this workspace."""
    p = j.page
    await p.keyboard.press("Escape")
    await j.start_recording()
    await settle(j, 900)
    st = await j.vis('[aria-label*=" - Settings"]', timeout=8000)
    await j.click(st, label="에이전트 설정")
    await settle(j, 1200)
    row, _ = await row_control(j, "Customizations")
    manage = await j.find_text("Manage", exact=True)
    if row:
        await j.hover(row, label="Customizations", pause=700)
    if manage:
        await j.click(manage, label="Manage")
        await settle(j, 2200)
    await j.shot("ag_5v_11_customizations")
    for t in ("AGENTS.md", "voc-weekly-report"):
        el = await j.find_text(t, exact=False)
        if el:
            await j.mark_target(t, el)
            await j.hover(el, label=t, pause=900)
    await j.shot("ag_5v_12_customizations_items",
                 targets={t: t for t in ("AGENTS.md", "voc-weekly-report")})
    await p.keyboard.press("Escape")
    await settle(j, 800)
    print(await j.stop_recording("ag5v_custom"))


# ------------------------------------------------------------------------------------------------ Lab 6 (MCP · BigQuery)
L6_ENV = (f"lab.env를 이 실습 프로젝트 값으로 채워 주세요: PROJECT_ID={LAB_PROJECT_ID}, PROJECT_NUMBER={LAB_PROJECT_NUMBER}, "
          f"REGION=us-central1, GE_APP_ID={LAB_GE_APP_ID}, GE_LOCATION=us. "
          "그다음 setup/load_to_bigquery.sh를 실행해서 VOC 데이터를 BigQuery에 올리고, 주별 건수를 알려 주세요.")
L6_QUERY = (f"방금 설치한 BigQuery MCP 도구(get_table_info, execute_sql_readonly)를 직접 호출해서 {LAB_PROJECT_ID} 프로젝트의 "
            "cymbal_cx.voc_tickets 테이블 구조를 확인하고, 지난주(2026-10-19 ~ 2026-10-25) 분류별 문의 건수를 "
            "그 전주와 비교한 표로 보여 주세요.")
L6_INSIGHT = (f"BigQuery MCP의 execute_sql_readonly 도구로 {LAB_PROJECT_ID}.cymbal_cx.voc_tickets에서 로봇청소기 '앱 연결' 문의를 "
              "일자별로 조회해서 언제부터 늘었는지 찾아 주세요. 늘어난 날 전후의 문의 내용도 3건만 보여 주세요"
              "(고객 이름·연락처는 가려서).")
L6_SKILL = ("voc-weekly-report 스킬이 CSV 대신 BigQuery MCP로 cymbal_cx.voc_tickets의 최신 데이터를 조회하도록 "
            "SKILL.md를 고쳐 주세요. 데이터 출처 표기도 BigQuery 테이블로 바꾸고, 파일 링크는 상대 경로로 써 주세요.")
L6_RUN_REST = " 지난주(2026-10-19 ~ 2026-10-25) 보고서를 BigQuery 최신 데이터로 다시 만들어 주세요."

MCP_ALLOW = ("Yes, allow this time", "Allow once", "Allow", "Approve", "Run tool", "Run")


async def approve_any(j):
    """Command approvals ('Allow running this command?'), file-access / MCP permission cards that use the same
    'Yes, allow this time' + Submit form, and MCP tool-call approval buttons (text varies)."""
    if await j.approve_command():
        return True
    opt = await j.find_text("Yes, allow this time", exact=True)
    if opt:
        card = None
        for q in ("Allow read access to this path?", "Allow write access to this path?", "Allow access", "Allow"):
            card = await j.find_text(q, exact=False)
            if card:
                break
        if card:
            await j.mark_target("권한 승인", card)
        await j.click(opt, label="허용", steps=16)
        await settle(j, 400)
        sub = j.page.get_by_role("button", name="Submit")
        if await sub.count():
            await j.click(sub.last, label="Submit", steps=12)
        else:
            await j.page.keyboard.press("Enter")
        await settle(j, 800)
        print("approved permission card", flush=True)
        return True
    for t in MCP_ALLOW:
        loc = j.page.get_by_role("button", name=t, exact=True)
        for i in range(await loc.count()):
            el = loc.nth(i)
            b = await el.bounding_box()
            if b and b["x"] > 700 and 60 < b["y"] < 800:
                j.mark("target", label="도구 승인", box=b)
                await j.click(el, label="도구 승인", steps=14)
                await settle(j, 800)
                print("approved tool call:", t, flush=True)
                return True
    return False


async def ask_mcp(j, prompt, label, rec, mid_shot=None, mid_at=35, end_shot=None, new=True, after=None, slash=None,
                  prep=True, recheck=25):
    """Like ask_and_wait, but approves MCP tool calls too; optional '/skill' prefix picked from the slash menu.
    prep=True closes all editor tabs first (no stale editors with local paths / hover popups in the take)."""
    if prep:
        # an EMPTY editor shows a large placeholder logo → keep a harmless workspace file open instead
        # (workspace files have relative breadcrumbs; files outside the workspace would show a local path)
        await prep_editor(j, prep if isinstance(prep, str) else "요청서_CX팀.md")
    await j.page.keyboard.press("Escape")
    await j.page.mouse.move(1000, 300, steps=6)
    await j.start_recording(name=rec)
    await settle(j, 1000)
    if new:
        await new_chat(j, record=True)
    await clear_input(j)
    if slash:
        inp = await j.input_box()
        await j.click(inp, label="입력창")
        await j.type_text("/" + slash[:3], delay=110, label="슬래시")
        await settle(j, 1300)
        item = await j.find_text(slash, exact=False)
        if item:
            await j.mark_target(slash, item)
        await j.page.keyboard.press("Enter")
        await settle(j, 700)
        await j.type_text(prompt, delay=22, label=label + " 입력")
    else:
        await type_prompt(j, prompt, label, delay=22)
    await j.mark_target(label + " 프롬프트", await j.input_box())
    await j.submit(label=label)
    t0 = time.monotonic()
    took = False

    async def tick():
        nonlocal took
        if mid_shot and not took and time.monotonic() - t0 > mid_at:
            await j.shot(mid_shot)
            took = True
        await approve_any(j)
        if time.monotonic() - t0 > 25 and await j.page.evaluate("() => /Queued Messages/.test(document.body.innerText)"):
            raise RuntimeError("prompt is queued behind a background task in this conversation — use new=True")
    await j.wait_agent(timeout=1500, stable=10, label=label, on_tick=tick, recheck=recheck)
    await settle(j, 1500)
    if end_shot:
        await j.page.mouse.move(1000, 200, steps=8)
        await j.shot(end_shot)
    acc = await j.find_text("Accept all", exact=True)
    if acc:
        await j.click(acc, label="Accept all")
        await settle(j, 1500)
    if after:
        await after(j)
    print(await j.stop_recording(rec))


async def l6_env(j):
    await prep_editor(j)
    await ask_mcp(j, L6_ENV, "환경 변수와 적재", "ag6v_env", mid_shot="ag_6v_00_loading", mid_at=40,
                  end_shot="ag_6v_01_env")


async def store_item(j, text):
    loc = j.page.get_by_text(text, exact=True)
    for i in range(await loc.count()):
        b = await loc.nth(i).bounding_box()
        if b and b["x"] > 700 and b["y"] > 180:
            return loc.nth(i)
    return None


async def plugin_tab(j, name):
    loc = j.page.locator("button.antigravity-plugin-page-sidebar-button", has_text=name)
    return loc.first if await loc.count() else None


async def l6_install(j):
    """'…' (Additional Options) → MCP Servers → MCP Store: search BigQuery → Install → Tools → Manage → raw config.
    The store opens with a non-public server list for a moment: it is bracketed by cut_start/cut_end events
    — writers MUST cut that interval (non-public names must never be shown)."""
    p = j.page
    await prep_editor(j)
    await toggle_sidebar(j, False)
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording(name="ag6v_install")
    await settle(j, 1000)
    b = await header_icon(j, "Additional Options")
    if not b:
        raise RuntimeError("Additional Options button not found")
    await j.click_xy(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, label="추가 옵션", box=b)
    await settle(j, 900)
    item = await j.find_text("MCP Servers", exact=True)
    await j.mark_target("MCP Servers 메뉴", item)
    await j.shot("ag_6v_02_menu", targets={"MCP Servers": item})
    await j.hover(item, label="MCP Servers", pause=600)
    j.mark("cut_start", label="non-public MCP store list visible")
    await j.click(item, label="MCP Servers")
    inp = p.locator('input[placeholder="Search MCP servers"]')
    for _ in range(40):
        if await inp.count():
            break
        await p.wait_for_timeout(100)
    await inp.first.click()
    await p.keyboard.type("BigQuery", delay=18)
    await p.wait_for_timeout(900)
    j.mark("cut_end", label="store filtered to BigQuery")
    await settle(j, 700)
    await j.mark_target("검색창", inp.first)
    bq = await store_item(j, "BigQuery")
    await j.mark_target("BigQuery 항목", bq)
    await j.shot("ag_6v_03_store_search", targets={"BigQuery": bq, "Search": inp.first})
    await j.hover(bq, label="BigQuery 항목", pause=800)
    await j.click(bq, label="BigQuery 항목")
    await settle(j, 2600)
    inst = p.get_by_role("button", name="Install", exact=True)
    inst = inst.first if await inst.count() else None
    if inst:
        await j.mark_target("Install", inst)
    await j.shot("ag_6v_04_bigquery_page", targets={"Install": inst} if inst else None)
    if inst:
        await j.hover(inst, label="Install", pause=900)
        await j.click(inst, label="Install")
        await settle(j, 3000)
    en = await j.find_text("Enabled", exact=True)
    if en:
        await j.mark_target("Enabled", en)
    tools = await plugin_tab(j, "Tools")
    await j.shot("ag_6v_05_installed", targets={k: v for k, v in (("Enabled", en), ("Tools", tools)) if v})
    if tools:
        await j.hover(tools, label="Tools", pause=600)
        await j.click(tools, label="Tools")
        await settle(j, 2000)
        first = await j.find_text("1. list_dataset_ids", exact=True)
        if first:
            await j.mark_target("도구 목록", first)
        await j.shot("ag_6v_06_tools", targets={"1. list_dataset_ids": first} if first else None)
        await p.mouse.move(600, 520, steps=10)
        for _ in range(4):
            await p.mouse.wheel(0, 240)
            await settle(j, 650)
        await settle(j, 900)
        ex = await j.find_text("execute_sql_readonly", exact=False)
        if ex:
            await j.mark_target("execute_sql_readonly", ex)
        await j.shot("ag_6v_07_tools_more")
    cfg = await plugin_tab(j, "Configure")
    if cfg:
        await j.click(cfg, label="Configure")
        await settle(j, 1500)
        nc = await j.find_text("No configuration needed", exact=False)
        if nc:
            await j.mark_target("No configuration needed", nc)
        await j.shot("ag_6v_08_configure")
    man = p.get_by_role("button", name="Manage MCP Servers", exact=True)
    if await man.count():
        await j.hover(man.first, label="Manage MCP Servers", pause=700)
        await j.click(man.first, label="Manage MCP Servers")
        await settle(j, 2200)
        await j.shot("ag_6v_09_manage")
        raw = await j.find_text("View raw config", exact=True)
        if raw:
            await j.mark_target("View raw config", raw)
            await j.hover(raw, label="View raw config", pause=700)
            await j.click(raw, label="View raw config")
            await settle(j, 2500)
            await j.shot("ag_6v_10_raw_config")
    back = p.get_by_role("button", name="Back to Agent", exact=True)
    if await back.count():
        await j.click(back.first, label="Back to Agent")
        await settle(j, 1200)
    print(await j.stop_recording("ag6v_install"))


async def l6_query(j):
    await ask_mcp(j, L6_QUERY, "MCP 조회", "ag6v_query", mid_shot="ag_6v_11_querying", mid_at=30,
                  end_shot="ag_6v_12_query_result")


async def l6_insight(j):
    await ask_mcp(j, L6_INSIGHT, "급증 원인 찾기", "ag6v_insight", mid_shot="ag_6v_13_insight_running", mid_at=30,
                  end_shot="ag_6v_14_insight")


async def l6_skill(j):
    await ask_mcp(j, L6_SKILL, "스킬 업그레이드", "ag6v_skill", end_shot="ag_6v_15_skill_mcp")


async def l6_run(j):
    await ask_mcp(j, L6_RUN_REST, "BigQuery로 보고서", "ag6v_run", mid_shot="ag_6v_16_run", mid_at=30,
                  end_shot="ag_6v_17_run_done", slash="voc-weekly-report")


# ------------------------------------------------------------------------------------------------ Lab 7 (임원 보고 슬라이드)
L7_SLIDES = ("voc-weekly-report 스킬과 BigQuery MCP로 지난주(2026-10-19 ~ 2026-10-25) 데이터를 확인해서, "
             "templates/exec_deck_template.html 회사 템플릿으로 임원 보고 슬라이드 6장을 slides/weekly_2026-10-19.html로 "
             "만들어 주세요. 템플릿의 CSS와 발표 모드는 그대로 두고 [대괄호] 자리만 실제 데이터로 채워 주세요. "
             "1 표지 2 핵심 3줄 3 주간 추이 4 안전 이슈 긴급 문의(미완료 강조) 5 로봇청소기 앱 연결 급증 6 다음 할 일. "
             "AGENTS.md 규칙을 지켜 주세요.")
L7_PDF = ("/browser slides/weekly_2026-10-19.html을 열어 6장이 잘 보이는지 확인하고, 한 장에 한 슬라이드씩 "
          "slides/weekly_2026-10-19.pdf로 내보내 주세요. 확인한 화면은 스크린샷으로 남겨 주세요.")
L7_EDIT = ("2번 슬라이드 핵심 3줄은 문장이 길어서 한 줄로 읽히게 짧게 줄여 주세요. 3번 슬라이드 주별 접수 차트의 "
           "빨간 안전 이슈 선에는 주별 건수를 숫자로 표시해 주세요. "
           "고친 뒤 PDF를 다시 내보내고, 바뀐 두 장의 스크린샷을 보여 주세요.")


async def l7_slides(j):
    await prep_editor(j)
    await ask_mcp(j, L7_SLIDES, "슬라이드 만들기", "ag7v_slides", mid_shot="ag_7v_01_making", mid_at=45,
                  end_shot="ag_7v_02_slides")


async def l7_pdf(j):
    async def after(j):
        await open_newest_artifact(j, shot="ag_7v_04_report", scroll=4, shot2="ag_7v_05_report_more")
    await ask_mcp(j, L7_PDF, "PDF 내보내기", "ag7v_pdf", mid_shot="ag_7v_03_browser", mid_at=45,
                  end_shot="ag_7v_03b_pdf_done", after=after)


async def l7_edit(j):
    async def after(j):
        await open_newest_artifact(j, shot="ag_7v_07_edit_report", scroll=4, shot2="ag_7v_08_edit_report_more")
    await ask_mcp(j, L7_EDIT, "슬라이드 고치기", "ag7v_edit", mid_shot="ag_7v_06_editing", mid_at=45,
                  end_shot="ag_7v_06b_edited", after=after)


async def l7_view(j):
    """Explorer → slides/ → the slide images the agent exported (real files, image preview in the editor)."""
    p = j.page
    await prep_editor(j)
    await toggle_sidebar(j, True)
    await p.mouse.move(1000, 300, steps=6)
    await j.start_recording(name="ag7v_view")
    await settle(j, 900)
    sl = await tree_item(j, "slides")
    if sl and (await sl.get_attribute("aria-expanded")) != "true":
        await j.click(sl, label="slides")
        await settle(j, 900)
    for k, n in ((1, "ag_7v_09_slide1"), (3, "ag_7v_10_slide3"), (4, "ag_7v_11_slide4"), (5, "ag_7v_12_slide5")):
        it = await tree_item(j, f"weekly_2026-10-19_slide_{k}.png")
        if not it:
            continue
        await j.click(it, label=f"slide_{k}.png")
        await settle(j, 1800)
        await p.mouse.move(1000, 760, steps=8)
        await settle(j, 500)
        ed = p.locator(".editor-group-container").first
        await j.mark_target(f"슬라이드 {k}", ed)
        await j.shot(n, targets={f"slide {k}": ed})
        await settle(j, 1200)
    print(await j.stop_recording("ag7v_view"))


# ------------------------------------------------------------------------------------------------ Lab 8 (ADK 에이전트)
L8_CREATE = ("agents-cli로 cymbal-voc-agent라는 ADK 에이전트 프로젝트를 만들어 주세요. lab.env의 PROJECT_ID와 REGION을 쓰고, "
             "배포 대상은 Agent Runtime, 프로토타입(최소 구성)으로요.")
L8_TOOLS = ("cymbal-voc-agent에 BigQuery cymbal_cx.voc_tickets를 조회하는 도구 2개를 넣어 주세요. "
            "get_weekly_summary(week_start): 분류별·제품별 건수와 전주 대비 증감, "
            "list_urgent_tickets(only_open): 안전 이슈 긴급 문의 목록(고객 이름·연락처 마스킹). "
            "에이전트 지침은 한국어로, AGENTS.md 규칙을 따르게 하고, 프로젝트 ID는 lab.env에서 읽어 주세요.")
L8_RUN = ("agents-cli run으로 '지난주 긴급 문의 중 아직 처리 안 된 건 알려 줘'를 보내고, 명령을 백그라운드로 돌리지 말고 "
          "끝날 때까지 기다렸다가 도구 호출 내용과 에이전트의 답변을 그대로 보여 주세요.")
L8_EVAL = ("평가 케이스 3개(주간 요약 · 미처리 긴급 문의 · 제품별 질문)를 만들고 agents-cli eval run으로 평가한 뒤 "
           "결과를 요약해 주세요.")


async def l8_create(j):
    await prep_editor(j)
    await ask_mcp(j, L8_CREATE, "에이전트 만들기", "ag8v_create", mid_shot="ag_8v_01_creating", mid_at=60,
                  end_shot="ag_8v_02_created")


async def l8_tools(j):
    await ask_mcp(j, L8_TOOLS, "도구 추가", "ag8v_tools", mid_shot="ag_8v_03_tools_working", mid_at=60,
                  end_shot="ag_8v_04_tools")


async def l8_run(j):
    await ask_mcp(j, L8_RUN, "에이전트 실행", "ag8v_run", mid_shot="ag_8v_05_running", mid_at=40,
                  end_shot="ag_8v_06_run_result")


async def l8_eval(j):
    await ask_mcp(j, L8_EVAL, "에이전트 평가", "ag8v_eval", mid_shot="ag_8v_07_eval_running", mid_at=60,
                  end_shot="ag_8v_08_eval_result")


# ------------------------------------------------------------------------------------------------ Lab 9 (배포 + GE 게시)
L9_DEPLOY = ("lab.env의 PROJECT_ID와 REGION으로 agents-cli deploy를 써서 cymbal-voc-agent를 Agent Runtime에 배포해 주세요. "
             "배포 명령은 백그라운드로 돌리지 말고 끝날 때까지 기다린 뒤, 배포된 에이전트가 BigQuery를 읽을 수 있도록 "
             "필요한 IAM 권한(BigQuery 데이터 보기·작업 실행)도 부여하고 결과를 알려 주세요.")
L9_PUBLISH = ("배포한 cymbal-voc-agent를 agents-cli publish gemini-enterprise로 Gemini Enterprise 앱에 등록해 주세요. "
              "앱 ID·위치·표시 이름은 lab.env의 GE_APP_ID, GE_LOCATION, GE_DISPLAY_NAME 값을 그대로 쓰면 되니 "
              "앱 목록은 조회하지 말고 바로 등록해 주세요.")


async def l9_deploy(j):
    await prep_editor(j)
    await ask_mcp(j, L9_DEPLOY, "배포", "ag9v_deploy", mid_shot="ag_9v_01_deploying", mid_at=90,
                  end_shot="ag_9v_02_deployed")


async def l9_publish(j):
    await ask_mcp(j, L9_PUBLISH, "GE 게시", "ag9v_publish", mid_shot="ag_9v_03_publishing", mid_at=40,
                  end_shot="ag_9v_04_published")


L9_IAM = ("배포된 cymbal-voc-agent(Agent Runtime)가 BigQuery의 cymbal_cx 데이터를 읽을 수 있도록 IAM 권한"
          "(roles/bigquery.dataViewer, roles/bigquery.jobUser)을 부여하고, 부여된 결과를 확인해서 알려 주세요. "
          "명령은 백그라운드로 돌리지 말고 끝날 때까지 기다려 주세요.")


async def l9_iam(j):
    await ask_mcp(j, L9_IAM, "권한 부여", "ag9v_iam", mid_shot="ag_9v_02b_iam_working", mid_at=40,
                  end_shot="ag_9v_02c_iam_done")


# ------------------------------------------------------------------------------------------------ Lab 10 (운영 자동화)
L10_SCHEDULE_REST = (" 매주 월요일 오전 8시 30분에 voc-weekly-report 스킬로 지난주 보고서를 BigQuery 최신 데이터로 만들어 "
                     "reports/에 저장하고, 안전 이슈 긴급 건이 있으면 맨 위에 요약하도록 예약해 주세요.")
L10_STATUS = "방금 예약한 작업의 상태와 다음 실행 시각을 알려 주세요."
L10_SUB = ("서브에이전트 두 개에게 나눠서 동시에 진행해 주세요: (1) .agents/skills/voc-weekly-report/scripts/weekly_stats.py의 "
           "단위 테스트 작성·실행 (2) README.md에 '매주 운영 가이드'(월요일 자동 보고 흐름, 데이터 확인, 장애 시 대처) 섹션 추가. "
           "끝나면 결과를 합쳐서 알려 주세요.")


async def open_schedule_card(j):
    """After the answer: expand the 'Scheduled 30 8 * * 1' card (scheduled prompt + Status: Active) and show it."""
    chip = await j.find_text("Scheduled", exact=False)
    if not chip:
        print("WARNING: Scheduled chip not found", flush=True)
        return
    await j.click(chip, label="Scheduled 카드")
    await settle(j, 1300)
    await j.page.mouse.move(1150, 420, steps=8)
    for _ in range(3):
        await j.page.mouse.wheel(0, -120)
        await settle(j, 350)
    await settle(j, 900)
    st = await j.find_text("Status", exact=False)
    if st:
        await j.mark_target("Status: Active", st)
    await j.shot("ag_10v_01b_schedule_card")
    await settle(j, 2500)
    # the conversation now holds an active cron → a new message waits in 'Queued Messages' → Send Now
    inp = await j.input_box()
    await j.click(inp, label="입력창 (상태 확인)")
    await j.type_text(L10_STATUS, delay=22, label="상태 확인 입력")
    await j.mark_target("상태 확인 프롬프트", inp)
    await j.submit(label="상태 확인")
    await settle(j, 2200)
    q = await j.find_text("Queued Messages", exact=False)
    if q:
        await j.mark_target("Queued Messages", q)
    btn = j.page.locator('button[aria-label="Send Now"]')
    if await btn.count():
        await settle(j, 1200)
        await j.click(btn.first, label="Send Now")
    else:
        print("WARNING: no Send Now button (message not queued?)", flush=True)
    await j.wait_agent(timeout=300, stable=8, label="상태 확인", recheck=5)
    await settle(j, 1500)
    await j.page.mouse.move(1000, 200, steps=8)
    await j.shot("ag_10v_01c_status")
    await settle(j, 2500)


async def l10_schedule(j):
    await prep_editor(j)
    await ask_mcp(j, L10_SCHEDULE_REST, "주간 예약", "ag10v_schedule", end_shot="ag_10v_01_scheduled",
                  slash="schedule", after=open_schedule_card)


async def show_readme_guide(j):
    """After the merged report: open README.md at the new '매주 운영 가이드' section (line read from disk)."""
    lines = (WORK / "README.md").read_text(encoding="utf-8").splitlines()
    ln = next((i + 1 for i, t in enumerate(lines) if "운영 가이드" in t and t.lstrip().startswith("#")), None)
    if not ln:
        print("WARNING: README.md has no '운영 가이드' heading yet", flush=True)
    await toggle_sidebar(j, True)
    item = await root_tree_item(j, "README.md")
    if item:
        await j.click(item, label="README.md")
    else:
        await open_file(j, "README.md")
    await settle(j, 1200)
    if ln:
        await j.page.keyboard.press("Control+g")
        await settle(j, 500)
        await j.page.keyboard.type(str(ln), delay=60)
        await j.page.keyboard.press("Enter")
        await settle(j, 1200)
        await j.page.keyboard.press("Escape")
    await j.page.mouse.move(600, 430, steps=6)
    await settle(j, 1500)
    await j.shot("ag_10v_04_readme_guide")
    await settle(j, 2500)


async def l10_sub(j):
    # the main agent ends its first turn while the two subagents work, and resumes with the merged report when they
    # finish → keep recording through that pause (recheck up to 8 min)
    await ask_mcp(j, L10_SUB, "서브에이전트", "ag10v_sub", mid_shot="ag_10v_02_subagents", mid_at=40,
                  end_shot="ag_10v_03_sub_done", recheck=480, after=show_readme_guide)


async def main(*which):
    async with AGRec() as j:
        await settle(j, 1200)
        for w in which:
            print("==", w, flush=True)
            await globals()[w](j)


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:]))
