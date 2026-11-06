"""Drive the REAL Antigravity desktop app (recording-only instance, CDP :9333) — same API as capture/ge.py.

Start the instance first:  production/capture/agy/launch_rec.sh
Viewport: 1440x810 CSS px, stills at DPR 2 (2880x1620). Recordings land in production/assets/recordings/<name>/.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ge import GE  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

AGY_CDP = os.environ.get("AGY_CDP_URL", "http://localhost:9333")
AGY_W, AGY_H, AGY_DPR = 1440, 810, 2  # same canvas as GE so the render engine and portal treat both alike


class AGY(GE):
    async def __aenter__(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(AGY_CDP)
        pages = [p for c in self.browser.contexts for p in c.pages if p.url.startswith("https://127.0.0.1")]
        if not pages:
            raise RuntimeError("no Antigravity window on :9333 (relaunch with launch_rec.sh)")
        self.page = pages[0]
        self.ctx = self.page.context
        self.cdp = await self.ctx.new_cdp_session(self.page)
        await self.set_viewport()
        await self.install_cursor()
        return self

    async def set_viewport(self, w=AGY_W, h=AGY_H, dpr=AGY_DPR):
        await self.cdp.send("Emulation.setDeviceMetricsOverride",
                            {"width": w, "height": h, "deviceScaleFactor": dpr, "mobile": False})

    async def refresh_page(self):
        """Re-attach after the app navigates to a new origin/port (e.g. onboarding -> main)."""
        pages = [p for c in self.browser.contexts for p in c.pages if p.url.startswith("https://127.0.0.1")]
        if pages and pages[0] is not self.page:
            self.page = pages[0]
            self.cdp = await self.page.context.new_cdp_session(self.page)
            await self.set_viewport()
        await self.install_cursor()
