"""Explore Gemini Notebook (iframe) step by step. Each call performs ONE action then dumps controls + low-res still.

usage: python3 nb_explore.py <name> [--text "새로 만들기"] [--label "aria"] [--upload path] [--type "text"] [--enter]
"""
import asyncio, sys, json, argparse
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from ge import GE, SHOTS
from helpers import DUMP_JS

OUT = SHOTS / '_explore'

FIND_JS = r"""
([needle, exact]) => {
  const res = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      const t = (n.nodeValue || '').trim();
      if (!t) continue;
      if (exact ? t === needle : t.includes(needle)) {
        const el = n.parentElement; if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 4 && r.height > 4) res.push({x: r.x, y: r.y, w: r.width, h: r.height, t});
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return res;
}
"""


def nb_frame(page):
    for f in page.frames:
        if '/notebooklm/' in f.url:
            return f
    return None


async def frame_offset(page, frame):
    el = await frame.frame_element()
    b = await el.bounding_box()
    return b['x'], b['y']


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('--text')
    ap.add_argument('--contains', action='store_true')
    ap.add_argument('--label')
    ap.add_argument('--css')
    ap.add_argument('--upload')
    ap.add_argument('--type')
    ap.add_argument('--enter', action='store_true')
    ap.add_argument('--wait', type=int, default=3000)
    ap.add_argument('--nth', type=int, default=0)
    a = ap.parse_args()
    async with GE() as ge:
        p = ge.page
        f = nb_frame(p)
        if not f:
            raise SystemExit('notebook frame not found: ' + p.url)
        ox, oy = await frame_offset(p, f)
        target = None
        if a.text:
            hits = await f.evaluate(FIND_JS, [a.text, not a.contains])
            print('hits', [(round(h['x']), round(h['y']), h['t'][:30]) for h in hits][:6], flush=True)
            if hits:
                h = hits[a.nth]
                target = (ox + h['x'] + h['w'] / 2, oy + h['y'] + h['h'] / 2)
        if a.label:
            loc = f.locator(f'[aria-label="{a.label}"]')
            for i in range(await loc.count()):
                b = await loc.nth(i).bounding_box()
                if b and b['width'] > 2:
                    target = (b['x'] + b['width'] / 2, b['y'] + b['height'] / 2)
                    break
        if a.css:
            loc = f.locator(a.css)
            for i in range(await loc.count()):
                b = await loc.nth(i).bounding_box()
                if b and b['width'] > 2:
                    target = (b['x'] + b['width'] / 2, b['y'] + b['height'] / 2)
                    print('css target', a.css, b, flush=True)
                    break
        if target:
            await p.mouse.move(*target, steps=12)
            if a.upload:
                async with p.expect_file_chooser() as fc:
                    await p.mouse.click(*target)
                chooser = await fc.value
                await chooser.set_files(a.upload.split('|'))
                print('uploaded', a.upload, flush=True)
            else:
                await p.mouse.click(*target)
            await p.wait_for_timeout(a.wait)
        if a.type:
            await p.keyboard.type(a.type, delay=15)
            if a.enter:
                await p.keyboard.press('Enter')
            await p.wait_for_timeout(a.wait)
        f = nb_frame(p) or f
        await p.screenshot(path=str(OUT / f'{a.name}.jpg'), type='jpeg', quality=55)
        print('frame url', f.url[:120], 'offset', ox, oy, flush=True)
        items = await f.evaluate(DUMP_JS)
        seen = set()
        for it in items:
            k = (it['txt'], it['al'])
            if k in seen or not (it['txt'] or it['al']):
                continue
            seen.add(k)
            print(json.dumps(it, ensure_ascii=False)[:170], flush=True)


if __name__ == "__main__":
    asyncio.run(main())
