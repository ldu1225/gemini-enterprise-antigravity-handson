#!/usr/bin/env python3
"""Opening-presentation slides -> pseudo recordings for render.py `screen` segments.

Own designed graphics only (DESIGN_v2 tokens; no product UI, no logos, no customer names).
Each slide has build steps: elements with data-step="k" are visible from state k on.
State k is shown from rec time k*STEP_T (state 0 at t=0); 0.2 s crossfade frames before each state.
Narration can anchor sentences with  "at": k*STEP_T .

    python3 production/render/out/openings/make_slides.py [slide_id ...]
Outputs: production/render/out/openings/recs/<slide_id>/{frames/*.jpg, frames.json}
         production/render/out/openings/slides/<slide_id>.html (+ preview_<id>.jpg 1280px)
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "fonts"
SLIDES = HERE / "slides"
RECS = HERE / "recs"
W, H, DPR = 1200, 675, 1.8
STEP_T = 2.0
FADE_N, FADE_T = 6, 0.2

GE = "#4285F4"
AG = "#9B72CB"
GREEN = "#34A853"

CSS = """
@font-face{font-family:P;src:url('FONTS/Pretendard-Regular.otf');font-weight:400}
@font-face{font-family:P;src:url('FONTS/Pretendard-Medium.otf');font-weight:500}
@font-face{font-family:P;src:url('FONTS/Pretendard-SemiBold.otf');font-weight:600}
@font-face{font-family:P;src:url('FONTS/Pretendard-Bold.otf');font-weight:700}
@font-face{font-family:P;src:url('FONTS/Pretendard-ExtraBold.otf');font-weight:800}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1200px;height:675px;overflow:hidden}
body{font-family:P,sans-serif;color:#F3F5F8;word-break:keep-all;
  background:radial-gradient(900px 520px at 8% 0%,var(--glow) 0%,transparent 70%),
             radial-gradient(800px 600px at 100% 100%,rgba(217,101,112,.10) 0%,transparent 70%),#0B0F17;}
.wrap{position:absolute;inset:0;padding:42px 64px 0 64px}
.kicker{font-size:15px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
  background:linear-gradient(135deg,#4285F4 0%,#9B72CB 55%,#D96570 100%);-webkit-background-clip:text;color:transparent}
.rule{width:64px;height:3px;border-radius:2px;margin:10px 0 12px;
  background:linear-gradient(90deg,#4285F4,#9B72CB 55%,#D96570)}
h1{font-size:40px;font-weight:800;letter-spacing:-.01em;line-height:1.25}
.sub{font-size:19px;color:#9AA3B2;margin-top:8px;font-weight:500}
.card{background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);border-radius:16px;
  box-shadow:0 8px 24px rgba(0,0,0,.25)}
.mono{font-family:'JetBrains Mono',Menlo,monospace}
.chip{display:inline-block;padding:4px 12px;border-radius:999px;font-size:14px;font-weight:600;
  border:1px solid rgba(255,255,255,.14);color:#C9D1DC;background:rgba(255,255,255,.05)}
.acc{color:var(--acc)}
.hide{opacity:0 !important}
.num{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;
  font-weight:800;font-size:17px;color:#fff;background:linear-gradient(135deg,#4285F4,#9B72CB 60%,#D96570)}
.arrow{color:#5B6472;font-size:34px;font-weight:300;align-self:center}
.foot{position:absolute;left:64px;right:64px;top:640px;font-size:15px;color:#7D8696}
"""

JS = """
function setStep(k){document.querySelectorAll('[data-step]').forEach(e=>{
  e.classList.toggle('hide', parseInt(e.dataset.step) > k);});}
"""


def page(sid: str, acc: str, glow: str, kicker: str, title: str, sub: str, body: str, extra_css: str = "") -> str:
    css = CSS.replace("FONTS", FONTS.as_uri()) + extra_css
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}
:root{{--acc:{acc};--glow:{glow}}}</style><script>{JS}</script></head>
<body><div class="wrap"><div class="kicker">{kicker}</div><div class="rule"></div><h1>{title}</h1>
{f'<div class="sub">{sub}</div>' if sub else ''}{body}</div></body></html>"""


e = html.escape


# ------------------------------------------------------------------ slide bodies
def flow3(items, top=210, step0=1):
    """three (or n) cards in a row with arrows; items = [(tag, title, lines)]"""
    cols = []
    for i, (tag, t, lines) in enumerate(items):
        if i:
            cols.append(f'<div class="arrow" data-step="{step0 + i}">→</div>')
        li = "".join(f'<li>{x}</li>' for x in lines)
        cols.append(f'''<div class="card fc" data-step="{step0 + i}"><div class="chip">{tag}</div>
          <div class="ft">{t}</div><ul>{li}</ul></div>''')
    return f'<div class="flow" style="top:{top}px">{"".join(cols)}</div>'


FLOW_CSS = """
.flow{position:absolute;left:64px;right:64px;display:flex;gap:18px;align-items:stretch}
.fc{flex:1;padding:28px 26px}
.ft{font-size:27px;font-weight:800;margin:16px 0 14px}
.fc ul{list-style:none}.fc li{font-size:18px;color:#B8C0CC;line-height:1.55;padding-left:18px;position:relative;margin-bottom:6px}
.fc li:before{content:'';position:absolute;left:0;top:11px;width:7px;height:7px;border-radius:50%;background:var(--acc)}
.fc.hl{border-color:var(--acc);background:rgba(66,133,244,.08)}
"""

GRID_CSS = """
.grid{position:absolute;left:64px;right:64px;display:grid;gap:16px}
.g{padding:22px 24px}
.g .t{font-size:22px;font-weight:800;margin-bottom:8px;display:flex;align-items:center;gap:10px}
.g .d{font-size:16.5px;color:#AEB6C2;line-height:1.5}
.dot{width:10px;height:10px;border-radius:50%;background:var(--acc);flex:none}
"""


def slides() -> dict[str, str]:
    S: dict[str, str] = {}
    geg = "rgba(66,133,244,.22)"
    agg = "rgba(155,114,203,.24)"

    # ================= GE ===================================================================
    S["ge_s_shift"] = page("ge_s_shift", GE, geg, "일하는 방식의 변화", "검색 → 답변 → 실행", "AI가 하는 일이 점점 커지고 있습니다", flow3([
        ("과거", "검색", ["키워드를 넣고 링크를 하나씩 열어 읽기", "정리와 판단은 모두 내 몫"]),
        ("지금", "답변", ["질문하면 AI가 자료를 읽고", "출처와 함께 정리해서 답하기"]),
        ("이제", "실행", ["목표를 주면 AI가 계획을 세우고", "도구를 써서 일을 끝까지 진행", "사람은 방향을 정하고 결과를 검토"]),
    ], top=212), FLOW_CSS + ".fc:last-child{border-color:rgba(66,133,244,.55);background:rgba(66,133,244,.07)}")

    hub = f"""
    <div class="hub">
      <div class="card center" data-step="1"><div class="ct">Gemini Enterprise</div><div class="cd">업무용 AI의 하나의 입구</div></div>
      <div class="card q q1" data-step="1"><div class="t"><span class="dot"></span>AI 어시스턴트</div><div class="d">질문 · 요약 · 글쓰기 · 파일과 데이터 분석</div></div>
      <div class="card q q2" data-step="2"><div class="t"><span class="dot"></span>에이전트</div><div class="d">Deep Research · Gemini Notebook<br>내가 만든 채팅 에이전트 · 워크플로</div></div>
      <div class="card q q3" data-step="3"><div class="t"><span class="dot"></span>회사 데이터 연결</div><div class="d">커넥터로 메일 · 문서 · 협업 도구를<br>권한 그대로 연결</div></div>
      <div class="card q q4" data-step="4"><div class="t"><span class="dot"></span>보안과 관리</div><div class="d">관리자가 기능 · 모델 · 공유를 관리<br>회사 데이터는 모델 학습에 쓰지 않음</div></div>
    </div>"""
    S["ge_s_gate"] = page("ge_s_gate", GE, geg, "Gemini Enterprise 한눈에", "한 화면에서 쓰는 업무용 AI", "", hub, """
.hub{position:absolute;left:64px;right:64px;top:160px;height:385px}
.center{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:290px;padding:30px 24px;text-align:center;
  border-color:rgba(66,133,244,.6);background:rgba(66,133,244,.10)}
.ct{font-size:28px;font-weight:800}.cd{font-size:17px;color:#AEB6C2;margin-top:8px}
.q{position:absolute;width:380px;padding:20px 22px}
.q .t{font-size:22px;font-weight:800;display:flex;gap:10px;align-items:center;margin-bottom:8px}
.q .d{font-size:16.5px;color:#AEB6C2;line-height:1.5}
.dot{width:10px;height:10px;border-radius:50%;background:var(--acc)}
.q1{left:0;top:0}.q2{right:0;top:0}.q3{left:0;bottom:0}.q4{right:0;bottom:0}
""")

    tiles = [
        (1, "채팅 · Google 검색", "출처가 달린 답, 후속 질문으로 다듬기"),
        (1, "파일 · 데이터 분석", "엑셀 · PDF를 올려 표와 차트로"),
        (1, "Canvas", "문서 · 슬라이드 만들고 Office · PDF로 내보내기"),
        (1, "이미지 · 동영상", "Nano Banana 이미지 · Veo 3.1 동영상"),
        (2, "Deep Research", "자료를 찾아 읽고 인용이 달린 보고서"),
        (2, "Gemini Notebook", "내 자료 기반 답변 · 오디오 개요 · 마인드맵"),
        (2, "스킬 · 프로젝트", "반복 지침을 스킬로, 주제별 작업 공간"),
        (2, "에이전트 · 워크플로", "코딩 없이 Workflow Builder로 만들기"),
    ]
    g = "".join(f'<div class="card g" data-step="{s}"><div class="t"><span class="dot"></span>{t}</div><div class="d">{d}</div></div>'
                for s, t, d in tiles)
    models = """<div class="models" data-step="3"><span class="ml">모델 선택</span>
      <span class="chip">Auto</span><span class="chip">Gemini 4 Argon</span><span class="chip">Gemini 3.8 Flash</span>
      <span class="chip">Claude Opus 5.5 · Sonnet 5.5 <small>(관리자가 켠 경우)</small></span></div>"""
    S["ge_s_features"] = page("ge_s_features", GE, geg, "핵심 기능 지도", "오늘 만나게 될 기능", "",
                              f'<div class="grid" style="top:160px;grid-template-columns:repeat(4,1fr)">{g}</div>{models}',
                              GRID_CSS + """.g{min-height:140px;padding:20px 20px}
.models{position:absolute;left:64px;right:64px;top:472px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.ml{font-size:16px;font-weight:700;color:#9AA3B2;margin-right:6px}.models .chip{font-size:16px;padding:6px 14px}
.models small{color:#8A93A3;font-weight:500}""")

    prompt = """
    <div class="bad card" data-step="0"><span class="lb">막연한 질문</span><span class="q">“1인 가구 트렌드 알려줘”</span>
      <span class="res">→ 누구를 위한, 어디에 쓸 답인지 알 수 없음</span></div>
    <div class="good card">
      <div class="lb2">4요소 프롬프트</div>
      <div class="row" data-step="1"><span class="tag t1">역할</span><span class="tx">Cymbal 마케팅팀의 시장 분석 담당자로서</span><span class="hint">누구의 입장에서</span></div>
      <div class="row" data-step="2"><span class="tag t2">작업</span><span class="tx">최근 1년 1인 가구 트렌드를 찾아 정리해 주세요.</span><span class="hint">무엇을</span></div>
      <div class="row" data-step="3"><span class="tag t3">맥락</span><span class="tx">다음 주 신제품 출시 전략 회의에서 쓸 자료입니다.</span><span class="hint">왜 · 어디에</span></div>
      <div class="row" data-step="4"><span class="tag t4">형식</span><span class="tx">트렌드 | 근거 | 시사점 표로, 출처와 함께</span><span class="hint">어떤 모양으로</span></div>
    </div>"""
    S["ge_s_prompt"] = page("ge_s_prompt", GE, geg, "좋은 답을 얻는 비결", "프롬프트의 4요소 — 역할 · 작업 · 맥락 · 형식", "", prompt, """
.bad{position:absolute;left:64px;right:64px;top:158px;padding:18px 26px;display:flex;gap:18px;align-items:center}
.lb{font-size:15px;font-weight:700;color:#8A93A3}.q{font-size:22px;font-weight:700;color:#C9D1DC}.res{font-size:16px;color:#8A93A3;margin-left:auto}
.good{position:absolute;left:64px;right:64px;top:240px;padding:22px 26px;border-color:rgba(66,133,244,.5)}
.lb2{font-size:15px;font-weight:700;color:#8AB4F8;margin-bottom:10px}
.row{display:flex;align-items:center;gap:18px;padding:10px 0;border-top:1px solid rgba(255,255,255,.06)}
.row:first-of-type{border-top:none}
.tag{flex:none;width:74px;text-align:center;padding:6px 0;border-radius:999px;font-weight:800;font-size:17px;color:#0B0F17}
.t1{background:#8AB4F8}.t2{background:#C58AF9}.t3{background:#F28B82}.t4{background:#81C995}
.tx{font-size:22px;font-weight:700}.hint{margin-left:auto;font-size:15px;color:#7D8696}
""")

    safe = [
        (1, "회사 데이터는 모델 학습에 쓰이지 않습니다", "Gemini Enterprise는 고객 데이터를 모델 학습에 사용하지 않습니다."),
        (2, "원래 권한이 그대로 적용됩니다", "연결된 메일 · 문서도 내가 볼 수 있는 자료만 답변에 쓰입니다."),
        (3, "AI의 답은 초안입니다", "숫자와 사실은 출처 원문과 대조하고, 최종 판단은 사람이 합니다."),
        (4, "공유와 민감 정보는 신중하게", "공유 링크의 범위를 확인하고, 민감한 정보는 회사 정책을 따릅니다."),
    ]
    sg = "".join(f'<div class="card g" data-step="{s}"><div class="t"><span class="num">{s}</span>{t}</div><div class="d">{d}</div></div>'
                 for s, t, d in safe)
    S["ge_s_safety"] = page("ge_s_safety", GE, geg, "안심하고 쓰기", "보안과 데이터, 이것만 기억하세요", "",
                            f'<div class="grid" style="top:160px;grid-template-columns:1fr 1fr">{sg}</div>'
                            '<div class="foot" data-step="4" style="top:478px">오늘 실습의 회사명 Cymbal(심벌)과 모든 파일 · 수치는 실습용 가상 데이터입니다.</div>',
                            GRID_CSS + ".g{padding:22px 24px;min-height:140px}.g .t{font-size:22px;gap:12px}.g .d{font-size:17.5px;margin-left:46px}")

    labs_ge = [
        (1, 1, "입문", "시작하기", "첫 화면 · 테마 · 개인화 · 첫 질문"),
        (1, 2, "입문", "프롬프트로 답 얻기", "4요소 · 웹 검색과 출처 · 공유"),
        (2, 3, "기본", "데이터 분석 + Canvas", "엑셀 → 차트 → 보고 슬라이드"),
        (2, 4, "기본", "이미지 · 동영상", "Nano Banana 비주얼 · Veo 3.1 티저"),
        (2, 5, "기본", "Deep Research & Notebook", "시장 조사 → 오디오 개요 · 마인드맵"),
        (2, 6, "기본", "생산성", "스킬 · 프로젝트 · 라이브러리 · 커넥터"),
        (3, 7, "심화", "채팅 에이전트 만들기", "Cymbal 사내 지원 데스크"),
        (3, 8, "심화", "워크플로 만들기", "고객 문의 분류 · 조건 분기 · 승인"),
        (3, 9, "기본", "공유 · 갤러리 · 관리", "만든 에이전트를 팀과 나누기"),
    ]
    S["ge_s_labs"] = page("ge_s_labs", GE, geg, "오늘의 실습 지도", "Lab 1 – 9", "", lab_grid(labs_ge), LAB_CSS)

    # ================= AG ===================================================================
    S["ag_s_shift"] = page("ag_s_shift", AG, agg, "개발 방식의 변화", "자동완성 → 대화 → 에이전트", "AI에게 맡기는 단위가 한 줄에서 작업 전체로", flow3([
        ("한 줄", "자동완성", ["타이핑하는 코드의", "다음 몇 줄을 제안"]),
        ("한 조각", "대화형 도우미", ["질문하면 코드 조각과 설명", "붙여 넣고 고치는 건 내 몫"]),
        ("작업 전체", "에이전트", ["목표를 주면 계획 · 실행 · 검증", "파일 · 터미널 · 브라우저를 직접 사용", "사람은 방향을 정하고 검토 · 승인"]),
    ], top=212), FLOW_CSS + ".fc:last-child{border-color:rgba(155,114,203,.6);background:rgba(155,114,203,.08)}")

    fam = [
        (1, "Antigravity 2.0", "데스크톱 앱", "에이전트 중심 작업 공간 — 이 실습의 주 무대"),
        (2, "Antigravity CLI", "agy", "터미널에서 같은 에이전트를 실행"),
        (3, "Antigravity for IDEs", "확장", "VS Code · JetBrains 등 익숙한 IDE 안에서"),
        (4, "Antigravity SDK", "pip install google-antigravity", "내 Python 코드에서 에이전트를 실행"),
    ]
    fg = "".join(f'<div class="card g" data-step="{s}"><div class="t"><span class="dot"></span>{t}</div>'
                 f'<div class="m mono">{e(m)}</div><div class="d">{d}</div></div>' for s, t, m, d in fam)
    S["ag_s_family"] = page("ag_s_family", AG, agg, "Antigravity는", "에이전트와 함께 만드는 개발 플랫폼", "같은 에이전트를 앱 · CLI · IDE · SDK에서",
                            f'<div class="grid" style="top:212px;grid-template-columns:repeat(4,1fr)">{fg}</div>',
                            GRID_CSS + ".g{min-height:230px;padding:22px 20px}.g .m{font-size:14px;color:#C58AF9;margin:6px 0 14px}.g .d{font-size:17.5px}"
                            ".card.g:first-child{border-color:rgba(155,114,203,.6);background:rgba(155,114,203,.08)}")

    loop = [
        (1, "요청", "목표와 제약을 적어 보내기"),
        (2, "계획", "/plan → Implementation Plan 아티팩트"),
        (3, "검토 · 승인", "댓글로 고치고 Proceed"),
        (4, "실행", "파일 쓰기 · 터미널 · 브라우저"),
        (5, "확인", "변경 검토 Accept · Reject, Walkthrough"),
    ]
    lp = "".join(
        (f'<div class="arrow" data-step="{s}">→</div>' if s > 1 else "") +
        f'<div class="card st" data-step="{s}"><span class="num">{s}</span><div class="t">{t}</div><div class="d">{e(d)}</div></div>'
        for s, t, d in loop)
    S["ag_s_loop"] = page("ag_s_loop", AG, agg, "에이전트와 일하는 흐름", "맡기고, 검토하고, 승인합니다", "",
                          f'<div class="loop">{lp}</div><div class="foot" data-step="5" style="top:420px">'
                          '사람은 처음(목표)과 중간(계획 검토), 끝(변경 승인)을 맡고, 그 사이의 실행은 에이전트가 합니다.</div>', """
.loop{position:absolute;left:64px;right:64px;top:175px;display:flex;gap:10px;align-items:stretch}
.st{flex:1;padding:24px 18px;min-height:220px}.st .t{font-size:24px;font-weight:800;margin:16px 0 10px}
.st .d{font-size:16.5px;color:#AEB6C2;line-height:1.5}.arrow{font-size:28px}
.foot{font-size:18px;color:#AEB6C2}""")

    perm = [
        (1, "Request Review", "명령을 실행하기 전에 매번 확인", "처음 시작할 때 · 회사 코드"),
        (2, "Default", "샌드박스 안에서 실행, 밖으로 나가면 승인 요청", "일상 작업"),
        (3, "Turbo", "확인 없이 자동 실행", "연습용 폴더에서만"),
    ]
    pg = "".join(f'<div class="card g" data-step="{s}"><div class="t mono">{t}</div><div class="d">{d}</div>'
                 f'<div class="chip">{w}</div></div>' for s, t, d, w in perm)
    S["ag_s_safety"] = page("ag_s_safety", AG, agg, "권한과 안전", "에이전트가 할 수 있는 일은 내가 정합니다", "",
                            f'<div class="grid" style="top:162px;grid-template-columns:repeat(3,1fr)">{pg}</div>'
                            '<div class="card admin" data-step="4"><b>회사 계정(GE 라이선스)</b> 관리자가 콘솔 '
                            '<span class="mono">Gemini Enterprise › Settings › AI developer tools</span>에서 '
                            '파일 접근 · 터미널 자동 실행 · 브라우저 · MCP · 허용 모델 정책을 정합니다.</div>',
                            GRID_CSS + """.g{min-height:190px;padding:26px 26px}.g .t{font-size:24px;color:#E9DDFB}.g .d{font-size:18px;margin:8px 0 18px}
.admin{position:absolute;left:64px;right:64px;top:378px;padding:20px 26px;font-size:18px;color:#C9D1DC;line-height:1.6;border-color:rgba(52,168,83,.45)}
.admin b{color:#81C995;margin-right:8px}.admin .mono{font-size:15.5px;color:#E9DDFB}""")

    cus = [
        (1, "규칙 Rules", "AGENTS.md · .agents/rules/*.md", "팀이 언제나 지킬 원칙 — 한국어, 개인정보 마스킹, 안전 이슈는 맨 위"),
        (2, "스킬 Skills", ".agents/skills/<이름>/SKILL.md", "필요할 때 골라 쓰는 작업 절차 — 요청이 description과 맞으면 자동으로, "
                                                              '<span style="white-space:nowrap">/이름</span>으로 직접'),
        (3, "MCP 연결", "MCP Store · BigQuery", "회사 도구 · 데이터를 잇는 표준 플러그 — 에이전트가 회사 데이터를 직접 조회"),
    ]
    cg = "".join(f'<div class="card g" data-step="{s}"><div class="t"><span class="dot"></span>{t}</div>'
                 f'<div class="m mono">{e(m)}</div><div class="d">{d}</div></div>' for s, t, m, d in cus)
    S["ag_s_custom"] = page("ag_s_custom", AG, agg, "에이전트 길들이기", "규칙 · 스킬 · MCP", "한 번 적어 두고 연결해 두면, 매번 설명하지 않아도 됩니다",
                            f'<div class="grid" style="top:212px;grid-template-columns:repeat(3,1fr)">{cg}</div>',
                            GRID_CSS + ".g{min-height:230px;padding:22px 22px}.g .m{font-size:14.5px;color:#C58AF9;margin:6px 0 14px}.g .d{font-size:18px}"
                            ".card.g:last-child{border-color:rgba(66,133,244,.5);background:rgba(66,133,244,.07)}")

    mcp = """
    <div class="mcp">
      <div class="card agent" data-step="1"><div class="t"><span class="dot"></span>Antigravity 에이전트</div>
        <div class="d">요청을 보고 필요한 도구를 골라 호출합니다</div></div>
      <div class="plug" data-step="1"><div class="line"></div><div class="pill">MCP</div><div class="line"></div>
        <div class="calls mono">get_table_info · execute_sql_readonly</div></div>
      <div class="svcs">
        <div class="card svc hl" data-step="2"><div class="t">BigQuery</div><div class="d">회사 데이터 · <span class="mono">cymbal_cx.voc_tickets</span></div></div>
        <div class="card svc" data-step="2"><div class="t">GitHub</div><div class="d">코드 · 이슈 · 풀 리퀘스트</div></div>
        <div class="card svc" data-step="2"><div class="t">그 밖의 서비스</div><div class="d">MCP 서버를 제공하는 도구라면</div></div>
      </div>
    </div>
    <div class="how" data-step="3">
      <span class="chip">① MCP Store에서 설치</span><span class="ar">→</span>
      <span class="chip">② 도구 목록 확인 · 필요한 것만 켜기</span><span class="ar">→</span>
      <span class="chip">③ 호출 전에 승인 카드로 확인</span>
    </div>"""
    S["ag_s_mcp"] = page("ag_s_mcp", AG, agg, "MCP · Model Context Protocol", "에이전트와 회사 데이터를 잇는 표준 플러그",
                         "폴더 안의 CSV 대신, 회사 시스템의 데이터를 에이전트가 직접 조회합니다", mcp, """
.mcp{position:absolute;left:64px;right:64px;top:200px;height:250px;display:flex;align-items:center}
.dot{width:10px;height:10px;border-radius:50%;background:var(--acc);flex:none}
.agent{width:270px;padding:24px 22px;border-color:rgba(155,114,203,.6);background:rgba(155,114,203,.09)}
.agent .t,.svc .t{font-size:22px;font-weight:800;display:flex;align-items:center;gap:10px}
.agent .d{font-size:17px;color:#AEB6C2;margin-top:10px;line-height:1.5}
.plug{flex:1;position:relative;display:flex;align-items:center;height:100%;padding:0 4px}
.plug .line{flex:1;height:2px;background:linear-gradient(90deg,rgba(155,114,203,.25),rgba(155,114,203,.95),rgba(155,114,203,.25))}
.pill{padding:10px 24px;border-radius:999px;font-size:24px;font-weight:800;letter-spacing:.08em;color:#fff;
  background:linear-gradient(135deg,#4285F4,#9B72CB 60%,#D96570);box-shadow:0 0 26px rgba(155,114,203,.45)}
.calls{position:absolute;top:calc(50% + 34px);left:0;right:0;text-align:center;font-size:13.5px;color:#C58AF9}
.svcs{width:340px;display:flex;flex-direction:column;gap:12px}
.svc{padding:14px 20px}.svc .t{font-size:20px}.svc .d{font-size:15.5px;color:#AEB6C2;margin-top:4px}
.svc .d .mono{font-size:14px;color:#8AB4F8}
.svc.hl{border-color:rgba(66,133,244,.55);background:rgba(66,133,244,.08)}
.how{position:absolute;left:64px;right:64px;top:482px;display:flex;align-items:center;gap:12px;justify-content:center}
.how .chip{font-size:17px;padding:8px 16px;color:#E3E7ED}.how .ar{color:#5B6472;font-size:22px}
""")

    adk = [
        (1, "만들기", "agents-cli scaffold create"),
        (2, "실행", "agents-cli run · playground"),
        (3, "평가", "agents-cli eval"),
        (4, "배포", "agents-cli deploy → Agent Runtime"),
        (5, "게시", "agents-cli publish gemini-enterprise"),
    ]
    ap = "".join(
        (f'<div class="arrow" data-step="{s}">→</div>' if s > 1 else "") +
        f'<div class="card st" data-step="{s}"><span class="num">{s}</span><div class="t">{t}</div><div class="d mono">{e(d)}</div></div>'
        for s, t, d in adk)
    S["ag_s_adk"] = page("ag_s_adk", AG, agg, "ADK + agents-cli", "만든 에이전트를 회사 전체가 쓰도록", "ADK는 Google의 에이전트 개발 키트, agents-cli는 그 전 과정을 돕는 명령줄 도구",
                         f'<div class="loop">{ap}</div><div class="foot" data-step="5" style="top:440px">'
                         '게시가 끝나면 동료들이 Gemini Enterprise 웹앱에서 이 에이전트를 바로 씁니다 — 명령은 에이전트가 대신 실행합니다.</div>', """
.loop{position:absolute;left:64px;right:64px;top:212px;display:flex;gap:10px;align-items:stretch}
.st{flex:1;padding:24px 18px;min-height:200px}.st .t{font-size:24px;font-weight:800;margin:16px 0 10px}
.st .d{font-size:13.5px;color:#C58AF9;line-height:1.5}.arrow{font-size:28px}.foot{font-size:18px;color:#AEB6C2}""")

    signin = """
    <div class="two">
      <div class="card side biz" data-step="1"><div class="btn">Use Business Account</div>
        <div class="who">회사에서 Gemini Enterprise 라이선스를 받은 경우</div>
        <ul><li>사용량은 회사 GE 구독에 포함</li><li>관리자가 정한 보안 정책 · 허용 모델 적용</li>
        <li>관리자: 콘솔에서 AI developer tools 켜기</li></ul><div class="chip">Lab 1</div></div>
      <div class="card side per" data-step="2"><div class="btn">Continue with Google</div>
        <div class="who">개인 Google 계정으로 쓰는 경우</div>
        <ul><li>무료: 주간 할당량 · Gemini 3.8 Flash</li><li>Google AI Pro · Ultra: 더 높은 할당량</li>
        <li>유료 요금제에서 Gemini 4 Argon · Claude 등</li></ul><div class="chip">Lab 2</div></div>
    </div>"""
    S["ag_s_signin"] = page("ag_s_signin", AG, agg, "시작하기", "로그인 방법은 두 가지", "첫 화면에서 내 상황에 맞는 버튼을 고릅니다", signin, """
.two{position:absolute;left:64px;right:64px;top:200px;display:grid;grid-template-columns:1fr 1fr;gap:22px}
.side{padding:24px 26px;min-height:300px}
.btn{display:inline-block;font-size:21px;font-weight:800;padding:10px 20px;border-radius:10px;border:1.5px solid rgba(255,255,255,.25)}
.biz{border-color:rgba(52,168,83,.5)}.biz .btn{border-color:#81C995;color:#CDEFD6}
.per .btn{border-color:#8AB4F8;color:#D2E3FC}
.who{font-size:19px;font-weight:700;margin:18px 0 12px}
.side ul{list-style:none;margin-bottom:18px}.side li{font-size:17.5px;color:#B8C0CC;line-height:1.6;padding-left:18px;position:relative}
.side li:before{content:'';position:absolute;left:0;top:11px;width:7px;height:7px;border-radius:50%;background:var(--acc)}""")

    reqs = [
        (1, "요청 1", "VOC 대시보드", "주간 문의 건수 · 제품별 · 분류별 건수와 긴급 문의 목록을 한 화면에", ["Lab 3", "Lab 4"]),
        (2, "요청 2", "주간 보고 자동화", "매주 월요일 08:30까지 지난주 요약과 임원 보고 슬라이드", ["Lab 5", "Lab 6", "Lab 7", "Lab 10"]),
        (3, "요청 3", "VOC 도우미", "팀원 누구나 Gemini Enterprise에서 “지난주 긴급 문의 알려 줘”", ["Lab 8", "Lab 9"]),
    ]
    rq = "".join(f'<div class="card rq" data-step="{s}"><div class="no">{n}</div><div class="t">{t}</div><div class="d">{e(d)}</div>'
                 f'<div class="labs">{"".join(f"<span class=lb>{x}</span>" for x in ls)}</div></div>' for s, n, t, d, ls in reqs)
    must = ('<div class="must" data-step="4"><span class="ml">지켜야 할 것</span>'
            + "".join(f'<span class="chip">{x}</span>' for x in ["개인정보 마스킹", "외부 CDN 금지", "한국어 화면", "안전 이슈는 맨 위"])
            + '</div><div class="note" data-step="4">회사명 Cymbal(심벌)과 고객 문의 300건은 모두 실습용 가상 데이터입니다.</div>')
    S["ag_s_story"] = page("ag_s_story", AG, agg, "오늘의 프로젝트", "CX팀장의 요청서 한 장",
                           "매주 월요일 반나절 걸리던 VOC(고객의 소리) 보고를, 에이전트와 함께 바꿉니다",
                           f'<div class="reqs">{rq}</div>{must}', """
.reqs{position:absolute;left:64px;right:64px;top:200px;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.rq{padding:22px 24px;min-height:228px;display:flex;flex-direction:column}
.rq .no{font-size:14px;font-weight:700;color:#C58AF9;letter-spacing:.08em}
.rq .t{font-size:27px;font-weight:800;margin:8px 0 10px}
.rq .d{font-size:17.5px;color:#B8C0CC;line-height:1.55;flex:1}
.rq .labs{margin-top:14px;display:flex;gap:6px;flex-wrap:wrap}
.lb{font-size:14.5px;font-weight:700;padding:4px 11px;border-radius:999px;background:rgba(155,114,203,.18);color:#DCC8F5}
.must{position:absolute;left:64px;right:64px;top:458px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.must .ml{font-size:16px;font-weight:700;color:#9AA3B2;margin-right:4px}
.must .chip{font-size:16px;padding:6px 14px;color:#E3E7ED}
.note{position:absolute;left:64px;right:64px;top:510px;font-size:15px;color:#7D8696}
""")

    start = [
        (1, 1, "입문", "시작하기 A", "GE 라이선스 · Use Business Account"),
        (1, 2, "입문", "시작하기 B", "개인 계정 · Continue with Google"),
    ]
    proj = [
        (2, 3, "입문", "프로젝트 받기", "요청서 파악 · @멘션 · /plan"),
        (2, 4, "기본", "VOC 대시보드", "Proceed · 변경 검토 · /browser"),
        (2, 5, "기본", "규칙 · 스킬", "AGENTS.md · 주간 보고 SKILL.md"),
        (3, 6, "기본", "MCP · BigQuery", "MCP Store · 회사 데이터 조회"),
        (3, 7, "기본", "임원 슬라이드", "HTML 슬라이드 → PDF"),
        (4, 8, "심화", "ADK 에이전트", "VOC 분석 · agents-cli run · eval"),
        (4, 9, "심화", "배포 · GE 게시", "Agent Runtime → Gemini Enterprise"),
        (4, 10, "심화", "운영 자동화", "/schedule · 서브에이전트"),
    ]
    S["ag_s_labs"] = page("ag_s_labs", AG, agg, "오늘의 실습 지도", "Lab 1 – 10", "", lab_path(start, proj), LABP_CSS)
    return S


LAB_CSS = """
.labs{position:absolute;left:64px;right:64px;top:148px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.lab{padding:16px 18px;display:flex;gap:14px;align-items:flex-start;min-height:112px}
.ln{flex:none;font-size:30px;font-weight:800;width:40px;color:var(--acc);line-height:1.1}
.lt{font-size:19px;font-weight:800;margin-bottom:6px}.ld{font-size:15.5px;color:#AEB6C2;line-height:1.45}
.lv{font-size:12.5px;font-weight:700;padding:2px 10px;border-radius:999px;margin-left:8px;vertical-align:3px}
.l1{background:rgba(129,201,149,.16);color:#81C995}.l2{background:rgba(138,180,248,.16);color:#8AB4F8}.l3{background:rgba(242,139,130,.16);color:#F28B82}
"""

LABP_CSS = """
.glabel{position:absolute;top:146px;font-size:14.5px;font-weight:700;color:#9AA3B2;letter-spacing:.02em}
.glabel b{color:#DCC8F5;font-weight:800}
.gl1{left:64px}.gl2{left:324px}
.start{position:absolute;left:64px;top:176px;width:236px;display:grid;grid-template-rows:158px 158px;row-gap:16px}
.proj{position:absolute;left:324px;right:64px;top:176px;display:grid;grid-template-columns:1fr 22px 1fr 22px 1fr 22px 1fr;
  grid-template-rows:158px 158px;row-gap:16px}
.lc{padding:16px 16px}
.lc .hd{display:flex;align-items:center;justify-content:space-between}
.lc .n{font-size:28px;font-weight:800;color:var(--acc);line-height:1}
.lc .t{font-size:19px;font-weight:800;margin:12px 0 6px;white-space:nowrap}
.lc .d{font-size:14.5px;color:#AEB6C2;line-height:1.45}
.lc.s{border-color:rgba(52,168,83,.38)}.lc.s .n{color:#81C995}
.par{align-self:center;text-align:center;color:#6B7486;font-size:19px}
.lv{font-size:12.5px;font-weight:700;padding:2px 10px;border-radius:999px}
.l1{background:rgba(129,201,149,.16);color:#81C995}.l2{background:rgba(138,180,248,.16);color:#8AB4F8}.l3{background:rgba(242,139,130,.16);color:#F28B82}
.pfoot{position:absolute;left:324px;right:64px;top:524px;font-size:15.5px;color:#8A93A3}
"""


def lab_path(start, proj) -> str:
    """AG map: Lab 1–2 (start column) + one project path Lab 3–10 (2 rows x 4, arrows inside a row)."""
    lv = {"입문": "l1", "기본": "l2", "심화": "l3"}

    def cell(s, n, l, t, d, cls=""):
        return (f'<div class="card lc {cls}" data-step="{s}"><div class="hd"><span class="n">{n}</span>'
                f'<span class="lv {lv[l]}">{l}</span></div><div class="t">{t}</div><div class="d">{e(d)}</div></div>')

    st = "".join(cell(*x, cls="s") for x in start)
    pj = []
    for i, x in enumerate(proj):
        if i % 4:
            pj.append(f'<div class="par" data-step="{x[0]}">→</div>')
        pj.append(cell(*x))
    return (f'<div class="glabel gl1" data-step="1">시작하기 · 로그인</div>'
            f'<div class="glabel gl2" data-step="2"><b>Cymbal CX팀 VOC 프로젝트</b> — 같은 cymbal-voc 폴더를 이어서 키웁니다</div>'
            f'<div class="start">{st}</div><div class="proj">{"".join(pj)}</div>'
            f'<div class="pfoot" data-step="4">앞 Lab의 결과물이 다음 Lab의 재료가 됩니다 · 모든 데이터는 실습용 가상 데이터</div>')


def lab_grid(labs) -> str:
    lv = {"입문": "l1", "기본": "l2", "심화": "l3"}
    cells = "".join(
        f'<div class="card lab" data-step="{s}"><div class="ln">{n}</div><div><div class="lt">{t}<span class="lv {lv[l]}">{l}</span></div>'
        f'<div class="ld">{e(d)}</div></div></div>' for s, n, l, t, d in labs)
    return f'<div class="labs">{cells}</div>'


# ------------------------------------------------------------------ render
def render(ids: list[str]) -> None:
    from playwright.sync_api import sync_playwright
    allp = slides()
    ids = ids or list(allp)
    SLIDES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=DPR)
        for sid in ids:
            f = SLIDES / f"{sid}.html"
            f.write_text(allp[sid], encoding="utf-8")
            pg.goto(f.as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(250)
            steps = pg.evaluate("Math.max(0,...[...document.querySelectorAll('[data-step]')].map(e=>parseInt(e.dataset.step)))")
            imgs = []
            for k in range(steps + 1):
                pg.evaluate(f"setStep({k})")
                pg.wait_for_timeout(60)
                buf = pg.screenshot(type="png")
                imgs.append(cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR))
            pack(sid, imgs)
            prev = cv2.resize(imgs[-1], (1280, 720), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(SLIDES / f"preview_{sid}.jpg"), prev, [cv2.IMWRITE_JPEG_QUALITY, 70])
            print(f"{sid}: {steps} build steps -> {RECS / sid}")
        b.close()


def pack(sid: str, imgs: list[np.ndarray]) -> None:
    d = RECS / sid
    if d.exists():
        shutil.rmtree(d)
    (d / "frames").mkdir(parents=True)
    frames = []
    ts0 = 1_800_000_000.0

    def put(img, t):
        name = f"{len(frames):06d}.jpg"
        cv2.imwrite(str(d / "frames" / name), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        frames.append({"file": name, "ts": ts0 + t})

    put(imgs[0], 0.0)
    for k in range(1, len(imgs)):
        t = k * STEP_T
        for j in range(1, FADE_N):
            a = j / FADE_N
            put(cv2.addWeighted(imgs[k - 1], 1 - a, imgs[k], a, 0), t - FADE_T + a * FADE_T)
        put(imgs[k], t)
    put(imgs[-1], (len(imgs)) * STEP_T + 6.0)        # hold (defines duration)
    (d / "frames.json").write_text(json.dumps(frames))
    (d / "events.json").write_text(json.dumps([{"kind": "rec_start", "wall": ts0},
                                               {"kind": "rec_stop", "wall": frames[-1]["ts"]}]))


if __name__ == "__main__":
    render(sys.argv[1:])
