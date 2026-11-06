# -*- coding: utf-8 -*-
"""Gemini Enterprise track labs (schema: production/content/v2/schema.md).

Each finished lab lives in production/content/v2/ge_labs/<id>.py (LAB dict). Labs not yet produced fall back
to the skeleton below and render as '준비 중' pages.
"""
import importlib.util
from pathlib import Path

_SKELETON = [
    {"id": "lab1", "no": 1, "title": "시작하기", "subtitle": "첫 화면 · 화면 구성 · 테마와 개인화 · 첫 질문", "level": "입문", "minutes": 15, "steps": []},
    {"id": "lab2", "no": 2, "title": "프롬프트로 답 얻기", "subtitle": "4요소 프롬프트 · 웹 검색과 출처 · 후속 질문 · 공유", "level": "입문", "minutes": 20, "steps": []},
    {"id": "lab3", "no": 3, "title": "데이터 분석 + Canvas", "subtitle": "영업 실적 엑셀 → 차트 → 보고 슬라이드", "level": "기본", "minutes": 25, "steps": []},
    {"id": "lab4", "no": 4, "title": "이미지 · 동영상", "subtitle": "캠페인 비주얼(Nano Banana) + 티저(Veo 3.1)", "level": "기본", "minutes": 20, "steps": []},
    {"id": "lab5", "no": 5, "title": "Deep Research & Gemini Notebook", "subtitle": "시장 조사 → 노트북 → 동영상·오디오 개요 · 슬라이드 · 인포그래픽", "level": "기본", "minutes": 35, "steps": []},
    {"id": "lab6", "no": 6, "title": "생산성", "subtitle": "스킬 · 프로젝트 · 라이브러리 · 커넥터", "level": "기본", "minutes": 20, "steps": []},
    {"id": "lab7", "no": 7, "title": "채팅 에이전트 만들기", "subtitle": "Cymbal 사내 지원 데스크 — 지식 · 하위 에이전트 · 테스트", "level": "심화", "minutes": 35, "steps": []},
    {"id": "lab8", "no": 8, "title": "워크플로 만들기", "subtitle": "고객 문의 자동 분류 — 조건 분기 · 정보 요청 · 승인", "level": "심화", "minutes": 40, "steps": []},
    {"id": "lab9", "no": 9, "title": "에이전트 공유 · 갤러리 · 관리", "subtitle": "만든 에이전트를 팀과 나누고 관리하기", "level": "기본", "minutes": 15, "steps": []},
]


def _load(lab_id):
    path = Path(__file__).resolve().parent / "ge_labs" / f"{lab_id}.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"ge_labs_{lab_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.LAB


LABS = [_load(s["id"]) or s for s in _SKELETON]
