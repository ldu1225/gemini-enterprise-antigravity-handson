"""wait_media(): wait until N generated images/videos are rendered in the GE answer (MEDIA_JS counter)."""
import time

from helpers import MEDIA_JS


async def wait_media(ge, kind, count, timeout=420):
    p = ge.page
    t0 = time.monotonic()
    ge.mark('wait_start', label=f'{kind}>={count}')
    st = {}
    while time.monotonic() - t0 < timeout:
        st = await p.evaluate(MEDIA_JS)
        if st[kind] >= count:
            break
        await p.wait_for_timeout(1500)
    ge.mark('wait_end', label=kind, secs=round(time.monotonic() - t0, 1))
    await p.wait_for_timeout(2500)
    return st
