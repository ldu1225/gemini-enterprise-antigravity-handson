"""Chat housekeeping for the Cymbal GE app (not recorded).
  python3 chats.py list
  python3 chats.py delete <substr> [<substr> ...]   # delete every chat whose title contains a substring
  python3 chats.py scan <substr>                     # open chat and run the brand-leak scan
"""
import asyncio
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME  # noqa: E402

HOME = APP_HOME + '?hl=ko'
LIST_JS = r"""() => { const out=[]; const w=(r)=>{ for (const e of r.querySelectorAll('a[href*="/r/session/"]')) {
  const b=e.getBoundingClientRect(); out.push({t:(e.innerText||e.getAttribute('aria-label')||'').trim(), href:e.getAttribute('href'), y:b.y, w:b.width}); }
  for (const e of r.querySelectorAll('*')) if (e.shadowRoot) w(e.shadowRoot); }; w(document); return out; }"""


async def chats(ge):
    await ge.goto(HOME, wait=4500)
    seen, out = set(), []
    for c in await ge.page.evaluate(LIST_JS):
        if c['href'] not in seen and c['t']:
            seen.add(c['href'])
            out.append(c)
    return out


async def delete_current(ge):
    p = ge.page
    await ge.click(await ge.vis('[aria-label="작업 메뉴"]'), steps=4)
    await p.wait_for_timeout(900)
    await ge.click(await ge.vis_text('삭제'), steps=4)
    await p.wait_for_timeout(1200)
    btns = p.get_by_role('button', name='삭제')
    for i in range(await btns.count() - 1, -1, -1):
        b = await btns.nth(i).bounding_box()
        if b and b['width'] > 2:
            await ge.click(btns.nth(i), steps=4)
            break
    await p.wait_for_timeout(2000)


async def main(cmd, args):
    async with GE() as ge:
        if cmd == 'list':
            for c in await chats(ge):
                print(repr(c['t'][:70]), c['href'][-30:])
        elif cmd == 'delete':
            while True:
                victims = [c for c in await chats(ge) if any(a in c['t'] for a in args)]
                if not victims:
                    break
                c = victims[0]
                print('deleting', c['t'][:60])
                await ge.goto('https://vertexaisearch.cloud.google.com' + c['href'] if c['href'].startswith('/') else c['href'], wait=4000)
                await delete_current(ge)
        elif cmd == 'scan':
            c = [c for c in await chats(ge) if args[0] in c['t']][0]
            await ge.goto('https://vertexaisearch.cloud.google.com' + c['href'] if c['href'].startswith('/') else c['href'], wait=5000)
            print(c['t'], await ge.brand_scan())


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
