"""GE v2 Lab 7 (채팅 에이전트 심화 — Cymbal 사내 지원 데스크) — REAL UI recordings.
  ge7a_build  : 새 에이전트 > 채팅 에이전트 -> 규정 PDF 첨부 -> 자연어 설명으로 에이전트 생성
  ge7b_test   : 미리보기에서 질문 2개 테스트 -> 플로우 탭 전환
  ge7c_create : 에이전트 노드 세부 설정(요청 사항 · 모델 · 지식) 확인 -> 생성
  ge7d_use    : 에이전트와 채팅 -> 홈에서 @Cymbal 사내 지원 데스크 멘션 호출
Run: python3 ge7.py [a b c d]
"""
import asyncio
import json
import sys
import time

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME, ROOT, RECS  # noqa: E402
from helpers import type_prompt, smooth_scroll, click_xy, FIND_TEXT_JS, DUMP_JS  # noqa: E402

HOME = APP_HOME + '?hl=ko'
PDF_TRAVEL = str(ROOT / 'production/samples/v2/build/Cymbal_출장비_및_경비처리_규정_가상.pdf')
AGENT_URL_FILE = RECS / 'ge7_agent_url.txt'
AGENT = 'Cymbal 사내 지원 데스크'

DESC = (
    "Cymbal 임직원의 출장·경비·휴가·IT 보안 규정 질문에 답하는 'Cymbal 사내 지원 데스크' 에이전트를 만들어 주세요.\n"
    "첨부한 「출장비 및 경비처리 규정」 문서만 근거로 답하고, 근거가 된 장 번호를 함께 알려 주세요.\n"
    "문서에 없는 내용은 추측하지 말고 \"피플팀·재무팀 헬프데스크에 문의해 주세요\"라고 안내해 주세요.\n"
    "금액과 기한은 표로 정리하고, 답변은 5줄 이내로 간결하게 해 주세요."
)
Q1 = "미국 출장을 가는 팀장의 1박 숙박비 한도는 얼마인가요?"
Q2 = "출장 중에 법인카드를 잃어버렸어요. 어떻게 해야 하나요?"
Q3 = "정산 기한을 넘기면 어떻게 되나요?"
Q4 = "고객 접대 식사비 한도는 얼마인가요?"


async def find_word(ge, word, maxw=460, maxh=70, miny=0):
    hits = await ge.page.evaluate(FIND_TEXT_JS, [word, maxw, maxh, miny])
    return [h for h in hits if h['x'] < 1440]


async def in_view(ge, label):
    items = await ge.page.evaluate(DUMP_JS)
    for i in items:
        if (i['al'] == label or i['txt'] == label) and 0 <= i['x'] < 1440 and 0 <= i['y'] < 810:
            return i
    return None


async def wait_canvas(ge, timeout=360):
    p = ge.page
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        busy = await p.evaluate(FIND_TEXT_JS, ['처리 중', 400, 60, 0])
        gen = await in_view(ge, '생성')
        pbox = await preview_input(ge)
        if (gen or pbox) and not busy:
            return gen or pbox
        await p.wait_for_timeout(2500)
    return None


async def open_new_agent(ge, which):
    p = ge.page
    await ge.click(await ge.vis_label('새 에이전트'), label='새 에이전트')
    await p.wait_for_timeout(900)
    chat = (await p.evaluate(FIND_TEXT_JS, ['채팅 에이전트', 300, 60, 0]))[-1]
    await p.mouse.move(chat['x'] + 30, chat['y'] + chat['h'] / 2, steps=12)
    await p.wait_for_timeout(300)
    target = chat if which == '채팅 에이전트' else (await p.evaluate(FIND_TEXT_JS, [which, 300, 60, 0]))[-1]
    await click_xy(ge, target, which)


async def preview_input(ge):
    loc = ge.page.locator('[contenteditable="true"]')
    best = None
    for i in range(await loc.count()):
        b = await loc.nth(i).bounding_box()
        if b and b['width'] > 50 and b['x'] > 560:
            best = loc.nth(i)
    return best


async def ask_preview(ge, text, label='preview'):
    p = ge.page
    t0 = time.monotonic()
    box = None
    while time.monotonic() - t0 < 120:
        box = await preview_input(ge)
        if box:
            break
        await p.wait_for_timeout(1500)
    if not box:
        raise RuntimeError('preview input not found')
    await ge.click(box, label='미리보기 입력창')
    if text:
        await type_prompt(ge, text, delay=20)
    await p.keyboard.press('Enter'); ge.mark('submit', label=label)
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=180, stable=4, label=label)
    await ge.set_rate(1)
    await p.wait_for_timeout(1200)


async def clip_a(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await open_new_agent(ge, '채팅 에이전트')
    await p.wait_for_timeout(4000)
    await ge.shot('ge_7_01_chat_agent_start')
    add = await ge.vis_label('파일 추가')
    async with p.expect_file_chooser() as fc_info:
        await ge.click(add, label='파일 추가')
        await p.wait_for_timeout(800)
        try:
            up = await ge.vis('[aria-label="파일 업로드"]', timeout=2500)
            await ge.click(up, label='파일 업로드')
        except Exception:
            pass
    fc = await fc_info.value
    await fc.set_files(PDF_TRAVEL)
    ge.mark('upload', label='출장비 및 경비처리 규정 PDF')
    await p.wait_for_timeout(3500)
    await ge.click(await ge.vis('[contenteditable="true"]'), label='에이전트 설명 입력')
    await type_prompt(ge, DESC, delay=15)
    await p.wait_for_timeout(600)
    await ge.shot('ge_7_02_agent_description')
    await p.keyboard.press('Enter'); ge.mark('submit', label='agent_desc')
    await ge.set_rate(4)
    ge.mark('wait_start', label='agent_build')
    t0 = time.monotonic()
    await wait_canvas(ge, timeout=360)
    ge.mark('wait_end', label='agent_build', secs=round(time.monotonic() - t0, 1))
    await ge.set_rate(1)
    await p.wait_for_timeout(2500)
    await ge.shot('ge_7_03_agent_generated')
    AGENT_URL_FILE.write_text(p.url)
    print(await ge.stop_recording('ge7a_build'), flush=True)


async def clip_b(ge):
    p = ge.page
    await ge.install_cursor()
    await wait_canvas(ge, timeout=300)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_7_03_agent_generated')
    AGENT_URL_FILE.write_text(p.url)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await ask_preview(ge, Q1, 'preview_q1')
    await ge.shot('ge_7_05_preview_answer1')
    await ask_preview(ge, Q2, 'preview_q2')
    await ge.shot('ge_7_06_preview_answer2')
    tab = await find_word(ge, '플로우', 140, 50, 0)
    if tab:
        await click_xy(ge, tab[0], '플로우 탭')
        await p.wait_for_timeout(3000)
    await ge.shot('ge_7_07_flow_tab')
    print(await ge.stop_recording('ge7b_test'), flush=True)


async def clip_c(ge):
    p = ge.page
    await ge.install_cursor()
    await ge.start_recording()
    await p.wait_for_timeout(800)
    node = [h for h in await find_word(ge, '사내 지원', 420, 50) if h['x'] > 700]
    if not node:
        node = [h for h in await find_word(ge, 'Cymbal', 420, 50) if h['x'] > 700]
    print('node', node, flush=True)
    if node:
        await click_xy(ge, node[0], '에이전트 노드')
        await p.wait_for_timeout(2500)
    await ge.shot('ge_7_08_node_config')
    await smooth_scroll(ge, 500)
    await p.wait_for_timeout(1200)
    await ge.shot('ge_7_09_node_config_more')
    await smooth_scroll(ge, 700)
    await p.wait_for_timeout(1200)
    await ge.shot('ge_7_10_node_config_bottom')
    btn = await find_word(ge, '생성', 120, 50)
    print('create btn', btn, flush=True)
    if btn:
        await click_xy(ge, btn[-1], '생성')
        await p.wait_for_timeout(4500)
    await ge.shot('ge_7_11_after_create')
    print(await ge.stop_recording('ge7c_create'), flush=True)


async def clip_d(ge):
    p = ge.page
    await ge.install_cursor()
    await ge.start_recording()
    await p.wait_for_timeout(800)
    btn = await find_word(ge, '에이전트와 채팅', 300, 60)
    if btn:
        await click_xy(ge, btn[0], '에이전트와 채팅')
        await p.wait_for_timeout(4500)
    await ge.ensure_sidebar()
    await p.wait_for_timeout(800)
    await ge.shot('ge_7_12_agent_chat_home')
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await type_prompt(ge, Q3, delay=22)
    await p.keyboard.press('Enter'); ge.mark('submit', label='agent_q3')
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=180, stable=4, label='agent_q3')
    await ge.set_rate(1)
    await p.wait_for_timeout(1200)
    await ge.shot('ge_7_13_agent_chat_answer')
    # @mention from main assistant
    await ge.goto(HOME, wait=4000)
    await p.mouse.move(900, 600)
    await p.wait_for_timeout(800)
    await ge.shot('ge_7_14_sidebar_agent_listed')
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    await p.keyboard.type('@', delay=80)
    await p.wait_for_timeout(1200)
    await p.keyboard.type('Cymbal', delay=100)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_7_15_mention_list')
    hits = await find_word(ge, '사내 지원', 420, 60)
    if hits:
        await click_xy(ge, hits[-1], '@Cymbal 사내 지원 데스크')
        await p.wait_for_timeout(800)
    else:
        await p.keyboard.press('Enter')
    await type_prompt(ge, ' ' + Q4, delay=22)
    await p.wait_for_timeout(500)
    await ge.shot('ge_7_16_mention_prompt')
    await p.keyboard.press('Enter'); ge.mark('submit', label='mention_q4')
    await ge.set_rate(3)
    await ge.wait_answer_done(timeout=180, stable=4, label='mention_q4')
    await ge.set_rate(1)
    await p.wait_for_timeout(1200)
    await ge.shot('ge_7_17_mention_answer')
    print(await ge.stop_recording('ge7d_use'), flush=True)


async def main(which):
    async with GE() as ge:
        for k, fn in (('a', clip_a), ('b', clip_b), ('c', clip_c), ('d', clip_d)):
            if k in which:
                await fn(ge)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or ['a', 'b', 'c', 'd']))
