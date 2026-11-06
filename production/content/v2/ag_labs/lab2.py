# -*- coding: utf-8 -*-
"""AG Lab 2 — 시작하기 B: 개인 Google 계정. REAL recording ag2a_signin (welcome → Continue with Google → browser
sign-in wait). Plan facts: antigravity.google/docs/plans, /models (2026-10-26). CSS 1440x810."""

LAB = {
    "id": "lab2", "no": 2, "level": "입문", "minutes": 10, "video": "ag2",
    "title": "시작하기 B — 개인 Google 계정",
    "subtitle": "Continue with Google · 요금제와 모델 차이",
    "goal": "회사 라이선스가 없어도 **개인 Google 계정**으로 Antigravity를 바로 써 볼 수 있습니다. 로그인 방법과 요금제(무료 · Google AI Pro · Google AI Ultra)별 차이를 알아봅니다.",
    "steps": [
        {
            "title": "앱 설치 후 Continue with Google",
            "body": [
                "[공식 다운로드 페이지](https://antigravity.google/download)에서 내 OS(macOS · Windows · Linux)에 맞는 설치 파일을 받아 설치합니다.",
                "앱을 처음 실행하면 **Welcome to Antigravity** 화면이 나타납니다. 개인 계정은 파란색 **Continue with Google**을 누릅니다.",
            ],
            "shot": "ag_2_01_welcome", "caption": "첫 화면 — 개인 계정은 [Continue with Google]",
            "callouts": [{"box": [505, 280, 430, 40], "label": "Continue with Google — 개인 계정", "pos": "above"}],
        },
        {
            "title": "브라우저에서 로그인하고 앱으로 돌아오기",
            "body": [
                "버튼을 누르면 기본 브라우저가 열리고 Google 로그인 화면이 나타납니다. 앱에는 로그인을 기다리는 표시가 돌아갑니다.",
                "브라우저에서 계정을 고르고 승인하면 앱으로 자동으로 돌아와 작업 폴더를 고르는 화면으로 넘어갑니다.",
                "다른 계정으로 바꾸고 싶다면 앱의 **Back**을 눌러 처음 화면으로 돌아갑니다.",
            ],
            "shot": "ag_2_02_waiting", "caption": "브라우저 로그인을 기다리는 중 — [Back]으로 취소",
            "callouts": [{"box": [505, 280, 430, 40], "label": "브라우저 로그인 대기 중", "pos": "above"}, {"box": [696, 333, 48, 22], "label": "Back — 취소", "pos": "below"}],
            "note": "브라우저가 열리지 않으면 첫 화면 아래 **Having trouble signing in?** 을 눌러 안내를 따르세요. 학교·회사에서 관리하는 계정은 개인 요금제를 쓸 수 없다는 안내가 나올 수 있습니다. 이때는 Lab 1(회사 계정)을 따르세요.",
        },
        {
            "title": "요금제별 차이 — 할당량과 모델",
            "body": [
                "모든 요금제에서 에이전트 · Plan · 아티팩트 · 브라우저 · 예약 작업 · CLI 같은 핵심 기능은 똑같이 쓸 수 있습니다. 다른 것은 **할당량**과 **고를 수 있는 모델**입니다.",
                "- **무료** 주 단위로 갱신되는 할당량 · Gemini 3.8 Flash 같은 Gemini 모델",
                "- **Google AI Pro** 5시간마다 갱신되는 넉넉한 할당량(주간 한도 안에서) · Gemini 4 Argon, Claude 모델 포함",
                "- **Google AI Ultra** 가장 높은 할당량과 주간 한도 · 파트너 모델 상시 사용",
            ],
            "tip": "실습(Lab 3~6)은 무료 요금제의 Gemini 3.8 Flash로도 충분히 따라 할 수 있습니다. 긴 작업이 많은 Lab 7~8은 할당량을 넉넉히 남겨 두고 시작하세요.",
        },
        {
            "title": "할당량을 다 쓰면 — AI 크레딧",
            "body": [
                "할당량을 모두 쓰면 다음 갱신 때까지 기다리거나, Google AI Pro · Ultra 사용자는 **AI 크레딧**을 구매해 이어서 쓸 수 있습니다.",
                "설정의 **AI Credit Overages**에서 정합니다.",
                "- **Never** 할당량을 다 쓰면 갱신될 때까지 기다림",
                "- **Always** 할당량을 다 쓰면 구매한 크레딧을 자동으로 사용",
            ],
            "note": "개인 요금제에서는 본인 API 키(BYOK)로 한도를 늘리는 방식은 지원하지 않습니다.",
        },
        {
            "title": "회사 계정(Lab 1)과 무엇이 다른가요?",
            "body": [
                "- **결제** 개인: 내 Google 요금제 / 회사: GE 구독과 회사 Cloud 결제 계정",
                "- **정책** 개인: 내가 앱 설정에서 결정 / 회사: 관리자가 콘솔에서 정한 보안 정책·허용 모델이 우선",
                "- **데이터** 회사 코드와 데이터를 다룬다면 회사 계정(Use Business Account)을 쓰는 것이 원칙입니다.",
            ],
        },
    ],
    "check": [
        "Continue with Google로 로그인하는 흐름을 안다",
        "무료 · Google AI Pro · Google AI Ultra의 할당량과 모델 차이를 설명할 수 있다",
        "할당량이 떨어졌을 때 AI Credit Overages로 무엇을 정하는지 안다",
    ],
    "more": [
        "내 업무에서 Antigravity로 해 보고 싶은 일 3가지를 적고, 각각 무료 요금제로 충분한지 판단해 보세요.",
    ],
}
