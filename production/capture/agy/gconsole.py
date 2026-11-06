"""Drive the REAL Google Cloud console (admin screens) in the signed-in demo Chrome on CDP :9222.

Same API as capture/ge.py (click/move_to/type_text/mark/shot/start_recording/stop_recording) plus the measured-box
helpers of agy/agrec.py: every still writes `<stem>.boxes.json` (named targets + every visible text leaf, CSS px of the
1440x810 viewport) and `mark_target`/`hover` record events with DOM boxes, so callouts are authored from measurements
(AGENTS.md §1).

Isolation: the console runs in its OWN window (Target.createTarget newWindow) — the Gemini Enterprise tabs
(the GE app cid) are never navigated, closed or brought to front. The window's target id is kept in
production/capture/agy/.gc_target so later scripts reuse the same window.
"""
from __future__ import annotations
import os

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ge import GE, CDP_URL  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

W, H, DPR = 1440, 810, 2
PROJECT = os.environ.get("LAB_PROJECT_ID", "your-project-id")
STATE = Path(__file__).resolve().parent / ".gc_target"


class GC(GE):
    def __init__(self, viewport=True):
        super().__init__()
        self._want_viewport = viewport

    async def __aenter__(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(CDP_URL)
        self.ctx = self.browser.contexts[0]
        self.page = await self._own_page()
        self.cdp = await self.ctx.new_cdp_session(self.page)
        if self._want_viewport:
            await self.set_viewport()
            iw, ih, dpr = await self.page.evaluate("() => [innerWidth, innerHeight, devicePixelRatio]")
            if (iw, ih) != (W, H):
                print(f"WARNING: viewport {iw}x{ih} dpr {dpr} (expected {W}x{H})", flush=True)
        return self

    async def _target_id(self, page):
        s = await self.ctx.new_cdp_session(page)
        try:
            return (await s.send("Target.getTargetInfo"))["targetInfo"]["targetId"]
        finally:
            await s.detach()

    async def _own_page(self):
        want = STATE.read_text().strip() if STATE.is_file() else ""
        if want:
            for p in self.ctx.pages:
                try:
                    if await self._target_id(p) == want:
                        return p
                except Exception:
                    pass
        bs = await self.browser.new_browser_cdp_session()
        res = await bs.send("Target.createTarget", {"url": "about:blank", "newWindow": True})
        tid = res["targetId"]
        STATE.write_text(tid)
        for _ in range(50):
            for p in self.ctx.pages:
                try:
                    if await self._target_id(p) == tid:
                        return p
                except Exception:
                    pass
            await asyncio.sleep(0.2)
        raise RuntimeError("new console window not found")

    async def set_viewport(self, w=W, h=H, dpr=DPR):
        await self.cdp.send("Emulation.setDeviceMetricsOverride",
                            {"width": w, "height": h, "deviceScaleFactor": dpr, "mobile": False})

    async def goto(self, url, wait=6000, sidebar=False):
        await self.page.goto(url, wait_until="domcontentloaded")
        await self.page.wait_for_timeout(wait)
        await self.install_cursor()

    # ------------------------------------------------------------- measured boxes (callout ground truth)
    LEAVES_JS = r"""() => { const out = []; const seen = new Set();
      const walk = (root) => { for (const e of root.querySelectorAll('*')) {
        if (e.shadowRoot) walk(e.shadowRoot);
        const r = e.getBoundingClientRect();
        if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
        const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) continue;
        const al = e.getAttribute('aria-label') || e.getAttribute('title') || '';
        const t = e.children.length ? '' : (e.innerText || e.textContent || '').trim();
        if (!t && !al) continue;
        const key = (t || al) + '|' + Math.round(r.x) + ',' + Math.round(r.y) + ',' + Math.round(r.width);
        if (seen.has(key)) continue; seen.add(key);
        out.push({t: t.slice(0, 240), a: al.slice(0, 120), tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '',
                  b: [Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]});
      } }; walk(document); return out; }"""

    async def box_of(self, loc):
        """CSS-px [x, y, w, h] of a locator, of a JS function returning a DOMRect-like dict, or of a literal box."""
        if isinstance(loc, (list, tuple)):
            return [round(float(v), 1) for v in loc]
        if isinstance(loc, str):
            r = await self.page.evaluate(loc)
            return [round(r["x"], 1), round(r["y"], 1), round(r["width"], 1), round(r["height"], 1)] if r else None
        try:
            b = await loc.bounding_box()
        except Exception:
            return None
        return [round(b["x"], 1), round(b["y"], 1), round(b["width"], 1), round(b["height"], 1)] if b else None

    async def shot(self, name: str, clip: dict | None = None, full=False, targets: dict | None = None):
        """Still (DPR 2 → 2880x1620) + `<name>.boxes.json`: named targets and every visible text leaf (CSS px)."""
        await self.hide_cursor()
        await self.page.wait_for_timeout(250)
        boxes = {}
        for label, loc in (targets or {}).items():
            b = await self.box_of(loc)
            if b:
                boxes[label] = b
            else:
                print(f"WARNING: target {label!r} not found for shot {name}", flush=True)
        path = await super().shot(name, clip=clip, full=full)
        try:
            leaves = await self.page.evaluate(self.LEAVES_JS)
        except Exception:
            leaves = []
        path.with_suffix(".boxes.json").write_text(
            json.dumps({"viewport": [W, H], "targets": boxes, "leaves": leaves}, ensure_ascii=False), encoding="utf-8")
        return path

    async def mark_target(self, label: str, loc):
        """Recording event with a measured box: render scripts use {"at": "target:<label>"} or box "target:<label>"."""
        b = await self.box_of(loc)
        if b:
            self.mark("target", label=label, box={"x": b[0], "y": b[1], "width": b[2], "height": b[3]})
        else:
            print(f"WARNING: target {label!r} not found", flush=True)
        return b

    async def hover(self, locator, label="", steps=22, pause=900):
        box = await self.move_to(locator, steps=steps, pause=150)
        self.mark("hover", label=label, box=box)
        await self.page.wait_for_timeout(pause)
        return box

    async def text(self, n=6000):
        return await self.page.evaluate(f"() => document.body.innerText.slice(0, {n})")

    # ------------------------------------------------------------- DOM-measured boxes
    LEAF_JS = r"""([text, o]) => { o = o || {};
      const match = (t) => o.prefix ? t.startsWith(text) : t === text;
      const inside = (r) => r.width >= 1 && r.height >= 1 && (o.xmin == null || r.x >= o.xmin) && (o.xmax == null || r.x <= o.xmax)
                         && (o.ymin == null || r.y >= o.ymin) && (o.ymax == null || r.y <= o.ymax);
      const hits = [];
      for (const e of document.querySelectorAll('*')) {
        const t = (e.innerText || '').trim(); if (!match(t)) continue;
        if ([...e.children].some(c => match((c.innerText || '').trim()))) continue;      // deepest element only
        const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none') continue;
        if (inside(e.getBoundingClientRect())) hits.push(e); }
      const e = hits[o.nth || 0]; if (!e) return null;
      let a = e;
      for (let i = 0; i < (o.up || 0) && a.parentElement; i++) a = a.parentElement;
      if (o.must) { let b = e; while (b && !o.must.every(m => (b.innerText || '').includes(m))) b = b.parentElement; if (b) a = b; }
      if (o.minw || o.minh) { while (a.parentElement) { const r = a.getBoundingClientRect();
          if ((!o.minw || r.width >= o.minw) && (!o.minh || r.height >= o.minh)) break; a = a.parentElement; } }
      const r = a.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }"""

    ROLE_JS = r"""([sel, o]) => { o = o || {};
      for (const e of document.querySelectorAll(sel)) { const r = e.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) continue; if (o.xmin != null && r.x < o.xmin) continue;
        if (o.text && !(e.innerText || '').includes(o.text)) continue;
        return [r.x, r.y, r.width, r.height]; }
      return null; }"""

    async def lb(self, text, **o):
        """Box [x, y, w, h] (CSS px) of the deepest visible element whose text is `text` (or an ancestor:
        up=n levels, must=[strings it must contain], minw/minh). Filters: xmin/xmax/ymin/ymax/nth/prefix."""
        b = await self.page.evaluate(self.LEAF_JS, [text, o])
        return [round(v, 1) for v in b] if b else None

    async def rb(self, selector, **o):
        b = await self.page.evaluate(self.ROLE_JS, [selector, o])
        return [round(v, 1) for v in b] if b else None

    @staticmethod
    def union(*boxes):
        bs = [b for b in boxes if b]
        x0, y0 = min(b[0] for b in bs), min(b[1] for b in bs)
        x1, y1 = max(b[0] + b[2] for b in bs), max(b[1] + b[3] for b in bs)
        return [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]

    async def move_box(self, box, steps=22, pause=250):
        x, y = box[0] + box[2] / 2, box[1] + box[3] / 2
        await self.page.mouse.move(x, y, steps=steps)
        await self.page.wait_for_timeout(pause)

    async def click_box(self, box, label="", steps=22, pause=350):
        await self.move_box(box, steps=steps)
        self.mark("click", label=label, box={"x": box[0], "y": box[1], "width": box[2], "height": box[3]})
        await self.page.mouse.down()
        await self.page.wait_for_timeout(70)
        await self.page.mouse.up()
        await self.page.wait_for_timeout(pause)
        return box

    async def hover_box(self, box, label="", steps=22, pause=900):
        await self.move_box(box, steps=steps, pause=150)
        self.mark("hover", label=label, box={"x": box[0], "y": box[1], "width": box[2], "height": box[3]})
        await self.page.wait_for_timeout(pause)
        return box

    SCROLLER_AT_JS = r"""([x, y, tag]) => { document.querySelectorAll(`[data-gc-scroll="${tag}"]`).forEach(o => o.removeAttribute('data-gc-scroll'));
      let e = document.elementFromPoint(x, y);
      while (e) { const cs = getComputedStyle(e);
        if (/(auto|scroll)/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 4) { e.setAttribute('data-gc-scroll', tag); return e.scrollTop; }
        e = e.parentElement; }
      return null; }"""

    SMOOTH_JS = r"""([tag, top, dur]) => new Promise(res => { const s = document.querySelector(`[data-gc-scroll="${tag}"]`);
      if (!s) return res(null); const y0 = s.scrollTop; const t0 = performance.now();
      const f = (t) => { const k = Math.min(1, (t - t0) / dur); const e = k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        s.scrollTop = y0 + (top - y0) * e; if (k < 1) requestAnimationFrame(f); else res(s.scrollTop); };
      requestAnimationFrame(f); })"""

    async def scroller(self, x, y, tag):
        """Tag the scrollable ancestor of the element at (x, y); returns its scrollTop (None if none)."""
        return await self.page.evaluate(self.SCROLLER_AT_JS, [x, y, tag])

    async def smooth_scroll(self, tag, top, dur=700, settle=500):
        """Deterministic eased scroll of a tagged scroller to `top` (real page scroll, ~0.7 s)."""
        y = await self.page.evaluate(self.SMOOTH_JS, [tag, top, dur])
        await self.page.wait_for_timeout(settle)
        return y
