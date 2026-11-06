"""Shared helpers for the v2 (Cymbal, generic) hands-on sample-file generators.

Shared helpers for the synthetic Cymbal practice files.
All data produced by these scripts is FICTIONAL (실습용 가상 데이터).
Rendering runs a private headless Chromium via Playwright (never the shared
Chrome on :9222) and blocks every non-local request.
"""
from __future__ import annotations

import html
import pathlib
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent          # production/samples/v2
ROOT = HERE.parents[2]                                  # repository root
OUT = HERE / "build"                                    # finished files
PREV = OUT / "previews"
WORK = HERE / "work"                                    # intermediate HTML / page shots
KEYS = HERE / "answer_keys"

DISCLAIMER = "실습용 가상 데이터 — Cymbal(심벌)은 가상의 회사이며 실제 기업·인물과 무관"
SHORT_DISC = "실습용 가상 데이터"
COMPANY = "Cymbal"
COMPANY_KO = "심벌"

# Pretendard (SIL OFL) self-hosted subsets from the v1 archive — used for HTML previews only.
# PDFs use NanumGothic: Chromium/Skia emits variable fonts (PretendardVariable) as Type3 glyphs,
# which breaks the PDF text layer (spaces between every syllable) — verified in work/fonttest.py.
PRETENDARD_DIR = ROOT / "production" / "site_build_v2" / "vendor" / "fonts"   # Pretendard web font (OFL)


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


FILES = {
    "sales": nfc("Cymbal_제품별_지역별_월별매출_2026_가상.xlsx"),
    "cs": nfc("Cymbal_고객문의_로그_2026-10_가상.xlsx"),
    "travel": nfc("Cymbal_출장비_및_경비처리_규정_가상.pdf"),
    "leave": nfc("Cymbal_휴가_및_근무제도_규정_가상.pdf"),
    "it": nfc("Cymbal_IT보안_및_계정관리_가이드_가상.pdf"),
    "brief": nfc("Cymbal_신제품_브리프_에어폴_프로_가상.pdf"),
    "brand": nfc("Cymbal_브랜드_가이드_가상.pdf"),
    "skill_zip": nfc("Cymbal_보고서스타일_스킬.zip"),
    "skill_md": "skills/cymbal-report-style/SKILL.md",
    "bundle": nfc("Cymbal_실습파일_전체.zip"),
}

# Design tokens (production/DESIGN_v2.md §1)
INK = "#0E1116"
SUB = "#5B6472"
LINE = "#E5E7EB"
BG = "#F7F8FA"
DARK = "#0B0F17"
BLUE = "#4285F4"        # GE accent / Cymbal Blue
VIOLET = "#9B72CB"
CORAL = "#D96570"
OK = "#1E8E3E"
WARN = "#F29900"
INFO = "#1A73E8"
DANGER = "#D93025"
GRAD = f"linear-gradient(135deg,{BLUE} 0%,{VIOLET} 55%,{CORAL} 100%)"

FONT_STACK = "'Pretendard','Apple SD Gothic Neo','AppleSDGothicNeo',sans-serif"


def pretendard_css() -> str:
    """@font-face rules pointing at the local Pretendard subsets (file:// URIs)."""
    css_path = PRETENDARD_DIR / "pretendard.css"
    if not css_path.is_file():
        return ""
    base = (PRETENDARD_DIR / "pretendard").as_uri()
    return css_path.read_text(encoding="utf-8").replace("url('pretendard/", f"url('{base}/")


def e(value) -> str:
    return html.escape(str(value), quote=True)


def out_path(key: str) -> pathlib.Path:
    return OUT / FILES[key]


def preview_path(filename: str) -> pathlib.Path:
    stem = pathlib.PurePosixPath(filename).name
    if stem.upper() == "SKILL.MD":
        stem = "cymbal-report-style"
    else:
        stem = stem.rsplit(".", 1)[0]
    return PREV / nfc(f"{stem}.png")


# ---------------------------------------------------------------------------
# Playwright rendering (same paginator as v1)
# ---------------------------------------------------------------------------
A4_CSS_WIDTH = 793.7  # 210mm @ 96dpi

PAGINATE_JS = r"""
() => {
  const flow = document.getElementById('flow');
  const tpl = document.getElementById('page-tpl');
  if (!flow || !tpl) return {pages: document.querySelectorAll('.page').length, log: []};
  const log = [];
  const blocks = Array.from(flow.children);
  let content = null;
  const newPage = (label) => {
    const p = tpl.content.firstElementChild.cloneNode(true);
    flow.parentNode.insertBefore(p, flow);
    const sec = p.querySelector('.sec-label');
    if (sec && label) sec.textContent = label;
    content = p.querySelector('.content');
    return content;
  };
  let label = '';
  const fits = () => content.scrollHeight <= content.clientHeight + 0.5;
  const isHeading = (el) => /^H[1-4]$/.test(el.tagName);
  const name = (b) => b.dataset.id || b.className;
  const place = (b) => {
    content.appendChild(b);
    if (fits()) return;
    const alone = content.children.length === 1;
    const splittable = !b.classList.contains('keep') && b.children.length > 1;
    if (splittable) {
      const shell = b.cloneNode(false);
      content.insertBefore(shell, b);
      content.removeChild(b);
      while (b.firstElementChild) {
        const k = b.firstElementChild;
        shell.appendChild(k);
        if (!fits()) { b.insertBefore(k, b.firstChild); break; }
      }
      while (shell.lastElementChild && isHeading(shell.lastElementChild)) {
        b.insertBefore(shell.lastElementChild, b.firstChild);
      }
      if (!b.firstElementChild) return;
      if (shell.firstElementChild) {
        log.push('split: ' + name(b));
        newPage(label);
        place(b);
        return;
      }
      shell.remove();
      if (!alone) { newPage(label); place(b); return; }
      content.appendChild(b);
      log.push('TOO TALL: ' + name(b));
      return;
    }
    if (!alone) {
      content.removeChild(b);
      newPage(label);
      content.appendChild(b);
      log.push('auto-break before: ' + name(b));
    }
    if (!fits()) log.push('TOO TALL: ' + name(b));
  };
  for (const b of blocks) {
    if (b.classList.contains('pb')) {
      label = b.dataset.label || label;
      newPage(label);
      continue;
    }
    if (!content) newPage(label);
    place(b);
  }
  flow.remove();
  const pages = Array.from(document.querySelectorAll('.page'));
  pages.forEach((p, i) => {
    const n = p.querySelector('.pno');
    if (n) n.textContent = (i + 1) + ' / ' + pages.length;
    p.style.breakAfter = (i === pages.length - 1) ? 'auto' : 'page';
  });
  const toc = {};
  document.querySelectorAll('[data-toc]').forEach(el => {
    const idx = pages.indexOf(el.closest('.page')) + 1;
    const key = el.dataset.toc;
    if (!(key in toc)) toc[key] = idx;
  });
  document.querySelectorAll('[data-toc-ref]').forEach(li => {
    const pg = li.querySelector('.pg');
    const key = li.dataset.tocRef;
    if (pg && key in toc) pg.textContent = String(toc[key]);
  });
  return {pages: pages.length, log, toc};
}
"""

OVERFLOW_JS = r"""
() => Array.from(document.querySelectorAll('.page')).map((p, i) => {
  const c = p.querySelector('.content');
  if (!c) return {page: i + 1, over: 0, fill: null};
  let bottom = 0;
  for (const ch of c.children) bottom = Math.max(bottom, ch.offsetTop + ch.offsetHeight);
  return {page: i + 1, over: Math.round(c.scrollHeight - c.clientHeight),
          fill: Math.round(100 * bottom / c.clientHeight)};
})
"""


def _block_remote(route):
    url = route.request.url
    if url.startswith(("file:", "data:", "about:")):
        route.continue_()
    else:
        route.abort()


def render_document(html_str: str, pdf_path: pathlib.Path, png_path: pathlib.Path | None,
                    *, preview_width: int = 1200) -> dict:
    """Render paginated HTML → PDF (A4) and page-1 PNG preview. Returns a report."""
    from playwright.sync_api import sync_playwright

    WORK.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = WORK / (pdf_path.stem + ".html")
    tmp.write_text(html_str, encoding="utf-8")
    report: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            dsf = preview_width / A4_CSS_WIDTH
            page = browser.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=dsf)
            page.route("**/*", _block_remote)
            page.emulate_media(media="print")
            page.goto(tmp.as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready.then(() => true)")
            report["paginate"] = page.evaluate(PAGINATE_JS)
            report["overflow"] = [o for o in page.evaluate(OVERFLOW_JS)]
            page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)
            if png_path is not None:
                png_path.parent.mkdir(parents=True, exist_ok=True)
                page.locator(".page").first.screenshot(path=str(png_path))
            (WORK / (pdf_path.stem + ".paginated.html")).write_text(page.content(), encoding="utf-8")
        finally:
            browser.close()
    return report


def render_png(html_str: str, png_path: pathlib.Path, *, width: int = 1200, selector: str = "#shot",
               scale: float = 1.0, name: str = "shot") -> None:
    """Render an HTML snippet and screenshot the element matching `selector`."""
    from playwright.sync_api import sync_playwright

    WORK.mkdir(parents=True, exist_ok=True)
    tmp = WORK / f"{name}.html"
    tmp.write_text(html_str, encoding="utf-8")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": int(width / scale) + 40, "height": 1000},
                                    device_scale_factor=scale)
            page.route("**/*", _block_remote)
            page.goto(tmp.as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.locator(selector).screenshot(path=str(png_path))
        finally:
            browser.close()
