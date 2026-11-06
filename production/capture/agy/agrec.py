"""Drive the recording-only Antigravity desktop app instance over CDP :9334 (class AGRec).

Set AG_CDP_URL to point at another CDP endpoint (default http://localhost:9334).

Launch:  production/capture/agy/launch_ag_rec_voc.sh   (isolated HOME $AG_REC_HOME/home, workspace $AG_REC_HOME/work)
Same API as capture/ge.py (click/move_to/type_text/mark/shot/start_recording/stop_recording/brand_scan).
Canvas 1440x810 CSS, stills DPR 2 (2880x1620).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ge import GE  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

AG_CDP = os.environ.get("AG_CDP_URL", "http://localhost:9334")
W, H, DPR = 1440, 810, 2


def _is_main(p):
    return p.url.startswith("vscode-file://") and p.url.endswith("/workbench.html")


class AGRec(GE):
    k = 1.0   # DOM CSS px → capture CSS px (1440×810). 1.0 when window.zoomLevel makes the viewport exactly 1440×810

    async def __aenter__(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(AG_CDP)
        pages = [p for c in self.browser.contexts for p in c.pages if _is_main(p)]
        if not pages:
            raise RuntimeError("no Antigravity workbench on :9334 (relaunch launch_ag_rec_voc.sh)")
        self.page = pages[0]
        self.ctx = self.page.context
        self.cdp = await self.ctx.new_cdp_session(self.page)
        await self.set_viewport()
        await self.install_cursor()
        await self.measure_viewport()
        return self

    async def measure_viewport(self):
        """Electron ignores the device-metrics override for layout (it only scales the captured image), so the real
        CSS viewport decides the coordinate space of every DOM box. Boxes are converted to the 1440×810 capture space."""
        iw, ih, dpr = await self.page.evaluate("() => [innerWidth, innerHeight, devicePixelRatio]")
        self.k = W / iw
        if abs(iw - W) > 1 or abs(ih - H) > 1:
            print(f"WARNING: viewport is {iw}x{ih} (dpr {dpr:.3f}), not {W}x{H} — set window.zoomLevel so the window "
                  f"content is exactly {W}x{H} CSS px; recorded boxes are scaled by {self.k:.4f}", flush=True)
        if abs(iw / ih - W / H) > 0.01:
            print(f"WARNING: viewport aspect {iw / ih:.4f} != {W / H:.4f}: captures will be distorted", flush=True)
        return iw, ih, dpr

    def _cap(self, box):
        if not box or self.k == 1.0:
            return box
        if isinstance(box, dict):
            return {kk: (round(v * self.k, 1) if kk in ("x", "y", "width", "height") else v) for kk, v in box.items()}
        return [round(v * self.k, 1) for v in box]

    def mark(self, kind: str, **kw):
        if "box" in kw:
            kw["box"] = self._cap(kw["box"])
        super().mark(kind, **kw)

    async def set_viewport(self, w=W, h=H, dpr=DPR):
        await self.cdp.send("Emulation.setDeviceMetricsOverride",
                            {"width": w, "height": h, "deviceScaleFactor": dpr, "mobile": False})

    # ---------------------------------------------------------------- resilient recording
    # A CDP drop (Target closed) during a long agent run used to lose the whole take (frames live in memory).
    # Now: frames are always written; wait_agent() reconnects and resumes the screencast; aborted takes are saved.
    _rec_name = None

    def _on_frame(self, params):
        import base64
        ts = params.get("metadata", {}).get("timestamp", time.time())
        self._frames.append((ts, base64.b64decode(params["data"])))
        cdp = self.cdp

        async def ack():
            try:
                await cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
            except Exception:
                pass
        asyncio.ensure_future(ack())

    async def _start_screencast(self, quality=88):
        self.cdp.on("Page.screencastFrame", self._on_frame)
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": quality, "maxWidth": 1920,
                                                     "maxHeight": 1080, "everyNthFrame": 1})

    async def start_recording(self, quality=88, name=None):
        self._frames = []
        self.events = []
        self._t0 = time.monotonic()
        self._recording = True
        self._rec_name = name
        self._quality = quality
        await self.set_viewport()
        await self._start_screencast(quality)
        self.mark("rec_start")

    async def reconnect(self):
        """Re-attach to the Antigravity workbench after a CDP drop and resume the screencast (frames so far are kept)."""
        print(f"WARNING: CDP session lost — reconnecting ({len(self._frames)} frames kept)", flush=True)
        try:
            await self.pw.stop()
        except Exception:
            pass
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(AG_CDP)
        pages = [p for c in self.browser.contexts for p in c.pages if _is_main(p)]
        if not pages:
            raise RuntimeError("no Antigravity workbench on :9334 after reconnect")
        self.page = pages[0]
        self.ctx = self.page.context
        self.cdp = await self.ctx.new_cdp_session(self.page)
        await self.set_viewport()
        await self.install_cursor()
        await self.measure_viewport()
        if self._recording:
            await self._start_screencast(getattr(self, "_quality", 88))
        self.mark("reconnect", frames=len(self._frames))

    async def stop_recording(self, name: str):
        self.mark("rec_stop")
        try:
            await asyncio.wait_for(self.cdp.send("Page.stopScreencast"), 10)
        except Exception as e:  # session already gone: still save what we have
            print(f"WARNING: stopScreencast failed ({type(e).__name__}); saving {len(self._frames)} frames", flush=True)
        self._recording = False
        out = Path(__file__).resolve().parents[2] / "assets" / "recordings" / name
        frames_dir = out / "frames"
        if frames_dir.exists():
            import shutil
            shutil.rmtree(frames_dir)
        frames_dir.mkdir(parents=True, exist_ok=True)
        index = []
        for i, (ts, data) in enumerate(self._frames):
            fn = f"{i:06d}.jpg"
            (frames_dir / fn).write_bytes(data)
            index.append({"file": fn, "ts": ts})
        (out / "frames.json").write_text(json.dumps(index))
        (out / "events.json").write_text(json.dumps(self.events, ensure_ascii=False, indent=1))
        return out, len(index)

    async def __aexit__(self, *exc):
        try:
            if self._recording:
                name = f"{self._rec_name or 'take'}_aborted"
                print(f"WARNING: recording aborted — saving partial take as {name}", flush=True)
                try:
                    print(await self.stop_recording(name), flush=True)
                except Exception as e:
                    print(f"WARNING: could not save partial take: {e!r}", flush=True)
        finally:
            try:
                await self.pw.stop()
            except Exception:
                pass

    # ---------------------------------------------------------------- measured boxes (callout ground truth)
    LEAVES_JS = r"""() => { const out = []; const seen = new Set();
      for (const e of document.querySelectorAll('*')) {
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
      } return out; }"""

    async def box_of(self, loc):
        """CSS-px [x, y, w, h] of a locator or of the newest visible element containing this text."""
        el = await self.find_text(loc, exact=False) if isinstance(loc, str) else loc
        if el is None:
            return None
        try:
            b = await el.bounding_box()
        except Exception:
            return None
        return [round(b["x"], 1), round(b["y"], 1), round(b["width"], 1), round(b["height"], 1)] if b else None

    async def shot(self, name: str, clip: dict | None = None, full=False, targets: dict | None = None):
        """Still (DPR 2) + `<name>.boxes.json`: named targets and every visible text leaf with its CSS-px box."""
        boxes = {}
        for label, loc in (targets or {}).items():
            b = await self.box_of(loc)
            if b:
                boxes[label] = self._cap(b)
            else:
                print(f"WARNING: target {label!r} not found for shot {name}", flush=True)
        path = await super().shot(name, clip=clip, full=full)
        try:
            leaves = await self.page.evaluate(self.LEAVES_JS)
        except Exception:
            leaves = []
        for lf in leaves:
            lf["b"] = self._cap(lf["b"])
        path.with_suffix(".boxes.json").write_text(
            json.dumps({"viewport": [W, H], "targets": boxes, "leaves": leaves}, ensure_ascii=False), encoding="utf-8")
        return path

    async def mark_target(self, label: str, loc):
        """Recording event with a measured box: render scripts can use {"at": "target:<label>"} for a callout."""
        b = await self.box_of(loc)
        if b:
            self.mark("target", label=label, box={"x": b[0], "y": b[1], "width": b[2], "height": b[3]})
        else:
            print(f"WARNING: target {label!r} not found", flush=True)
        return b

    async def text(self, n=4000):
        return await self.page.evaluate(f"() => document.body.innerText.slice(0, {n})")

    async def press(self, key, label=""):
        self.mark("key", key=key, label=label)
        await self.page.keyboard.press(key)

    async def submit(self, label="submit"):
        self.mark("submit", label=label)
        await self.page.keyboard.press("Enter")

    async def box_at(self, x, y):
        """Bounding box of the clickable element under (x, y) (CSS px)."""
        return await self.page.evaluate(
            """([x, y]) => { let e = document.elementFromPoint(x, y);
                 for (let i = 0; e && i < 6; i++) { const r = e.getBoundingClientRect();
                   if (e.matches('button,a,[role=button],[role=menuitem],[role=option],[role=tab],li,.setting-dropdown-label') || r.width > 18) {
                     return {x: r.x, y: r.y, width: r.width, height: r.height}; }
                   e = e.parentElement; }
                 return {x: x - 12, y: y - 12, width: 24, height: 24}; }""", [x, y])

    async def click_xy(self, x, y, label="", steps=22, pause=350, box=None):
        box = box or await self.box_at(x, y)
        await self.page.mouse.move(x, y, steps=steps)
        await self.page.wait_for_timeout(250)
        self.mark("click", label=label, box=box)
        await self.page.mouse.down()
        await self.page.wait_for_timeout(70)
        await self.page.mouse.up()
        await self.page.wait_for_timeout(pause)
        return box

    async def hover(self, locator, label="", steps=22, pause=900):
        box = await self.move_to(locator, steps=steps, pause=150)
        self.mark("hover", label=label, box=box)
        await self.page.wait_for_timeout(pause)
        return box

    async def hover_xy(self, x, y, label="", steps=22, pause=900, box=None):
        box = box or await self.box_at(x, y)
        await self.page.mouse.move(x, y, steps=steps)
        self.mark("hover", label=label, box=box)
        await self.page.wait_for_timeout(pause)
        return box

    async def input_box(self):
        return await self.vis('[aria-label="Message input"]', timeout=20000)

    async def new_chat(self, record=True):
        """Agent panel header '+' (new conversation)."""
        if record:
            return await self.click_xy(1322, 53, label="새 대화")
        await self.page.mouse.click(1322, 53)
        await self.page.wait_for_timeout(600)

    async def wait_for_text(self, rx, timeout=600, label=""):
        import re as _re
        t0 = time.monotonic()
        pat = _re.compile(rx)
        while time.monotonic() - t0 < timeout:
            if pat.search(await self.text(200000)):
                return True
            await self.page.wait_for_timeout(1000)
        return False

    async def find_text(self, text, exact=True, tag=None):
        """First visible element with this text right now (no waiting), or None."""
        loc = self.page.locator(tag).filter(has_text=text) if tag else self.page.get_by_text(text, exact=exact)
        n = await loc.count()
        for i in range(n - 1, -1, -1):  # newest (lowest on screen) first
            el = loc.nth(i)
            try:
                b = await el.bounding_box()
            except Exception:
                b = None
            if b and b["width"] > 2 and b["height"] > 2 and 0 <= b["y"] < 810:
                return el
        return None

    async def approve_command(self, choice="Yes, allow this time"):
        """Answer the 'Allow running this command?' card: pick an option, then Submit."""
        if not await self.find_text("Allow running this command?"):
            return False
        opt = await self.find_text(choice, exact=True)
        if opt:
            await self.click(opt, label="허용", steps=18)
            await self.page.wait_for_timeout(400)
        sub = self.page.get_by_role("button", name="Submit")
        if await sub.count():
            sub = sub.last
            try:
                await sub.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass
            await self.click(sub, label="Submit", steps=12)
        else:
            await self.page.keyboard.press("Enter")
        await self.page.wait_for_timeout(800)
        return True

    def auto(self, commands=True, accept_all=False, proceed=False, log=True):
        """on_tick handler for wait_agent: approve commands / Accept all / Proceed automatically (all marked)."""
        async def tick():
            if commands and await self.approve_command():
                if log:
                    print("approved command", flush=True)
            if accept_all:
                b = await self.find_text("Accept all", exact=True)
                if b and not await self.find_text("Allow running this command?"):
                    await self.click(b, label="Accept all")
                    if log:
                        print("accept all", flush=True)
            if proceed:
                b = await self.find_text("Proceed", exact=True, tag="button")
                if b:
                    await self.click(b, label="Proceed")
                    if log:
                        print("proceed", flush=True)
        return tick

    # Agent panel busy probe: the app shows a stop/cancel control while the agent works
    BUSY_JS = r"""
    () => {
      let busy = false;
      for (const e of document.querySelectorAll('[aria-label],[title]')) {
        const s = (e.getAttribute('aria-label') || '') + ' ' + (e.getAttribute('title') || '');
        if (/(Stop|Cancel generation|Cancel|중지)/i.test(s)) {
          const r = e.getBoundingClientRect();
          if (r.width > 0 && r.height > 0) { busy = true; break; }
        }
      }
      // the Send button is replaced by a stop control while the agent works
      let send = false;
      for (const e of document.querySelectorAll('[aria-label="Send message"]')) {
        const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) send = true;
      }
      if (!send) busy = true;
      const queued = /Sends after agent finishes working/.test(document.body.innerText);
      return {n: document.body.innerText.length, busy, queued};
    }
    """

    async def _safe(self, coro_fn, default=None, tries=3):
        """Run an async CDP/page call; on a dropped session reconnect and retry."""
        for i in range(tries):
            try:
                return await coro_fn()
            except Exception as e:
                msg = str(e)
                if "closed" not in msg and "Target" not in msg and "disconnected" not in msg.lower():
                    raise
                await asyncio.sleep(1.5)
                try:
                    await self.reconnect()
                except Exception as e2:
                    print(f"WARNING: reconnect failed ({e2!r})", flush=True)
        return default

    async def wait_agent(self, timeout=600, stable=8.0, min_wait=5.0, label="", on_tick=None, recheck=25):
        """Wait until agent output stops changing (and no visible stop control). Survives CDP drops (reconnects)."""
        self.mark("wait_start", label=label)
        t0 = time.monotonic()
        last_n, last_change = -1, time.monotonic()
        await asyncio.sleep(min_wait)
        idle = {"n": 0, "busy": True, "queued": False}
        while time.monotonic() - t0 < timeout:
            st = await self._safe(lambda: self.page.evaluate(self.BUSY_JS), default=idle)
            now = time.monotonic()
            if st["n"] != last_n:
                last_n, last_change = st["n"], now
            if st.get("queued"):
                print("WARNING: message queued (agent still busy in background)", flush=True)
            if on_tick:
                r = await self._safe(on_tick)
                if r == "done":
                    break
            if not st["busy"] and not st.get("queued") and now - last_change >= stable:
                # the agent may resume after a backgrounded command finishes: re-check for a while
                resumed = False
                for _ in range(int(recheck)):
                    await asyncio.sleep(1.0)
                    st2 = await self._safe(lambda: self.page.evaluate(self.BUSY_JS), default=st)
                    if on_tick:
                        await self._safe(on_tick)
                    if st2["busy"] or st2["n"] != st["n"]:
                        resumed = True
                        break
                if not resumed:
                    break
                last_n, last_change = -1, time.monotonic()
            await asyncio.sleep(1.0)
        self.mark("wait_end", label=label, secs=round(time.monotonic() - t0, 1))
        return time.monotonic() - t0


async def probe(name="ag_probe"):
    async with AGRec() as j:
        await j.shot(name)
        print(await j.text(3000))


if __name__ == "__main__":
    asyncio.run(probe(*sys.argv[1:]))
