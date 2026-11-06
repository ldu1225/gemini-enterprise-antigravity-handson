"""Showcase recorder — film a REAL output file (HTML the agent built) in an own headless Chromium, crisp at 2x.

Why not the CDP screencast: in headless mode Page.startScreencast always delivers CSS-sized frames (1440x810), which
look soft once upscaled/zoomed in the 1920x1080 video. Here frames are Page.captureScreenshot JPEGs at DPR 2
(2880x1620 = CSS 1440x810, css_scale 2.0): ~15–18 fps while something moves (`fast()` windows around cursor moves and
clicks) and ~3 fps during static holds. Frame timestamps and event `wall` times use the same epoch clock (time.time()),
the format production/render/engine/recording.py reads (frames.json [{file, ts}], events.json, meta.json).

Isolation: own browser instance, page content only (no browser chrome, no URL bar, nothing from the user's screen),
never the demo Chrome (:9222) or the recording Antigravity instance (:9334).
"""
from __future__ import annotations
import os

import asyncio
import base64
import json
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ge import GE, RECS, SHOTS  # noqa: E402  (demo-cursor JS, event conventions)

W, H, DPR = 1440, 810, 2
# leak denylist for captured pages: local paths + anything you add via LEAK_DENYLIST="a,b,c" (e.g. real
# customer names, your username, your project id)
BAD = ["/Users/", "/home/", "file://"] + [w for w in os.environ.get("LEAK_DENYLIST", "").split(",") if w]

LEAVES_JS = r"""() => { const out = []; const seen = new Set();
  for (const e of document.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
    const st = getComputedStyle(e); if (st.visibility === 'hidden' || st.display === 'none' || +st.opacity === 0) continue;
    if (e.id === '__demo_cursor' || e.closest('#__demo_cursor')) continue;
    const al = e.getAttribute('aria-label') || e.getAttribute('title') || '';
    const t = e.children.length ? '' : (e.innerText || e.textContent || '').trim();
    if (!t && !al) continue;
    const key = (t || al) + '|' + Math.round(r.x) + ',' + Math.round(r.y) + ',' + Math.round(r.width);
    if (seen.has(key)) continue; seen.add(key);
    out.push({t: t.slice(0, 240), a: al.slice(0, 120), tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '',
              b: [Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]});
  }
  return out; }"""

# visible element box: nth match of `sel` (inside `root` selector if given), optional text filter / closest() ancestor
BOX_JS = r"""([sel, nth, up, txt, root]) => {
  const R = root ? (document.querySelector(root) || document) : document;
  let els = [...R.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect();
    return r.width > 2 && r.height > 2 && r.bottom > 0 && r.top < innerHeight; });
  if (txt) els = els.filter(e => (e.textContent || '').includes(txt));
  let e = els[nth || 0]; if (!e) return null;
  if (up) { const a = e.closest(up); if (a) e = a; }
  const r = e.getBoundingClientRect();
  const x0 = Math.max(0, r.x), y0 = Math.max(0, r.y), x1 = Math.min(innerWidth, r.right), y1 = Math.min(innerHeight, r.bottom);
  return [x0, y0, x1 - x0, y1 - y0].map(v => Math.round(v * 10) / 10); }"""


class Showcase(GE):
    def __init__(self):
        super().__init__()
        self._fast = 0
        self._task = None
        # Page.captureScreenshot running concurrently swallows mouse down/up in headless Chromium → input and
        # captures never overlap (the lock is held for each capture and around every press)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ lifecycle
    async def open(self, url: str, settle=1500):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch()
        self.ctx = await self.browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=DPR)
        self.page = await self.ctx.new_page()
        self.cdp = await self.ctx.new_cdp_session(self.page)
        await self.set_viewport(W, H, DPR)
        await self.page.goto(url, wait_until="load")
        await self.page.wait_for_timeout(settle)
        return self

    async def scan(self, extra=()):
        text = await self.page.evaluate("document.body.innerText")
        hits = [b for b in list(BAD) + list(extra) if b in text]
        print("brand/path scan:", hits or "clean")
        if hits:
            raise SystemExit(f"page text contains {hits} — do not capture")

    async def close(self):
        try:
            await self.browser.close()
        finally:
            await self.pw.stop()

    # ------------------------------------------------------------------ measuring
    async def box(self, sel, nth=0, up=None, txt=None, root=None):
        return await self.page.evaluate(BOX_JS, [sel, nth, up, txt, root])

    async def target(self, label, sel, nth=0, up=None, txt=None, root=None, mark=True):
        b = await self.box(sel, nth, up, txt, root)
        if not b:
            print(f"  !! no box for {label} ({sel})")
            return None
        if mark:
            self.mark("target", label=label, box={"x": b[0], "y": b[1], "width": b[2], "height": b[3]})
        return b

    async def text_box(self, text, exact=False):
        loc = self.page.get_by_text(text, exact=exact)
        for i in range(await loc.count()):
            b = await loc.nth(i).bounding_box()
            if b and b["width"] > 2 and 0 <= b["y"] < H:
                return [round(b["x"], 1), round(b["y"], 1), round(b["width"], 1), round(b["height"], 1)]
        return None

    # ------------------------------------------------------------------ input (events carry DOM boxes)
    @asynccontextmanager
    async def fast(self):
        self._fast += 1
        try:
            yield
        finally:
            await asyncio.sleep(0.35)
            self._fast -= 1

    async def move(self, x, y, steps=20):
        async with self.fast():
            await self.page.mouse.move(x, y, steps=steps)

    async def click_box(self, b, label, pause=650):
        x, y = b[0] + b[2] / 2, b[1] + b[3] / 2
        box = {"x": b[0], "y": b[1], "width": b[2], "height": b[3]}
        async with self.fast():
            await self.page.mouse.move(x, y, steps=24)
            self.mark("hover", label=label, box=box)
            await self.page.wait_for_timeout(pause)
            self.mark("click", label=label, box=box)
            async with self._lock:
                await self.page.mouse.down()
                await self.page.wait_for_timeout(70)
                await self.page.mouse.up()
                await self.page.wait_for_timeout(120)
            await self.page.wait_for_timeout(380)
        return box

    async def select_box(self, b, value, label, pause=650):
        """Real <select>: hover + click event on its box, then pick the option (headless has no native popup)."""
        box = await self.click_box(b, label, pause)
        async with self.fast():
            sel = await self.page.evaluate_handle(
                "([x, y]) => document.elementFromPoint(x, y).closest('select')", [b[0] + b[2] / 2, b[1] + b[3] / 2])
            async with self._lock:
                await sel.as_element().select_option(value)
            self.mark("select", label=label, value=value, box=box)
            await self.page.wait_for_timeout(700)
        return box

    async def key(self, key, label=None):
        async with self.fast():
            async with self._lock:
                await self.page.keyboard.press(key)
                await self.page.wait_for_timeout(120)
            if label:
                self.mark("key", label=label, key=key)
            await self.page.wait_for_timeout(300)

    async def scroll_to(self, y, label=None, ms=900):
        async with self.fast():
            await self.page.evaluate(
                "([y, ms]) => new Promise(res => { const y0 = scrollY, t0 = performance.now();"
                " const f = t => { const k = Math.min(1, (t - t0) / ms), e = k < .5 ? 2*k*k : 1 - Math.pow(-2*k + 2, 2) / 2;"
                " scrollTo(0, y0 + (y - y0) * e); k < 1 ? requestAnimationFrame(f) : res(); }; requestAnimationFrame(f); })",
                [y, ms])
            if label:
                self.mark("scroll", label=label, y=y)
            await self.page.wait_for_timeout(300)

    # ------------------------------------------------------------------ recording (screenshot-based, 2x)
    async def _shoot(self):
        while self._recording:
            t0 = time.time()
            try:
                async with self._lock:
                    t0 = time.time()
                    r = await self.cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 88})
            except Exception as e:  # page closing
                print("capture stopped:", e)
                break
            t1 = time.time()
            self._frames.append(((t0 + t1) / 2, base64.b64decode(r["data"])))
            if not self._fast:
                await asyncio.sleep(max(0.0, 0.33 - (t1 - t0)))

    async def start_rec(self):
        self._frames, self.events = [], []
        self._t0 = time.monotonic()
        self._recording = True
        self.mark("rec_start")
        self._task = asyncio.ensure_future(self._shoot())
        await asyncio.sleep(0.2)

    async def stop_rec(self, name: str, source: str):
        self.mark("rec_stop")
        await asyncio.sleep(0.4)
        self._recording = False
        if self._task:
            await self._task
        out = RECS / name
        if out.exists():
            for f in (out / "frames").glob("*.jpg"):
                f.unlink()
        frames_dir = out / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        index = []
        for i, (ts, data) in enumerate(sorted(self._frames, key=lambda f: f[0])):
            fn = f"{i:06d}.jpg"
            (frames_dir / fn).write_bytes(data)
            index.append({"file": fn, "ts": ts})
        (out / "frames.json").write_text(json.dumps(index))
        (out / "events.json").write_text(json.dumps(self.events, ensure_ascii=False, indent=1))
        (out / "meta.json").write_text(json.dumps({"css_width": W, "css_height": H, "dpr": DPR, "source": source},
                                                  ensure_ascii=False))
        print("recording", out, len(index), "frames")
        return out, len(index)

    # ------------------------------------------------------------------ stills
    async def still(self, stem: str, targets: dict, source: str, hide_cursor=True):
        if hide_cursor:
            await self.hide_cursor()
            await self.page.wait_for_timeout(150)
        res = await self.cdp.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        path = SHOTS / f"{stem}.png"
        path.write_bytes(base64.b64decode(res["data"]))
        leaves = await self.page.evaluate(LEAVES_JS)
        path.with_suffix(".boxes.json").write_text(json.dumps(
            {"viewport": [W, H], "targets": targets, "leaves": leaves, "source": source}, ensure_ascii=False),
            encoding="utf-8")
        print(stem, targets)
        return path
