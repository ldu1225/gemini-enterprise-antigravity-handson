"""AG Lab 4 — the FINISHED VOC dashboard, used for real (REAL output, no mockups).

The dashboard is what the agent built in the recording workspace (index.html · styles.css · app.js reading
data/voc_tickets.csv). Like the learner does in Lab 4 (`python3 -m http.server`), it is served from that folder by a
local HTTP server (127.0.0.1, random port, only for the capture) and opened in an own headless Chromium
(showcase.py: page content only — no URL bar, nothing from the user's screen; 2x frames).
Note: Lab 5's rule check later touched index.html/app.js (date format YYYY-MM-DD, unit label, data-source footer) —
this is the dashboard after that; numbers and features are Lab 4's.

Take 2 (Lab 4 writer, 2026-10-29):
- the page header is `position: sticky` (89 CSS px) → every scroll target is placed below it (header + 16 px);
  take 1 scrolled KPI/chart cards to y≈24, so their titles sat under the header and the KPI numbers were clipped
- the 4주 차 bar click shrinks the safety list above (10 → 6 rows, −220 px); the scroll position is corrected in the
  same input lock (no frame is captured in between), like Chrome's scroll anchoring — the chart stays in place
- per-card KPI targets, bar-row targets (제품별/분류별), the header KPI row in the 6-row top views ("D 상단 KPI …"),
  and a tag per filter state, so every video callout can come from a `target:` event
- still ag_4v_22 = 제품별 · 분류별 for LAST WEEK (after the bar click) — what the video shows

Outputs
  recording  production/assets/recordings/ag4v_dash — 2880x1620 frames (CSS 1440x810)
             hover/click/select events with DOM boxes + `target` events (labels "D …") at each view
  stills     production/assets/shots/ag_4v_2<n>_dash_*.png (2880x1620) + .boxes.json

Usage: python3 ag4_dash.py [rec|stills|all]
"""
from __future__ import annotations
import os

import asyncio
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from showcase import Showcase  # noqa: E402

ROOT = Path(os.environ.get("AG_REC_HOME", str(Path.home() / "ag-rec-voc"))) / "work" / "cymbal-voc"
SOURCE = "headless Chromium · index.html + app.js + data/voc_tickets.csv (agent output, Lab 4)"
PARK = (1425, 400)  # right page margin (cards span x 44–1396)
LAST_WEEK = "2026-10-19"
KPI_CARDS = ["문의 건수", "안전 이슈", "처리 완료율", "만족도"]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    s = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(ROOT)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


async def header_h(d: Showcase) -> float:
    return float(await d.page.evaluate("() => document.querySelector('header.top-header').getBoundingClientRect().height"))


async def top_targets(d: Showcase, mark=True, tag=""):
    t = {}
    for label, sel, kw in [
        (f"D 기준 주차{tag}", "#weekFilter", {}),
        (f"D 제품 선택{tag}", "#productFilter", {}),
        (f"D 긴급만 보기{tag}", "label.urgent-toggle-label", {}),
        (f"D 안전 이슈 (긴급 문의) 목록{tag}", "section.urgent-section", {}),
        (f"D 긴급 목록 표{tag}", "table.urgent-table", {}),
    ]:
        b = await d.target(label, sel, mark=mark, **kw)
        if b:
            t[label] = b
    badges = await d.page.evaluate("() => [...document.querySelectorAll('.urgent-section .badge')].map(e => {"
                                   " const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })"
                                   ".filter(b => b[2] > 2 && b[1] >= 0 && b[1] < innerHeight)")
    if badges:
        x0 = min(b[0] for b in badges); y0 = min(b[1] for b in badges)
        x1 = max(b[0] + b[2] for b in badges); y1 = max(b[1] + b[3] for b in badges)
        b = [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]
        t[f"D 긴급·미완료 배지{tag}"] = b
        if mark:
            d.mark("target", label=f"D 긴급·미완료 배지{tag}", box={"x": b[0], "y": b[1], "width": b[2], "height": b[3]})
    # with 6 safety rows (last week) the KPI row is fully visible below the list
    full = await d.page.evaluate("() => { const r = document.querySelector('section.kpi-grid').getBoundingClientRect();"
                                 " return r.top >= 0 && r.bottom <= innerHeight; }")
    if full:
        for label, sel, nth in [(f"D 상단 KPI 4개{tag}", "section.kpi-grid", 0)] + [
                (f"D 상단 KPI {n}{tag}", "article.kpi-card", i) for i, n in enumerate(KPI_CARDS)]:
            b = await d.target(label, sel, nth, mark=mark)
            if b:
                t[label] = b
    return t


async def mid_targets(d: Showcase, mark=True, tag=""):
    t = {}
    for label, sel, nth, up, txt in [
        (f"D KPI 4개{tag}", "section.kpi-grid", 0, None, None),
        *[(f"D KPI {n}{tag}", "article.kpi-card", i, None, None) for i, n in enumerate(KPI_CARDS)],
        (f"D 주간 문의 추이 차트{tag}", "h2.chart-title", 0, "article.chart-card", "주간 문의 추이"),
        (f"D 4주 차 막대{tag}", f"g.week-bar-group[data-week='{LAST_WEEK}']", 0, None, None),
    ]:
        b = await d.target(label, sel, nth, up, txt, mark=mark)
        if b:
            t[label] = b
    return t


async def low_targets(d: Showcase, mark=True, tag=""):
    t = {}
    for label, txt in [(f"D 제품별 문의 건수{tag}", "제품별 문의 건수"), (f"D 분류별 문의 건수{tag}", "분류별 문의 건수")]:
        b = await d.target(label, "h2.chart-title", 0, "article.chart-card", txt, mark=mark)
        if b:
            t[label] = b
    for label, sel in [(f"D 로봇청소기 막대{tag}", "#productChartContainer g.hbar-row[data-name='로봇청소기']"),
                       (f"D 안전 이슈 막대{tag}", "#categoryChartContainer g.hbar-row[data-name='안전 이슈']"),
                       (f"D 앱 연결 막대{tag}", "#categoryChartContainer g.hbar-row[data-name='앱 연결']")]:
        b = await d.target(label, sel, mark=mark)
        if b:
            t[label] = b
    return t


async def y_of(d: Showcase, sel: str, pad: float | None = None) -> int:
    """Page y that puts `sel` just below the sticky header (header height + 16 px)."""
    if pad is None:
        pad = await header_h(d) + 16
    return int(await d.page.evaluate("([s, p]) => { const e = document.querySelector(s); "
                                     "return Math.max(0, e.getBoundingClientRect().top + scrollY - p); }", [sel, pad]))


async def y_low(d: Showcase) -> int:
    """Product/category row: chart cards just below the sticky header (their titles visible)."""
    return await y_of(d, "#productChartContainer", None) - await d.page.evaluate(
        "() => { const c = document.querySelector('#productChartContainer'); const a = c.closest('article.chart-card');"
        " return c.getBoundingClientRect().top - a.getBoundingClientRect().top; }")


async def click_keep(d: Showcase, b, label: str, anchor: str, pause=650):
    """click_box() for a click that re-renders content ABOVE the viewport: the scroll position is corrected inside
    the input lock (no frame is captured in between), so `anchor` stays where it was (like scroll anchoring)."""
    x, y = b[0] + b[2] / 2, b[1] + b[3] / 2
    box = {"x": b[0], "y": b[1], "width": b[2], "height": b[3]}
    async with d.fast():
        await d.page.mouse.move(x, y, steps=24)
        d.mark("hover", label=label, box=box)
        await d.page.wait_for_timeout(pause)
        top0 = await d.page.evaluate("s => document.querySelector(s).getBoundingClientRect().top", anchor)
        d.mark("click", label=label, box=box)
        async with d._lock:
            await d.page.mouse.down()
            await d.page.wait_for_timeout(70)
            await d.page.mouse.up()
            shift = await d.page.evaluate(
                "([s, t0]) => new Promise(res => { let n = 0, tot = 0; const f = () => {"
                " const t = document.querySelector(s).getBoundingClientRect().top;"
                " if (Math.abs(t - t0) > 0.5) { scrollBy(0, t - t0); tot += t - t0; }"
                " if (++n < 6) requestAnimationFrame(f); else res(tot); }; f(); })", [anchor, top0])
            await d.page.wait_for_timeout(120)
        print(f"  click_keep {label}: scroll corrected by {shift:.1f} px")
        await d.page.wait_for_timeout(380)
    return box


async def record(name="ag4v_dash"):
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    d = await Showcase().open(url, settle=2200)
    try:
        await d.scan()
        await d.install_cursor()
        await d.page.mouse.move(*PARK)
        await d.start_rec()
        await d.page.wait_for_timeout(600)
        await top_targets(d)                                   # 1 top: safety list first (전체 4주)
        await d.page.wait_for_timeout(5000)
        await d.scroll_to(await y_of(d, "section.kpi-grid"), "KPI·주간 추이")   # 2 KPIs + weekly chart
        await d.page.wait_for_timeout(500)
        await mid_targets(d)
        await d.page.wait_for_timeout(5000)
        bar = await d.box(f"g.week-bar-group[data-week='{LAST_WEEK}'] rect")
        await click_keep(d, bar, "4주 차 막대", "section.kpi-grid")  # 3 last-week bar → week filter, view kept
        await d.page.wait_for_timeout(700)
        await mid_targets(d, tag=" (지난주)")
        await d.move(*PARK, steps=16)
        await d.page.wait_for_timeout(5000)
        await d.scroll_to(await y_low(d), "제품별·분류별")       # 4 product / category breakdown (last week)
        await d.page.wait_for_timeout(500)
        await low_targets(d, tag=" (지난주)")
        await d.page.wait_for_timeout(5000)
        await d.scroll_to(0, "맨 위")                          # 5 the CX team's question: air purifier · urgent only
        await d.page.wait_for_timeout(600)
        await top_targets(d, tag=" (지난주)")
        await d.page.wait_for_timeout(2500)
        await d.select_box(await d.box("#productFilter"), "공기청정기", "제품 선택")
        await d.page.wait_for_timeout(400)
        await top_targets(d, tag=" (공기청정기)")
        await d.page.wait_for_timeout(1500)
        await d.click_box(await d.box("label.urgent-toggle-label"), "긴급만 보기")
        await d.page.wait_for_timeout(700)
        await d.move(*PARK, steps=16)
        t = await top_targets(d, tag=" (공기청정기·긴급)")
        print("filtered top:", t)
        await d.page.wait_for_timeout(6000)
        await d.scroll_to(await y_of(d, "section.kpi-grid"), "KPI (공기청정기·긴급)")
        await d.page.wait_for_timeout(500)
        await mid_targets(d, tag=" (공기청정기·긴급)")
        await d.page.wait_for_timeout(5000)
        await d.stop_rec(name, SOURCE)
    finally:
        await d.close()
        srv.shutdown()


async def stills():
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    d = await Showcase().open(url, settle=2200)
    try:
        await d.scan()
        await d.still("ag_4v_20_dash_top", await top_targets(d, mark=False), SOURCE + " — top (전체 4주)")
        await d.page.evaluate("y => scrollTo(0, y)", await y_of(d, "section.kpi-grid"))
        await d.page.wait_for_timeout(500)
        await d.still("ag_4v_21_dash_kpi", await mid_targets(d, mark=False), SOURCE + " — KPI + 주간 추이 (전체 4주)")
        await d.page.select_option("#weekFilter", LAST_WEEK)        # = clicking the 4주 차 bar
        await d.page.wait_for_timeout(600)
        await d.page.evaluate("y => scrollTo(0, y)", await y_low(d))
        await d.page.wait_for_timeout(500)
        await d.still("ag_4v_22_dash_breakdown", await low_targets(d, mark=False),
                      SOURCE + " — 제품별·분류별 (지난주: 4주 차 막대 클릭 후)")
        await d.page.evaluate("() => scrollTo(0, 0)")
        await d.page.select_option("#productFilter", "공기청정기")
        await d.page.click("label.urgent-toggle-label")
        await d.page.wait_for_timeout(900)
        await d.still("ag_4v_23_dash_filtered", await top_targets(d, mark=False),
                      SOURCE + " — 지난주 · 공기청정기 · 긴급만 보기")
        await d.page.evaluate("y => scrollTo(0, y)", await y_of(d, "section.kpi-grid"))
        await d.page.wait_for_timeout(500)
        await d.still("ag_4v_24_dash_filtered_kpi", await mid_targets(d, mark=False),
                      SOURCE + " — KPI (지난주 · 공기청정기 · 긴급만 보기)")
    finally:
        await d.close()
        srv.shutdown()


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("stills", "all"):
        asyncio.run(stills())
    if what in ("rec", "all"):
        asyncio.run(record())
