"""Preview PNGs (1200px wide) for the xlsx files, the skill and the bundle (adapted from v1 build_previews.py).

PDF previews (page 1) are produced by build_*_pdf.py from the same paginated DOM that is printed to PDF.
xlsx previews are HTML re-creations of the first sheet using the same data + formatting rules as build_xlsx.py.
Previews use Pretendard (self-hosted subsets) — screenshots are raster, so the variable font is fine here.
"""
from __future__ import annotations

import data_inquiries as Q
import data_sales as S
from common import (BG, BLUE, DANGER, DISCLAIMER, FILES, FONT_STACK, GRAD, INK, LINE, OUT, SUB, e,
                    preview_path, pretendard_css, render_png)

GRID = "#E1E3E6"
FONTS = pretendard_css()

SHEET_CSS = f"""
{FONTS}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #EEF0F3; font-family: {FONT_STACK}; color: {INK}; }}
#shot {{ width: 1200px; background: #fff; }}
.fbar {{ display: flex; align-items: center; gap: 12px; padding: 14px 20px; background: #fff; border-bottom: 1px solid {LINE}; }}
.fbar .ext {{ background: #1E7145; color: #fff; font-weight: 800; font-size: 12px; border-radius: 6px; padding: 5px 8px; letter-spacing: .04em; }}
.fbar .fn {{ font-weight: 800; font-size: 16px; letter-spacing: -0.01em; }}
.fbar .chip {{ margin-left: auto; font-size: 12px; font-weight: 800; color: {DANGER}; background: #FDF0EF; border: 1px solid #F6CBC7; border-radius: 999px; padding: 4px 12px; }}
.wrap {{ position: relative; overflow: hidden; }}
table.xl {{ border-collapse: collapse; table-layout: fixed; font-size: 13px; }}
table.xl td {{ border: 1px solid {GRID}; height: 25px; padding: 0 7px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
table.xl .colh {{ background: #F3F4F6; color: #6B7280; font-weight: 600; font-size: 12px; text-align: center; height: 22px; }}
table.xl .rowh {{ background: #F3F4F6; color: #6B7280; font-size: 12px; text-align: center; }}
table.xl .corner {{ background: #E9EBEE; }}
table.xl .title td.t {{ height: 38px; font-size: 18px; font-weight: 800; }}
table.xl .title .disc {{ color: {DANGER}; font-size: 13px; font-weight: 800; margin-left: 14px; }}
table.xl .hdr td {{ background: {BLUE}; color: #fff; font-weight: 800; text-align: center; border-color: #2B63C6; height: 34px; white-space: normal; line-height: 1.2; word-break: keep-all; font-size: 12.5px; }}
table.xl tr.band td.c {{ background: {BG}; }}
table.xl td.r {{ text-align: right; font-variant-numeric: tabular-nums; }}
table.xl td.m {{ text-align: center; }}
.fade {{ position: absolute; left: 0; right: 0; bottom: 0; height: 90px; background: linear-gradient(rgba(255,255,255,0), #fff 85%); }}
.tabs {{ display: flex; align-items: stretch; gap: 2px; background: #F3F4F6; border-top: 1px solid {GRID}; padding: 0 16px; height: 38px; }}
.tabs span {{ display: flex; align-items: center; padding: 0 18px; font-size: 13px; color: {SUB}; font-weight: 600; }}
.tabs span.on {{ background: #fff; color: {INK}; font-weight: 800; box-shadow: inset 0 -3px 0 {BLUE}; }}
.tabs .more {{ margin-left: auto; color: {SUB}; font-size: 12px; }}
"""


def sheet_html(fname, title, headers, widths, rows, tabs, *, max_rows, note):
    cols = len(headers)
    letters = [chr(ord("A") + i) for i in range(cols)]
    colgroup = '<col style="width:42px">' + "".join(f'<col style="width:{w}px">' for w in widths)
    out = [f'<table class="xl" style="width:{42 + sum(widths)}px"><colgroup>{colgroup}</colgroup>']
    out.append('<tr><td class="colh corner"></td>' + "".join(f'<td class="colh">{c}</td>' for c in letters) + "</tr>")
    out.append(f'<tr class="title"><td class="rowh">1</td><td class="t" colspan="{cols}">{e(title)}'
               f'<span class="disc">※ 실습용 가상 데이터</span></td></tr>')
    out.append('<tr class="hdr"><td class="rowh" style="background:#F3F4F6;color:#6B7280;border-color:#E1E3E6">2</td>'
               + "".join(f"<td>{e(h)}</td>" for h in headers) + "</tr>")
    for i, row in enumerate(rows[:max_rows]):
        cells = "".join(f'<td class="c {cls}">{e(v)}</td>' for v, cls in row)
        out.append(f'<tr class="{"band" if i % 2 else ""}"><td class="rowh">{i + 3}</td>{cells}</tr>')
    out.append("</table>")
    tab_html = "".join(f'<span class="{"on" if i == 0 else ""}">{e(t)}</span>' for i, t in enumerate(tabs))
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{SHEET_CSS}</style></head>
<body><div id="shot">
  <div class="fbar"><span class="ext">XLSX</span><span class="fn">{e(fname)}</span><span class="chip">실습용 가상 데이터</span></div>
  <div class="wrap">{"".join(out)}<div class="fade"></div></div>
  <div class="tabs">{tab_html}<span class="more">{e(note)}</span></div>
</div></body></html>"""


def sales_preview() -> None:
    rows = []
    for r in S.rows():
        rows.append([(r["월"], "m"), (r["분기"], "m"), (r["제품"], "m"), (r["지역"], "m"),
                     (f"{r['판매수량(대)']:,}", "r"), (f"{r['평균판매가(원)']:,}", "r"), (f"{r['매출액(백만원)']:,.1f}", "r"),
                     (f"{r['매출총이익(백만원)']:,.1f}", "r"), (f"{r['매출총이익률(%)']:.1f}", "r")])
    html = sheet_html(FILES["sales"], "Cymbal 제품별·지역별 월별 매출 (2026년 1~9월)", S.SALES_COLS,
                      [86, 70, 120, 84, 116, 130, 130, 150, 136], rows, ["매출데이터", "목표"],
                      max_rows=22, note="225행 × 9열 · 목표 45행 · 2개 시트")
    render_png(html, preview_path(FILES["sales"]), name="preview_sales")


def cs_preview() -> None:
    rows = []
    for r in Q.public_rows():
        rows.append([(r["문의번호"], "m"), (r["접수일시"].strftime("%Y-%m-%d %H:%M"), "m"), (r["채널"], "m"),
                     (r["고객명(가상)"], "m"), (r["제품"], "m"), (r["주문번호"], "m"), (r["문의내용"], "")])
    html = sheet_html(FILES["cs"], "Cymbal 고객 문의 로그 (2026년 10월 1~25일, 60건)", Q.COLUMNS,
                      [108, 140, 92, 100, 104, 132, 480], rows, ["문의로그"], max_rows=22,
                      note="60행 × 7열 · 분류·긴급도는 직접 판단")
    render_png(html, preview_path(FILES["cs"]), name="preview_cs")


def skill_preview() -> None:
    text = (OUT / FILES["skill_md"]).read_text(encoding="utf-8")
    out = []
    for i, ln in enumerate(text.split("\n")[:40]):
        cls = ""
        if ln == "---":
            cls = "fm"
        elif ln.startswith(("name:", "description:")):
            k, v = ln.split(":", 1)
            out.append(f'<div class="ln"><span class="no">{i + 1}</span><span class="key">{e(k)}:</span><span class="val">{e(v)}</span></div>')
            continue
        elif ln.startswith("#"):
            cls = "h"
        elif ln.startswith(">"):
            cls = "q"
        out.append(f'<div class="ln {cls}"><span class="no">{i + 1}</span><span>{e(ln) or "&nbsp;"}</span></div>')
    css = f"""{FONTS}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#EEF0F3; font-family:{FONT_STACK}; }}
#shot {{ width:1200px; background:#0B0F17; color:#E6E8EB; }}
.fbar {{ display:flex; align-items:center; gap:12px; padding:16px 22px; background:#121826; border-bottom:1px solid #1F2937; }}
.fbar .ext {{ background:{BLUE}; color:#fff; font-weight:800; font-size:12px; border-radius:6px; padding:5px 8px; }}
.fbar .fn {{ font-weight:800; font-size:16px; color:#fff; }}
.fbar .path {{ color:#9AA4B2; font-size:13px; font-family: Menlo, monospace; }}
.fbar .chip {{ margin-left:auto; font-size:12px; font-weight:800; color:#FFD9D6; border:1px solid #6A2A2A; border-radius:999px; padding:4px 12px; }}
.code {{ padding:14px 0 18px; font-family: Menlo, 'Pretendard', monospace; font-size:13.5px; line-height:1.62; }}
.ln {{ display:flex; gap:16px; padding:0 22px; white-space:pre-wrap; word-break:break-all; }}
.ln .no {{ flex:none; width:28px; text-align:right; color:#4B5563; }}
.ln.fm span:last-child {{ color:#F29900; }}
.ln .key {{ color:#7DD3FC; font-weight:700; flex:none; }}
.ln .val {{ color:#FDE68A; }}
.ln.h span:last-child {{ color:#A8C7FA; font-weight:800; }}
.ln.q span:last-child {{ color:#A7F3D0; }}
.foot {{ display:flex; justify-content:space-between; padding:12px 22px; background:#121826; border-top:1px solid #1F2937; color:#9AA4B2; font-size:12.5px; }}
"""
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body><div id="shot">
<div class="fbar"><span class="ext">SKILL</span><span class="fn">SKILL.md</span><span class="path">cymbal-report-style/SKILL.md</span><span class="chip">실습용 가상 데이터</span></div>
<div class="code">{"".join(out)}</div>
<div class="foot"><span>스킬 업로드용 · {e(FILES["skill_zip"])}</span><span>※ {e(DISCLAIMER)}</span></div>
</div></body></html>"""
    render_png(html, preview_path("SKILL.md"), name="preview_skill")


BUNDLE_ITEMS = [("sales", "제품별·지역별 월별 매출", "Lab 3"), ("cs", "고객 문의 로그 60건", "Lab 8"),
                ("travel", "출장비·경비처리 규정", "Lab 7"), ("leave", "휴가·근무제도 규정", "Lab 7"),
                ("it", "IT보안·계정관리 가이드", "Lab 7"), ("brief", "신제품 브리프 AirPole Pro", "Lab 4"),
                ("brand", "브랜드 가이드", "Lab 4·6"), ("skill_md", "보고서 스타일 스킬", "Lab 6")]


def bundle_preview() -> None:
    def prev(k):
        return preview_path("SKILL.md" if k == "skill_md" else FILES[k])
    cards = "".join(
        f'<div class="card"><div class="img" style="background-image:url(\'{prev(k).as_uri()}\')"></div>'
        f'<div class="cap"><b>{e(t)}</b><span>{e(lab)}</span></div></div>' for k, t, lab in BUNDLE_ITEMS)
    css = f"""{FONTS}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#EEF0F3; font-family:{FONT_STACK}; }}
#shot {{ width:1200px; padding:34px 40px 28px; background:linear-gradient(160deg,#FFFFFF 0%,#F1F5FE 55%,#F3EEFA 100%); }}
.top {{ display:flex; align-items:flex-end; gap:16px; margin-bottom:22px; }}
.top .zip {{ background:{INK}; color:#fff; font-weight:800; font-size:13px; border-radius:8px; padding:7px 10px; }}
.top h1 {{ font-size:30px; font-weight:800; letter-spacing:-0.03em; color:{INK}; }}
.top h1 em {{ font-style:normal; background:{GRAD}; -webkit-background-clip:text; background-clip:text; color:transparent; }}
.top .chip {{ margin-left:auto; font-size:13px; font-weight:800; color:{DANGER}; background:#fff; border:1px solid #F6CBC7; border-radius:999px; padding:6px 14px; }}
.grid {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; }}
.card {{ background:#fff; border-radius:16px; box-shadow:0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(15,23,42,.06); overflow:hidden; }}
.card .img {{ height:190px; background-size:cover; background-position:top left; border-bottom:1px solid {LINE}; }}
.card .cap {{ padding:11px 14px 13px; display:flex; flex-direction:column; gap:3px; }}
.card .cap b {{ font-size:14.5px; letter-spacing:-0.01em; color:{INK}; }}
.card .cap span {{ font-size:12.5px; font-weight:800; color:{BLUE}; }}
.foot {{ margin-top:18px; display:flex; justify-content:space-between; font-size:13px; color:{SUB}; }}
.foot b {{ color:{INK}; }}
"""
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body><div id="shot">
<div class="top"><span class="zip">ZIP</span><h1>Cymbal 실습 파일 <em>전체</em></h1><span class="chip">실습용 가상 데이터</span></div>
<div class="grid">{cards}</div>
<div class="foot"><span><b>{e(FILES["bundle"])}</b> · 엑셀 2 · PDF 5 · 스킬 1</span><span>※ {e(DISCLAIMER)}</span></div>
</div></body></html>"""
    render_png(html, preview_path(FILES["bundle"]), name="preview_bundle")


if __name__ == "__main__":
    sales_preview()
    cs_preview()
    skill_preview()
    bundle_preview()
    print("previews done")
