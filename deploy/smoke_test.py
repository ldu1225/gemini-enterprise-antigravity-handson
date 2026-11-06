"""Live smoke test of the deployed portal (own headless Chromium — never touches the :9222 demo browser)."""
import asyncio, json, sys
from playwright.async_api import async_playwright

if len(sys.argv) < 2:
    sys.exit("usage: smoke_test.py <portal base url>   e.g. https://<service>-<number>.<region>.run.app/")
URL = sys.argv[1]


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel="chrome", headless=True)
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        console, failed, csp = [], [], []
        pg.on("console", lambda m: console.append((m.type, m.text[:200])) if m.type in ("error", "warning") else None)
        pg.on("requestfailed", lambda r: failed.append((r.url[:120], r.failure)))
        pg.on("response", lambda r: failed.append((r.url[:120], r.status)) if r.status >= 400 else None)
        await pg.goto(URL, wait_until="networkidle")
        await pg.wait_for_timeout(1500)
        # scroll through to trigger lazy images
        h = await pg.evaluate("document.body.scrollHeight")
        for y in range(0, h, 1400):
            await pg.evaluate(f"window.scrollTo(0, {y})")
            await pg.wait_for_timeout(120)
        await pg.wait_for_timeout(1500)
        vids = await pg.evaluate("""() => Array.from(document.querySelectorAll('video')).map(v => ({src: (v.currentSrc || (v.querySelector('source')||{}).src || '').split('/').pop(), ready: v.readyState, poster: !!v.poster}))""")
        frames = [f.url for f in pg.frames]
        imgs_broken = await pg.evaluate("""() => Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0).map(i => (i.id || i.className || i.outerHTML.slice(0, 80)))""")
        print(json.dumps({"console": console, "failed": failed, "videos": vids, "frames": frames, "broken_imgs": imgs_broken, "height": h}, ensure_ascii=False, indent=1))
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
