# -*- coding: utf-8 -*-
"""v2 portal — site meta and tracks (schema: production/content/v2/schema.md).

Cymbal(심벌)은 Google 공식 가상 브랜드입니다. 모든 실습 데이터는 가상입니다.
"""

SITE = {
    "title": "Hands-on Lab",
    "org": "Cymbal",
    "hero_kicker": "Gemini Enterprise · Antigravity Hands-on Lab",
    "hero_title": ["AI와 함께 일하는 방법,", "직접 해 보며 익히세요"],
    "hero_sub": "실제 화면을 녹화한 영상과 단계별 가이드로 Gemini Enterprise와 Antigravity를 처음부터 끝까지 따라 합니다.",
    "files_src": "production/samples/v2/build",
    "video_src": "production/video_v2",
    "footer_note": "이 포털의 제품 화면 이미지와 영상은 모두 **실제 앱에서 캡처·녹화한 화면**입니다. "
                   "Cymbal(심벌)은 Google의 가상 브랜드이며, 실습 파일과 예시의 회사 수치·규정은 모두 **가상 데이터**입니다.",
    "next_steps": [
        {
            "no": "01",
            "kicker": "내일 당장",
            "title": "4요소 프롬프트와 보고서 스킬 1개 등록하기",
            "body": "요청하실 때 **역할 · 맥락 · 작업 · 형식** 네 가지만 챙겨 보세요. 자주 쓰는 보고서·이메일 양식은 **스킬(`/`)** 로 한 번 등록해 두면 매번 설명할 필요가 없습니다.",
        },
        {
            "no": "02",
            "kicker": "이번 주",
            "title": "우리 부서 규정·매뉴얼 PDF로 에이전트 만들기",
            "body": "팀에서 반복해서 받는 질문(출장·경비·휴가·IT·구매 절차)을 골라 최신 PDF 문서를 지식으로 넣은 **채팅 에이전트**를 만들고 `@멘션`으로 호출해 보세요.",
        },
        {
            "no": "03",
            "kicker": "이번 달",
            "title": "주간 동향 조사와 정례 보고를 워크플로로 자동화하기",
            "body": "매주 반복하는 시장·규제 뉴스 수집과 요약은 **워크플로**에 맡기고, 마지막에 **인간 참여형(승인)** 단계를 두어 안전하게 검토 후 공유하세요.",
        },
        {
            "no": "04",
            "kicker": "개발 · 확장",
            "title": "Antigravity로 웹앱·ADK 에이전트 만들고 GE에 게시하기",
            "body": "Antigravity에서 계획(Plan) 기반으로 사내 도구와 ADK 에이전트를 개발하고, `agents-cli deploy` · `publish gemini-enterprise`로 전사 Gemini Enterprise 앱에 배포해 보세요.",
        },
    ],
    "references": [
        {"title": "Gemini Enterprise 공식 문서", "desc": "기능 가이드 · 에이전트 빌더 · 워크플로 · 관리자 설정", "url": "https://docs.cloud.google.com/gemini/enterprise/docs?hl=ko"},
        {"title": "Gemini Enterprise 출시 노트", "desc": "최신 모델 · 커넥터 · 에이전트 기능 업데이트 내역", "url": "https://docs.cloud.google.com/gemini/enterprise/docs/release-notes?hl=ko"},
        {"title": "Google Antigravity 공식 문서", "desc": "설치 · Plan & Review · 스킬·규칙 · MCP · 엔터프라이즈 설정", "url": "https://antigravity.google/docs"},
        {"title": "Vertex AI Agent Builder & ADK 문서", "desc": "Agent Development Kit · Agent Runtime 배포 · GE 게시", "url": "https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview"},
    ],
    # 홈 '결과물' 벤토: 실습에서 실제로 만든 결과물 캡처(stem) — 카드를 누르면 해당 Lab으로 이동.
    # span: 넓은 화면 12칸 그리드에서 차지하는 칸 수(한 줄 합 12), focus: 카드에 맞춰 잘라 보일 위치 "x y"(%),
    # zoom: 결과물 부분을 크게 보이도록 focus 기준 확대(1~3, 실제 캡처를 자르는 것 — 편집 아님)
    "showcase": [
        {"track": "ag", "lab": "lab7", "stem": "ag_7v_21_deck_s1", "span": 7, "focus": "50 40",
         "title": "임원 보고 슬라이드 6장", "desc": "회사 템플릿과 BigQuery 데이터로 에이전트가 만든 주간 VOC 보고 — PDF까지 한 번에"},
        {"track": "ag", "lab": "lab4", "stem": "ag_4v_20_dash_top", "span": 5, "focus": "0 0",
         "title": "VOC 대시보드", "desc": "안전 이슈를 맨 위에, 고객 이름 · 연락처는 가린 고객 문의 대시보드"},
        {"track": "ge", "lab": "lab3", "stem": "ge_3_32_canvas_ready", "span": 5, "focus": "78 36", "zoom": 1.3,
         "title": "Canvas 발표 자료", "desc": "엑셀 매출 데이터를 분석해 바로 만든 4분기 전략 슬라이드"},
        {"track": "ag", "lab": "lab9", "stem": "ag_9v_07_ge_answer", "span": 7, "focus": "60 30", "zoom": 1.35,
         "title": "Gemini Enterprise의 VOC 도우미", "desc": "직접 만든 ADK 에이전트를 배포 · 게시해 GE에서 한국어로 질문"},
        {"track": "ge", "lab": "lab5", "stem": "ge_5_30_nb_infographic", "span": 6, "focus": "75 54", "zoom": 1.5,
         "title": "Gemini Notebook 스튜디오", "desc": "브리프 PDF 한 장으로 인포그래픽 · 슬라이드 · 동영상 개요 · 오디오 오버뷰까지"},
        {"track": "ge", "lab": "lab4", "stem": "ge_4_32_video_full", "span": 6, "focus": "52 24", "zoom": 1.7,
         "title": "Veo로 만든 제품 영상", "desc": "신제품 브리프 한 장으로 만든 AirPole Pro 티저 동영상"},
    ],
    # 홈 히어로의 움직이는 창: 실제 앱 캡처가 오른쪽 → 가운데 → 왼쪽으로 자동으로 넘어갑니다(정지 · 이전/다음 버튼 포함).
    # 첫 항목이 가운데, 두 번째가 오른쪽, 마지막 항목이 왼쪽에서 시작합니다(스크립트가 없을 때도 이 세 장이 보임).
    "stage": [
        {"stem": "ge_3_32_canvas_ready", "title": "Gemini Enterprise · 데이터 분석 & Canvas"},
        {"stem": "ag_7v_21_deck_s1", "title": "결과물 · 에이전트가 만든 임원 보고 슬라이드"},
        {"stem": "ge_5_30_nb_infographic", "title": "Gemini Enterprise · Gemini Notebook 인포그래픽"},
        {"stem": "ag_4v_20_dash_top", "title": "결과물 · 에이전트가 만든 VOC 대시보드"},
        {"stem": "ge_4_32_video_full", "title": "Gemini Enterprise · Veo로 만든 제품 영상"},
        {"stem": "ag_9v_07_ge_answer", "title": "Gemini Enterprise · 직접 만든 VOC 도우미"},
        {"stem": "ag_4_03_build_done", "title": "Antigravity · 에이전트와 함께 개발"},
    ],
}

TRACKS = [
    {
        "id": "ge",
        "title": "Gemini Enterprise",
        "short": "GE",
        "tagline": "프롬프트부터 데이터 분석, 에이전트와 워크플로까지 — 매일의 업무를 AI와 함께.",
        "hero_line": "매일의 업무를 AI와 함께",  # 트랙 페이지 히어로 둘째 줄(그라디언트)
        "audience": "일반 사무직(비개발자)",
        "accent": "#4285F4",
        "opening": {"video": "ge_opening", "title": "Gemini Enterprise로 일하는 방식",
                    "desc": "실습을 시작하기 전에 Gemini Enterprise가 무엇이고 업무를 어떻게 바꾸는지 살펴봅니다."},
        "prep": [
            "회사에서 안내받은 **Gemini Enterprise 접속 주소**로 로그인해 주세요. (Chrome 또는 Edge 최신 버전 권장)",
            "아래 **실습 파일 전체 다운로드(ZIP)** 를 받아 바탕화면에 압축을 풀어 두세요.",
            "화면 언어가 영어로 보이면 주소 끝에 `?hl=ko`를 붙이거나 Google 계정 언어를 한국어로 바꾸세요.",
            "각 Lab은 **데모 영상 확인 → 프롬프트 복사·실행 → 체크리스트 점검** 순서로 진행합니다.",
        ],
        "files": [
            {"file": "Cymbal_제품별_지역별_월별매출_2026_가상.xlsx", "title": "제품별·지역별 월별 매출 2026 (가상)", "desc": "2026년 1~9월 5개 제품 × 5개 지역 월별 판매수량·매출·매출총이익과 월간 목표 — 데이터 분석·차트·Canvas 실습용 엑셀", "labs": ["lab3"], "preview": "previews/Cymbal_제품별_지역별_월별매출_2026_가상.png"},
            {"file": "Cymbal_고객문의_로그_2026-10_가상.xlsx", "title": "고객 문의 로그 2026-10 (가상)", "desc": "10월 고객 문의 60건(채널·제품·문의내용) — 분류·긴급도 판단과 답변 초안을 만드는 워크플로 실습용 엑셀", "labs": ["lab8"], "preview": "previews/Cymbal_고객문의_로그_2026-10_가상.png"},
            {"file": "Cymbal_출장비_및_경비처리_규정_가상.pdf", "title": "출장비 및 경비처리 규정 (가상)", "desc": "직급·지역별 일비·숙박 한도, 법인카드, 7영업일 정산·지연 조치, 영수증·접대비 규정 7쪽 PDF — 사내 지원 데스크 에이전트 지식", "labs": ["lab7"], "preview": "previews/Cymbal_출장비_및_경비처리_규정_가상.png"},
            {"file": "Cymbal_휴가_및_근무제도_규정_가상.pdf", "title": "휴가 및 근무제도 규정 (가상)", "desc": "연차 발생·이월, 반차·반반차, 경조사 휴가표, 재택근무 주 2일, 코어타임 6쪽 PDF — 사내 지원 데스크 에이전트 지식", "labs": ["lab7"], "preview": "previews/Cymbal_휴가_및_근무제도_규정_가상.png"},
            {"file": "Cymbal_IT보안_및_계정관리_가이드_가상.pdf", "title": "IT보안 및 계정관리 가이드 (가상)", "desc": "비밀번호·계정 잠금 해제·장비·소프트웨어 승인·보안 사고 신고·헬프데스크 티켓 6쪽 PDF — 사내 지원 데스크 에이전트 지식", "labs": ["lab7"], "preview": "previews/Cymbal_IT보안_및_계정관리_가이드_가상.png"},
            {"file": "Cymbal_신제품_브리프_에어폴_프로_가상.pdf", "title": "신제품 브리프 — AirPole Pro (가상)", "desc": "기둥형 스마트 공기청정기 런칭 브리프(타깃·기능·카피·톤앤매너·티저 스토리보드) 3쪽 PDF — 이미지·동영상·워크플로 참조 파일", "labs": ["lab4", "lab5", "lab8"], "preview": "previews/Cymbal_신제품_브리프_에어폴_프로_가상.png"},
            {"file": "Cymbal_브랜드_가이드_가상.pdf", "title": "브랜드 가이드 (가상)", "desc": "브랜드 컬러·워드마크·톤 오브 보이스·금지 표현·고객 응대 원칙 2쪽 PDF — 스킬·톤앤매너 기준", "labs": ["lab4", "lab6"], "preview": "previews/Cymbal_브랜드_가이드_가상.png"},
            {"file": "Cymbal_보고서스타일_스킬.zip", "title": "보고서 스타일 스킬 (ZIP)", "desc": "결론 먼저·3줄 요약·표·다음 단계·금지 표현을 적용하는 cymbal-report-style 스킬 — 스킬 업로드에 그대로 올리는 ZIP", "labs": ["lab6"], "preview": "previews/cymbal-report-style.png"},
            {"file": "skills/cymbal-report-style/SKILL.md", "title": "보고서 스타일 스킬 원본 (SKILL.md)", "desc": "cymbal-report-style 스킬 원본 마크다운 — 내용 확인용", "labs": ["lab6"], "preview": "previews/cymbal-report-style.png"},
            {"file": "Cymbal_실습파일_전체.zip", "title": "실습 파일 전체 다운로드 (ZIP)", "desc": "실습 파일 8종(엑셀 2, PDF 5, 스킬)과 안내문을 한 번에 내려받는 압축 파일", "labs": [], "preview": "previews/Cymbal_실습파일_전체.png", "bundle": True},
        ],
        "faq": [
            {"q": "실습에서 만든 대화나 올린 파일은 다른 사람이나 모델 학습에 쓰이나요?",
             "a": "아니요. Gemini Enterprise에 입력한 프롬프트와 업로드한 문서는 조직 외부로 유출되지 않으며 Google 기반 모델 학습에 사용되지 않습니다. 직접 **공유**하지 않는 한 내 계정에서만 보입니다."},
            {"q": "AI가 만든 답변이나 차트가 영상과 조금 다른데 괜찮나요?",
             "a": "네, 생성형 AI 특성상 문장 표현이나 표 구성은 매번 조금씩 달라질 수 있습니다. 핵심 수치와 출처 근거가 맞는지만 확인하시면 됩니다."},
            {"q": "내가 만든 채팅 에이전트나 워크플로를 팀원에게 공유하려면 어떻게 하나요?",
             "a": "에이전트 갤러리의 카드 메뉴(**⋮ → 공유**)에서 동료나 부서 그룹을 지정해 공유할 수 있습니다. 수정 사항은 **업데이트**를 눌러야 공유 버전에 반영됩니다(Lab 7·8·9 참고)."},
            {"q": "Gemini 4 Carbon도 쓸 수 있나요?",
             "a": "**Gemini 4 Carbon**은 Gemini 4 Argon과 함께 나온 Gemini 4 세대의 새 모델로, 깊이 있는 분석과 복잡한 작업에 고르는 고성능 모델입니다. "
                  "조직 관리자가 허용한 모델만 입력창의 **모델 선택**(Auto)에 보이므로, 목록에 Carbon이 있으면 실습에서 **Gemini 4 Argon**을 고르는 자리에서 그대로 바꿔 골라도 됩니다. "
                  "이 포털의 영상과 화면은 Gemini 4 Argon · 3.8 Flash로 녹화했습니다(Lab 1 · 7)."},
        ],
    },
    {
        "id": "ag",
        "title": "Antigravity",
        "short": "AG",
        "tagline": "CX팀의 요청 하나를 일주일 만에 — 대시보드 → MCP로 회사 데이터 연결 → 보고 자동화 → 전사 에이전트까지.",
        "hero_line": "에이전트와 함께 만드는 개발",
        "audience": "개발자 · 기술 친화적 현업",
        "accent": "#9B72CB",
        "cover": "ag_7v_21_deck_s1",  # finished deliverable (Lab 7 deck the agent built) — shows the result, not the IDE
        "opening": {"video": "ag_opening", "title": "에이전트와 함께 만드는 개발",
                    "desc": "Antigravity 앱·CLI·SDK가 무엇이고, 에이전트에게 일을 맡기는 방법을 살펴봅니다."},
        "prep": [
            "[antigravity.google/download](https://antigravity.google/download)에서 **Antigravity 데스크톱 앱**을 설치해 주세요.",
            "회사 GE 라이선스가 있다면 **Use Business Account**(Lab 1), 개인 계정이라면 **Continue with Google**(Lab 2)로 로그인합니다.",
            "아래 **Cymbal VOC 스타터(ZIP)** 를 받아 홈 폴더 아래에 풀어 두세요. Lab 3부터 Lab 10까지 **이 `cymbal-voc` 폴더 하나를 계속 키워 갑니다.**",
            "Lab 6(MCP · BigQuery)부터는 Google Cloud 프로젝트가 필요합니다. `lab.env` 맨 위 변수(`PROJECT_ID` 등)만 내 값으로 바꾸고 `bash setup/load_to_bigquery.sh`로 실습 데이터를 올려 두세요.",
            "Lab 8·9(ADK 에이전트 · 배포 · GE 게시)를 직접 실행하려면 `gcloud` CLI와 `agents-cli`, `gcloud auth application-default login`이 필요합니다.",
        ],
        "files": [
            {"file": "Cymbal_VOC_스타터.zip", "title": "Cymbal VOC 스타터 프로젝트 (ZIP)", "desc": "CX팀 요청서 · 고객 문의 300건(4주, 가상) · lab.env · BigQuery 적재 스크립트 — Lab 3~10에서 계속 키워 가는 실습 폴더 cymbal-voc", "labs": ["lab3", "lab4", "lab5", "lab6", "lab7", "lab8", "lab9", "lab10"], "preview": "previews/Cymbal_VOC_스타터.png", "bundle": True},
            {"file": "cymbal-voc/요청서_CX팀.md", "title": "요청서 — 주간 VOC 보고 자동화 (가상)", "desc": "스토리의 출발점. CX팀장이 보낸 요청 3가지(대시보드 · 주간 보고 자동화 · GE 도우미)와 지켜야 할 것", "labs": ["lab3"], "preview": "previews/Cymbal_VOC_요청서.png"},
            {"file": "Cymbal_브랜드_가이드_가상.pdf", "title": "Cymbal 브랜드 가이드 (가상)", "desc": "대시보드·임원 보고 슬라이드에 쓰는 브랜드 컬러·톤 오브 보이스 기준 PDF", "labs": ["lab4", "lab7"], "preview": "previews/Cymbal_브랜드_가이드_가상.png"},
        ],
        "faq": [
            {"q": "Lab마다 새 폴더를 만들어야 하나요?",
             "a": "아니요. Lab 3에서 연 **`cymbal-voc`** 폴더 하나를 Lab 10까지 계속 씁니다. 앞 Lab의 결과물(대시보드 · 규칙 · 스킬 · 슬라이드 · 에이전트)이 다음 Lab의 재료가 되므로 순서대로 진행하는 것을 권장합니다."},
            {"q": "MCP가 무엇이고, BigQuery 없이도 따라 할 수 있나요?",
             "a": "**MCP**(Model Context Protocol)는 외부 도구·데이터를 에이전트에 연결하는 표준입니다. Lab 6은 Google Cloud의 **BigQuery MCP 서버**로 회사 데이터를 직접 조회합니다. Google Cloud 프로젝트가 없다면 Lab 3~5, 7, 10은 CSV만으로 진행하고 Lab 6은 영상으로 흐름을 익히세요."},
            {"q": "명령어 예시의 PROJECT_ID나 REGION은 어디에서 바꾸나요?",
             "a": "`cymbal-voc/lab.env` 맨 위의 변수(`PROJECT_ID`, `PROJECT_NUMBER`, `REGION`, `BQ_DATASET`, `GE_APP_ID` 등)만 내 환경에 맞게 고치면, 가이드의 명령을 그대로 복사해 실행할 수 있습니다."},
            {"q": "에이전트가 터미널 명령을 바로 실행하지 않게 하려면 어떻게 하나요?",
             "a": "에이전트 설정에서 **Auto Execution**과 **Review Policy**를 **Request Review**로 두면 셸 명령과 파일 변경 전에 승인을 거칩니다(Lab 3). 회사 GE 라이선스라면 관리자 정책이 우선합니다(Lab 1)."},
            {"q": "Gemini 4 Carbon으로 실습해도 되나요?",
             "a": "네. **Gemini 4 Carbon**은 Gemini 4 Argon과 함께 나온 Gemini 4 세대의 새 모델로, 깊이 있는 분석과 복잡한 작업에 고르는 고성능 모델입니다. "
                  "입력창 아래 **모델 선택** 목록에 보이면 Lab 3에서 **Gemini 4 Argon Medium**을 고르는 자리에서 Carbon을 골라도 같은 흐름으로 진행됩니다. "
                  "목록에 없다면 요금제나 회사 관리자의 **허용 모델**(Model availability) 설정 때문입니다(Lab 1 · 2). 영상은 Gemini 4 Argon으로 녹화했습니다."},
        ],
    },
]
