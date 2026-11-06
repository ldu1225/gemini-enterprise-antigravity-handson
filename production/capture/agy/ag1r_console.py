"""AG Lab 1 (시작하기 A — GE 라이선스): REAL Google Cloud console admin screens for AI developer tools.

Chrome :9222 (signed in as the demo admin), in its OWN window (agy/gconsole.py) — the Gemini Enterprise tabs are
never touched. Project $LAB_PROJECT_ID, location us. Read-only: edit panels are opened and ALWAYS closed with Cancel;
nothing is saved. The Apps list is never shown (it lists other demo apps).

    python3 production/capture/agy/ag1r_console.py stills    # gc_ag_1r_01..08 (+ .boxes.json, CSS px of 1440x810)
    python3 production/capture/agy/ag1r_console.py record    # recording ag1r_console (click/hover/target events)

Callouts must be authored from the saved boxes / recorded events only (AGENTS.md §1).
"""
from __future__ import annotations
import os

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gconsole import GC  # noqa: E402

BASE = "https://console.cloud.google.com/gemini-enterprise"
PROJECT = os.environ.get("LAB_PROJECT_ID", "your-project-id")
URL_DEV = f"{BASE}/settings/ai-developer-tools?project={PROJECT}"
URL_AUTH = f"{BASE}/settings/authentication?project={PROJECT}"   # direct URL: no Learn tutorial side panel
URL_MET = f"{BASE}/developer-tools-monitoring?project={PROJECT}"

EDITS_JS = r"""() => { const out = [];
  for (const b of document.querySelectorAll('button, a[role=button]')) {
    const t = (b.innerText || '').trim(); if (t !== 'Edit') continue;
    const r = b.getBoundingClientRect(); if (r.width < 2) continue;
    let p = b.parentElement, ctx = '';
    for (let i = 0; i < 4 && p; i++) { ctx = (p.innerText || '').trim().split('\n')[0]; if (ctx && ctx !== 'Edit') break; p = p.parentElement; }
    out.push({ctx, b: [r.x, r.y, r.width, r.height]}); }
  return out; }"""

BTN_JS = r"""([name, ymin, ymax, xmin]) => { for (const b of document.querySelectorAll('button')) {
    const t = (b.innerText || '').trim(); if (t !== name) continue; const r = b.getBoundingClientRect();
    if (r.width < 2 || r.y < ymin || r.y > ymax || r.x < xmin) continue; return [r.x, r.y, r.width, r.height]; }
  return null; }"""


GROUP_JS = r"""([text]) => {   // metrics dashboard: header grid item + every chart item until the next group header
  const leaf = [...document.querySelectorAll('*')].find(e => (e.innerText || '').trim() === text &&
                 [...e.children].every(c => (c.innerText || '').trim() !== text));
  if (!leaf) return null;
  const head = leaf.closest('ktd-grid-item'); if (!head) return null;
  const items = [...head.parentElement.children].filter(e => e.tagName.toLowerCase() === 'ktd-grid-item');
  const hr = head.getBoundingClientRect();
  const nxt = items.filter(e => e.classList.contains('header')).map(e => e.getBoundingClientRect().y)
                   .filter(y => y > hr.y + 1).sort((a, b) => a - b);
  const yEnd = nxt.length ? nxt[0] : Infinity;
  let x0 = hr.x, y0 = hr.y, x1 = hr.right, y1 = hr.bottom;
  for (const e of items) { const r = e.getBoundingClientRect();
    if (r.height > 0 && r.y >= hr.y && r.y < yEnd - 1) { x0 = Math.max(hr.x, Math.min(x0, r.x)); x1 = Math.min(hr.right, Math.max(x1, r.right)); y1 = Math.max(y1, r.bottom); } }
  return [x0, y0, x1 - x0, y1 - y0]; }"""


async def group_box(g, text):
    b = await g.page.evaluate(GROUP_JS, [text])
    return [round(v, 1) for v in b] if b else None


# ------------------------------------------------------------------------------------------------ helpers
async def clean(g):
    """Close side panels that are not part of the lesson (Gemini Cloud Assist chat, Learn tutorial) — exact labels."""
    p = g.page
    for label in ("Close Gemini chat panel.", "Close tutorial"):
        loc = p.locator(f'[aria-label="{label}"]')
        for i in range(await loc.count()):
            b = await loc.nth(i).bounding_box()
            if b and b["width"] > 2:
                await loc.nth(i).click()
                await p.wait_for_timeout(900)
    ok = p.get_by_text("OK, got it", exact=True)
    if await ok.count():
        try:
            await ok.first.click(timeout=2000)
        except Exception:
            pass


async def edit_box(g, ctx):
    edits = await g.page.evaluate(EDITS_JS)
    cand = [e for e in edits if e["ctx"].startswith(ctx)]
    return [round(v, 1) for v in cand[0]["b"]] if cand else None


async def button(g, name, ymin=0, ymax=810, xmin=0):
    b = await g.page.evaluate(BTN_JS, [name, ymin, ymax, xmin])
    return [round(v, 1) for v in b] if b else None


async def main_top(g):
    return await g.scroller(700, 520, "main")


async def scroll_main_to(g, top, dur=800):
    await main_top(g)
    return await g.smooth_scroll("main", top, dur=dur)


async def bring_heading(g, text, y_target, dur=800, **o):
    """Scroll the main page so that the heading `text` sits at y_target (CSS px)."""
    cur = await main_top(g)
    b = await g.lb(text, **o)
    return await g.smooth_scroll("main", max(0, cur + b[1] - y_target), dur=dur)


async def panel_cancel(g, record=False):
    b = await button(g, "Cancel", ymin=700, xmin=860)
    if not b:
        raise RuntimeError("panel Cancel not found")
    if record:
        await g.click_box(b, label="Cancel", steps=16)
    else:
        await g.page.mouse.click(b[0] + b[2] / 2, b[1] + b[3] / 2)
    await g.page.wait_for_timeout(1200)


async def open_panel(g, ctx, record=False, label=None):
    b = await edit_box(g, ctx)
    if record:
        await g.click_box(b, label=label or f"{ctx} Edit")
    else:
        await g.page.mouse.click(b[0] + b[2] / 2, b[1] + b[3] / 2)
    await g.page.wait_for_timeout(2600)


async def open_models_dropdown(g, record=False):
    field = await g.lb("Antigravity authorized models", xmin=880, minw=400)
    if record:
        await g.click_box(field, label="Antigravity authorized models", steps=16)
    else:
        await g.page.mouse.click(field[0] + field[2] / 2, field[1] + field[3] / 2)
    await g.page.wait_for_timeout(1500)
    lst = await g.rb('[role="listbox"]', xmin=880)
    await g.scroller(lst[0] + lst[2] / 2, lst[1] + lst[3] / 2, "list")
    return field


# ------------------------------------------------------------------------------------------------ measured targets
async def t_top(g):
    p = g.page
    return {
        "AI developer tools 탭": await g.box_of(p.get_by_role("tab", name="AI developer tools")),
        "Current location": await g.lb("Current location:", up=2),
        "AI developer tools 사용": await g.lb("AI developer tools", xmin=290, xmax=420, ymin=200, ymax=330, up=3),
        "Security": await g.lb("Security", xmin=290, xmax=420, must=["MCP servers"]),
        "Settings 메뉴": await g.lb("Settings", xmax=260, minh=28),
    }


async def t_security_panel(g):
    return {
        "Outside of file access policy": await g.lb("Outside of file access policy", xmin=860, must=["Deny", "Allow"]),
        "Terminal auto-execution mode": await g.lb("Terminal auto-execution mode", xmin=860, must=["Require review", "Always proceed"]),
        "Sandbox mode": await g.lb("Sandbox mode", xmin=860, up=3),
        "Browser access": await g.lb("Browser access", xmin=860, up=3),
    }


async def t_compliance(g):
    return {
        "Compliance": await g.lb("Compliance", xmin=290, xmax=420, must=["Metadata logging"]),
        "Features": await g.lb("Features", xmin=290, xmax=420, must=["/teamwork-preview command"]),
    }


async def t_features_panel(g):
    boost = g.union(await g.lb("/boost command", xmin=880, up=2),
                    await g.lb("Multi-agent reasoning pipeline", xmin=880, prefix=True))
    team = g.union(await g.lb("/teamwork-preview command", xmin=880, up=2),
                   await g.lb("Collaborative multi-agent team", xmin=880, prefix=True))
    # the toggle row spans the whole panel width; keep the box to the visible label/description width
    return {"/boost command": boost, "/teamwork-preview command": team}


async def t_models_list(g):
    lst = await g.rb('[role="listbox"]', xmin=880)
    argon = g.union(*[await g.lb(f"Gemini 4 Argon ({lv})", xmin=880, minh=24) for lv in ("High", "Low", "Medium")])
    flash = g.union(*[await g.lb(f"Gemini 3.8 Flash ({lv})", xmin=880, minh=24) for lv in ("High", "Low", "Medium")])
    return {"Google 모델 목록": lst, "Gemini 4 Argon": argon, "Gemini 3.8 Flash": flash}


async def t_partner(g):
    warn = await g.lb("Important billing and quota info", must=["Cloud Billing console"], minw=760)
    head = await g.lb("Anthropic Models", up=4)
    last_txt = await g.lb("Claude Sonnet 5.5 (Medium)")
    last_row = await g.lb("Claude Sonnet 5.5 (Medium)", up=2)
    ant = g.union(head, [last_row[0], last_txt[1], last_row[2], last_txt[3] + 4])
    return {"Important billing and quota info": warn, "Anthropic Models": ant}


async def t_metrics_top(g):
    return {
        "시간 범위": await g.lb("Last 1 day", up=5),
        "Active Users (Adoption)": await group_box(g, "Active Users (Adoption)"),
        "Developer tools metrics 메뉴": await g.lb("Developer tools metrics", xmax=260, minh=28),
    }


async def t_metrics_tools(g):
    return {"Tools & API calls": await group_box(g, "Tools & API calls")}


async def t_metrics_tokens(g):
    return {
        "Token Usage & Context Caching": await group_box(g, "Token Usage & Context Caching"),
        "Total tokens (sum)": await g.lb("Total tokens (sum)", minh=120),
    }


def check_visible(name, targets):
    for k, b in targets.items():
        if not b:
            raise RuntimeError(f"{name}: target {k!r} not found")
        x, y, w, h = b
        if x < 0 or y < 0 or x + w > 1440.5 or y + h > 810.5:
            print(f"NOTE {name}: target {k!r} {b} is (partly) outside the viewport", flush=True)


# ------------------------------------------------------------------------------------------------ stills
async def stills(g):
    p = g.page
    await g.goto(URL_DEV, wait=9000)
    await clean(g)
    await scroll_main_to(g, 0, dur=60)
    await p.mouse.move(1380, 760)

    t = await t_top(g)
    check_visible("01", t)
    await g.shot("gc_ag_1r_01_devtools", targets=t)

    await open_panel(g, "Security")
    t = await t_security_panel(g)
    check_visible("02", t)
    await g.shot("gc_ag_1r_02_security_edit", targets=t)
    await panel_cancel(g)

    await bring_heading(g, "Compliance", 160, dur=60, xmin=290, xmax=420)
    t = await t_compliance(g)
    check_visible("03", t)
    await g.shot("gc_ag_1r_03_compliance", targets=t)

    await open_panel(g, "Features")
    t = await t_features_panel(g)
    check_visible("04", t)
    await g.shot("gc_ag_1r_04_features_edit", targets=t)
    await panel_cancel(g)

    await bring_heading(g, "Google models", 300, dur=60, xmin=290, xmax=420)
    await open_panel(g, "Google models")
    await open_models_dropdown(g)
    await g.smooth_scroll("list", 100000, dur=60)
    t = await t_models_list(g)
    check_visible("05", t)
    await g.shot("gc_ag_1r_05_google_models", targets=t)
    cb = await button(g, "Cancel", ymin=150, ymax=650, xmin=1000)      # dropdown Cancel (keeps the selection empty)
    await p.mouse.click(cb[0] + cb[2] / 2, cb[1] + cb[3] / 2)
    await p.wait_for_timeout(900)
    await panel_cancel(g)

    await scroll_main_to(g, 0, dur=60)
    warn = await g.lb("Important billing and quota info", must=["Cloud Billing console"], minw=760)
    await scroll_main_to(g, warn[1] - 141, dur=60)
    t = await t_partner(g)
    check_visible("06", t)
    await g.shot("gc_ag_1r_06_partner_models", targets=t)

    await g.goto(URL_MET, wait=12000)
    await clean(g)
    await p.mouse.move(1380, 760)
    t = await t_metrics_top(g)
    check_visible("07", t)
    await g.shot("gc_ag_1r_07_metrics", targets=t)

    await bring_heading(g, "Tools & API calls", 100, dur=60)
    await p.wait_for_timeout(2500)
    t = await t_metrics_tools(g)
    grp = t["Tools & API calls"]
    # the group (header + 3 charts) is ~756 px tall and the dashboard viewport is 733 px: box = its visible part
    t["Tools & API calls"] = [grp[0], grp[1], grp[2], round(min(grp[1] + grp[3], 806) - grp[1], 1)]
    check_visible("08", t)
    await g.shot("gc_ag_1r_08_metrics_tools", targets=t)
    await scroll_main_to(g, 0, dur=60)


# ------------------------------------------------------------------------------------------------ recording
async def record(g):
    p = g.page
    # --- prep (not recorded): Settings page, clean, neutral cursor
    await g.goto(URL_AUTH, wait=9000)
    await clean(g)
    await p.mouse.move(760, 600)
    await p.wait_for_timeout(1500)

    await g.start_recording()
    await p.wait_for_timeout(1800)
    t = await t_top(g)
    await g.mark_target("Settings 메뉴", t["Settings 메뉴"])
    await p.wait_for_timeout(1200)

    # STEP 4 — AI developer tools tab: location + on/off
    await g.click(p.get_by_role("tab", name="AI developer tools"), label="AI developer tools 탭")
    await p.wait_for_timeout(3800)
    await scroll_main_to(g, 0, dur=40)
    t = await t_top(g)
    await g.mark_target("Current location", t["Current location"])
    sw = await g.rb('[role="switch"]')                       # the on/off switch itself (cursor only)
    await g.hover_box(sw or t["AI developer tools 사용"], label="AI developer tools 스위치", pause=600)
    await g.mark_target("AI developer tools 사용", t["AI developer tools 사용"])
    await p.wait_for_timeout(3200)

    # STEP 5 — Security policies (edit panel, Cancel) + Compliance
    await open_panel(g, "Security", record=True, label="Security Edit")
    t = await t_security_panel(g)
    await g.mark_target("Outside of file access policy", t["Outside of file access policy"])
    await g.mark_target("Terminal auto-execution mode", t["Terminal auto-execution mode"])
    await g.mark_target("Sandbox mode", t["Sandbox mode"])
    await g.mark_target("Browser access", t["Browser access"])
    await p.wait_for_timeout(4200)
    await panel_cancel(g, record=True)
    await p.mouse.move(700, 520, steps=10)
    await bring_heading(g, "Compliance", 160, dur=900, xmin=290, xmax=420)
    t = await t_compliance(g)
    await g.mark_target("Compliance", t["Compliance"])
    await g.mark_target("Features", t["Features"])
    await p.wait_for_timeout(3200)

    # STEP 6 — Features (/boost, /teamwork-preview)
    await open_panel(g, "Features", record=True, label="Features Edit")
    t = await t_features_panel(g)
    await g.mark_target("/boost command", t["/boost command"])
    await g.mark_target("/teamwork-preview command", t["/teamwork-preview command"])
    await p.wait_for_timeout(4200)
    await panel_cancel(g, record=True)

    # STEP 7 — Model availability: Google models list, then Non-Google (Anthropic) models
    await p.mouse.move(700, 520, steps=10)
    await bring_heading(g, "Google models", 300, dur=900, xmin=290, xmax=420)
    await p.wait_for_timeout(1200)
    await open_panel(g, "Google models", record=True, label="Google models Edit")
    await open_models_dropdown(g, record=True)
    t = await t_models_list(g)
    await g.mark_target("Google 모델 목록", t["Google 모델 목록"])
    await p.wait_for_timeout(2600)
    lst = t["Google 모델 목록"]
    await p.mouse.move(lst[0] + lst[2] / 2, lst[1] + lst[3] * 0.6, steps=10)
    await g.smooth_scroll("list", 100000, dur=900)
    t = await t_models_list(g)
    await g.mark_target("Gemini 4 Argon", t["Gemini 4 Argon"])
    await g.mark_target("Gemini 3.8 Flash", t["Gemini 3.8 Flash"])
    await p.wait_for_timeout(3600)
    cb = await button(g, "Cancel", ymin=150, ymax=650, xmin=1000)
    await g.click_box(cb, label="목록 Cancel", steps=14)
    await p.wait_for_timeout(700)
    await panel_cancel(g, record=True)
    await p.mouse.move(700, 520, steps=10)
    cur = await main_top(g)
    warn = await g.lb("Important billing and quota info", must=["Cloud Billing console"], minw=760)
    await g.smooth_scroll("main", cur + warn[1] - 141, dur=1100)
    t = await t_partner(g)
    await g.mark_target("Important billing and quota info", t["Important billing and quota info"])
    await g.mark_target("Anthropic Models", t["Anthropic Models"])
    await p.wait_for_timeout(4200)

    # STEP 9 — Developer tools metrics
    nav = await g.lb("Developer tools metrics", xmax=260, minh=28)
    await g.click_box(nav, label="Developer tools metrics")
    g.mark("wait_start", label="metrics")
    await p.wait_for_timeout(9000)
    g.mark("wait_end", label="metrics")
    t = await t_metrics_top(g)
    await g.mark_target("시간 범위", t["시간 범위"])
    await g.mark_target("Active Users (Adoption)", t["Active Users (Adoption)"])
    await p.wait_for_timeout(4200)
    await p.mouse.move(800, 520, steps=10)
    await bring_heading(g, "Token Usage & Context Caching", 100, dur=1000)
    await p.wait_for_timeout(1500)
    t = await t_metrics_tokens(g)
    await g.mark_target("Total tokens (sum)", t["Total tokens (sum)"])
    await p.wait_for_timeout(2800)
    await bring_heading(g, "Tools & API calls", 100, dur=1000)
    await p.wait_for_timeout(1500)
    t = await t_metrics_tools(g)
    grp = t["Tools & API calls"]
    t["Tools & API calls"] = [grp[0], grp[1], grp[2], round(min(grp[1] + grp[3], 806) - grp[1], 1)]
    await g.mark_target("Tools & API calls", t["Tools & API calls"])
    await p.wait_for_timeout(4000)
    out = await g.stop_recording("ag1r_console")
    print("recorded", out, flush=True)
    await scroll_main_to(g, 0, dur=60)


async def main(mode):
    async with GC() as g:
        if mode == "stills":
            await stills(g)
        elif mode == "record":
            await record(g)
        else:
            raise SystemExit("usage: ag1r_console.py stills|record")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "stills"))
