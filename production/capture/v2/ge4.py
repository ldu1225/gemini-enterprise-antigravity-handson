"""GE v2 Lab 4 (이미지 · 동영상 · 마케팅) — REAL UI recordings.
  ge4a_brief : 신제품 브리프 PDF 업로드 -> 키 비주얼 이미지 프롬프트 받기
  ge4b_image : 도구 선택 > 이미지 만들기 -> 키 비주얼 생성(Nano Banana)
  ge4c_edit  : 이어서 수정(저녁 무드 · 무드 라이트) -> 이미지 확대/다운로드 메뉴
  ge4d_video : 도구 선택 > 동영상 만들기(Veo 3.1) -> 8초 티저 생성 -> 재생
Run: python3 ge4.py [a b c d]
"""
import asyncio
import glob
import sys
import time

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME, ROOT  # noqa: E402
from helpers import type_prompt, smooth_scroll, submit, MEDIA_JS  # noqa: E402
from media_wait import wait_media  # noqa: E402

HOME = APP_HOME + '?hl=ko'
BRIEF = [f for f in glob.glob(str(ROOT / 'production/samples/v2/build/*.pdf')) if '브리프' in f][0]
SESSION = ROOT / 'production/assets/recordings/ge4_session.txt'

P1 = ("이 브리프를 바탕으로 캠페인 키 비주얼 이미지 프롬프트를 한국어 한 문단으로 써 주세요.\n"
      "브리프의 톤앤매너와 금지 사항을 지키고, 이미지 안에 글자나 로고는 넣지 말아 주세요. 다른 AI 서비스나 회사 이름은 쓰지 마세요.")
P2 = "위 프롬프트로 가로형 캠페인 키 비주얼 이미지를 만들어 주세요."
P3 = "같은 장면을 해 질 무렵 분위기로 바꾸고, 제품 윗부분의 무드 라이트 링이 은은한 푸른빛으로 켜진 모습으로 수정해 주세요."
P4 = ("햇살이 드는 미니멀한 거실, 하얀 기둥형 공기청정기 윗부분의 무드 라이트 링이 천천히 켜지고 "
      "얇은 커튼이 바람에 살짝 흔들리는 8초 영상을 만들어 주세요. 카메라는 천천히 다가가고, 사람과 글자는 넣지 마세요.")

ERR_JS = ("() => { let f=false; const w=r=>{for(const e of r.querySelectorAll('*')){if(e.shadowRoot)w(e.shadowRoot);"
          " if(!e.children.length && /문제가 발생했습니다/.test(e.textContent||'')){const b=e.getBoundingClientRect(); if(b.width>2&&b.height>2) f=true;}}}; w(document); return f; }")
UPLOAD_DONE_JS = r"""
() => { let caption = false, spin = false;
  function scan(root) { for (const e of root.querySelectorAll('*')) { if (e.shadowRoot) scan(e.shadowRoot);
      const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
      const tag = e.tagName.toLowerCase();
      if (tag.includes('progress') || e.getAttribute('role') === 'progressbar') spin = true;
      if (e.childElementCount === 0 && /PDF/i.test(e.textContent || '') && r.y > 150) caption = true; } }
  scan(document); return caption && !spin; }
"""
LEAKS = []


async def guard(ge, where):
    hits = await ge.brand_scan(extra=['Midjourney', 'DALL', 'Stable Diffusion', 'Firefly', 'ChatGPT', 'OpenAI'])
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
    ge.mark('upload', label='브리프 PDF')
    t0 = time.monotonic()
    while time.monotonic() - t0 < 40:
        if await p.evaluate(UPLOAD_DONE_JS):
            break
        await p.wait_for_timeout(500)
    print(f'upload done in {time.monotonic() - t0:.1f}s', flush=True)
    await p.wait_for_timeout(1200)


async def pick_tool(ge, name, shot=None):
    p = ge.page
    await ge.click(await ge.vis_label('도구 선택'), label='도구 선택')
    await p.wait_for_timeout(1100)
    if shot:
        await ge.shot(shot)
    await ge.click(await ge.vis_text(name, exact=False), label=name)
    await p.wait_for_timeout(1000)


async def ask(ge, text, shot, rate=3, timeout=420, stable=9, insert=False, media=None):
    p = ge.page
    await ge.click(await ge.vis('[contenteditable="true"]'), label='입력창')
    if insert:
        await ge.insert_text(text, label='prompt')
    else:
        await type_prompt(ge, text, delay=20)
    await p.wait_for_timeout(600)
    base = await p.evaluate(MEDIA_JS)
    await submit(ge)
    await ge.set_rate(rate)
    if media:
        st = await wait_media(ge, media, base[media] + 1, timeout=timeout)
        print('media', st, flush=True)
        secs = await ge.wait_answer_done(timeout=120, stable=4, min_wait=1, label=shot + '_text')
    else:
        secs = await ge.wait_answer_done(timeout=timeout, stable=stable, min_wait=8, label=shot)
    print(f'{shot}: answered in {secs:.0f}s', flush=True)
    await ge.set_rate(1)
    await p.wait_for_timeout(1500)
    if await p.evaluate(ERR_JS):
        raise SystemExit(f'ANSWER ERROR at {shot}')
    await ge.shot(shot)


async def scroll_chat(ge, amount):
    await ge.page.mouse.move(860, 360, steps=10)
    await ge.page.wait_for_timeout(200)
    await smooth_scroll(ge, amount, step=110, pause=120)
    await ge.page.wait_for_timeout(1000)


async def to_bottom(ge):
    await ge.page.mouse.move(860, 360)
    await smooth_scroll(ge, 40000, step=4000, pause=60)
    await ge.page.wait_for_timeout(800)


async def ensure_session(ge):
    url = SESSION.read_text().strip()
    if ge.page.url.split('?')[0] != url.split('?')[0]:
        await ge.goto(url, wait=5000)
    await to_bottom(ge)


async def clip_a(ge):
    p = ge.page
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    await upload(ge, BRIEF)
    await ge.shot('ge_4_01_brief_attached')
    await ask(ge, P1, 'ge_4_02_prompt_answer', timeout=240)
    SESSION.write_text(p.url)
    await p.wait_for_timeout(1500)
    print(await ge.stop_recording('ge4a_brief'), flush=True)
    await guard(ge, 'brief')


async def clip_b(ge):
    p = ge.page
    await ensure_session(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await pick_tool(ge, '이미지 만들기', shot='ge_4_10_tools_menu')
    await ge.shot('ge_4_11_image_tool_on')
    await ask(ge, P2, 'ge_4_12_image', timeout=300, media='imgs')
    await to_bottom(ge)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_4_13_image_full')
    print(await ge.stop_recording('ge4b_image'), flush=True)


async def clip_c(ge):
    p = ge.page
    await ensure_session(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await ask(ge, P3, 'ge_4_20_edit', timeout=300, media='imgs')
    await to_bottom(ge)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_4_21_edit_full')
    print(await ge.stop_recording('ge4c_edit'), flush=True)
    await guard(ge, 'image')


async def clip_d(ge):
    p = ge.page
    await ensure_session(ge)
    await ge.start_recording()
    await p.wait_for_timeout(800)
    await pick_tool(ge, '동영상 만들기')
    await ge.shot('ge_4_30_video_tool_on')
    await ask(ge, P4, 'ge_4_31_video', rate=4, timeout=600, stable=12, insert=True, media='vids')
    await to_bottom(ge)
    await p.wait_for_timeout(1500)
    await ge.shot('ge_4_32_video_full')
    print(await ge.stop_recording('ge4d_video'), flush=True)
    await guard(ge, 'video')


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
