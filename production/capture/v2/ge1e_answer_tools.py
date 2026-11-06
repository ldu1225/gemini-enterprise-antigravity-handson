"""GE v2 Lab 1 / clip E: answer toolbar — 표 복사/다운로드, 응답 복사, ⋮ 옵션 메뉴, 추천 후속 질문, 채팅 작업 메뉴.
Re-opens the chat created in ge1d ('Gemini Enterprise 업무 활용')."""
import asyncio
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME  # noqa: E402

TXT_JS = """(minx) => { const out=[]; const w=(r)=>{for(const e of r.querySelectorAll('*')){ if(e.shadowRoot) w(e.shadowRoot);
  const t=(e.innerText||'').trim(); if(e.children.length===0 && t && t.length<60){const b=e.getBoundingClientRect();
  if(b.width>2&&b.x>minx&&b.y>40&&b.y<800) out.push([t,Math.round(b.x),Math.round(b.y)]);}}}; w(document); return out; }"""


async def hover(ge, loc, label, dwell=1200):
    box = await ge.move_to(loc, steps=18, pause=200)
    ge.mark("hover", label=label, box=box)
    await ge.page.wait_for_timeout(dwell)


async def main():
    async with GE() as ge:
        p = ge.page
        await ge.goto(APP_HOME + '?hl=ko', wait=4500)
        await p.get_by_text('Gemini Enterprise 업무 활용', exact=True).first.click()
        await p.wait_for_timeout(3500)
        await p.mouse.move(1200, 500)
        await p.mouse.wheel(0, 3000)
        await p.wait_for_timeout(1500)
        await ge.start_recording()
        await p.wait_for_timeout(1200)
        await hover(ge, await ge.vis('[aria-label="표 복사"]'), '표 복사')
        await hover(ge, await ge.vis('[aria-label="표 다운로드"]'), '표 다운로드')
        await hover(ge, await ge.vis('[aria-label="응답 복사"]'), '응답 복사')
        await ge.click(await ge.vis('[aria-label="이 답변에 대한 옵션 더보기"]'), label='옵션 더보기')
        await p.wait_for_timeout(1600)
        print('answer menu:', [t for t in await p.evaluate(TXT_JS, 400) if t[2] > 380][:20])
        await ge.shot('ge_1_23_answer_menu')
        await p.keyboard.press('Escape')
        await p.wait_for_timeout(800)
        chips = p.locator('button').filter(has_text='광고 카피')
        if await chips.count():
            await hover(ge, chips.first, '추천 후속 질문', dwell=1500)
        await ge.click(await ge.vis('[aria-label="작업 메뉴"]'), label='작업 메뉴')
        await p.wait_for_timeout(1600)
        print('chat menu:', [t for t in await p.evaluate(TXT_JS, 1000) if t[2] < 300][:20])
        await ge.shot('ge_1_24_chat_menu')
        await p.keyboard.press('Escape')
        await p.wait_for_timeout(1200)
        print(await ge.stop_recording('ge1e_answer_tools'))


if __name__ == "__main__":
    asyncio.run(main())
