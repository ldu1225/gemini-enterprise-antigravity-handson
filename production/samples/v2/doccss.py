"""Shared print CSS + decorative SVG art for the fictional Cymbal PDF documents (adapted from v1 doccss.py).

Art is abstract (concentric arcs / dot grid) — no real logos, no UI mockups.
"""
from __future__ import annotations

import math
import random

from common import BG, BLUE, CORAL, DANGER, DISCLAIMER, INK, LINE, OK, SUB, VIOLET, WARN, e

# PDF body font: NanumGothic (SIL OFL) embeds as TrueType CID (Type0) in Chromium PDFs → clean text layer.
# Pretendard is only available as a variable font here, which Chromium emits as Type3 (broken extraction).
DOC_FONT_STACK = "'NanumGothic','Nanum Gothic','Apple SD Gothic Neo',sans-serif"
ACC = BLUE
ACC_DARK = "#1F4FB8"

BASE_CSS = f"""
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: #fff; }}
body {{
  font-family: {DOC_FONT_STACK}; color: {INK}; font-size: 9pt; line-height: 1.55;
  word-break: keep-all; overflow-wrap: break-word;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}
b, strong {{ font-weight: 700; }}
.page {{ position: relative; width: 210mm; height: 297mm; overflow: hidden; background: #fff; }}
.hdr {{
  position: absolute; top: 0; left: 16mm; right: 16mm; height: 16mm;
  display: flex; align-items: flex-end; gap: 2.6mm; padding-bottom: 2.2mm;
  font-size: 7.4pt; color: {SUB}; border-bottom: 0.3mm solid {LINE};
}}
.hdr::after {{ content: ""; position: absolute; left: 0; bottom: -0.3mm; width: 24mm; height: 0.6mm; background: {ACC}; }}
.hdr .brand {{ font-weight: 800; color: {ACC}; font-size: 8.2pt; letter-spacing: .01em; }}
.hdr .dt {{ font-weight: 700; color: {INK}; }}
.hdr .vd {{ color: {DANGER}; font-weight: 700; border: 0.25mm solid #F3B8B3; border-radius: 999px; padding: 0 2mm; font-size: 6.8pt; }}
.hdr .sec-label {{ margin-left: auto; }}
.content {{ position: absolute; top: 21mm; bottom: 16mm; left: 16mm; right: 16mm; overflow: hidden; }}
.ftr {{
  position: absolute; bottom: 0; left: 16mm; right: 16mm; height: 12mm;
  display: flex; align-items: center; justify-content: space-between;
  font-size: 7pt; color: {SUB}; border-top: 0.25mm solid {LINE};
}}
.ftr .disc {{ color: {DANGER}; font-weight: 700; }}
.ftr .pno {{ font-weight: 700; color: {INK}; letter-spacing: .02em; }}

h2.sec {{
  display: flex; align-items: center; gap: 2.4mm; font-size: 12.5pt; font-weight: 800;
  letter-spacing: -0.02em; margin: 1.6mm 0 1.6mm; padding-bottom: 1.3mm; border-bottom: 0.25mm solid {LINE};
}}
h2.sec .no {{
  flex: none; height: 6.6mm; padding: 0 2mm; border-radius: 1.8mm; background: {ACC}; color: #fff;
  font-size: 8.6pt; display: inline-flex; align-items: center; justify-content: center;
}}
h2.sec .en {{ margin-left: auto; font-size: 7.4pt; font-weight: 700; color: {SUB}; letter-spacing: .06em; }}
h3 {{ font-size: 9.6pt; font-weight: 700; margin: 2mm 0 0.8mm; }}
h3 .n {{ color: {ACC}; margin-right: 1.6mm; font-weight: 800; }}
p {{ margin: 0 0 1.4mm; }}
.blk {{ padding-bottom: 1mm; }}
ol.cl {{ list-style: none; margin: 0 0 1.3mm; }}
ol.cl > li {{ display: flex; gap: 1.6mm; margin-bottom: 0.6mm; }}
ol.cl > li > .k {{ flex: none; min-width: 5.2mm; color: {ACC_DARK}; font-weight: 700; }}
ul.dot {{ list-style: disc outside; margin: 0 0 1.3mm; padding-left: 3.8mm; }}
ul.dot > li {{ margin-bottom: 0.5mm; padding-left: 0.4mm; }}
ul.dot > li::marker {{ color: {ACC}; font-size: 0.85em; }}
table.t {{ width: 100%; border-collapse: collapse; font-size: 8.4pt; margin: 0.9mm 0 1.6mm; line-height: 1.45; }}
table.t th {{
  background: #EEF3FE; font-weight: 700; color: {INK}; text-align: center; padding: 1.1mm 1.6mm;
  border-top: 0.55mm solid {ACC}; border-bottom: 0.3mm solid #C9D6F2;
}}
table.t td {{ padding: 1mm 1.6mm; border-bottom: 0.25mm solid {LINE}; vertical-align: middle; }}
table.t td.c {{ text-align: center; }}
table.t td.r {{ text-align: right; font-variant-numeric: tabular-nums; }}
table.t td.k {{ font-weight: 700; background: #FAFBFC; text-align: center; }}
table.t td.hi {{ font-weight: 800; color: {ACC_DARK}; }}
.fn {{ font-size: 7.9pt; color: {SUB}; margin: -0.6mm 0 1.6mm; }}
.ex {{
  font-size: 8.4pt; background: {BG}; border: 0.25mm dashed #C3CAD5;
  border-radius: 2mm; padding: 1.4mm 2.8mm; margin: 0.6mm 0 1.8mm;
}}
.ex b {{ color: {ACC_DARK}; }}
.note {{
  background: #F1F6FE; border-left: 1.1mm solid {ACC}; border-radius: 1.8mm;
  padding: 1.7mm 3mm; margin: 1mm 0 1.6mm; font-size: 8.5pt;
}}
.note.red {{ background: #FDF0EF; border-left-color: {DANGER}; }}
.note.warn {{ background: #FEF6E7; border-left-color: {WARN}; }}
.note.green {{ background: #EDF7F0; border-left-color: {OK}; }}
.note .lbl {{ font-weight: 800; margin-right: 1.6mm; }}
.note.red .lbl {{ color: {DANGER}; }}
.note ul.dot {{ margin: 0.8mm 0 0; }}
.disc-banner {{
  background: #FDF0EF; border: 0.3mm solid #F6CBC7; border-left: 1.4mm solid {DANGER};
  border-radius: 2.2mm; padding: 3mm 4mm;
}}
.disc-banner .t {{ color: {DANGER}; font-weight: 800; font-size: 10.5pt; letter-spacing: -0.01em; }}
.disc-banner .d {{ font-size: 8pt; color: #3A3F46; margin-top: 0.6mm; }}
.qa {{ display: grid; grid-template-columns: 6.4mm 1fr; column-gap: 2.4mm; row-gap: 0.5mm; padding: 1.5mm 0; border-bottom: 0.25mm solid {LINE}; }}
.qa .q, .qa .a {{ width: 5.8mm; height: 5.8mm; border-radius: 50%; font-weight: 800; font-size: 8pt; display: flex; align-items: center; justify-content: center; }}
.qa .q {{ background: {ACC}; color: #fff; }}
.qa .a {{ background: #EEF0F3; color: {INK}; }}
.qa .qt {{ font-weight: 800; font-size: 9.3pt; align-self: center; letter-spacing: -0.01em; }}
.qa .at {{ color: #262B31; font-size: 8.8pt; }}
.steps {{ display: flex; align-items: stretch; gap: 1.6mm; margin: 1.2mm 0 2mm; }}
.step {{ flex: 1; background: {BG}; border: 0.25mm solid {LINE}; border-radius: 2.2mm; padding: 2mm 1.6mm 1.8mm; text-align: center; }}
.step .sn {{ display: inline-flex; width: 5.2mm; height: 5.2mm; border-radius: 50%; background: {ACC}; color: #fff; font-weight: 800; font-size: 7.6pt; align-items: center; justify-content: center; }}
.step .st {{ font-weight: 800; font-size: 8.5pt; margin-top: 0.8mm; }}
.step .ss {{ font-size: 7.3pt; color: {SUB}; line-height: 1.38; margin-top: 0.4mm; }}
.defs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.2mm 3mm; margin: 0.6mm 0 1.3mm; }}
.defs div {{ display: flex; gap: 2mm; align-items: baseline; background: {BG}; border-radius: 1.6mm; padding: 1.2mm 2.2mm; font-size: 8.3pt; }}
.defs .term {{ flex: none; width: 17mm; font-weight: 800; color: {ACC_DARK}; }}
.contact {{ margin-top: 2.4mm; display: flex; justify-content: space-between; align-items: center; background: {BG};
  border-radius: 2.2mm; padding: 2.2mm 3.2mm; font-size: 8.3pt; }}
.contact b {{ color: {ACC_DARK}; }}
"""

COVER_CSS = f"""
.cover .band {{ position:absolute; left:0; top:0; width:210mm; height:122mm; color:#fff; overflow:hidden;
  background: linear-gradient(135deg, #1B3F8F 0%, {ACC} 52%, {VIOLET} 100%); }}
.cover .band .art {{ position:absolute; right:-30mm; top:-26mm; width:170mm; height:170mm; }}
.cover .band .art svg {{ width:100%; height:100%; }}
.cover .brandline {{ position:absolute; left:18mm; top:15mm; display:flex; align-items:baseline; gap:3mm; }}
.cover .wordmark {{ font-size:16pt; font-weight:800; letter-spacing:.02em; }}
.cover .brandline .kor {{ font-size:8.6pt; color:rgba(255,255,255,.88); font-weight:700; }}
.cover .vchip {{ position:absolute; right:18mm; top:15mm; background:#fff; color:{DANGER}; font-weight:800; font-size:8.6pt;
  border-radius:999px; padding:1mm 3.4mm; }}
.cover .kicker {{ position:absolute; left:18mm; top:45mm; font-size:8.4pt; letter-spacing:.22em; font-weight:700; color:rgba(255,255,255,.86); }}
.cover h1 {{ position:absolute; left:18mm; top:52mm; font-size:32pt; line-height:1.2; font-weight:800; letter-spacing:-0.035em; }}
.cover .en {{ position:absolute; left:18mm; top:95mm; font-size:10.5pt; color:rgba(255,255,255,.92); }}
.cover .chips {{ position:absolute; left:18mm; bottom:8mm; display:flex; gap:2mm; }}
.cover .chips span {{ border:0.3mm solid rgba(255,255,255,.7); border-radius:999px; padding:0.7mm 3mm; font-size:7.8pt; font-weight:700; }}
.cover-body {{ position:absolute; top:131mm; left:18mm; right:18mm; display:grid; grid-template-columns: 1.08fr 1fr; gap:10mm; }}
.cover h4 {{ font-size:8.8pt; font-weight:800; color:{ACC_DARK}; letter-spacing:.03em; margin:0 0 1.6mm; padding-bottom:1.2mm; border-bottom:0.4mm solid {INK}; }}
.cover h4.second {{ margin-top:5mm; }}
table.meta {{ width:100%; border-collapse:collapse; }}
table.meta td {{ padding:1.15mm 0; border-bottom:0.25mm solid {LINE}; font-size:8.4pt; vertical-align:top; }}
table.meta td:first-child {{ width:21mm; color:{SUB}; font-weight:700; }}
table.rev {{ width:100%; border-collapse:collapse; font-size:7.8pt; }}
table.rev td {{ padding:1mm 0.6mm; border-bottom:0.25mm solid {LINE}; vertical-align:top; }}
table.rev td:first-child {{ width:13mm; font-weight:700; }} table.rev td:nth-child(2) {{ width:17mm; color:{SUB}; }}
ol.toc {{ list-style:none; }}
ol.toc li {{ display:flex; align-items:baseline; padding:1.12mm 0; border-bottom:0.25mm dotted #C9CDD3; font-size:8.7pt; }}
ol.toc .no {{ width:9mm; color:{ACC_DARK}; font-weight:800; }}
ol.toc .tt {{ flex:1; }}
ol.toc .pg {{ color:{SUB}; font-weight:700; }}
.cover .disc-banner {{ position:absolute; left:18mm; right:18mm; bottom:22mm; }}
.cover-foot {{ position:absolute; left:18mm; right:18mm; bottom:9mm; display:flex; justify-content:space-between;
  font-size:7.8pt; color:{SUB}; border-top:0.25mm solid {LINE}; padding-top:2.2mm; }}
.cover-foot b {{ color:{INK}; }}
"""


def arcs_art(size: float = 170, seed: int = 3) -> str:
    """Abstract concentric arcs + dot grid (deterministic, white strokes)."""
    rng = random.Random(seed)
    parts = []
    cx, cy = size * 0.62, size * 0.42
    for i in range(14):
        r = 12 + i * 7.5
        a0 = rng.uniform(0, 360)
        sweep = rng.uniform(70, 250)
        x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
        x1, y1 = cx + r * math.cos(math.radians(a0 + sweep)), cy + r * math.sin(math.radians(a0 + sweep))
        large = 1 if sweep > 180 else 0
        op = 0.18 + 0.4 * rng.random()
        parts.append(f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 {large} 1 {x1:.1f},{y1:.1f}" fill="none" '
                     f'stroke="#fff" stroke-width="{0.5 + rng.random() * 0.9:.2f}" stroke-linecap="round" opacity="{op:.2f}"/>')
    for gx in range(0, int(size), 9):
        for gy in range(0, int(size), 9):
            if rng.random() < 0.18:
                parts.append(f'<circle cx="{gx}" cy="{gy}" r="0.7" fill="#fff" opacity="{0.15 + rng.random() * 0.3:.2f}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">{"".join(parts)}</svg>'


def page_template(brand: str, doc_title: str, right: str) -> str:
    return f"""
<template id="page-tpl">
  <div class="page">
    <div class="hdr"><span class="brand">{e(brand)}</span><span class="dt">{e(doc_title)}</span><span class="vd">실습용 가상 데이터</span><span class="sec-label">{e(right)}</span></div>
    <div class="content"></div>
    <div class="ftr"><span class="disc">※ {e(DISCLAIMER)}</span><span class="pno"></span></div>
  </div>
</template>"""


def table(headers, rows, col_cls=None, *, cls="t", widths=None, raw=False) -> str:
    col_cls = col_cls or [""] * len(headers)
    colgroup = ""
    if widths:
        colgroup = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in widths) + "</colgroup>"
    th = "".join(f"<th>{h if raw else e(h)}</th>" for h in headers)
    trs = []
    for row in rows:
        tds = "".join(f'<td class="{col_cls[i]}">{(c if raw else e(c))}</td>' for i, c in enumerate(row))
        trs.append(f"<tr>{tds}</tr>")
    return f'<table class="{cls}">{colgroup}<thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


# ---- small block helpers (author markup is trusted; data values go through e()) ----
def sec(no: str, title: str, en: str, body: str, toc: str | None = None) -> str:
    return (f'<section class="blk" data-id="sec{e(no)}" data-toc="{e(toc or no)}"><h2 class="sec"><span class="no">{e(no)}</span>'
            f'{e(title)}<span class="en">{e(en)}</span></h2>{body}</section>')


def blk(body: str, bid: str = "") -> str:
    return f'<section class="blk" data-id="{e(bid)}">{body}</section>'


def h3(num: str, title: str) -> str:
    return f'<h3><span class="n">{e(num)}</span>{e(title)}</h3>'


def ul(items: list[str]) -> str:
    return '<ul class="dot">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def clauses(items: list[tuple[str, str]]) -> str:
    """Numbered clause list: [("①", "text"), ...]."""
    return '<ol class="cl">' + "".join(f'<li><span class="k">{e(k)}</span><span>{v}</span></li>' for k, v in items) + "</ol>"


CIRC = "①②③④⑤⑥⑦⑧⑨⑩"


def cl(*texts: str) -> str:
    return clauses([(CIRC[i], t) for i, t in enumerate(texts)])


def note(label: str, body: str, kind: str = "") -> str:
    return f'<div class="note {kind}"><span class="lbl">{e(label)}</span>{body}</div>'


def qa(q: str, a: str) -> str:
    return ('<div class="qa"><span class="q">Q</span><span class="qt">' + e(q) + '</span>'
            '<span class="a">A</span><span class="at">' + e(a) + '</span></div>')


def cover(*, kicker: str, title_html: str, en: str, doc_no: str, rev: str, effective: str, dept: str,
          scope: str, revs: list[tuple[str, str, str]], toc: list[tuple[str, str]], contact: str,
          purpose: str, seed: int = 3) -> str:
    meta = [("문서번호", doc_no), ("버전", rev), ("시행일", effective), ("주관부서", dept),
            ("적용대상", scope), ("보안등급", "사내한정 (실습용 가상 문서)")]
    meta_html = "".join(f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in meta)
    rev_html = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in revs)
    toc_html = "".join(f'<li data-toc-ref="{e(n)}"><span class="no">{e(n)}</span><span class="tt">{e(t)}</span>'
                       f'<span class="pg">-</span></li>' for n, t in toc)
    return f"""
<div class="page cover">
  <div class="band">
    <div class="art">{arcs_art(seed=seed)}</div>
    <div class="brandline"><span class="wordmark">Cymbal</span><span class="kor">심벌 · 사내 규정</span></div>
    <div class="vchip">실습용 가상 데이터</div>
    <div class="kicker">{e(kicker)}</div>
    <h1>{title_html}</h1>
    <div class="en">{e(en)}</div>
    <div class="chips"><span>{e(doc_no)}</span><span>{e(rev)}</span><span>시행 {e(effective)}</span></div>
  </div>
  <div class="cover-body">
    <div>
      <h4>문서 정보</h4>
      <table class="meta">{meta_html}</table>
      <h4 class="second">개정 이력</h4>
      <table class="rev">{rev_html}</table>
    </div>
    <div>
      <h4>목차</h4>
      <ol class="toc">{toc_html}</ol>
    </div>
  </div>
  <div class="disc-banner">
    <div class="t">※ {e(DISCLAIMER)}</div>
    <div class="d">{e(purpose)} 문서번호·금액·절차·연락처 등 모든 내용은 가상이며 실제 기업의 규정과 관련이 없습니다.</div>
  </div>
  <div class="cover-foot"><span><b>{e(dept)}</b> · {e(contact)}</span><span>{e(doc_no)} · {e(rev)}</span></div>
</div>"""
