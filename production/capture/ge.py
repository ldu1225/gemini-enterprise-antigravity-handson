"""Helpers to drive the REAL Gemini Enterprise web app over Chrome DevTools Protocol.

All screenshots / recordings are captured from the live product UI (no mockups).
The demo Chrome instance must already be running with --remote-debugging-port=9222
and be signed in to the Gemini Enterprise app.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import time
from pathlib import Path

from playwright.async_api import async_playwright, Page

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "production" / "assets" / "shots"
RECS = ROOT / "production" / "assets" / "recordings"
SHOTS.mkdir(parents=True, exist_ok=True)
RECS.mkdir(parents=True, exist_ok=True)

CDP_URL = os.environ.get("GE_CDP_URL", "http://localhost:9222")
# The Gemini Enterprise web app used for the recordings: a clean demo app (fictional Cymbal content only).
# Set GE_APP_CID to your app's config id (the <cid> in https://vertexaisearch.cloud.google.com/us/home/cid/<cid>).
APP_CID = os.environ.get("GE_APP_CID", "YOUR_GE_APP_CID")
APP_HOME = f"https://vertexaisearch.cloud.google.com/us/home/cid/{APP_CID}"

# 1440x810 CSS px. Screencast frames are always CSS-sized (1440x810); stills use CDP at DPR 2 (2880x1620).
VIEW_W, VIEW_H, DPR = 1440, 810, 2


class GE:
    def __init__(self):
        self.pw = None
        self.browser = None
        self.ctx = None
        self.page: Page | None = None
        self.cdp = None
        self._frames: list[tuple[float, bytes]] = []
        self._recording = False
        self.events: list[dict] = []
        self._t0 = None

    async def __aenter__(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(CDP_URL)
        self.ctx = self.browser.contexts[0]
        pages = [p for p in self.ctx.pages if APP_CID in p.url]
        self.page = pages[0] if pages else await self.ctx.new_page()
        await self.page.bring_to_front()
        self.cdp = await self.ctx.new_cdp_session(self.page)
        await self.set_viewport()
        return self

    async def __aexit__(self, *exc):
        try:
            if self._recording:
                await self.stop_recording("aborted")
        finally:
            # keep the page open for the next script; just detach
            await self.pw.stop()

    async def set_viewport(self, w=VIEW_W, h=VIEW_H, dpr=DPR):
        await self.cdp.send(
            "Emulation.setDeviceMetricsOverride",
            {"width": w, "height": h, "deviceScaleFactor": dpr, "mobile": False},
        )

    async def goto(self, url=APP_HOME, wait=4000, sidebar=True):
        await self.page.goto(url, wait_until="domcontentloaded")
        await self.page.wait_for_timeout(wait)
        if sidebar:
            await self.ensure_sidebar()
        await self.install_cursor()

    async def ensure_sidebar(self):
        """Expand the left navigation if it is collapsed (state persists across pages)."""
        p = self.page
        for label in ("사이드바 열기", "Open sidebar"):
            loc = p.locator(f'[aria-label="{label}"]')
            for i in range(await loc.count()):
                b = await loc.nth(i).bounding_box()
                if b and b["width"] > 2:
                    await loc.nth(i).click()
                    await p.wait_for_timeout(800)
                    return True
        return False

    async def shot(self, name: str, clip: dict | None = None, full=False):
        """High-res still via CDP (device pixels, DPR 2 => 2880x1620)."""
        path = SHOTS / f"{name}.png"
        params = {"format": "png", "captureBeyondViewport": False}
        if clip:
            params["clip"] = {**clip, "scale": 1}
        res = await self.cdp.send("Page.captureScreenshot", params)
        path.write_bytes(base64.b64decode(res["data"]))
        self.mark("shot", name=name)
        return path

    # ------------------------------------------------------------------ cursor
    async def install_cursor(self):
        """Inject a visible demo cursor + click ripple (CDP screencasts don't include the OS cursor)."""
        js = r"""
        (() => {
          if (window.__demoCursor) return;
          const NS = 'http://www.w3.org/2000/svg';
          const wrap = document.createElement('div');
          wrap.id = '__demo_cursor';
          Object.assign(wrap.style, {position:'fixed', left:'0px', top:'0px', width:'28px', height:'28px',
            zIndex: 2147483647, pointerEvents:'none', transform:'translate(-200px,-200px)',
            transition:'transform 0.06s linear', filter:'drop-shadow(0 2px 3px rgba(0,0,0,.35))'});
          const svg = document.createElementNS(NS, 'svg');
          svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('width', '28'); svg.setAttribute('height', '28');
          const p = document.createElementNS(NS, 'path');
          p.setAttribute('d', 'M4 2 L4 19 L8.5 14.8 L11.6 21.5 L14.4 20.3 L11.3 13.7 L17.5 13.4 Z');
          p.setAttribute('fill', '#ffffff'); p.setAttribute('stroke', '#111111'); p.setAttribute('stroke-width', '1.4');
          p.setAttribute('stroke-linejoin', 'round');
          svg.appendChild(p); wrap.appendChild(svg);
          document.documentElement.appendChild(wrap);
          window.__demoCursor = wrap;
          document.addEventListener('mousemove', e => {
            wrap.style.transform = `translate(${e.clientX - 4}px, ${e.clientY - 2}px)`;
          }, true);
          document.addEventListener('mousedown', e => {
            const r = document.createElement('div');
            Object.assign(r.style, {position:'fixed', left:(e.clientX-18)+'px', top:(e.clientY-18)+'px', width:'36px', height:'36px',
              borderRadius:'50%', border:'3px solid rgba(66,133,244,.95)', background:'rgba(66,133,244,.18)',
              zIndex:2147483646, pointerEvents:'none', transform:'scale(.4)', opacity:'1',
              transition:'transform .45s ease-out, opacity .45s ease-out'});
            document.documentElement.appendChild(r);
            requestAnimationFrame(() => { r.style.transform = 'scale(1.6)'; r.style.opacity = '0'; });
            setTimeout(() => r.remove(), 600);
          }, true);
        })();
        """
        await self.page.evaluate(js)

    async def hide_cursor(self):
        await self.page.evaluate("() => { const c=document.getElementById('__demo_cursor'); if(c) c.style.transform='translate(-200px,-200px)'; }")

    # ------------------------------------------------------------- interaction
    async def vis(self, selector: str, timeout=15000):
        """First visible element matching a CSS selector (pierces shadow DOM)."""
        loc = self.page.locator(selector)
        t0 = time.monotonic()
        while (time.monotonic() - t0) * 1000 < timeout:
            n = await loc.count()
            for i in range(n):
                el = loc.nth(i)
                try:
                    b = await el.bounding_box()
                except Exception:
                    b = None
                if b and b["width"] > 2 and b["height"] > 2:
                    return el
            await self.page.wait_for_timeout(250)
        raise RuntimeError(f"no visible element for {selector}")

    async def vis_label(self, label: str, timeout=15000):
        return await self.vis(f'[aria-label="{label}"]', timeout)

    async def vis_text(self, text: str, exact=True, timeout=15000):
        loc = self.page.get_by_text(text, exact=exact)
        t0 = time.monotonic()
        while (time.monotonic() - t0) * 1000 < timeout:
            n = await loc.count()
            for i in range(n):
                el = loc.nth(i)
                try:
                    b = await el.bounding_box()
                except Exception:
                    b = None
                if b and b["width"] > 2 and b["height"] > 2:
                    return el
            await self.page.wait_for_timeout(250)
        raise RuntimeError(f"no visible text {text}")

    async def move_to(self, locator, steps=22, pause=250):
        await locator.scroll_into_view_if_needed()
        box = await locator.bounding_box()
        if not box:
            raise RuntimeError("element has no bounding box")
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        await self.page.mouse.move(x, y, steps=steps)
        await self.page.wait_for_timeout(pause)
        return box

    async def click(self, locator, label: str = "", steps=22, pause=350):
        box = await self.move_to(locator, steps=steps)
        self.mark("click", label=label, box=box)
        await self.page.mouse.down()
        await self.page.wait_for_timeout(70)
        await self.page.mouse.up()
        await self.page.wait_for_timeout(pause)
        return box

    async def type_text(self, text: str, delay=35, label: str = ""):
        self.mark("type_start", label=label, chars=len(text))
        await self.page.keyboard.type(text, delay=delay)
        self.mark("type_end", label=label)

    async def insert_text(self, text: str, label: str = ""):
        """Paste-like insertion for long prompts (keeps video short)."""
        self.mark("paste", label=label, chars=len(text))
        await self.page.keyboard.insert_text(text)

    # ------------------------------------------------------- generation wait
    PROBE_JS = r"""
    () => {
      let n = 0, busy = false;
      const busyRe = /(중지|Stop)/;
      function walk(root) {
        for (const e of root.querySelectorAll('*')) {
          if (e.shadowRoot) { n += (e.shadowRoot.textContent || '').length; walk(e.shadowRoot); }
          const al = e.getAttribute && (e.getAttribute('aria-label') || '');
          if (al && busyRe.test(al)) {
            const r = e.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) busy = true;
          }
        }
      }
      n += (document.body.textContent || '').length;
      walk(document);
      return {n, busy};
    }
    """

    async def wait_answer_done(self, timeout=240, stable=5.0, min_wait=4.0, label=""):
        """Wait until the assistant finished streaming: no visible stop button and text stable."""
        p = self.page
        self.mark("wait_start", label=label)
        t0 = time.monotonic()
        last_n, last_change = -1, time.monotonic()
        await p.wait_for_timeout(int(min_wait * 1000))
        while time.monotonic() - t0 < timeout:
            st = await p.evaluate(self.PROBE_JS)
            now = time.monotonic()
            if st["n"] != last_n:
                last_n, last_change = st["n"], now
            if not st["busy"] and now - last_change >= stable:
                break
            await p.wait_for_timeout(700)
        self.mark("wait_end", label=label, secs=round(time.monotonic() - t0, 1))
        return time.monotonic() - t0

    # ------------------------------------------------------- brand-leak guard
    BRANDS = ["삼성", "Samsung", "SK", "현대", "Hyundai", "롯데", "한화", "포스코", "POSCO",
              "GS", "CJ", "네이버", "카카오", "쿠팡", "Bespoke", "비스포크", "다이슨", "Dyson", "코웨이", "위닉스",
              "샤오미", "Xiaomi", "Apple", "애플", "아마존", "Amazon"]
    SCAN_JS = r"""
    () => { const out = []; const seen = new Set();
      const w = (root) => { for (const e of root.querySelectorAll('*')) { if (e.shadowRoot) w(e.shadowRoot);
        if (e.children.length) continue; const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;
        for (const s of [(e.innerText || e.textContent || '').trim(), e.getAttribute('aria-label') || '']) {
          if (s && !seen.has(s)) { seen.add(s); out.push(s); } } } };
      w(document); return out; }
    """

    async def brand_scan(self, extra: list[str] | None = None, scroll_all=True) -> list[str]:
        """Return visible strings that contain a real brand name (whole-word match for latin brands)."""
        import re
        p = self.page
        texts: list[str] = []
        if scroll_all:
            # main chat scroller: walk top -> bottom so lazily rendered parts are seen
            await p.mouse.wheel(0, -40000)
            await p.wait_for_timeout(400)
            for _ in range(30):
                texts += await p.evaluate(self.SCAN_JS)
                before = await p.evaluate("() => { const s=[...document.querySelectorAll('*')].find(e=>e.scrollHeight>e.clientHeight+50 && getComputedStyle(e).overflowY!='visible'); return s? s.scrollTop: 0 }")
                await p.mouse.wheel(0, 600)
                await p.wait_for_timeout(250)
                after = await p.evaluate("() => { const s=[...document.querySelectorAll('*')].find(e=>e.scrollHeight>e.clientHeight+50 && getComputedStyle(e).overflowY!='visible'); return s? s.scrollTop: 0 }")
                if after == before:
                    break
        texts += await p.evaluate(self.SCAN_JS)
        hits = []
        for b in self.BRANDS + (extra or []):
            pat = re.compile(rf"(?<![A-Za-z]){re.escape(b)}(?![A-Za-z])") if b.isascii() else re.compile(re.escape(b))
            hits += [f"{b}: {t[:90]}" for t in set(texts) if pat.search(t)]
        return sorted(set(hits))

    # --------------------------------------------------------------- recording
    def mark(self, kind: str, **kw):
        t = time.monotonic()
        rel = (t - self._t0) if self._t0 else None
        # "wall" uses the same epoch clock as CDP screencast frame metadata.timestamp
        self.events.append({"t": rel, "wall": time.time(), "kind": kind, **kw})

    async def start_recording(self, quality=88):
        self._frames = []
        self.events = []
        self._t0 = time.monotonic()
        self._recording = True
        await self.set_viewport()  # re-assert: the override was sometimes dropped after navigations

        def on_frame(params):
            ts = params.get("metadata", {}).get("timestamp", time.time())
            self._frames.append((ts, base64.b64decode(params["data"])))
            asyncio.ensure_future(self.cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]}))

        self.cdp.on("Page.screencastFrame", on_frame)
        await self.cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": quality, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1},
        )
        self.mark("rec_start")

    async def set_rate(self, every_nth: int = 1, quality: int = 88):
        """Restart screencast with a different frame decimation (1 = all frames)."""
        if not self._recording:
            return
        await self.cdp.send("Page.stopScreencast")
        await self.cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": quality, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": every_nth},
        )
        self.mark("rate", every_nth=every_nth)

    async def stop_recording(self, name: str):
        self.mark("rec_stop")
        await self.cdp.send("Page.stopScreencast")
        self._recording = False
        out = RECS / name
        frames_dir = out / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        index = []
        for i, (ts, data) in enumerate(self._frames):
            fn = f"{i:06d}.jpg"
            (frames_dir / fn).write_bytes(data)
            index.append({"file": fn, "ts": ts})
        (out / "frames.json").write_text(json.dumps(index))
        (out / "events.json").write_text(json.dumps(self.events, ensure_ascii=False, indent=1))
        return out, len(index)


def run(coro):
    asyncio.run(coro)
