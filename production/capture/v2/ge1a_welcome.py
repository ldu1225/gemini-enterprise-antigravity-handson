"""GE v2 Lab 1 / clip A: first-login welcome dialog (Korean UI) -> 시작하기 -> home. REAL UI recording.
One-shot: the welcome dialog only appears on the very first visit to the app."""
import asyncio
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME  # noqa: E402


async def main():
    async with GE() as ge:
        p = ge.page
        await ge.goto(APP_HOME + '?hl=ko', wait=6000, sidebar=False)
        await p.mouse.move(1100, 620)
        await ge.start_recording()
        await p.wait_for_timeout(2200)
        await ge.shot('ge_1_01_welcome')
        body = p.get_by_text('Gemini의 모든 기능을 활용해', exact=False).first
        await ge.move_to(body, steps=26, pause=600)
        await p.mouse.wheel(0, 160)
        await p.wait_for_timeout(2200)
        start = p.get_by_text('시작하기', exact=True).first
        await ge.click(start, label='시작하기')
        await p.wait_for_timeout(4000)
        await ge.shot('ge_1_02_home')
        await p.mouse.move(860, 520, steps=24)
        await p.wait_for_timeout(1500)
        out, n = await ge.stop_recording('ge1a_welcome')
        print('saved', out, n, 'frames')


if __name__ == "__main__":
    asyncio.run(main())
