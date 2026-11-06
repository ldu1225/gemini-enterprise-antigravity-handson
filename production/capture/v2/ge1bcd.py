"""GE v2 Lab 1 / clips B-D (REAL UI recordings, Korean UI):
  ge1b_tour      : sidebar + composer tour (hover each item, short dwell)
  ge1c_settings  : 설정 > 디자인(테마·채팅 밀도·홈페이지 요소) > 개인화(이름·직무·업종·메모리)
  ge1d_firstchat : 모델 선택 메뉴 -> 첫 질문 -> 답변 -> 답변 아래 도구(복사·좋아요 등) -> 새 채팅
Run: python3 ge1bcd.py [b|c|d ...]   (default: all)
"""
import asyncio
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME  # noqa: E402

HOME = APP_HOME + '?hl=ko'
TXT_JS = """(minx) => { const out=[]; const w=(r)=>{for(const e of r.querySelectorAll('*')){ if(e.shadowRoot) w(e.shadowRoot);
  const t=(e.innerText||'').trim(); if(e.children.length===0 && t && t.length<80){const b=e.getBoundingClientRect();
  if(b.width>2&&b.x>minx&&b.y>40&&b.y<800) out.push([t,Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]);}}};
  w(document); return out; }"""


async def hover(ge, loc, label, dwell=1100):
    box = await ge.move_to(loc, steps=18, pause=200)
    ge.mark("hover", label=label, box=box)
    await ge.page.wait_for_timeout(dwell)


async def clip_tour(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 560)
    await ge.start_recording()
    await p.wait_for_timeout(1500)
    for al in ["새 채팅", "수신함", "검색", "라이브러리", "프로젝트", "스킬", "에이전트", "Gemini Notebook",
               "Deep Research", "새 에이전트", "Antigravity 살펴보기", "알림", "설정 및 도움말"]:
        await hover(ge, await ge.vis(f'[aria-label="{al}"]', timeout=5000), al, dwell=1300)
    await ge.shot("ge_1_03_sidebar")
    for al in ["파일 추가", "도구 선택", "소스", "모델 선택"]:
        await ge.click(await ge.vis(f'[aria-label="{al}"]', timeout=5000), label=al)
        await p.wait_for_timeout(2600)
        await p.keyboard.press('Escape')
        await p.wait_for_timeout(700)
    await hover(ge, await ge.vis('[aria-label="마이크 사용"]', timeout=5000), '마이크 사용', dwell=1400)
    await p.mouse.move(900, 600, steps=18)
    await p.wait_for_timeout(1200)
    print(await ge.stop_recording("ge1b_tour"))


async def open_settings(ge, tab, record=True):
    p = ge.page
    c = ge.click if record else (lambda loc, label='': loc.click())
    await c(p.locator('[aria-label="설정 및 도움말"]').first, label='설정 및 도움말')
    await p.wait_for_timeout(1000)
    await c(p.get_by_text(tab, exact=True).first, label=tab)
    await p.wait_for_timeout(1400)


async def clip_settings(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    # unrecorded reset: theme = 시스템, empty profile
    await open_settings(ge, '디자인', record=False)
    await p.get_by_text('시스템', exact=True).first.click()
    await p.wait_for_timeout(500)
    await p.get_by_text('개인화', exact=True).first.click()
    await p.wait_for_timeout(900)
    for lbl in ['사용하고 싶은 이름', '직책 또는 직무']:
        f = p.locator(f'input[aria-label="{lbl}"]').first
        if await f.count():
            await f.fill('')
    await p.keyboard.press('Escape')
    await p.wait_for_timeout(800)
    await ge.goto(HOME, wait=4000)
    await p.mouse.move(860, 560)

    await ge.start_recording()
    await p.wait_for_timeout(1200)
    await ge.click(p.locator('[aria-label="설정 및 도움말"]').first, label='설정 및 도움말')
    await p.wait_for_timeout(1300)
    await ge.shot('ge_1_10_settings_menu')
    await ge.click(p.get_by_text('디자인', exact=True).first, label='디자인')
    await p.wait_for_timeout(1500)
    await ge.shot('ge_1_11_design')
    await ge.click(p.get_by_text('어둡게', exact=True).first, label='어둡게')
    await p.wait_for_timeout(2200)
    await ge.shot('ge_1_12_design_dark')
    await ge.click(p.get_by_text('밝게', exact=True).first, label='밝게')
    await p.wait_for_timeout(1800)
    await hover(ge, p.get_by_text('채팅 밀도', exact=True).first, '채팅 밀도', dwell=1200)
    await hover(ge, p.get_by_text('홈페이지 요소', exact=True).first, '홈페이지 요소', dwell=1500)
    await ge.shot('ge_1_13_design_light')

    await ge.click(p.get_by_text('개인화', exact=True).first, label='개인화')
    await p.wait_for_timeout(1500)
    await ge.shot('ge_1_14_personalize_empty')
    await ge.click(p.locator('input[aria-label="사용하고 싶은 이름"]').first, label='사용하고 싶은 이름')
    await ge.type_text('이하나', delay=120, label='이름')
    await ge.click(p.locator('input[aria-label="직책 또는 직무"]').first, label='직책 또는 직무')
    await ge.type_text('마케팅팀 매니저', delay=85, label='직무')
    await p.wait_for_timeout(600)
    try:
        await ge.click(p.locator('[aria-label="업종"]').first, label='업종')
        await p.wait_for_timeout(1400)
        opts = p.locator('md-select-option, [role=option]')
        texts = [t.strip() for t in await opts.all_inner_texts()]
        print('industry options:', texts[:40])
        await ge.shot('ge_1_15_industry')
        target = None
        for want in ['기술', '소비재', '전자', '제조', 'Technology', '소매']:
            cand = opts.filter(has_text=want)
            if await cand.count():
                target = cand.first
                break
        if target is not None:
            await ge.click(target, label='업종 선택')
        else:
            await p.keyboard.press('Escape')
        await p.wait_for_timeout(1000)
    except Exception as e:  # noqa: BLE001
        print('industry select skipped:', e)
    await ge.shot('ge_1_16_personalize_filled')
    mem = p.get_by_text('메모리', exact=True).first
    await hover(ge, mem, '메모리', dwell=1800)
    await p.mouse.wheel(0, 300)
    await p.wait_for_timeout(1600)
    await ge.shot('ge_1_17_memory')
    print([t for t in await p.evaluate(TXT_JS, 560)][:40])
    await p.keyboard.press('Escape')
    await p.wait_for_timeout(1400)
    print(await ge.stop_recording('ge1c_settings'))


async def clip_firstchat(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1200)
    await ge.click(p.locator('[aria-label="모델 선택"]').first, label='모델 선택')
    await p.wait_for_timeout(1800)
    await ge.shot('ge_1_20_model_menu')
    print('model menu:', [t for t in await p.evaluate(TXT_JS, 700) if t[2] > 380][:30])
    await p.keyboard.press('Escape')
    await p.wait_for_timeout(800)
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    q = "안녕하세요! 저는 마케팅팀에서 일합니다. Gemini Enterprise로 제 업무에서 바로 해 볼 수 있는 일을 5가지만 표로 정리해 주세요."
    await ge.type_text(q, delay=38, label='첫 질문')
    await p.wait_for_timeout(700)
    ge.mark('submit', label='전송')
    await p.keyboard.press('Enter')
    await ge.wait_answer_done(timeout=180, label='답변')
    await p.wait_for_timeout(1200)
    await ge.shot('ge_1_21_first_answer')
    await p.mouse.wheel(0, 600)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_1_22_answer_tools')
    for al in ["복사", "대답 복사", "좋아요", "마음에 들어요", "싫어요", "공유", "다시 생성", "더보기"]:
        loc = p.locator(f'[aria-label="{al}"]')
        if await loc.count():
            try:
                await hover(ge, loc.last, al, dwell=900)
            except Exception:  # noqa: BLE001
                pass
    await ge.click(p.locator('[aria-label="새 채팅"]').first, label='새 채팅')
    await p.wait_for_timeout(2000)
    print(await ge.stop_recording('ge1d_firstchat'))


async def main(which):
    async with GE() as ge:
        if 'b' in which:
            await clip_tour(ge)
        if 'c' in which:
            await clip_settings(ge)
        if 'd' in which:
            await clip_firstchat(ge)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ['b', 'c', 'd']))
