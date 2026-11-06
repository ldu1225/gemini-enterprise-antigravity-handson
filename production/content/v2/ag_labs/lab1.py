# -*- coding: utf-8 -*-
"""AG Lab 1 — 시작하기 A: Gemini Enterprise 라이선스로 Antigravity 쓰기.

Sources (2026-10-26/27): cloud.google.com/gemini/enterprise/docs/ai-developer-tools-overview,
ai-developer-tools-settings, ai-developer-tools-metrics; antigravity.google/docs/install, /enterprise.
Console stills gc_ag_1r_* are REAL captures of the Google Cloud console (lab test project, location us, 2026-10-27,
production/capture/agy/ag1r_console.py — edit panels were opened and closed with Cancel, nothing was saved).
Every callout box comes from the DOM boxes saved next to the still (<stem>.boxes.json, CSS px of 1440x810);
boxes whose content touches the element edge are padded by 3-6 px (same as the video renderer's ring padding); the
metrics "Active Users (Adoption)" box starts 6 px above its header row (y=176) so it does not overlap the time-range box.
ag_2_01_welcome is the REAL Antigravity sign-in screen (CSS 1440x810).
"""

DOC_SETTINGS = "https://cloud.google.com/gemini/enterprise/docs/ai-developer-tools-settings"
DOC_METRICS = "https://cloud.google.com/gemini/enterprise/docs/ai-developer-tools-metrics"

LAB = {
    "id": "lab1", "no": 1, "level": "입문", "minutes": 15, "video": "ag1",
    "title": "시작하기 A — GE 라이선스",
    "subtitle": "관리자 콘솔 설정 + Use Business Account 로그인",
    "goal": "회사에서 **Gemini Enterprise(GE) 라이선스**를 받았다면, 별도 개인 요금제 없이 Antigravity를 쓸 수 있습니다. 관리자가 콘솔에서 무엇을 켜야 하는지 확인하고, 사용자는 **Use Business Account**로 로그인합니다.",
    "steps": [
        {
            "title": "먼저 확인하기 — 어떤 로그인 방법을 쓰나요?",
            "body": [
                "Antigravity 첫 화면에는 로그인 버튼이 두 개 있습니다.",
                "- **Use Business Account** 회사가 GE 라이선스를 배정한 경우(이번 Lab)",
                "- **Continue with Google** 개인 Google 계정으로 쓰는 경우(Lab 2)",
                "회사 계정으로 쓰면 사용량이 회사 GE 구독에 포함되고, 관리자가 정한 보안 정책·허용 모델이 그대로 적용됩니다.",
            ],
            "shot": "ag_2_01_welcome", "caption": "Antigravity 첫 화면 — 회사 계정은 [Use Business Account]",
            "callouts": [{"box": [505, 336, 430, 40], "label": "Use Business Account — 회사 계정(GE 라이선스)", "pos": "below"}],
            "tip": "어떤 계정을 써야 할지 모르겠다면 사내 IT 담당자에게 \"Gemini Enterprise 라이선스가 배정되어 있는지\" 먼저 물어보세요.",
        },
        {
            "title": "관리자 준비 ① — 지원 에디션과 결제 계정",
            "body": [
                "AI developer tools(Antigravity 포함)는 아래 GE 에디션에서 쓸 수 있습니다.",
                "- **Standard · Plus · Pay-as-you-go · Standard Emerging Market**",
                "- Frontline 에디션은 지원하지 않습니다.",
                "GE 구독이 연결된 Google Cloud 프로젝트는 **인보이스(월별 청구서) 결제 계정**에 연결되어 있어야 합니다. 신용카드로 결제하는 셀프서비스 결제 계정은 지원하지 않습니다.",
            ],
            "note": "Gemini 모델 사용량은 에디션별 사용자 크레딧에서 차감되고, 관리자가 허용한 파트너 모델(예: Claude)은 Cloud 결제 계정에 사용량만큼 청구됩니다.",
        },
        {
            "title": "관리자 준비 ② — API와 IAM 역할",
            "body": [
                "콘솔에서 기능을 켜면 필요한 API가 자동으로 활성화되지만, 라이선스를 배정하기 전에 미리 켜 두면 설정 오류를 줄일 수 있습니다.",
                "역할은 두 가지입니다.",
                "- **Gemini Enterprise Admin** (`roles/discoveryengine.agentspaceAdmin`) 설정·지표 화면을 관리합니다. 이 역할만으로는 도구를 쓸 수 없습니다.",
                "- **Gemini Enterprise User** (`roles/discoveryengine.agentspaceUser`) 실제로 Antigravity를 쓰는 개발자에게 부여합니다.",
            ],
            "code": {"lang": "bash", "text": "# ── 변수 — 본인 환경에 맞게 이 두 줄만 고치세요 ──\nexport PROJECT_ID=\"my-project-id\"            # GE 구독이 연결된 프로젝트\nexport DEV_GROUP=\"dev-team@example.com\"       # Antigravity를 쓸 개발자 그룹\n\ngcloud services enable discoveryengine.googleapis.com \\\n  businessaicode.googleapis.com aiplatform.googleapis.com \\\n  --project=\"${PROJECT_ID}\"\n\n# 개발자에게 사용자 역할 부여(그룹 단위 권장)\ngcloud projects add-iam-policy-binding \"${PROJECT_ID}\" \\\n  --member=\"group:${DEV_GROUP}\" \\\n  --role=roles/discoveryengine.agentspaceUser"},
            "tip": "특정 그룹만 AI developer tools를 못 쓰게 하려면, 기본 역할에서 `businessaicode.*` 권한을 뺀 커스텀 역할을 만들어 부여합니다.",
        },
        {
            "title": "관리자 설정 ③ — AI developer tools 켜기",
            "body": [
                "Google Cloud 콘솔에서 **Gemini Enterprise → Settings**로 가서 **AI developer tools** 탭을 엽니다.",
                "- **Current location** 설정은 위치(`global` · `us` · `eu`)마다 따로 적용됩니다. GE 앱을 만든 위치인지 확인하고, 다른 위치는 **Edit**로 바꿔서 설정합니다(이 실습 프로젝트는 `us`).",
                "- **AI developer tools** 스위치를 켜면 GE 라이선스 사용자가 Antigravity 같은 AI 개발 도구를 쓸 수 있습니다. 필요한 API(Discovery Engine · Business AI Code)가 꺼져 있으면 이때 자동으로 켜집니다.",
                "새 Standard · Plus · Pay-as-you-go 구독은 구매한 위치에서 기본으로 켜져 있지만, 기존 구독은 관리자가 직접 켜야 합니다.",
            ],
            "shot": "gc_ag_1r_01_devtools", "caption": "Gemini Enterprise → Settings → AI developer tools (실제 콘솔)",
            "callouts": [
                {"box": [290.0, 197.0, 329.5, 44.0], "label": "Current location — 설정할 위치", "pos": "above"},
                {"box": [290.0, 253.0, 780.0, 84.3], "label": "AI developer tools — 켜짐", "pos": "below"},
            ],
        },
        {
            "title": "관리자 설정 ④ — 보안 정책과 로그",
            "body": [
                "같은 탭의 **Security** 오른쪽 **Edit**를 누르면 에이전트가 할 수 있는 일을 정하는 패널이 열립니다.",
                "- **Outside of file access policy** 작업 폴더 밖 파일 접근 — Deny(기본) · Always ask · Allow",
                "- **Terminal auto-execution mode** 터미널 명령 자동 실행 — Require review · Proceed in sandbox · Always proceed(기본)",
                "- **Sandbox mode** 에이전트 도구를 격리된 로컬 샌드박스로 제한(기본 꺼짐)",
                "- **Browser access** 브라우저 에이전트 제어. 켜면 **Allowed URLs**(허용 URL 목록)와 **Browser JavaScript execution policy**(Disabled · Request review · Allow)를 정합니다.",
                "- **MCP server** (Preview) 허용할 MCP 서버를 JSON으로 지정",
                "아래 **Compliance**에서는 감사용 **Prompts and responses logging**과 **Metadata logging**을 켭니다. 로그는 회사 프로젝트 안에 저장됩니다.",
                "어떤 값으로 정할지 고민된다면, 아래 프롬프트를 Gemini Enterprise나 Antigravity에 붙여 넣어 우리 팀용 초안부터 받아 보세요.",
            ],
            "prompt": "우리 팀이 Antigravity를 처음 도입할 때 권장할 보안 정책(파일 접근·터미널·브라우저·MCP)을 표로 정리해 주세요. 각 항목에 이유도 한 줄씩 적어 주세요.",
            "shots": [
                {"stem": "gc_ag_1r_02_security_edit", "caption": "Security → Edit 패널의 실제 선택지",
                 "callouts": [{"box": [882.0, 143.0, 524.0, 200.0], "label": "Outside of file access · Terminal auto-execution 정책", "pos": "above"}]},
                {"stem": "gc_ag_1r_03_compliance", "caption": "Compliance — 프롬프트·응답 로그, 메타데이터 로그",
                 "callouts": [{"box": [290.0, 150.3, 780.0, 155.0], "label": "Compliance — 감사 로그 설정", "pos": "below"}]},
            ],
            "note": "이 실습 프로젝트는 파일 접근 **Always ask**, 터미널 **Require review**로 바꿔 둔 상태입니다. 값을 바꾼 뒤에는 패널 아래 **Save**를 눌러야 적용됩니다(이 화면들은 Cancel로 닫았습니다).",
            "tip": "공식 권장 기본값 — 파일 접근은 **Deny** 유지, 터미널은 **Require review** 또는 **Proceed in sandbox**, 브라우저는 **Allowed URLs**로 제한. 팀이 익숙해지면 단계적으로 완화하세요.",
        },
        {
            "title": "관리자 설정 ⑤ — 기능: /boost · /teamwork-preview",
            "body": [
                "**Features** 오른쪽 **Edit**에서 여러 에이전트가 함께 일하는 고급 기능을 켜고 끕니다(기본: 둘 다 켜짐).",
                "- **/boost command** 어려운 소프트웨어 엔지니어링 작업을 위한 멀티 에이전트 추론",
                "- **/teamwork-preview command** 큰 프로젝트·복잡한 시뮬레이션·딥 리서치를 위한 에이전트 팀(Preview)",
                "사용자는 Antigravity 앱 2.18.0 이상 또는 CLI 1.2.10 이상에서 이 기능을 쓸 수 있습니다.",
            ],
            "shot": "gc_ag_1r_04_features_edit", "caption": "Features → Edit — /boost · /teamwork-preview 스위치",
            "callouts": [
                {"box": [885.0, 106.0, 518.0, 70.3], "label": "/boost command — 멀티 에이전트 추론", "pos": "above"},
                {"box": [885.0, 178.3, 518.0, 70.3], "label": "/teamwork-preview command — 에이전트 팀", "pos": "below"},
            ],
            "note": "두 기능은 토큰 사용량과 비용을 늘릴 수 있습니다. 비용 관리가 중요하면 꺼 둘 수 있습니다.",
        },
        {
            "title": "관리자 설정 ⑥ — 허용 모델",
            "body": [
                "**Model availability → Google models**의 기본값은 **All models**입니다. 목록을 비워 두면 지원되는 모든 Gemini 모델(새로 나오는 모델 포함)을 쓸 수 있습니다.",
                "특정 모델만 허용하려면 **Edit → Antigravity authorized models**에서 고릅니다. 목록에는 Gemini 4 Argon · Gemini 3.8 Flash · Gemini 3.7 Flash · Gemini 3.6 Flash · Gemini 3.1 Pro가 사고 수준(High · Medium · Low)별로 따로 있습니다. 하나라도 고르면 허용 목록이 되어, 고르지 않은 모델과 새 모델은 쓸 수 없습니다. "
                "**Gemini 4 Carbon** 같은 새 모델도 같은 규칙입니다 — 목록을 비워 두면(All models) 바로 쓸 수 있고, 허용 목록을 쓰고 있다면 관리자가 목록에 추가해야 합니다.",
                "**Non-Google models**에서는 Anthropic **Claude Opus 5.5 · Claude Sonnet 5.5**를 사고 수준(High · Low · Max · Medium)별 스위치로 켭니다. 기본은 꺼짐이고, 켤 때 제공사 약관에 동의해야 합니다.",
                "파트너 모델은 Cloud 결제 계정에 사용량만큼 청구됩니다. 구독형이라면 **Usage & Spending**에서 할당량 초과분 Pay-as-you-go 사용을 켜야 하고, Cloud Billing에서 지출 한도를 걸 수 있습니다.",
            ],
            "shots": [
                {"stem": "gc_ag_1r_05_google_models", "caption": "Google models → Edit — 실제 모델 목록",
                 "callouts": [{"box": [900.0, 141.0, 488.0, 256.0], "label": "Gemini 모델 목록 — High · Low · Medium", "pos": "above"}]},
                {"stem": "gc_ag_1r_06_partner_models", "caption": "Non-Google models — 결제 안내 · Anthropic 모델 스위치",
                 "callouts": [
                     {"box": [296.0, 140.7, 768.0, 182.0], "label": "Important billing and quota info — 초과 사용·지출 한도", "pos": "above"},
                     {"box": [290.0, 341.7, 780.0, 464.0], "label": "Claude Opus 5.5 · Sonnet 5.5 (기본 꺼짐)", "pos": "above"},
                 ]},
            ],
        },
        {
            "title": "사용자 — Use Business Account로 로그인하기",
            "body": [
                "Antigravity 앱을 [공식 다운로드 페이지](https://antigravity.google/download)에서 설치하고 실행합니다(macOS · Windows · Linux).",
                "- 첫 화면에서 **Use Business Account**를 누릅니다.",
                "- **Continue with Google Cloud**를 누르면 브라우저에서 회사 계정 로그인이 진행됩니다.",
                "- 회사가 Okta 같은 외부 ID 제공자를 쓴다면 **Advanced WIF Configuration**에 관리자가 알려 준 설정 문자열(`locations/global/workforcePools/…/providers/…`)을 입력합니다.",
                "- 로그인 후 **라이선스 선택** 화면에서 배정된 라이선스와 Google Cloud 프로젝트, 리전을 고르면 완료입니다.",
            ],
            "shot": "ag_2_01_welcome", "caption": "[Use Business Account] → Continue with Google Cloud → 라이선스 선택",
            "callouts": [{"box": [505, 336, 430, 40], "label": "Use Business Account", "pos": "below"}],
            "note": "CLI(`agy`)와 IDE 확장(Antigravity for IDEs)도 같은 회사 계정으로 로그인합니다. CLI 설치: `curl -fsSL https://antigravity.google/cli/install.sh | bash`",
        },
        {
            "title": "관리자 — 사용 현황 보기(Developer tools metrics)",
            "body": [
                "콘솔 왼쪽 메뉴 **Developer tools metrics**(Preview)에서 도입 현황을 봅니다. 오른쪽 위에서 기간을 바꿀 수 있습니다(기본 **Last 1 day**).",
                "- **Active Users (Adoption)** 시간·일·주·월 평균 활성 사용자와 추이",
                "- **Token Usage & Context Caching** 총 토큰, 일별 토큰 사용량, 컨텍스트 캐시 적중률",
                "- **Tools & API calls** 일별 API 호출(오류 유형별), 도구 호출, 사용자가 승인한 도구 호출(Daily Tool Calls Accepted)",
                "지표는 보통 5~15분 안에 반영되고, 차트에서 Cloud Monitoring 알림 정책도 만들 수 있습니다.",
            ],
            "shots": [
                {"stem": "gc_ag_1r_07_metrics", "caption": "Developer tools metrics — 기간 선택 · 활성 사용자",
                 "callouts": [
                     {"box": [1062.1, 134.0, 261.9, 32.0], "label": "Last 1 day — 기간 선택", "pos": "above"},
                     {"box": [314.0, 170.0, 1051.0, 576.0], "label": "Active Users (Adoption) — 활성 사용자", "pos": "above"},
                 ]},
                {"stem": "gc_ag_1r_08_metrics_tools", "caption": "Tools & API calls — API 호출 · 도구 호출 · 승인한 도구 호출",
                 "callouts": [{"box": [314.0, 78.0, 1051.0, 728.0], "label": "Tools & API calls", "pos": "inside"}]},
            ],
            "note": "이 실습 프로젝트는 아직 Antigravity 사용 기록이 없어 차트가 **No data**로 보입니다. 개발자가 쓰기 시작하면 같은 화면에 숫자와 그래프가 채워집니다. 화면 구성은 에디션·위치에 따라 다를 수 있으니 [공식 문서](https://cloud.google.com/gemini/enterprise/docs/ai-developer-tools-metrics)도 함께 확인하세요.",
        },
    ],
    "check": [
        "내가 Use Business Account와 Continue with Google 중 무엇을 써야 하는지 안다",
        "(관리자) 지원 에디션 · 인보이스 결제 계정 · 필요한 API와 역할을 확인했다",
        "(관리자) AI developer tools 켜기 · 보안 정책 · 기능 · 허용 모델 위치를 안다",
        "Use Business Account로 로그인하고 라이선스·프로젝트를 선택했다",
        "(관리자) Developer tools metrics에서 사용 현황을 확인할 수 있다",
    ],
    "more": [
        "Antigravity를 우리 회사에 처음 도입할 때 관리자가 확인할 순서를 체크리스트로 만들어 주세요. 에디션·결제 계정, API와 역할, AI developer tools 켜기, 보안 정책, 허용 모델, 사용 지표 확인을 포함해 주세요.",
    ],
}
