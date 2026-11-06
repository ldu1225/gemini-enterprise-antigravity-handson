"""Preview PNGs (1200px wide) for the Antigravity track starter files.

- previews/Cymbal_VOC_스타터.png — what is inside Cymbal_VOC_스타터.zip (folder tree + first CSV rows + Lab 3→10 journey)
- previews/Cymbal_VOC_요청서.png  — 요청서_CX팀.md rendered as a document page

Run after build_voc_starter.py (reads the files it wrote under build/cymbal-voc/).
These are file previews (document cards), not product UI — no IDE/console look-alikes.
"""
from __future__ import annotations

import csv
import re

from common import (BLUE, DANGER, DISCLAIMER, FONT_STACK, GRAD, INK, LINE, OUT, PREV, SUB, e, nfc,
                    pretendard_css, render_png)

PROJ = OUT / "cymbal-voc"
FONTS = pretendard_css()

JOURNEY = [("Lab 3", "요청서 파악 · 계획"), ("Lab 4", "VOC 대시보드"), ("Lab 5", "팀 규칙 · 스킬"),
           ("Lab 6", "MCP로 BigQuery"), ("Lab 7", "임원 보고 슬라이드"), ("Lab 8", "VOC 분석 에이전트"),
           ("Lab 9", "배포 · GE 게시"), ("Lab 10", "매주 자동 보고")]

TREE = [("cymbal-voc/", 0, "Lab 3~10 내내 키워 가는 실습 폴더"),
        ("README.md", 1, "프로젝트 소개 · 데이터 열 설명"),
        ("요청서_CX팀.md", 1, "출발점 — CX팀장의 요청 3가지"),
        ("lab.env", 1, "내 프로젝트 ID·리전 등 변수 (여기만 바꾸기)"),
        ("data/", 1, ""),
        ("voc_tickets.csv", 2, "고객 문의 300건 · 4주 (가상)"),
        ("setup/", 1, ""),
        ("load_to_bigquery.sh", 2, "Lab 6 준비 — BigQuery 적재")]

SHOW_COLS = ["ticket_id", "created_at", "product", "category", "severity", "status"]


def inline(s: str) -> str:
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def starter_preview() -> None:
    with (PROJ / "data" / "voc_tickets.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    tree = "".join(
        f'<div class="t d{d}"><span class="n{" dir" if n.endswith("/") else ""}">{e(n)}</span>'
        f'<span class="c">{e(c)}</span></div>' for n, d, c in TREE)
    head = "".join(f"<th>{e(c)}</th>" for c in SHOW_COLS)
    body = []
    for r in rows[:9]:
        cells = []
        for c in SHOW_COLS:
            v = r[c]
            cls = ""
            if c == "severity" and v == "긴급":
                cls = ' class="hot"'
            cells.append(f"<td{cls}>{e(v)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    journey = "".join(f'<div class="j"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in JOURNEY)
    css = f"""{FONTS}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#EEF0F3; font-family:{FONT_STACK}; color:{INK}; }}
#shot {{ width:1200px; padding:32px 38px 26px; background:linear-gradient(160deg,#FFFFFF 0%,#F1F5FE 55%,#F3EEFA 100%); }}
.top {{ display:flex; align-items:center; gap:14px; margin-bottom:20px; }}
.top .zip {{ background:{INK}; color:#fff; font-weight:800; font-size:13px; border-radius:8px; padding:7px 10px; }}
.top h1 {{ font-size:29px; font-weight:800; letter-spacing:-0.03em; }}
.top h1 em {{ font-style:normal; background:{GRAD}; -webkit-background-clip:text; background-clip:text; color:transparent; }}
.top .chip {{ margin-left:auto; font-size:13px; font-weight:800; color:{DANGER}; background:#fff; border:1px solid #F6CBC7; border-radius:999px; padding:6px 14px; }}
.row {{ display:grid; grid-template-columns: 430px 1fr; gap:18px; }}
.card {{ background:#fff; border-radius:16px; box-shadow:0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(15,23,42,.06); padding:16px 18px; }}
.card h2 {{ font-size:14px; font-weight:800; color:{SUB}; margin-bottom:10px; letter-spacing:-0.01em; }}
.t {{ display:flex; flex-direction:column; padding:5px 0; border-bottom:1px dashed {LINE}; }}
.t:last-child {{ border-bottom:0; }}
.t .n {{ font-family: Menlo, 'Pretendard', monospace; font-size:14px; font-weight:700; }}
.t .n.dir {{ color:{BLUE}; }}
.t .c {{ font-size:12.5px; color:{SUB}; }}
.t.d1 {{ padding-left:18px; }} .t.d2 {{ padding-left:36px; }}
table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
th {{ text-align:left; font-family: Menlo, monospace; font-size:11.5px; color:#fff; background:{BLUE}; padding:7px 8px; }}
td {{ padding:6px 8px; border-bottom:1px solid {LINE}; white-space:nowrap; }}
tr:nth-child(even) td {{ background:#F7F8FA; }}
td.hot {{ color:{DANGER}; font-weight:800; }}
.more {{ margin-top:8px; font-size:12.5px; color:{SUB}; }}
.journey {{ margin-top:18px; display:grid; grid-template-columns: repeat(8, 1fr); gap:8px; }}
.j {{ background:#fff; border-radius:12px; padding:10px 10px 11px; border:1px solid {LINE}; display:flex; flex-direction:column; gap:3px; }}
.j b {{ font-size:12.5px; color:{BLUE}; }}
.j span {{ font-size:13px; font-weight:700; letter-spacing:-0.02em; line-height:1.3; }}
.foot {{ margin-top:14px; display:flex; justify-content:space-between; font-size:12.5px; color:{SUB}; }}
"""
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body><div id="shot">
<div class="top"><span class="zip">ZIP</span><h1>Cymbal VOC <em>스타터 프로젝트</em></h1><span class="chip">실습용 가상 데이터</span></div>
<div class="row">
  <div class="card"><h2>폴더 구성</h2>{tree}</div>
  <div class="card"><h2>data/voc_tickets.csv — 처음 9행 (열 14개 중 6개)</h2>
    <table><tr>{head}</tr>{"".join(body)}</table>
    <div class="more">총 {len(rows)}행 · 2026-09-28 ~ 2026-10-25 · 고객 이름·연락처 열은 개인정보로 취급(가상)</div></div>
</div>
<div class="journey">{journey}</div>
<div class="foot"><span><b>{e(nfc("Cymbal_VOC_스타터.zip"))}</b> · 한 폴더를 Lab 3부터 Lab 10까지 계속 키워 갑니다</span><span>※ {e(DISCLAIMER)}</span></div>
</div></body></html>"""
    render_png(html, PREV / nfc("Cymbal_VOC_스타터.png"), name="preview_voc_starter")


def request_preview() -> None:
    md = (PROJ / nfc("요청서_CX팀.md")).read_text(encoding="utf-8")
    out, in_ul, in_ol = [], False, False

    def close():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
        if in_ol:
            out.append("</ol>")
        in_ul = in_ol = False

    for ln in md.split("\n"):
        if ln.startswith("# "):
            close(); out.append(f"<h1>{inline(ln[2:])}</h1>")
        elif ln.startswith("## "):
            close(); out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("> "):
            close(); out.append(f'<div class="disc">{inline(ln[2:])}</div>')
        elif ln.startswith("- "):
            if not in_ul:
                close(); out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(ln[2:])}</li>")
        elif re.match(r"\d+\. ", ln):
            if not in_ol:
                close(); out.append("<ol>"); in_ol = True
            out.append(f"<li>{inline(ln.split('. ', 1)[1])}</li>")
        elif ln.strip():
            close(); out.append(f"<p>{inline(ln)}</p>")
        else:
            close()
    close()
    css = f"""{FONTS}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#EEF0F3; font-family:{FONT_STACK}; color:{INK}; }}
#shot {{ width:1200px; background:#fff; }}
.fbar {{ display:flex; align-items:center; gap:12px; padding:14px 26px; border-bottom:1px solid {LINE}; background:#fff; }}
.fbar .ext {{ background:#5B6472; color:#fff; font-weight:800; font-size:12px; border-radius:6px; padding:5px 8px; }}
.fbar .fn {{ font-weight:800; font-size:16px; }}
.fbar .path {{ color:{SUB}; font-size:13px; font-family: Menlo, monospace; }}
.fbar .chip {{ margin-left:auto; font-size:12px; font-weight:800; color:{DANGER}; background:#FDF0EF; border:1px solid #F6CBC7; border-radius:999px; padding:4px 12px; }}
.doc {{ padding:26px 60px 30px; font-size:15.5px; line-height:1.7; }}
h1 {{ font-size:27px; font-weight:800; letter-spacing:-0.03em; margin-bottom:10px; }}
h2 {{ font-size:18px; font-weight:800; margin:18px 0 6px; padding-top:12px; border-top:1px solid {LINE}; color:{INK}; }}
.disc {{ font-size:13px; font-weight:700; color:{DANGER}; margin-bottom:10px; }}
ul, ol {{ padding-left:24px; }}
li {{ margin:2px 0; }}
b {{ font-weight:800; }}
code {{ font-family: Menlo, monospace; font-size:13.5px; background:#F1F3F4; border-radius:5px; padding:1px 6px; }}
"""
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body><div id="shot">
<div class="fbar"><span class="ext">MD</span><span class="fn">{e(nfc("요청서_CX팀.md"))}</span><span class="path">cymbal-voc/</span><span class="chip">실습용 가상 데이터</span></div>
<div class="doc">{"".join(out)}</div>
</div></body></html>"""
    render_png(html, PREV / nfc("Cymbal_VOC_요청서.png"), name="preview_voc_request")


if __name__ == "__main__":
    PREV.mkdir(parents=True, exist_ok=True)
    starter_preview()
    request_preview()
    print("voc previews done")
