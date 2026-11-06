"""AG Lab 2 / clip A: personal-account sign-in (REAL UI). The script clicks 'Continue with Google' while recording;
the human finishes Google sign-in in the browser; recording continues through the post-login onboarding screens.
Stills: ag_2_01_welcome, ag_2_02_waiting, ag_2_03_after_login.
"""
import asyncio
import time

from agy import AGY


async def main():
    async with AGY() as ag:
        p = ag.page
        await p.mouse.move(700, 600)
        await ag.start_recording()
        await p.wait_for_timeout(2000)
        await ag.shot("ag_2_01_welcome")
        txt0 = await p.evaluate("() => document.body.innerText")
        btn = "Continue with different account" if "Continue with different account" in txt0 else "Continue with Google"
        await ag.click(await ag.vis_text(btn), label=btn)
        await p.wait_for_timeout(3000)
        await ag.shot("ag_2_02_waiting")
        print("WAITING_FOR_HUMAN_LOGIN", flush=True)
        t0 = time.time()
        while time.time() - t0 < 900:
            await p.wait_for_timeout(2000)
            try:
                url = p.url
                txt = await p.evaluate("() => document.body.innerText.slice(0, 300)")
            except Exception:  # page swapped
                await ag.refresh_page()
                p = ag.page
                continue
            if ("Continue with Google" not in txt and "Use Business Account" not in txt
                    and "Continue with different account" not in txt):
                ag.mark("login_done", url=url)
                print("LOGIN_DONE", url, txt[:200].replace("\n", " | "), flush=True)
                break
        await p.wait_for_timeout(4000)
        await ag.shot("ag_2_03_after_login")
        print(await ag.stop_recording("ag2a_signin"))


asyncio.run(main())
