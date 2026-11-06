"""AG Lab 7 — the FINISHED slide deck, shown big (REAL output, no mockups).

The deck is the file the agent built in the recording workspace (`slides/weekly_2026-10-19.html`, after the Lab 7
feedback edit) from the company template `templates/exec_deck_template.html`, opened in an own headless Chromium
(showcase.py: page content only, 2x frames; never the demo Chrome :9222 or the recording app :9334). The deck's own
toolbar (슬라이드 발표 모드 ↔ 전체 보기 · ◀ 이전 · n / 6 · 다음 ▶) comes from the template and stays on screen.

Outputs
  recording  production/assets/recordings/ag7v_deck — 2880x1620 frames (CSS 1440x810, css_scale 2.0)
             hover/click events (DOM boxes of the deck buttons) + `target` events (measured DOM boxes of the key parts
             of each slide, emitted when that slide is on screen; labels "S<n> …")
  stills     production/assets/shots/ag_7v_2<n>_deck_s<n>.png (2880x1620) + .boxes.json (targets + leaves)

Usage: python3 ag7_deck.py [rec|stills|all]      (AG7_DECK=<html> overrides the deck path, for dry runs)
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from showcase import Showcase  # noqa: E402

DECK = Path(os.environ.get("AG7_DECK") or
            Path(os.environ.get("AG_REC_HOME", str(Path.home() / "ag-rec-voc"))) / "work" / "cymbal-voc" / "slides" / "weekly_2026-10-19.html")
SOURCE = "headless Chromium · slides/weekly_2026-10-19.html (agent output, Lab 7)"
PARK = (1418, 60)  # page margin right of the slide (presentation mode: slide spans x ≈ 85–1355): never covers content
CUR = ".current-slide"

# (label, selector, nth, closest-ancestor, text filter) — labels describe what is visibly inside the box
# selectors are the template's classes (templates/exec_deck_template.html), which the agent kept as instructed
# nth = -1 → union box of every visible match inside the current slide (a group: stat stack, takeaway list …)
SLIDES = {
    1: [("S1 안전 이슈 경보 배너", ".c-left .alert", 0, None, None),
        ("S1 이번 주 핵심 지표 4개", ".c-right", 0, None, None),
        ("S1 지표 4개 (6 · 91 · 20 · 45건)", ".c-right .stat", -1, None, None),
        ("S1 안전 이슈 6건", ".stat.red", 0, None, None)],
    2: [("S2 핵심 1 · 안전 이슈", ".hl", 0, None, None),
        ("S2 핵심 2 · 전체 접수량", ".hl", 1, None, None),
        ("S2 핵심 3 · 앱 연결 급증", ".hl", 2, None, None),
        ("S2 문장 1", ".hl .tx b", 0, None, None),
        ("S2 문장 2", ".hl .tx b", 1, None, None),
        ("S2 문장 3", ".hl .tx b", 2, None, None)],
    3: [("S3 지표 타일 4개", ".kpi-tiles", 0, None, None),
        ("S3 주별 접수 건수 차트", "svg.chart-bars", 0, ".card", None),
        ("S3 안전 이슈 선 · 주별 건수", "svg.chart-bars .dline, svg.chart-bars .dot, svg.chart-bars text[style*='--red']",
         -1, None, None),
        ("S3 지난주 분류별 건수", "svg.hbar", 0, ".card", None)],
    4: [("S4 미완료 긴급 문의 6건 배너", ".alert", 0, None, None),
        ("S4 긴급 문의 6건 표 (미완료 빨간색)", ".data-table", 0, None, None),
        ("S4 공통 증상 · 조치 현황 · 요청 사항", ".mini-cards", 0, None, None)],
    5: [("S5 앱 연결 주별 건수 차트", "svg.chart-bars", 0, ".card", None),
        ("S5 10월 14일 앱 업데이트 표시", "g.marker rect", 0, None, None),
        ("S5 원인 분석 4단계", ".steps", 0, None, None),
        ("S5 고객 원문", ".quote", 0, None, None)],
    6: [("S6 실행 3단계", ".process", 0, None, None),
        ("S6 담당 · 내용 · 기한", ".process-detail", 0, None, None),
        ("S6 임원 결정 요청", ".asks .card", 0, None, None),
        ("S6 다음 주 확인 지표", "table.watch", 0, ".card", None)],
}

BTN_JS = r"""(label) => { const b = [...document.querySelectorAll('button')].find(e => e.innerText.trim() === label);
  if (!b) return null; const r = b.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(v => Math.round(v * 10) / 10); }"""

UNION_JS = r"""([sel, root]) => { const R = document.querySelector(root) || document;
  const rs = [...R.querySelectorAll(sel)].map(e => e.getBoundingClientRect())
    .filter(r => r.width > 0.5 && r.height > 0.5 && r.bottom > 0 && r.top < innerHeight);
  if (!rs.length) return null;
  const x0 = Math.max(0, Math.min(...rs.map(r => r.left))), y0 = Math.max(0, Math.min(...rs.map(r => r.top)));
  const x1 = Math.min(innerWidth, Math.max(...rs.map(r => r.right))), y1 = Math.min(innerHeight, Math.max(...rs.map(r => r.bottom)));
  return [x0, y0, x1 - x0, y1 - y0].map(v => Math.round(v * 10) / 10); }"""


async def slide_targets(d: Showcase, n: int, mark=True) -> dict:
    out = {}
    for label, sel, nth, up, txt in SLIDES[n]:
        if nth == -1:
            b = await d.page.evaluate(UNION_JS, [sel, CUR])
            if b and mark:
                d.mark("target", label=label, box={"x": b[0], "y": b[1], "width": b[2], "height": b[3]})
            if not b:
                print(f"  !! no box for {label} ({sel})")
        else:
            b = await d.target(label, sel, nth, up, txt, root=CUR, mark=mark)
        if b:
            out[label] = b
    return out


async def button(d: Showcase, label: str):
    b = await d.page.evaluate(BTN_JS, label)
    if not b:
        raise RuntimeError(f"no deck button {label!r}")
    return b


async def counter(d: Showcase) -> str:
    return (await d.page.evaluate("(document.getElementById('slideIndicator')||{}).innerText || ''")).replace(" ", "")


async def record(name="ag7v_deck", hold=9000):
    d = await Showcase().open(DECK.as_uri())
    try:
        await d.scan()
        await d.install_cursor()
        await d.page.mouse.move(*PARK)
        await d.page.wait_for_timeout(300)
        await d.start_rec()
        await d.page.wait_for_timeout(600)
        await slide_targets(d, 1)                      # continuous view, as the file opens
        await d.page.wait_for_timeout(3000)
        await d.click_box(await button(d, "슬라이드 발표 모드"), "슬라이드 발표 모드")
        await d.page.wait_for_timeout(400)
        print("slide", await counter(d))
        await slide_targets(d, 1)
        await d.move(*PARK, steps=16)
        await d.page.wait_for_timeout(hold)
        for n in range(2, 7):
            await d.click_box(await button(d, "다음 ▶"), f"다음 {n}")
            await d.page.wait_for_timeout(300)
            c = await counter(d)
            print("slide", c)
            assert c == f"{n}/6", c
            await slide_targets(d, n)
            await d.move(*PARK, steps=16)
            await d.page.wait_for_timeout(hold + (1000 if n in (4, 5) else 0))
        await d.page.wait_for_timeout(1000)
        await d.stop_rec(name, SOURCE)
    finally:
        await d.close()


async def stills():
    d = await Showcase().open(DECK.as_uri())
    try:
        await d.scan()
        await (await d.page.wait_for_selector("text=슬라이드 발표 모드")).click()
        await d.page.wait_for_timeout(900)
        for n in range(1, 7):
            if n > 1:
                await d.page.keyboard.press("ArrowRight")
                await d.page.wait_for_timeout(900)
            assert await counter(d) == f"{n}/6", await counter(d)
            tg = await slide_targets(d, n, mark=False)
            for lab in ("전체 보기", "다음 ▶"):   # the mode button reads 전체 보기 while presenting
                tg[lab] = await button(d, lab)
            await d.still(f"ag_7v_2{n}_deck_s{n}", tg, SOURCE + " — presentation mode", hide_cursor=False)
    finally:
        await d.close()


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("stills", "all"):
        asyncio.run(stills())
    if what in ("rec", "all"):
        asyncio.run(record())
