"""AG Lab 8 — the eval report agents-cli wrote, shown big (REAL output, no mockups).

`cymbal-voc-agent/artifacts/grade_results/results_20261028_112106.html` is the report `agents-cli eval run` produced in
the ag8v_eval take (the take itself never scrolled the chat to the scores). Opened in an own headless Chromium
(showcase.py: page content only, 2x frames; never :9222/:9334). The tool outputs inside show the lab project id —
the demo project, as everywhere else on screen.

Outputs
  recording  production/assets/recordings/ag8v_score — 2880x1620 frames; `target` events labelled "E …"
  stills     ag_8v_09_scores (Summary Metrics + Case #0) · ag_8v_10_trace (Conversation Trace + Evaluation Metrics)
             · ag_8v_11_case1 (Case #1: 미처리 긴급 문의 → 6건 table)

Usage: python3 ag8_eval.py [rec|stills|all]
"""
from __future__ import annotations
import os

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from showcase import Showcase, BAD  # noqa: E402

REPORT = (Path(os.environ.get("AG_REC_HOME", str(Path.home() / "ag-rec-voc"))) / "work" / "cymbal-voc" / "cymbal-voc-agent" / "artifacts" / "grade_results"
          / "results_20261028_112106.html")
SOURCE = "headless Chromium · cymbal-voc-agent/artifacts/grade_results/results_20261028_112106.html (agents-cli eval)"
PARK = (1425, 420)

# element whose own text starts with `t` (nth match) → [x, y(viewport), w, h] / page top
FIND_JS = r"""([t, nth, up]) => {
  const els = [...document.querySelectorAll('h1,h2,h3,h4,summary,th,td,div,span,p,strong,b')].filter(e => {
    const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    return own.startsWith(t) && e.getBoundingClientRect().width > 2; });
  let e = els[nth || 0]; if (!e) return null;
  if (up) { const a = e.closest(up); if (a) e = a; }
  const r = e.getBoundingClientRect();
  return {box: [r.x, r.y, r.width, r.height].map(v => Math.round(v * 10) / 10), top: Math.round(r.top + scrollY)}; }"""


# deepest element whose text contains `t` (nth match in document order), optionally its closest(`up`) ancestor
DEEP_JS = r"""([t, nth, up]) => {
  const all = [...document.querySelectorAll('body *')].filter(e => (e.textContent || '').includes(t) &&
    e.getBoundingClientRect().width > 2 && ![...e.children].some(c => (c.textContent || '').includes(t)));
  let e = all[nth || 0]; if (!e) return null;
  if (up) { const a = e.closest(up); if (a) e = a; }
  const r = e.getBoundingClientRect();
  return {box: [r.x, r.y, r.width, r.height].map(v => Math.round(v * 10) / 10), top: Math.round(r.top + scrollY)}; }"""


async def find(d, text, nth=0, up=None, deep=False):
    return await d.page.evaluate(DEEP_JS if deep else FIND_JS, [text, nth, up])


def clip(b):
    x0, y0 = max(0, b[0]), max(0, b[1])
    x1, y1 = min(1440, b[0] + b[2]), min(810, b[1] + b[3])
    return [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)] if x1 > x0 and y1 > y0 else None


async def tgt(d, label, text, nth=0, up=None, mark=True, deep=False):
    f = await find(d, text, nth, up, deep)
    b = clip(f["box"]) if f else None
    if not b:
        print(f"  !! no box for {label}")
        return None
    if mark:
        d.mark("target", label=label, box={"x": b[0], "y": b[1], "width": b[2], "height": b[3]})
    return b


# (label, text, nth, closest-ancestor, deep-contains)
VIEWS = {
    "top": [("E Summary Metrics 표", "Mean Score", 0, "table", True),
            ("E custom_response_quality 5.0000", "custom_response_quality", 0, "tr", False),
            ("E Case #0 Prompt", "Prompt:", 0, "div", False)],
    "trace": [("E Function Call: get_weekly_summary", "Function Call: get_weekly_summary", 0, None, True),
              ("E Tool Output: get_weekly_summary", "Tool Output: get_weekly_summary", 0, None, True),
              ("E Evaluation Metrics 5.00", "Evaluation Metrics", 0, None, True)],
    "case1": [("E Case #1 답변 요약 (총 6건)", "총 6건", 0, "p", True),
              ("E Case #1 미완료 긴급 문의 표", "CX-2610-0259", 0, "table", True)],
}


async def view_targets(d, key, mark=True):
    out = {}
    for label, text, nth, up, deep in VIEWS[key]:
        b = await tgt(d, label, text, nth, up, mark, deep)
        if b:
            out[label] = b
    return out


async def tops(d):
    t_metrics = (await find(d, "Evaluation Metrics", 0, None, True))["top"]
    t_trace = max((await find(d, "Conversation Trace", 0, None, True))["top"] - 24, t_metrics + 190 - 810)
    t_case1 = (await find(d, "Final Response", 1, None, True))["top"] - 70
    return t_trace, t_case1


async def open_report():
    d = await Showcase().open(REPORT.as_uri(), settle=1200)
    text = await d.page.evaluate("document.body.innerText")
    hits = [b for b in BAD if b in text.replace(os.environ.get("LAB_PROJECT_ID", "your-project-id"), "")]
    print("brand/path scan:", hits or "clean (lab project id = demo project)")
    if hits:
        raise SystemExit(f"report text contains {hits}")
    return d


async def record(name="ag8v_score"):
    d = await open_report()
    try:
        t_trace, t_case1 = await tops(d)
        await d.install_cursor()
        await d.page.mouse.move(*PARK)
        await d.start_rec()
        await d.page.wait_for_timeout(500)
        await view_targets(d, "top")
        await d.page.wait_for_timeout(6000)
        await d.scroll_to(t_trace, "Conversation Trace", ms=1600)
        await d.page.wait_for_timeout(400)
        await view_targets(d, "trace")
        await d.page.wait_for_timeout(7000)
        await d.scroll_to(t_case1, "Case #1", ms=1600)
        await d.page.wait_for_timeout(400)
        await view_targets(d, "case1")
        await d.page.wait_for_timeout(6000)
        await d.stop_rec(name, SOURCE)
    finally:
        await d.close()


async def stills():
    d = await open_report()
    try:
        t_trace, t_case1 = await tops(d)
        await d.still("ag_8v_09_scores", await view_targets(d, "top", False), SOURCE + " — Summary Metrics")
        await d.page.evaluate("y => scrollTo(0, y)", t_trace)
        await d.page.wait_for_timeout(400)
        await d.still("ag_8v_10_trace", await view_targets(d, "trace", False), SOURCE + " — Case #0 trace + metric")
        await d.page.evaluate("y => scrollTo(0, y)", t_case1)
        await d.page.wait_for_timeout(400)
        await d.still("ag_8v_11_case1", await view_targets(d, "case1", False), SOURCE + " — Case #1")
    finally:
        await d.close()


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("stills", "all"):
        asyncio.run(stills())
    if what in ("rec", "all"):
        asyncio.run(record())
