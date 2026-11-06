"""GE v2 Lab 5 (Deep Research & Gemini Notebook · 전략) — REAL UI recordings.
  ge5a_dr_start  : 사이드바 Deep Research -> 조사 요청 -> 연구 계획 확인
  ge5a2_dr_go    : 연구 계획 하단 '연구 시작' 클릭 -> 실시간 웹 조사 진행 화면
  ge5b_dr_result : 완성된 보고서 살펴보기(제목 · 표 · 출처 · 결론 · 오디오 요약)
  ge5c_notebook  : Gemini Notebook -> 새 노트북 -> 브리프 PDF 업로드 -> 근거 질문 -> 출처 -> 스튜디오 마인드맵
Run: python3 ge5.py [a a2 b c]
"""
import asyncio
import sys
import time

sys.path.insert(0, __file__.rsplit('/', 2)[0])
from ge import GE, APP_HOME, ROOT  # noqa: E402
from helpers import type_prompt, click_xy, smooth_scroll, FIND_TEXT_JS  # noqa: E402
from nb_explore import nb_frame, FIND_JS  # noqa: E402

HOME = APP_HOME + '?hl=ko'
SESSION = ROOT / 'production/assets/recordings/ge5_dr_session.txt'
BRIEF_PDF = str(ROOT / 'production/samples/v2/build/Cymbal_신제품_브리프_에어폴_프로_가상.pdf')
# same text as the GE Lab 5 step prompt (production/content/v2/ge_labs/lab5.py).
# One short sentence per cell: the older wording made Notebook pack several items into one cell with raw `<br>`.
NB_Q = ("AirPole Pro의 핵심 타깃 3그룹을 표로 정리해 주세요. "
        "열은 타깃 그룹, 주요 고민, 추천 기능 3개로 하고 각 칸은 한 문장으로 짧게 써 주세요.")
NB_URL = ROOT / 'production/assets/recordings/ge5_nb_session.txt'

DR_PROMPT = ("Cymbal 전략기획팀 보고용으로, 국내 가정의 실내 공기질 관리에 대한 소비자 인식과 제도 변화를 조사해 주세요.\n"
             "미세먼지·환기 습관 변화, 반려동물·영유아 가구의 관심사, 실내공기질 관련 법·인증·표시 제도를 정부·공공 자료 중심으로 정리하고, "
             "신제품 기획에 주는 시사점으로 마무리해 주세요. 기업명·브랜드명·제품 모델명은 일절 쓰지 말고, 제조사 사례나 제품 비교표는 넣지 마세요.")

SCROLLER_JS = r"""
() => {
  let best = null, bestH = 0;
  function walk(root) {
    for (const e of root.querySelectorAll('*')) {
      if (e.shadowRoot) walk(e.shadowRoot);
      const cs = getComputedStyle(e);
      if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll') && e.scrollHeight > e.clientHeight + 50 && e.scrollHeight > bestH) {
        best = e; bestH = e.scrollHeight;
      }
    }
  }
  walk(document);
  window.__sc = best;
  return bestH;
}
"""

TARGET_JS = r"""
([kind, needle, pad]) => {
  const sc = window.__sc; if (!sc) return null;
  let el = null;
  function find(root) {
    for (const e of root.querySelectorAll(kind === 'text' ? 'h1,h2,h3,h4' : needle)) {
      if (kind !== 'text' || (e.textContent || '').includes(needle)) {
        const r = e.getBoundingClientRect();
        if (r.height > 0) { el = e; return true; }
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot && find(e.shadowRoot)) return true;
    return false;
  }
  find(document);
  if (!el) return null;
  const top = el.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop - pad;
  return Math.max(0, Math.round(top));
}
"""


async def glide(ge, top, ms=2400):
    if top is None:
        return
    await ge.page.evaluate("(t) => window.__sc && window.__sc.scrollTo({top: t, behavior: 'smooth'})", top)
    await ge.page.wait_for_timeout(ms)


async def clip_a2(ge):
    p = ge.page
    url = SESSION.read_text().strip()
    await ge.goto(url, wait=6000)
    await p.mouse.move(860, 420)
    await ge.start_recording()
    await p.wait_for_timeout(900)
    await smooth_scroll(ge, 3000, step=150, pause=110)
    await p.wait_for_timeout(1200)
    hits = await p.evaluate(FIND_TEXT_JS, ['연구 시작', 260, 60, 0])
    print('hits', hits, flush=True)
    if not hits:
        raise SystemExit('start button not found')
    await ge.shot('ge_5_03_dr_plan')
    await click_xy(ge, hits[-1], '연구 시작')
    await p.wait_for_timeout(2500)
    await ge.set_rate(4)
    await p.wait_for_timeout(12000)
    await ge.shot('ge_5_04_dr_running')
    await p.wait_for_timeout(20000)
    await ge.shot('ge_5_05_dr_progress')
    await ge.set_rate(1)
    print(await ge.stop_recording('ge5a2_dr_go'), flush=True)


async def clip_b(ge):
    url = SESSION.read_text().strip()
    p = ge.page
    await ge.goto(url, wait=6000)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 420:
        h = await p.evaluate(SCROLLER_JS)
        has_table = await p.evaluate(TARGET_JS, ['css', 'table', 110])
        if (h and h > 2200) or has_table is not None:
            break
        print(f'waiting for DR report... h={h} elapsed={time.monotonic()-t0:.0f}s', flush=True)
        await p.wait_for_timeout(8000)
    h = await p.evaluate(SCROLLER_JS)
    print('scroll height', h, flush=True)
    await p.evaluate("() => { if (window.__sc) window.__sc.scrollTop = 0; }")
    await p.wait_for_timeout(1200)
    await p.mouse.move(820, 420)
    await ge.start_recording()
    await p.wait_for_timeout(1500)
    t = await p.evaluate(TARGET_JS, ['css', 'h1,h2', 24])
    print('report top', t, flush=True)
    await glide(ge, t or 420, 2600)
    await ge.shot('ge_5_06_dr_report_top')
    t2 = await p.evaluate(TARGET_JS, ['css', 'table', 110])
    print('table top', t2, flush=True)
    await glide(ge, t2 or 1200, 2400)
    await ge.shot('ge_5_07_dr_report_table')
    links = await p.evaluate(r"""() => {
      const out = [];
      function scan(root) {
        for (const a of root.querySelectorAll('a[aria-label], a[href^="http"]')) {
          const r = a.getBoundingClientRect();
          if (r.width > 8 && r.height > 8 && r.y > 120 && r.y < 600 && r.x > 300)
            out.push({x: r.x + r.width / 2, y: r.y + r.height / 2, al: (a.getAttribute('aria-label') || a.textContent || '').slice(0, 50)});
        }
        for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
      }
      scan(document); return out.slice(0, 3);
    }""")
    print('citations in view', links, flush=True)
    if links:
        await p.mouse.move(links[0]['x'], links[0]['y'], steps=18)
        await p.wait_for_timeout(1800)
    await ge.shot('ge_5_08_dr_citation_hover')
    await p.mouse.move(820, 420, steps=10)
    t3 = await p.evaluate(TARGET_JS, ['text', '시사점', 24]) or await p.evaluate(TARGET_JS, ['text', '결론', 24])
    print('conclusion top', t3, flush=True)
    await glide(ge, t3 or max(0, (h or 3000) - 1100), 2600)
    await ge.shot('ge_5_09_dr_conclusion')
    await p.evaluate("() => window.__sc && window.__sc.scrollTo({top: window.__sc.scrollHeight, behavior: 'smooth'})")
    await p.wait_for_timeout(2400)
    await ge.shot('ge_5_10_dr_audio')
    try:
        await ge.click(await ge.vis_label('작업 메뉴', timeout=3000), label='작업 메뉴')
        await p.wait_for_timeout(1200)
        await ge.shot('ge_5_12_dr_action_menu')
        await p.keyboard.press('Escape')
    except Exception as e:
        print('menu skipped', e, flush=True)
    await p.wait_for_timeout(800)
    print(await ge.stop_recording('ge5b_dr_result'), flush=True)


CURSOR_FWD_JS = r"""
() => {
  if (window.__fwdCursor) return 'ok';
  const P = window.parent;
  if (!P || P === window || !window.frameElement) return 'no-parent';
  window.__fwdCursor = true;
  const off = () => { const r = window.frameElement.getBoundingClientRect(); return [r.left, r.top]; };
  document.addEventListener('mousemove', e => {
    const c = P.__demoCursor; if (!c) return;
    const [ox, oy] = off();
    c.style.transform = `translate(${e.clientX + ox - 4}px, ${e.clientY + oy - 2}px)`;
  }, true);
  document.addEventListener('mousedown', e => {
    const [ox, oy] = off();
    const d = P.document, r = d.createElement('div');
    Object.assign(r.style, {position: 'fixed', left: (e.clientX + ox - 18) + 'px', top: (e.clientY + oy - 18) + 'px',
      width: '36px', height: '36px', borderRadius: '50%', border: '3px solid rgba(66,133,244,.95)',
      background: 'rgba(66,133,244,.18)', zIndex: 2147483646, pointerEvents: 'none', transform: 'scale(.4)',
      opacity: '1', transition: 'transform .45s ease-out, opacity .45s ease-out'});
    d.documentElement.appendChild(r);
    P.requestAnimationFrame(() => { r.style.transform = 'scale(1.6)'; r.style.opacity = '0'; });
    P.setTimeout(() => r.remove(), 600);
  }, true);
  return 'installed';
}
"""


class NB:
    def __init__(self, ge):
        self.ge, self.p = ge, ge.page

    @property
    def f(self):
        return nb_frame(self.p)

    async def box_text(self, text, exact=True, nth=0, timeout=25, min_x=0):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            f = self.f
            if f:
                fb = await (await f.frame_element()).bounding_box()
                raw = await f.evaluate(FIND_JS, [text, exact])
                hits = [h for h in raw if h['x'] >= 0 and h['y'] >= 0 and (fb['x'] + h['x']) >= min_x]
                if len(hits) > nth:
                    h = hits[nth]
                    return {'x': fb['x'] + h['x'], 'y': fb['y'] + h['y'], 'width': h['w'], 'height': h['h']}
            await self.p.wait_for_timeout(400)
        raise RuntimeError('text not found in notebook: ' + text)

    async def box_css(self, css, timeout=25, min_x=0):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            f = self.f
            if f:
                loc = f.locator(css)
                for i in range(await loc.count()):
                    b = await loc.nth(i).bounding_box()
                    if b and b['width'] > 2 and b['height'] > 2 and b['x'] >= min_x:
                        return b
            await self.p.wait_for_timeout(400)
        raise RuntimeError('css not found in notebook: ' + css)

    async def click_box(self, b, label, pause=900):
        p = self.p
        await self.ensure_cursor()
        x, y = b['x'] + b['width'] / 2, b['y'] + b['height'] / 2
        await p.mouse.move(x, y, steps=20)
        await p.wait_for_timeout(280)
        self.ge.mark('click', label=label, box=b)
        await p.mouse.down(); await p.wait_for_timeout(70); await p.mouse.up()
        await p.wait_for_timeout(pause)

    async def ensure_cursor(self):
        """Forward mouse events from the (same-origin) Notebook iframe to the GE page's demo cursor overlay.

        The overlay only listens on the top document, so without this it freezes at the iframe edge."""
        f = self.f
        if f:
            try:
                await f.evaluate(CURSOR_FWD_JS)
            except Exception as e:
                print('cursor forwarder skipped', e, flush=True)

    async def count_css(self, css):
        f = self.f
        return await f.locator(css).count() if f else 0


# visible broken markdown in the chat column (frame x 300..860): raw <br>, raw **bold**, pipe-table rulers
BAD_JS = r"""
() => {
  const out = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      const t = n.nodeValue || '';
      if (!/<br|\*\*|\|\s*:?-{3}/i.test(t)) continue;
      const el = n.parentElement; if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.width > 2 && r.height > 2 && r.x > 300 && r.x < 860 && r.bottom > 0 && r.top < 810) out.push(t.trim().slice(0, 80));
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return out;
}
"""
# Studio artifact rows: first icon ligature = type (videocam, audio_spark, tablet, stacked_bar_chart, auto_tab_group, quiz, copy)
STUDIO_JS = r"""
() => {
  let pending = 0;
  const tw = document.createTreeWalker(document, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = tw.nextNode())) if (/생성\s*중|생성하는\s*중/.test(n.nodeValue || '')) pending++;
  const icons = [];
  for (const row of document.querySelectorAll('div.artifact-button-content')) {
    const ic = row.querySelector('mat-icon, .material-symbols-outlined, [class*=icon]');
    if (ic) icons.push((ic.textContent || '').trim());
  }
  return {pending, icons};
}
"""
ROW_JS = r"""
([icon, scroll]) => {
  for (const row of document.querySelectorAll('div.artifact-button-content')) {
    const ic = row.querySelector('mat-icon, .material-symbols-outlined, [class*=icon]');
    if (!ic || (ic.textContent || '').trim() !== icon) continue;
    if (scroll) row.scrollIntoView({block: 'center'});
    const r = row.getBoundingClientRect();
    if (r.width > 50 && r.height > 20) return {x: r.x, y: r.y, w: r.width, h: r.height};
  }
  return null;
}
"""
KINDS = ['audio_spark', 'videocam', 'tablet', 'stacked_bar_chart', 'auto_tab_group', 'quiz', 'copy']


async def tile(nb, label, pause=1800):
    """Studio tile (div[role=button][aria-label]) in the right panel."""
    b = await nb.box_css(f'div[role="button"][aria-label="{label}"]', timeout=15, min_x=1100)
    await nb.click_box(b, label, pause=pause)


async def press(nb, text, label, pause=1500, timeout=10):
    b = await nb.box_text(text, exact=True, timeout=timeout)
    await nb.click_box(b, label, pause=pause)


async def close_if(nb, labels, pause=900):
    for al in labels:
        try:
            b = await nb.box_css(f'[aria-label="{al}"]', timeout=2)
        except RuntimeError:
            continue
        await nb.click_box(b, al, pause=pause)


async def open_row(nb, icon, label, pause=2500):
    f = nb.f
    fb = await (await f.frame_element()).bounding_box()
    await f.evaluate(ROW_JS, [icon, True])
    await nb.p.wait_for_timeout(500)
    r = await f.evaluate(ROW_JS, [icon, False])
    if not r:
        raise RuntimeError('studio row not found: ' + icon)
    # click the start of the title: the floating [메모 추가] button covers the middle of the lowest rows
    box = {'x': fb['x'] + r['x'] + 40, 'y': fb['y'] + r['y'] + 8, 'width': 48, 'height': r['h'] - 16}
    await nb.click_box(box, label, pause=pause)


PLACE_CURSOR_JS = r"""
([x, y, ripple]) => {
  const c = window.__demoCursor; if (c) c.style.transform = `translate(${x - 4}px, ${y - 2}px)`;
  if (!ripple) return;
  const r = document.createElement('div');
  Object.assign(r.style, {position: 'fixed', left: (x - 18) + 'px', top: (y - 18) + 'px', width: '36px', height: '36px',
    borderRadius: '50%', border: '3px solid rgba(66,133,244,.95)', background: 'rgba(66,133,244,.18)',
    zIndex: 2147483646, pointerEvents: 'none', transform: 'scale(.4)', opacity: '1',
    transition: 'transform .45s ease-out, opacity .45s ease-out'});
  document.documentElement.appendChild(r);
  requestAnimationFrame(() => { r.style.transform = 'scale(1.6)'; r.style.opacity = '0'; });
  setTimeout(() => r.remove(), 600);
}
"""


async def click_viewer(nb, rx, ry, label, pause=1500):
    """Click (rx, ry) relative to the Studio's nested viewer iframe (quiz / flashcards)."""
    p, f = nb.p, nb.f
    loc = f.locator('iframe')
    boxes = [await loc.nth(i).bounding_box() for i in range(await loc.count())]
    boxes = [b for b in boxes if b and b['width'] > 200 and b['height'] > 200]
    if not boxes:
        raise RuntimeError('viewer iframe not found')
    b = max(boxes, key=lambda b: b['width'] * b['height'])
    x, y = b['x'] + b['width'] * rx, b['y'] + b['height'] * ry
    start = await p.evaluate("() => { const c = window.__demoCursor; if (!c) return null;"
                             " const m = /translate\\(([-\\d.]+)px, ([-\\d.]+)px\\)/.exec(c.style.transform);"
                             " return m ? [+m[1] + 4, +m[2] + 2] : null; }")
    sx, sy = start or (x - 60, y - 60)
    for i in range(1, 17):                       # eased glide of the drawn cursor
        t = i / 16
        e = t * t * (3 - 2 * t)
        await p.evaluate(PLACE_CURSOR_JS, [sx + (x - sx) * e, sy + (y - sy) * e, False])
        await p.wait_for_timeout(16)
    await p.mouse.move(x, y)
    await p.wait_for_timeout(250)
    nb.ge.mark('click', label=label, box={'x': x - 40, 'y': y - 14, 'width': 80, 'height': 28})
    await p.evaluate(PLACE_CURSOR_JS, [x, y, True])
    await p.mouse.down(); await p.wait_for_timeout(70); await p.mouse.up()
    await p.wait_for_timeout(pause)


async def clip_c(ge):
    p = ge.page
    nb = NB(ge)
    await ge.goto(HOME, wait=5000)
    await p.mouse.move(900, 600)
    await ge.start_recording()
    await p.wait_for_timeout(1000)
    # 1) open Gemini Notebook from sidebar
    await ge.click(await ge.vis_label('Gemini Notebook'), label='Gemini Notebook')
    new_btn = await nb.box_css('[aria-label="새 노트북"], button:has-text("새 노트북"), button:has-text("새로 만들기")', timeout=30)
    await p.wait_for_timeout(1500)
    # Notebook area only, cropped above the 2nd card row: an older notebook card there carries a real company name.
    # (1152x420: a full-width 1440x420 strip is so wide that srcset rounding reads as a stretched image on mobile)
    await ge.shot('ge_5_13_nb_home', clip={'x': 288, 'y': 0, 'width': 1152, 'height': 420})
    # 2) new notebook -> add-source dialog
    await nb.click_box(new_btn, '새 노트북', pause=2500)
    await nb.box_css('[aria-label="컴퓨터에서 소스 업로드"], button:has-text("파일 업로드"), button:has-text("소스 업로드")', timeout=30)
    await p.wait_for_timeout(800)
    await ge.shot('ge_5_14_nb_add_source')
    # 3) upload Cymbal AirPole Pro brief PDF
    b = await nb.box_css('[aria-label="컴퓨터에서 소스 업로드"], button:has-text("파일 업로드"), button:has-text("소스 업로드")')
    x, y = b['x'] + b['width'] / 2, b['y'] + b['height'] / 2
    await nb.ensure_cursor()
    await p.mouse.move(x, y, steps=18)
    ge.mark('click', label='컴퓨터에서 소스 업로드', box=b)
    async with p.expect_file_chooser() as fc:
        await p.mouse.down(); await p.wait_for_timeout(70); await p.mouse.up()
    await (await fc.value).set_files(BRIEF_PDF)
    ge.mark('upload', label='Cymbal_신제품_브리프_에어폴_프로_가상.pdf')
    await ge.set_rate(2)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 120 and not await nb.count_css('[aria-label="요약 복사"]'):
        await p.wait_for_timeout(800)
    await ge.set_rate(1)
    print(f'summary ready in {time.monotonic() - t0:.0f}s', flush=True)
    await p.wait_for_timeout(2500)
    await ge.shot('ge_5_15_nb_summary')
    # 4) grounded question in the center chat input (min_x=580 so we skip the left source search box!)
    qbox = await nb.box_css('textarea[aria-label="쿼리 상자"], textarea', min_x=580)
    await nb.click_box(qbox, '질문 입력', pause=500)
    ge.mark('type_start', label='prompt', chars=len(NB_Q))
    await p.keyboard.type(NB_Q, delay=20)
    ge.mark('type_end', label='prompt')
    await p.wait_for_timeout(500)
    before = await nb.count_css('[aria-label="클립보드에 모델 대답 복사"]')
    await p.keyboard.press('Enter'); ge.mark('submit', label='nb_question')
    await ge.set_rate(2)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 120 and await nb.count_css('[aria-label="클립보드에 모델 대답 복사"]') <= before:
        await p.wait_for_timeout(800)
    await ge.set_rate(1)
    print(f'answer in {time.monotonic() - t0:.0f}s', flush=True)
    await p.wait_for_timeout(2500)
    NB_URL.write_text(nb.f.url)
    bad = await nb.f.evaluate(BAD_JS)
    if bad:
        # never publish a broken table (raw <br>, ** or pipe rulers): stop here and change NB_Q
        raise RuntimeError(f'broken markdown in notebook answer: {bad[:4]}')
    ge.mark('view', label='답변 표')
    await ge.shot('ge_5_16_nb_answer')
    # 5) hover a citation number
    try:
        cb = await nb.box_text('1', exact=True, timeout=5, min_x=580)
        await nb.ensure_cursor()
        await p.mouse.move(cb['x'] + cb['width'] / 2, cb['y'] + cb['height'] / 2, steps=18)
        ge.mark('hover', label='인용 번호', box=cb)
        await p.wait_for_timeout(2000)
    except Exception as e:
        print('citation hover skipped', e, flush=True)
    await ge.shot('ge_5_17_nb_citation')
    await p.mouse.move(1000, 640, steps=14)
    await p.wait_for_timeout(600)
    # 6) Studio: start every output type from the same brief (mind map left out on purpose)
    ge.mark('view', label='스튜디오')
    await ge.shot('ge_5_18_nb_studio')
    await tile(nb, 'AI 오디오 오버뷰')
    await ge.shot('ge_5_21_nb_audio_dialog')
    try:
        await press(nb, '짧게', '짧게', pause=700, timeout=4)
    except RuntimeError as e:
        print('length option skipped', e, flush=True)
    await press(nb, '생성', '오디오 생성')
    await tile(nb, '동영상 개요')
    await ge.shot('ge_5_22_nb_video_dialog')
    await press(nb, '생성', '동영상 생성')
    await tile(nb, '슬라이드 자료')
    await press(nb, '생성', '슬라이드 생성')
    await tile(nb, '인포그래픽', pause=2200)
    await ge.shot('ge_5_23_nb_infographic_dialog')
    await press(nb, '생성', '인포그래픽 생성')
    await tile(nb, '보고서')
    b = await nb.box_css('[aria-label="브리핑 문서"]', timeout=8)
    await nb.click_box(b, '브리핑 문서', pause=1500)
    await tile(nb, '퀴즈')
    await press(nb, '생성', '퀴즈 생성')
    await tile(nb, '플래시카드')
    await press(nb, '생성', '플래시카드 생성', pause=2500)
    await p.mouse.move(1000, 640, steps=14)
    ge.mark('view', label='생성 중')
    await p.wait_for_timeout(1500)
    await ge.shot('ge_5_24_nb_generating')
    await p.wait_for_timeout(1500)
    print(await ge.stop_recording('ge5c_notebook'), flush=True)


async def wait_studio(ge, timeout=1500):
    """Block until every Studio output has finished (no '생성 중' rows, all 7 types present)."""
    nb = NB(ge)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        st = await nb.f.evaluate(STUDIO_JS)
        missing = [k for k in KINDS if k not in st['icons']]
        print(f'studio pending={st["pending"]} missing={missing} t={time.monotonic() - t0:.0f}s', flush=True)
        if st['pending'] == 0 and not missing:
            return True
        await ge.page.wait_for_timeout(15000)
    return False


async def clip_s(ge):
    """Open each finished Studio output (same notebook as clip_c)."""
    p = ge.page
    nb = NB(ge)
    want = NB_URL.read_text().strip().split('?')[0]
    if not nb.f or nb.f.url.split('?')[0] != want:
        raise RuntimeError(f'open the clip_c notebook first: {want}')
    # an open viewer replaces the artifact list: close it before checking readiness (not recorded)
    await close_if(nb, ['닫기', '슬라이드 자료 닫기', '인포그래픽 닫기', 'AI 동영상 오버뷰 닫기', '메모 보기 닫기',
                        '웹페이지 뷰어 닫기', '오디오 플레이어 닫기'], pause=700)
    if not await wait_studio(ge):
        raise RuntimeError('studio outputs not ready')
    await p.mouse.move(1000, 640)
    await ge.start_recording()
    await p.wait_for_timeout(1500)
    ge.mark('view', label='스튜디오 완료')
    await ge.shot('ge_5_25_nb_studio_done')
    # video overview: plays inside the Studio panel; skip ahead twice to show different scenes
    await open_row(nb, 'videocam', '동영상 개요 열기', pause=2500)
    try:
        vb = await nb.box_css('video', timeout=4)
        ge.mark('view', label='동영상 플레이어', box=vb)
        print('video box', vb, flush=True)
    except RuntimeError as e:
        print('video box skipped', e, flush=True)
    await p.mouse.move(1210, 690, steps=12)          # park the cursor under the player (stills without cursor)
    await p.wait_for_timeout(2000)
    await ge.shot('ge_5_26_nb_video')
    for i in range(2):
        try:
            b = await nb.box_css('[aria-label="앞으로 건너뛰기"]', timeout=3)
            await nb.click_box(b, f'앞으로 건너뛰기 {i + 1}', pause=1200)
            await p.mouse.move(1210, 690, steps=10)
            await p.wait_for_timeout(2600)
        except RuntimeError as e:
            print('skip ahead skipped', e, flush=True)
    await ge.shot('ge_5_26b_nb_video_scene')
    await close_if(nb, ['동영상 일시중지', 'AI 동영상 오버뷰 닫기'])
    # audio overview: bottom player in the Studio panel
    await open_row(nb, 'audio_spark', '오디오 오버뷰 열기', pause=4500)
    await ge.shot('ge_5_27_nb_audio')
    await close_if(nb, ['오디오 플레이어 일시중지', '오디오 플레이어 닫기'])
    # slide deck: expand, then flip through a few slides from the thumbnail rail
    await open_row(nb, 'tablet', '슬라이드 자료 열기', pause=3000)
    await close_if(nb, ['펼치기'], pause=2500)
    ge.mark('view', label='슬라이드 1')
    await ge.shot('ge_5_28_nb_slides')
    for k, stem in ((2, 'ge_5_28b_nb_slides_2'), (3, 'ge_5_29_nb_slides_more'), (5, 'ge_5_29b_nb_slides_5')):
        try:
            b = await nb.box_css(f'div[role="button"][aria-label="슬라이드 {k}"]', timeout=3)
            await nb.click_box(b, f'슬라이드 {k}', pause=2600)
            await ge.shot(stem)
        except RuntimeError as e:
            print('slide thumb skipped', k, e, flush=True)
    await close_if(nb, ['닫기', '슬라이드 자료 닫기'])
    # infographic: opens in a large viewer
    await open_row(nb, 'stacked_bar_chart', '인포그래픽 열기', pause=2500)
    await p.mouse.move(1300, 732, steps=12)          # empty strip under the image (no cursor on the result)
    await p.wait_for_timeout(1500)
    ge.mark('view', label='인포그래픽')
    await ge.shot('ge_5_30_nb_infographic')
    await p.wait_for_timeout(1500)
    await close_if(nb, ['닫기', '인포그래픽 닫기'])
    # briefing doc (report)
    await open_row(nb, 'auto_tab_group', '보고서 열기', pause=3000)
    await ge.shot('ge_5_31_nb_report')
    await close_if(nb, ['메모 보기 닫기'])
    # quiz
    await open_row(nb, 'quiz', '퀴즈 열기', pause=3000)
    await ge.shot('ge_5_32_nb_quiz')
    await close_if(nb, ['웹페이지 뷰어 닫기'])
    # flashcards: flip the first card. The card is a nested viewer iframe (text not reachable), so click the
    # measured 「정답 보기」 spot (52 % across, 78 % down) and draw the demo cursor there ourselves.
    await open_row(nb, 'copy', '플래시카드 열기', pause=3000)
    try:
        await click_viewer(nb, 0.52, 0.78, '정답 보기', pause=2200)
    except RuntimeError as e:
        print('flip skipped', e, flush=True)
    await ge.shot('ge_5_33_nb_flashcards')
    await close_if(nb, ['웹페이지 뷰어 닫기'])
    await p.wait_for_timeout(1200)
    print(await ge.stop_recording('ge5d_studio'), flush=True)


SCROLLER_JS = r"""
() => { let best = null, bestH = 0;
  function walk(root) { for (const e of root.querySelectorAll('*')) { if (e.shadowRoot) walk(e.shadowRoot);
      const cs = getComputedStyle(e);
      if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll') && e.scrollHeight > e.clientHeight + 50 && e.scrollHeight > bestH) { best = e; bestH = e.scrollHeight; } } }
  walk(document); window.__sc = best; return bestH; }
"""
# scrollTop that puts the n-th element matching css `pad` px below the scroller top
TARGET_JS = r"""
([css, n, pad]) => { const sc = window.__sc; if (!sc) return null; const els = [];
  function find(root) { for (const e of root.querySelectorAll(css)) { const r = e.getBoundingClientRect(); if (r.height > 0) els.push(e); }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) find(e.shadowRoot); }
  find(document); const el = els[n < 0 ? els.length + n : n]; if (!el) return null;
  return {top: Math.max(0, Math.round(el.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop - pad)), text: (el.textContent||'').trim().slice(0,80), count: els.length}; }
"""
CITE_JS = r"""() => { const out = [];
  function scan(root) { for (const a of root.querySelectorAll('a[aria-label], button[aria-label]')) { const r = a.getBoundingClientRect();
      const al = a.getAttribute('aria-label') || '';
      if (r.width > 8 && r.width < 160 && r.height > 8 && r.height < 40 && r.y > 150 && r.y < 600 && r.x > 300 && !/메뉴|복사|공유|좋아|싫어|더보기/.test(al)) out.push({x: r.x, y: r.y, w: r.width, h: r.height, al: al.slice(0, 60)}); }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot); }
  scan(document); return out.slice(0, 6); }"""


async def glide(ge, top, ms=2600):
    await ge.page.evaluate("(t) => window.__sc.scrollTo({top: t, behavior: 'smooth'})", top)
    await ge.page.wait_for_timeout(ms)


async def clip_b(ge):
    p = ge.page
    await ge.goto(SESSION.read_text().strip(), wait=7000)
    h = await p.evaluate(SCROLLER_JS)
    print('scroll height', h, flush=True)
    for css in ('h1', 'h2', 'h3', 'table'):
        print(css, await p.evaluate(TARGET_JS, [css, 0, 24]), await p.evaluate(TARGET_JS, [css, -1, 24]), flush=True)
    if '--probe' in sys.argv:
        return
    await p.evaluate("() => { window.__sc.scrollTop = 0; }")
    await p.wait_for_timeout(1200)
    await p.mouse.move(820, 420)
    await ge.start_recording()
    await p.wait_for_timeout(1500)
    await ge.shot('ge_5_10_dr_done_top')
    t = await p.evaluate(TARGET_JS, ['h1, h2', 0, 24])
    if t:
        await glide(ge, t['top'], 3200)
        ge.mark('view', label='보고서 제목')
        await ge.shot('ge_5_11_dr_report_top')
    t2 = await p.evaluate(TARGET_JS, ['table', 0, 110])
    if t2 and (not t or t2['top'] > t['top']):
        await glide(ge, t2['top'], 2800)
        ge.mark('view', label='표')
        await ge.shot('ge_5_12_dr_table')
    links = await p.evaluate(CITE_JS)
    print('citations', links, flush=True)
    if links:
        b = links[0]
        box = {'x': b['x'], 'y': b['y'], 'width': b['w'], 'height': b['h']}
        await p.mouse.move(b['x'] + b['w'] / 2, b['y'] + b['h'] / 2, steps=18)
        ge.mark('hover', label='출처', box=box)
        await p.wait_for_timeout(2200)
        await ge.shot('ge_5_13_dr_citation')
        await p.mouse.move(820, 420, steps=10)
    t3 = await p.evaluate(TARGET_JS, ['h2, h3', -1, 24])
    if t3:
        await glide(ge, t3['top'], 3000)
        ge.mark('view', label='마지막 절')
        await ge.shot('ge_5_14_dr_conclusion')
    await p.evaluate("() => window.__sc.scrollTo({top: window.__sc.scrollHeight, behavior: 'smooth'})")
    await p.wait_for_timeout(2800)
    ge.mark('view', label='맨 아래')
    await ge.shot('ge_5_15_dr_bottom')
    print(await ge.stop_recording('ge5b_dr_result'), flush=True)
    print('brand', await ge.brand_scan(), flush=True)


async def main(which):
    async with GE() as ge:
        for k, fn in (('a2', clip_a2), ('c', clip_c), ('s', clip_s), ('b', clip_b)):
            if k in which:
                await fn(ge)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or ['c', 's']))
