"""GE v2 Lab 3 (데이터 분석 + Canvas · 영업) — REAL UI recordings.
  ge3a_upload   : 모델 선택(Gemini 4 Argon) -> 엑셀 업로드 -> 분석 아이디어
  ge3b_analysis : 제품별 분기 매출·목표 달성률 표 + 변화 원인 가설
  ge3c_chart    : 온라인 매출 비중 추이 차트
  ge3d_canvas   : Canvas로 보고 슬라이드 5장 -> 슬라이드 넘기기 -> 내보내기 메뉴
Run: python3 ge3.py [a b c d]
"""
import asyncio
import glob
import sys
import time

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME, ROOT  # noqa: E402
from helpers import type_prompt, smooth_scroll, submit  # noqa: E402

HOME = APP_HOME + '?hl=ko'
XLSX = [f for f in glob.glob(str(ROOT / 'production/samples/v2/build/*.xlsx')) if '월별매출' in f][0]
SESSION = ROOT / 'production/assets/recordings/ge3_session.txt'
MODEL = 'Gemini 4 Argon'

P1 = "이 파일로 어떤 분석을 할 수 있는지 5가지만 알려 주세요."
P2 = ("제품별로 분기 매출액과 목표 달성률을 표로 정리해 주세요.\n"
      "그리고 1분기 대비 3분기에 가장 크게 달라진 제품 2개를 골라, 원인으로 볼 수 있는 가설을 데이터 근거와 함께 써 주세요.")
P3 = ("월별 전체 매출에서 온라인이 차지하는 비중을 꺾은선 차트로 그려 주세요.\n"
      "차트의 제목, 축 이름, 범례는 영어로 표시해 주세요.")
P4 = ("지금까지의 분석으로 영업본부장 보고용 슬라이드 5장을 만들어 주세요.\n"
      "구성: 표지 · 핵심 요약 · 제품별 실적과 달성률 · 온라인 채널 변화 · 4분기 실행 과제")

UPLOAD_DONE_JS = r"""
() => { let caption = false, spin = false;
  function scan(root) { for (const e of root.querySelectorAll('*')) { if (e.shadowRoot) scan(e.shadowRoot);
      const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
      const tag = e.tagName.toLowerCase();
      if (tag.includes('progress') || e.getAttribute('role') === 'progressbar') spin = true;
      if (e.childElementCount === 0 && /Excel|xlsx|스프레드시트/i.test(e.textContent || '') && r.y > 150) caption = true; } }
  scan(document); return caption && !spin; }
"""
LEAKS = []


async def guard(ge, where):
    hits = await ge.brand_scan()
    if hits:
        LEAKS.append((where, hits))
        print('BRAND LEAK', where, hits[:6], flush=True)


async def upload(ge, path):
    p = ge.page
    await ge.click(await ge.vis_label('파일 추가'), label='파일 추가')
    await p.wait_for_timeout(1000)
    item = await ge.vis_text('파일 업로드')
    async with p.expect_file_chooser() as fc_info:
        await ge.click(item, label='파일 업로드')
    fc = await fc_info.value
    await fc.set_files(path)
    ge.mark('upload', label='엑셀')
    t0 = time.monotonic()
    while time.monotonic() - t0 < 40:
        if await p.evaluate(UPLOAD_DONE_JS):
            break
        await p.wait_for_timeout(500)
    print(f'upload done in {time.monotonic() - t0:.1f}s', flush=True)
    await p.wait_for_timeout(1200)


async def pick_model(ge):
    p = ge.page
    await ge.click(await ge.vis_label('모델 선택'), label='모델 선택')
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis_text(MODEL), label=MODEL)
    await p.wait_for_timeout(900)


async def ask(ge, text, shot, rate=3, timeout=360):
    p = ge.page
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await type_prompt(ge, text, delay=20)
    await p.wait_for_timeout(500)
    await submit(ge)
    await ge.set_rate(rate)
    secs = await ge.wait_answer_done(timeout=timeout, stable=9, min_wait=6, label=shot)
    print(f'{shot}: answered in {secs:.0f}s', flush=True)
    err = await p.evaluate("() => { let f=false; const w=r=>{for(const e of r.querySelectorAll('*')){if(e.shadowRoot)w(e.shadowRoot); if(!e.children.length && /문제가 발생했습니다/.test(e.textContent||'')){const b=e.getBoundingClientRect(); if(b.width>2&&b.height>2) f=true;}}}; w(document); return f; }")
    if err:
        raise SystemExit(f'ANSWER ERROR at {shot}')
    await ge.set_rate(1)
    await p.wait_for_timeout(1200)
    await ge.shot(shot)


async def scroll_chat(ge, amount):
    await ge.page.mouse.move(860, 360, steps=10)
    await ge.page.wait_for_timeout(200)
    await smooth_scroll(ge, amount, step=110, pause=120)
    await ge.page.wait_for_timeout(1000)


async def reopen(ge):
    url = SESSION.read_text().strip()
    if ge.page.url.split('?')[0] == url.split('?')[0]:
        await ge.page.mouse.move(860, 360)
        await smooth_scroll(ge, 40000, step=4000, pause=60)
        await ge.page.wait_for_timeout(800)
        return
    await ge.goto(url, wait=5000)
    await ge.page.mouse.move(860, 360)
    await smooth_scroll(ge, 40000, step=4000, pause=60)
    await ge.page.wait_for_timeout(1200)


async def clip_a(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    # 4 Argon fails on xlsx uploads (2026-10-26) — keep Auto
    await upload(ge, XLSX)
    await ge.shot('ge_3_01_file_attached')
    await ask(ge, P1, 'ge_3_02_ideas')
    await scroll_chat(ge, 700)
    await ge.shot('ge_3_03_ideas_more')
    SESSION.write_text(p.url)
    print(await ge.stop_recording('ge3a_upload'), flush=True)
    await guard(ge, 'ideas')


async def clip_b(ge):
    await reopen(ge)
    await ge.start_recording()
    await ge.page.wait_for_timeout(800)
    await ask(ge, P2, 'ge_3_10_table', timeout=420)
    await scroll_chat(ge, 650)
    await ge.shot('ge_3_11_table_more')
    await scroll_chat(ge, 750)
    await ge.shot('ge_3_12_hypothesis')
    print(await ge.stop_recording('ge3b_analysis'), flush=True)
    await guard(ge, 'analysis')


async def clip_c(ge):
    await reopen(ge)
    await ge.start_recording()
    await ge.page.wait_for_timeout(800)
    await ask(ge, P3, 'ge_3_20_chart', timeout=420)
    await scroll_chat(ge, 500)
    await ge.shot('ge_3_21_chart_full')
    print(await ge.stop_recording('ge3c_chart'), flush=True)


async def clip_d(ge):
    p = ge.page
    await reopen(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await ge.click(await ge.vis_label('도구 선택'), label='도구 선택')
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis_text('Canvas'), label='Canvas')
    await p.wait_for_timeout(900)
    await ge.shot('ge_3_30_canvas_tool')
    await ask(ge, P4, 'ge_3_31_canvas_slides', rate=3, timeout=600)
    await p.wait_for_timeout(3000)
    await ge.shot('ge_3_32_canvas_ready')
    for i in (2, 3, 4):
        try:
            await ge.click(await ge.vis_label(f'슬라이드 {i}', timeout=3000), label=f'슬라이드 {i}')
            await p.wait_for_timeout(1800)
            await ge.shot(f'ge_3_3{i + 1}_slide{i}')
        except Exception as e:  # noqa: BLE001
            print('slide click skipped', e, flush=True)
    try:
        await ge.click(await ge.vis_label('슬라이드 1', timeout=3000), label='슬라이드 1')
        await p.wait_for_timeout(1200)
        await ge.click(await ge.vis_label('내보내기', timeout=5000), label='내보내기')
        await p.wait_for_timeout(1600)
        await ge.shot('ge_3_39_export_menu')
        await p.keyboard.press('Escape')
    except Exception as e:  # noqa: BLE001
        print('export skipped', e, flush=True)
    await p.wait_for_timeout(1200)
    print(await ge.stop_recording('ge3d_canvas'), flush=True)
    await guard(ge, 'canvas')


async def main(which):
    async with GE() as ge:
        for k, fn in (('a', clip_a), ('b', clip_b), ('c', clip_c), ('d', clip_d)):
            if k in which:
                await fn(ge)
    if LEAKS:
        print('LEAKS:', LEAKS)
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ['a', 'b', 'c', 'd']))
