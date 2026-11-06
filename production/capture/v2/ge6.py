"""GE v2 Lab 6 (생산성 — 스킬 · 프로젝트 · 라이브러리 · 검색 · 에이전트 투어) — REAL UI recordings.
  ge6a_skill_upload : 스킬 업로드 (Cymbal_보고서스타일_스킬.zip -> cymbal-report-style)
  ge6b_skill_use    : '/'로 cymbal-report-style 불러 쓰기 -> AirPole Pro 출시 점검 회의록 보고서 정리
  ge6c_tips_tour    : 라이브러리 · 프로젝트 · 검색 · 에이전트 둘러보기
Run: python3 ge6.py [a b c]
"""
import asyncio
import json
import sys

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME, ROOT  # noqa: E402
from helpers import FIND_TEXT_JS, DUMP_JS, click_xy, type_prompt, submit, smooth_scroll  # noqa: E402

HOME = APP_HOME + '?hl=ko'
SKILL_ZIP = str(ROOT / 'production/samples/v2/build/Cymbal_보고서스타일_스킬.zip')

MEMO = (
    "다음 회의 메모를 사내 표준 보고서 양식으로 정리해 주세요.\n"
    "회의: AirPole Pro 11월 출시 최종 점검 / 참석: 제품기획팀, 마케팅팀, 영업본부, CS팀\n"
    "내용: 1) 초도 물량 12,000대 생산 완료 및 물류센터 입고율 96% 달성, "
    "2) 온라인 사전예약 페이지 전환율 4.8%로 목표(3.5%) 초과 달성, "
    "3) 다만 야간 저소음 모드 안내 문구가 상세페이지마다 달라 고객 혼선 우려 있음, "
    "4) 출시 첫 주 초기 불량·필터 장착 문의 급증 대비 CS 전담 대응반 운영 필요"
)


async def text_box(ge, text, maxw=420, maxh=60):
    hits = await ge.page.evaluate(FIND_TEXT_JS, [text, maxw, maxh, 0])
    if not hits:
        raise RuntimeError('text not found: ' + text)
    return hits[0]


async def clip_a(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis_label('스킬'), label='스킬')
    await p.wait_for_timeout(2500)
    await ge.shot('ge_6_01_skills_empty')
    await click_xy(ge, await text_box(ge, '스킬 업로드'), '스킬 업로드')
    await p.wait_for_timeout(1800)
    await ge.shot('ge_6_02_skill_import_dialog')
    b = await text_box(ge, '파일 찾아보기')
    await p.mouse.move(b['x'] + b['w'] / 2, b['y'] + b['h'] / 2, steps=18)
    await p.wait_for_timeout(300)
    ge.mark('click', label='파일 찾아보기', box={'x': b['x'], 'y': b['y'], 'width': b['w'], 'height': b['h']})
    async with p.expect_file_chooser() as fc:
        await p.mouse.down(); await p.wait_for_timeout(70); await p.mouse.up()
    await (await fc.value).set_files(SKILL_ZIP)
    ge.mark('upload', label='Cymbal_보고서스타일_스킬.zip')
    await p.wait_for_timeout(2500)
    await ge.shot('ge_6_03_skill_file_selected')
    await ge.click(await ge.vis_label('가져오기'), label='가져오기')
    await p.wait_for_timeout(5000)
    await ge.shot('ge_6_04_skill_imported')
    print(await ge.stop_recording('ge6a_skill_upload'), flush=True)


async def clip_b(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await p.keyboard.type('/', delay=60)
    await p.wait_for_timeout(1600)
    await ge.shot('ge_6_05_slash_menu')
    opt = await ge.vis('[role="option"]', timeout=5000)
    await ge.click(opt, label='cymbal-report-style')
    await p.wait_for_timeout(900)
    await type_prompt(ge, MEMO, delay=12)
    await p.wait_for_timeout(700)
    await ge.shot('ge_6_06_skill_prompt')
    await submit(ge)
    await ge.set_rate(3)
    secs = await ge.wait_answer_done(timeout=240, stable=8, min_wait=6, label='skill_answer')
    await ge.set_rate(1)
    print(f'answer in {secs:.0f}s url={p.url}', flush=True)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_6_07_skill_answer')
    await p.mouse.move(860, 330, steps=10)
    await smooth_scroll(ge, 600, step=100, pause=130)
    await p.wait_for_timeout(1000)
    await ge.shot('ge_6_08_skill_answer_more')
    print(await ge.stop_recording('ge6b_skill_use'), flush=True)


async def clip_c(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    for label, shot, wait in [('라이브러리', 'ge_6_09_library', 3500), ('프로젝트', 'ge_6_10_projects', 3000)]:
        await ge.click(await ge.vis_label(label), label=label)
        await p.wait_for_timeout(wait)
        await ge.shot(shot)
    await ge.click(await ge.vis_label('검색'), label='검색')
    await p.wait_for_timeout(1500)
    await p.keyboard.type('에어폴', delay=120)
    await p.wait_for_timeout(2500)
    await ge.shot('ge_6_11_search')
    await p.keyboard.press('Escape')
    await p.wait_for_timeout(1000)
    await ge.click(await ge.vis_label('에이전트'), label='에이전트')
    await p.wait_for_timeout(3000)
    await ge.shot('ge_6_12_agents')
    print(await ge.stop_recording('ge6c_tips_tour'), flush=True)


async def main(which):
    async with GE() as ge:
        for k, fn in (('a', clip_a), ('b', clip_b), ('c', clip_c)):
            if k in which:
                await fn(ge)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or ['a', 'b', 'c']))
