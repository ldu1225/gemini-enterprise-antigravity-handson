"""AG Lab 9 — use the published 'Cymbal VOC 분석가' agent in the Gemini Enterprise web app (REAL UI, Chrome :9222).

Stills get <stem>.boxes.json (DOM leaves, CSS px) and key moments are `target` events, like agrec.py — callouts must be
authored from these measurements (AGENTS.md §1). GE pierces shadow DOM, so leaves are collected through shadow roots.

Usage: python3 ge_voc_agent.py [agents|ask|all]
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ge import GE, APP_HOME, SHOTS  # noqa: E402
from helpers import FIND_TEXT_JS  # noqa: E402

AGENT = "Cymbal VOC 분석가"
Q = "지난주(2026-10-19 ~ 2026-10-25) 안전 이슈 긴급 문의 중 아직 처리되지 않은 건을 알려 줘"

LEAVES_JS = r"""() => { const out = []; const seen = new Set();
  const walk = (root) => { for (const e of root.querySelectorAll('*')) { if (e.shadowRoot) walk(e.shadowRoot);
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
    const al = e.getAttribute('aria-label') || e.getAttribute('title') || '';
    const t = e.children.length ? '' : (e.innerText || e.textContent || '').trim();
    if (!t && !al) continue;
    const key = (t || al) + '|' + Math.round(r.x) + ',' + Math.round(r.y) + ',' + Math.round(r.width);
    if (seen.has(key)) continue; seen.add(key);
    out.push({t: t.slice(0, 240), a: al.slice(0, 120), tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '',
              b: [Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]});
  } };
  walk(document); return out; }"""


async def shot(ge, name, targets=None):
    path = await ge.shot(name)
    leaves = await ge.page.evaluate(LEAVES_JS)
    path.with_suffix(".boxes.json").write_text(json.dumps({"viewport": [1440, 810], "targets": targets or {},
                                                           "leaves": leaves}, ensure_ascii=False), encoding="utf-8")
    return path


async def find_text_box(ge, text, maxw=700, maxh=120, min_y=50):
    hits = await ge.page.evaluate(FIND_TEXT_JS, [text, maxw, maxh, min_y])
    return hits[-1] if hits else None


async def click_box(ge, b, label, pause=900):
    x, y = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    box = {"x": b["x"], "y": b["y"], "width": b["w"], "height": b["h"]}
    await ge.page.mouse.move(x, y, steps=22)
    ge.mark("hover", label=label, box=box)
    await ge.page.wait_for_timeout(pause)
    ge.mark("click", label=label, box=box)
    await ge.page.mouse.down()
    await ge.page.wait_for_timeout(70)
    await ge.page.mouse.up()
    return box


async def main(what="all"):
    async with GE() as ge:
        p = ge.page
        await ge.goto(APP_HOME + "?hl=ko", wait=4500)
        await ge.start_recording()
        await p.wait_for_timeout(1200)
        nav = await ge.vis_label("에이전트")
        hb = await ge.move_to(nav)
        ge.mark("hover", label="에이전트", box=hb)
        await p.wait_for_timeout(800)
        await ge.click(nav, label="에이전트")
        await p.wait_for_timeout(4500)
        card = None
        for _ in range(20):
            card = await find_text_box(ge, AGENT, maxw=600, maxh=80)
            if card:
                break
            await p.mouse.wheel(0, 400)
            await p.wait_for_timeout(700)
        if not card:
            await shot(ge, "ag_9v_05_ge_agents_missing")
            print("agent card not found", flush=True)
            print(await ge.stop_recording("ag9v_ge_use_aborted"))
            return
        hits = await ge.brand_scan(scroll_all=False)
        print("BRAND SCAN (agents page):", hits or "clean", flush=True)
        tb = {"x": card["x"], "y": card["y"], "width": card["w"], "height": card["h"]}
        ge.mark("target", label=AGENT, box=tb)
        await shot(ge, "ag_9v_05_ge_agents", targets={AGENT: [tb["x"], tb["y"], tb["width"], tb["height"]]})
        if what == "agents":
            print(await ge.stop_recording("ag9v_ge_agents"))
            return
        await click_box(ge, card, AGENT)
        await p.wait_for_timeout(5000)
        await shot(ge, "ag_9v_06_ge_agent_open")
        box = await ge.vis('[contenteditable="true"]', timeout=20000)
        await ge.click(box, label="입력창")
        await ge.type_text(Q, delay=30, label="질문 입력")
        await p.wait_for_timeout(600)
        bb = await box.bounding_box()
        if bb:
            ge.mark("target", label="질문", box=bb)
        await p.keyboard.press("Enter")
        ge.mark("submit", label="질문")
        await ge.wait_answer_done(timeout=420, stable=8, min_wait=6, label="답변")
        await p.wait_for_timeout(1500)
        await shot(ge, "ag_9v_07_ge_answer")
        await p.mouse.move(900, 500, steps=8)
        for _ in range(3):
            await p.mouse.wheel(0, 300)
            await p.wait_for_timeout(700)
        await shot(ge, "ag_9v_08_ge_answer_more")
        hits = await ge.brand_scan(scroll_all=False)
        print("BRAND SCAN (answer page):", hits or "clean", flush=True)
        print(await ge.stop_recording("ag9v_ge_use"))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
