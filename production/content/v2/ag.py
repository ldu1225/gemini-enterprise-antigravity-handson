# -*- coding: utf-8 -*-
"""Antigravity track labs (schema: production/content/v2/schema.md).

Each finished lab lives in production/content/v2/ag_labs/<id>.py (LAB dict). Labs not yet produced fall back
to the skeleton below and render as '준비 중' pages.
Screens were recorded on the Antigravity agent IDE desktop app;
see production/capture/agy/agrec.py.
"""
import importlib.util
from pathlib import Path

_SKELETON = [
    {"id": "lab1", "no": 1, "title": "시작하기 A — GE 라이선스", "subtitle": "관리자 콘솔 설정 + Use Business Account 로그인", "level": "입문", "minutes": 15, "steps": []},
    {"id": "lab2", "no": 2, "title": "시작하기 B — 개인 Google 계정", "subtitle": "Continue with Google, 요금제 차이", "level": "입문", "minutes": 10, "steps": []},
    # ---- storyline: Cymbal CX팀의 VOC(고객의 소리) 업무를 대시보드 → 회사 데이터(MCP) → 보고 자동화 → 전사 에이전트까지
    {"id": "lab3", "no": 3, "title": "프로젝트 받기 — 화면 구성과 기본 사용", "subtitle": "요청서·데이터 파악 · @멘션 · 명령 승인 · /plan", "level": "입문", "minutes": 20, "steps": []},
    {"id": "lab4", "no": 4, "title": "VOC 대시보드 만들기", "subtitle": "Proceed · 변경 검토 · /browser 검증 · 필터 추가", "level": "기본", "minutes": 30, "steps": []},
    {"id": "lab5", "no": 5, "title": "팀 규칙과 주간 보고 스킬", "subtitle": "AGENTS.md · SKILL.md · 자동 선택 · 슬래시 호출", "level": "기본", "minutes": 25, "steps": []},
    {"id": "lab6", "no": 6, "title": "MCP로 회사 데이터 연결 — BigQuery", "subtitle": "MCP Store · 도구 호출 · 실데이터 분석", "level": "기본", "minutes": 25, "steps": []},
    {"id": "lab7", "no": 7, "title": "임원 보고 슬라이드", "subtitle": "스킬 + BigQuery 데이터 → HTML 슬라이드 → PDF", "level": "기본", "minutes": 20, "steps": []},
    {"id": "lab8", "no": 8, "title": "VOC 분석 에이전트 — ADK", "subtitle": "agents-cli 생성 · 도구 · 실행 · 평가", "level": "심화", "minutes": 35, "steps": []},
    {"id": "lab9", "no": 9, "title": "배포 + Gemini Enterprise 게시", "subtitle": "Agent Runtime 배포 · GE 게시 · CX팀이 GE에서 사용", "level": "심화", "minutes": 30, "steps": []},
    {"id": "lab10", "no": 10, "title": "운영 자동화", "subtitle": "/schedule 주간 예약 · 서브에이전트 병렬 작업", "level": "심화", "minutes": 25, "steps": []},
]


def _load(lab_id):
    path = Path(__file__).resolve().parent / "ag_labs" / f"{lab_id}.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"ag_labs_{lab_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.LAB


LABS = [_load(s["id"]) or s for s in _SKELETON]
