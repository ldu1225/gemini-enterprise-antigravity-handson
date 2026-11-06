"""Off-camera probe helper: python3 probe.py <action> ...
  shot NAME                 -> still of current page (also prints visible texts summary)
  menu LABEL                -> click aria-label LABEL and shot
  home                      -> goto home
  texts                     -> print visible leaf texts (y-sorted)
  js "<expr>"               -> evaluate
"""
import asyncio
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME  # noqa: E402

TEXTS_JS = r"""() => { const out=[]; const w=(r)=>{ for (const e of r.querySelectorAll('*')) { if (e.shadowRoot) w(e.shadowRoot);
  if (e.children.length && !(e.getAttribute && e.getAttribute('aria-label'))) continue; const b=e.getBoundingClientRect(); if (b.width<1||b.height<1||b.y>820||b.y<-5) continue;
  const t=(e.innerText||e.textContent||'').trim().slice(0,60); const a=e.getAttribute&&e.getAttribute('aria-label')||'';
  if (t||a) out.push([Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height),t,a]); } }; w(document);
  return out; }"""


async def texts(ge):
    seen = set()
    for x, y, w, h, t, a in sorted(await ge.page.evaluate(TEXTS_JS), key=lambda r: (r[1], r[0])):
        k = (x, y, t, a)
        if k in seen:
            continue
        seen.add(k)
        print(f'{x:5d}{y:5d}{w:5d}{h:4d} | {t!r} | {a!r}')


async def main(args):
    async with GE() as ge:
        await ge.install_cursor()
        cmd = args[0]
        if cmd == 'home':
            await ge.goto(APP_HOME + '?hl=ko', wait=4500)
        elif cmd == 'goto':
            await ge.goto(args[1], wait=5000)
        elif cmd == 'menu':
            await ge.click(await ge.vis_label(args[1]), steps=4)
            await ge.page.wait_for_timeout(1200)
        elif cmd == 'clicktext':
            await ge.click(await ge.vis_text(args[1], exact=len(args) < 3), steps=4)
            await ge.page.wait_for_timeout(1500)
        elif cmd == 'clickxy':
            await ge.page.mouse.click(float(args[1]), float(args[2]))
            await ge.page.wait_for_timeout(1500)
        elif cmd == 'key':
            await ge.page.keyboard.press(args[1])
            await ge.page.wait_for_timeout(800)
        elif cmd == 'js':
            print(await ge.page.evaluate(args[1]))
        if cmd in ('texts',) or '--texts' in args:
            await texts(ge)
        if '--shot' in args:
            name = args[args.index('--shot') + 1]
            await ge.shot(name)
            print('shot', name)
        print('URL', ge.page.url)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
