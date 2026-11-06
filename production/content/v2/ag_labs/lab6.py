# -*- coding: utf-8 -*-
"""AG Lab 6 — MCP로 회사 데이터 연결 — BigQuery (cymbal-voc 스토리 Day 3).

REAL recordings (1440x810 CSS, Antigravity agent IDE desktop app; Lab 6 agent panel x 915–1440):
  ag6v_env · ag6v_install · ag6v_query · ag6v_insight · ag6v_skill · ag6v_run
Every callout box below is measured — DOM boxes from production/assets/shots/<stem>.boxes.json (leaves / targets),
Apple Vision OCR of the still or of the recording frame (production/qa/find_text.py, callout_audit.ocr), or a pixel
scan (tool toggles). Never eyeballed.

Observed in the recordings (do not over-claim):
- ENV: new chat → prompt with the lab's test-project values → agent analyzed load_to_bigquery.sh + lab.env, edited
  lab.env (+4 −4: PROJECT_ID · PROJECT_NUMBER · GE_APP_ID · GE_LOCATION), ran `bash setup/load_to_bigquery.sh` (no
  approval card in this take), answer after ~1 min 40 s: weekly 62 · 68 · 79 · 91 = 300 + 데이터 출처/기준일 line →
  Accept all.
- INSTALL: … (Additional Options) → MCP Servers → MCP Store filtered to "BigQuery" → BigQuery → Install → Enabled
  (store shows Installed) → Tools: 1. list_dataset_ids 2. get_dataset_info 3. list_table_ids 4. get_table_info
  5. execute_sql_readonly (SELECT only) 6. execute_sql (any query incl. INSERT/UPDATE/DELETE/CREATE) …, each with an
  on/off switch → Configure: "No configuration needed for BigQuery." → Manage MCP servers: BigQuery 9 / 9, 9 tools,
  View raw config.
- QUERY: two "Allow using this MCP tool?" cards (bigquery/get_table_info, bigquery/execute_sql_readonly; options Yes,
  allow this time / Yes, and always allow in this conversation / Yes, and always allow / No (tell the agent what to do
  instead)); JSON result with "numRows": "300"; answer after ~1 min: 안전 이슈 2 → 6건 (+200.0%) on top, 합계 79 → 91건
  (+12건, +15.2%), 데이터 출처: BigQuery …cymbal_cx.voc_tickets | 기준일: 2026-10-25.
- INSIGHT: four approvals; answer after ~1 min 40 s ("Worked for 1m"): 로봇청소기 앱 연결 37건, 2026-09-28 ~ 10-13 하루
  0~1건(4건) → 2026-10-14 하루 6건 → 10-14 ~ 10-25 33건; daily table marks 2026-10-14 "문의 급증 시작일". Masked
  example inquiries follow below (lead's observation; not visible in the frames).
- SKILL: SKILL.md rewritten in ~3 min (1 file changed +57 −16): BigQuery MCP 데이터 조회 절차 · 데이터 출처 표기 변경 ·
  상대 경로 링크([lab.env](../../../lab.env), [AGENTS.md](../../../AGENTS.md)) → Accept all.
- RUN: /voc → slash menu voc-weekly-report → prompt → four approvals → ~1 min 30 s → report regenerated; only the
  data-source line changed (+1 −1): data/voc_tickets.csv (또는 BigQuery …) → BigQuery cymbal_cx.voc_tickets |
  기준일: 2026-10-25. Chat summary: 안전 이슈 6건 (+4건, +200.0%), 6건 모두 공기청정기 전원 어댑터, 접수 3 · 처리중 3.

Hygiene (lead, 2026-10-28): the empty editor of query/insight/skill/run (and env before ~67 s, install before 11.6 s)
shows the empty-editor placeholder logo → portal stills of those moments are crops of the agent panel only
(ag_6v_2x_* = crops of real stills / real recording frames, provenance in <stem>.crop.json; viewport = crop CSS size).
Not used: the non-public MCP store list (install 7.0–9.1 s), ag_6v_10_raw_config (local-path breadcrumb + an extra
config entry), the skill-take editor diff (old file:/// link), agent rows with local paths (env 44.5–66.5 s,
skill 37–149 s), run 96.8–97.03 s (raw markdown link). The status-bar button label stays (no callout on it).
"""

P_ENV = ("lab.env를 이 실습 프로젝트 값으로 채워 주세요: PROJECT_ID=<내 프로젝트 ID>, PROJECT_NUMBER=<내 프로젝트 번호>, "
         "REGION=us-central1, GE_APP_ID=<내 Gemini Enterprise 앱 ID>, GE_LOCATION=<global|us|eu>. "
         "그다음 setup/load_to_bigquery.sh를 실행해서 VOC 데이터를 BigQuery에 올리고, 주별 건수를 알려 주세요.")
LAB_ENV = """# 실습 환경 변수 — 내 환경에 맞게 아래 값만 바꾸세요. (Lab 6 BigQuery · Lab 8 에이전트 · Lab 9 배포/게시에서 사용)
# 실습용 가상 데이터 프로젝트입니다. 이 파일에 비밀번호나 키를 넣지 마세요.
PROJECT_ID="your-project-id"        # Google Cloud 프로젝트 ID
PROJECT_NUMBER="000000000000"       # 프로젝트 번호 (콘솔 홈 대시보드에서 확인)
REGION="us-central1"                # Agent Runtime 배포 리전
BQ_DATASET="cymbal_cx"              # BigQuery 데이터셋 (setup/load_to_bigquery.sh가 만듭니다)
BQ_TABLE="voc_tickets"              # BigQuery 테이블
BQ_LOCATION="US"                    # BigQuery 데이터셋 위치
GE_APP_ID="your-ge-app-id"          # Gemini Enterprise 앱(엔진) ID — 콘솔 Gemini Enterprise > 앱 목록
GE_LOCATION="global"                # Gemini Enterprise 앱 위치 (global | us | eu)
GE_DISPLAY_NAME="Cymbal VOC 분석가"  # Gemini Enterprise에 보일 에이전트 이름"""
MCP_CONFIG = """{
  "mcpServers": {
    "bigquery": {
      "serverUrl": "https://bigquery.googleapis.com/mcp",
      "authProviderType": "google_credentials"
    }
  }
}"""
P_QUERY = ("방금 설치한 BigQuery MCP 도구(get_table_info, execute_sql_readonly)를 직접 호출해서 <내 프로젝트 ID> 프로젝트의 "
           "cymbal_cx.voc_tickets 테이블 구조를 확인하고, 지난주(2026-10-19 ~ 2026-10-25) 분류별 문의 건수를 그 전주와 "
           "비교한 표로 보여 주세요.")
P_INSIGHT = ("BigQuery MCP의 execute_sql_readonly 도구로 <내 프로젝트 ID>.cymbal_cx.voc_tickets에서 로봇청소기 '앱 연결' "
             "문의를 일자별로 조회해서 언제부터 늘었는지 찾아 주세요. 늘어난 날 전후의 문의 내용도 3건만 보여 주세요"
             "(고객 이름·연락처는 가려서).")
P_SKILL = ("voc-weekly-report 스킬이 CSV 대신 BigQuery MCP로 cymbal_cx.voc_tickets의 최신 데이터를 조회하도록 SKILL.md를 "
           "고쳐 주세요. 데이터 출처 표기도 BigQuery 테이블로 바꾸고, 파일 링크는 상대 경로로 써 주세요.")
P_RUN = "/voc-weekly-report 지난주(2026-10-19 ~ 2026-10-25) 보고서를 BigQuery 최신 데이터로 다시 만들어 주세요."

LAB = {
    "id": "lab6", "no": 6, "level": "기본", "minutes": 25, "video": "ag6",
    "title": "MCP로 회사 데이터 연결 — BigQuery",
    "subtitle": "MCP Store · 도구 목록 · MCP 도구 호출 · 스킬 업그레이드",
    "goal": "Lab 5에서 만든 팀 규칙(`AGENTS.md`)과 주간 보고 스킬(`voc-weekly-report`)에 이어서 진행합니다. 지금까지 쓴 "
            "`data/voc_tickets.csv`는 4주치 **복사본**일 뿐, 원본은 매일 회사 **BigQuery**(`cymbal_cx.voc_tickets`)에 "
            "쌓입니다. 이번 Lab에서는 **MCP(Model Context Protocol)** 로 에이전트를 회사 데이터에 직접 연결합니다. MCP는 "
            "에이전트가 외부 도구·데이터에 접속하는 *표준 플러그*입니다. MCP 서버를 하나 설치하면 에이전트가 쓸 수 있는 "
            "**도구**가 늘어나고, 에이전트는 도구를 부를 때마다 내 승인을 받습니다. **실습 변수 채우기 → BigQuery에 데이터 "
            "올리기 → MCP Store에서 BigQuery MCP 설치 → MCP 도구로 실데이터 조회·원인 찾기 → 주간 보고 스킬을 BigQuery로 "
            "업그레이드**까지 진행합니다.",
    "steps": [
        {
            "title": "실습 변수 채우고 BigQuery에 데이터 올리기",
            "body": [
                "Lab 5까지 쓰던 `cymbal-voc` 폴더를 Antigravity에서 그대로 엽니다. 이번 Lab에는 **BigQuery를 쓸 수 있는 내 "
                "Google Cloud 프로젝트**와, 터미널에서 `gcloud` · `bq` 명령을 쓸 수 있는 **Google Cloud CLI**(로그인까지 "
                "마친 상태)가 필요합니다.",
                "프로젝트 맨 위의 `lab.env`가 실습 변수 파일입니다(아래 코드). **여기 값만 내 환경에 맞게 바꾸면** 이후 Lab의 "
                "명령을 그대로 쓸 수 있습니다. `BQ_DATASET` · `BQ_TABLE` · `BQ_LOCATION`은 그대로 두세요. `GE_APP_ID` · "
                "`GE_LOCATION`은 Lab 9에서 쓰므로, 아직 모르면 기본값으로 두고 프로젝트 값만 바꿔도 됩니다.",
                "직접 고쳐도 되지만 이번에는 에이전트에게 맡깁니다. Agent 패널에서 **+**(새 대화)를 누르고, 아래 프롬프트의 "
                "`<…>` 부분을 **내 값**으로 바꿔 보냅니다. 녹화 화면에는 실습용 테스트 프로젝트 값이 보입니다.",
                "에이전트는 `setup/load_to_bigquery.sh`와 `lab.env`를 읽은 뒤 `lab.env`를 고칩니다(**Edited lab.env +4 −4**). "
                "편집기에는 바뀐 줄이 **빨간 줄(원래 값)** 과 **초록 줄(새 값)** 로 표시됩니다.",
                "이어서 `bash setup/load_to_bigquery.sh`를 실행합니다. 스크립트는 `lab.env`를 읽어 데이터셋 `cymbal_cx`를 "
                "만들고(이미 있으면 그대로 둡니다) `data/voc_tickets.csv` 300건을 테이블 `voc_tickets`에 올린 뒤, 주별 건수를 "
                "다시 셉니다. Lab 3에서 Auto Execution을 **Request Review**로 바꿨다면 실행 전에 **명령 실행 승인** 카드가 "
                "뜹니다 — 명령을 읽고 허용하세요(녹화에서는 바로 실행됐습니다).",
                "녹화에서는 약 **1분 40초** 뒤 결과가 나왔습니다. BigQuery에서 다시 센 주별 건수는 **62 · 68 · 79 · 91건(합계 "
                "300건)** 으로 CSV와 똑같고, 답 끝에는 Lab 5 팀 규칙대로 **데이터 출처와 기준일**이 붙었습니다. 오른쪽 아래 "
                "**Accept all**을 눌러 `lab.env` 변경을 확정합니다.",
            ],
            "prompt": P_ENV,
            "code": {"lang": "text", "file": "lab.env", "text": LAB_ENV},
            "shots": [
                {"stem": "ag_6v_20_env_run", "viewport": [525, 430],
                 "caption": "lab.env 수정(+4 −4) → setup/load_to_bigquery.sh 실행",
                 "callouts": [
                     {"box": [17, 208, 158, 24], "label": "Edited lab.env +4 −4", "pos": "above"},
                     {"box": [18, 252, 492, 72], "label": "Run bash setup/load_to_bigquery.sh", "pos": "below"},
                 ]},
                {"stem": "ag_6v_01_env",
                 "caption": "바뀐 lab.env 값과 BigQuery에서 다시 센 주별 건수(합계 300건)",
                 "callouts": [
                     {"box": [404, 121, 226, 218], "label": "PROJECT_ID · … · GE_LOCATION", "pos": "above"},
                     {"box": [970, 220, 436, 218], "label": "주별 건수 — 합계 300건", "pos": "above"},
                     {"box": [936, 452, 470, 46], "label": "데이터 출처 · 기준일", "pos": "below"},
                     {"box": [1327, 669, 73, 26], "label": "Accept all", "pos": "above"},
                 ]},
            ],
            "note": "녹화 화면의 프로젝트 ID·번호는 실습용 테스트 프로젝트 값입니다. 여러분은 반드시 **내 프로젝트 값**을 "
                    "넣으세요. `lab.env`에는 비밀번호나 키를 넣지 않습니다. 실습 데이터는 모두 가상입니다.",
        },
        {
            "title": "MCP Store에서 BigQuery MCP 설치",
            "body": [
                "**MCP 서버**는 에이전트에게 새 도구를 붙여 주는 플러그입니다. 이번에는 Google이 운영하는 **원격 BigQuery MCP "
                "서버**(`https://bigquery.googleapis.com/mcp`)를 설치합니다. 내 컴퓨터에 따로 프로그램을 깔지 않습니다.",
                "Agent 패널 오른쪽 위 **…**(Additional Options) → **MCP Servers**를 누르면 **MCP Store**가 열립니다. 검색창에 "
                "`BigQuery`를 입력하고 목록에서 **BigQuery**를 고릅니다. 이름이 비슷한 *Google BigQuery Data Transfer "
                "Service* · *Migration Service*와 헷갈리지 마세요.",
                "편집기에 **MCP: BigQuery** 페이지가 열리면 **Install**을 누릅니다. 몇 초 뒤 버튼이 **Enabled**로 바뀌고, "
                "스토어 목록의 BigQuery 옆에도 **Installed**가 표시됩니다.",
                "**Tools** 탭에서 에이전트가 새로 쓸 수 있게 된 도구를 확인합니다. 도구마다 오른쪽에 **켜기/끄기 스위치**가 "
                "있습니다.",
                "- `list_dataset_ids` · `list_table_ids` — 데이터셋·테이블 목록",
                "- `get_dataset_info` · `get_table_info` — 데이터셋·테이블 정보(열 구성, 행 수 등)",
                "- `execute_sql_readonly` — 읽기 전용 SQL(**SELECT만**) 실행",
                "- `execute_sql` — 데이터를 바꾸는 SQL(INSERT · UPDATE · DELETE · CREATE …)까지 실행",
                "**Configure** 탭에는 *No configuration needed for BigQuery.* 라고 나옵니다. 이 서버는 **내 Google Cloud "
                "로그인(ADC, Application Default Credentials)** 으로 인증하므로 따로 넣을 키가 없습니다. ADC를 만든 적이 "
                "없다면 터미널에서 아래 첫 번째 명령을 한 번 실행해 두세요.",
                "오른쪽 위 **Manage MCP Servers**를 누르면 설치한 서버와 켜진 도구 수(**BigQuery 9 / 9**, **9 tools**)를 "
                "한눈에 볼 수 있습니다. **View raw config**를 누르면 Store가 대신 써 준 설정 파일 `mcp_config.json`이 열립니다 "
                "— BigQuery 부분은 아래 두 번째 코드와 같습니다.",
            ],
            "code": [
                {"lang": "bash", "label": "ADC 로그인 (처음 한 번)", "text": "gcloud auth application-default login"},
                {"lang": "json", "file": "mcp_config.json", "text": MCP_CONFIG},
            ],
            "shots": [
                {"stem": "ag_6v_21_menu", "viewport": [525, 330],
                 "caption": "Agent 패널 … (Additional Options) → MCP Servers",
                 "callouts": [
                     {"box": [332, 79, 141, 23], "label": "MCP Servers", "pos": "below"},
                 ]},
                {"stem": "ag_6v_04_bigquery_page",
                 "caption": "MCP Store에서 BigQuery 선택 → MCP: BigQuery 페이지의 Install",
                 "callouts": [
                     {"box": [224, 107, 54, 26], "label": "Install", "pos": "below"},
                     {"box": [927, 256, 501, 66], "label": "BigQuery", "pos": "above"},
                 ]},
                {"stem": "ag_6v_06_tools",
                 "caption": "Tools 탭 — 에이전트가 새로 쓸 수 있게 된 도구(오른쪽은 켜기/끄기 스위치)",
                 "callouts": [
                     {"box": [120, 285, 129, 30], "label": "Tools", "pos": "below"},
                     {"box": [276, 228, 540, 282], "label": "1. list_dataset_ids … 5. execute_sql_readonly",
                      "pos": "above"},
                 ]},
                {"stem": "ag_6v_09_manage",
                 "caption": "Manage MCP servers — BigQuery 9 / 9 도구 켜짐",
                 "callouts": [
                     {"box": [124, 105, 209, 26], "label": "Manage MCP servers", "pos": "above"},
                     {"box": [134, 163, 126, 24], "label": "BigQuery 9 / 9", "pos": "below"},
                     {"box": [563, 105, 178, 26], "label": "9 tools · View raw config", "pos": "above"},
                 ]},
            ],
            "tip": "조회만 할 거라면 Tools 탭에서 `execute_sql`처럼 **데이터를 바꿀 수 있는 도구는 꺼 두세요.** 에이전트가 "
                   "실수로 테이블을 고칠 가능성 자체가 사라집니다. 필요한 도구만 켜는 것이 MCP를 안전하게 쓰는 기본입니다.",
            "note": "회사(Gemini Enterprise 라이선스) 계정이라면 관리자가 콘솔의 **Gemini Enterprise > Settings > AI developer "
                    "tools > MCP servers**(Lab 1)에서 MCP 서버를 허용해야 합니다. 허용되지 않으면 MCP Store를 쓸 수 없을 수 "
                    "있습니다. MCP Store 목록과 메뉴 위치는 계정·버전에 따라 조금 다르게 보일 수 있습니다.",
        },
        {
            "title": "MCP 도구로 실데이터 조회",
            "body": [
                "**+**로 새 대화를 열고 아래 프롬프트를 보냅니다(`<내 프로젝트 ID>`는 `lab.env`의 `PROJECT_ID`로). 방금 설치한 "
                "도구 이름(`get_table_info`, `execute_sql_readonly`)을 적어 주면 에이전트가 CSV 대신 MCP 도구로 조회합니다.",
                "에이전트가 MCP 도구를 부르기 직전마다 **Allow using this MCP tool?** 카드가 뜹니다. 카드 위쪽 **Tool "
                "arguments**에는 어느 프로젝트 · 데이터셋 · 테이블을 볼지(`projectId` · `datasetId` · `tableId`)가, 카드에는 "
                "부르려는 도구(`bigquery/get_table_info`)가 보입니다. 내용이 맞으면 고르고 **Submit**을 누릅니다.",
                "1. **Yes, allow this time** 이번 한 번만 허용",
                "2. **Yes, and always allow in this conversation** 이 대화에서는 같은 도구를 계속 허용",
                "3. **Yes, and always allow** 앞으로 항상 허용",
                "4. **No (tell the agent what to do instead)** 거절하고 대신 할 일 알려 주기",
                "녹화에서는 **Yes, allow this time**으로 두 번 허용했습니다. 첫 도구 `get_table_info`의 결과는 **JSON**으로 "
                "채팅에 표시되고, 테이블 정보에 `\"numRows\": \"300\"`(행 수 300)이 보입니다. 두 번째는 집계 SQL을 실행하는 "
                "`bigquery/execute_sql_readonly`였습니다.",
                "약 **1분** 뒤 답이 나왔습니다. 먼저 테이블 구조(열 이름 · 타입 · 설명)가, 이어서 **주간 분류별 문의 건수 비교** "
                "표(그 전주 2026-10-12 ~ 10-18 vs 지난주 2026-10-19 ~ 10-25)가 나옵니다.",
                "표 맨 위에는 팀 규칙대로 **안전 이슈 2건 → 6건(+200.0%)** 이 있고, 구매 문의 10 → 14건(+40.0%), 배송 14 → "
                "13건(−7.1%) 등이 이어집니다. 전체는 **79건 → 91건(+12건, +15.2%)** 이고, 마지막 줄에 **데이터 출처: BigQuery "
                "…cymbal_cx.voc_tickets | 기준일: 2026-10-25**가 붙었습니다.",
            ],
            "prompt": P_QUERY,
            "shots": [
                {"stem": "ag_6v_22_allow", "viewport": [525, 756],
                 "caption": "Allow using this MCP tool? — 도구 이름과 Tool arguments를 보고 허용",
                 "callouts": [
                     {"box": [43, 160, 460, 202], "label": "Tool arguments — datasetId · projectId · tableId",
                      "pos": "above"},
                     {"box": [12, 489, 500, 76], "label": "Allow using this MCP tool? · bigquery/get_table_info",
                      "pos": "above"},
                     {"box": [12, 567, 500, 31], "label": "Yes, allow this time", "pos": "below"},
                     {"box": [428, 703, 81, 32], "label": "Submit", "pos": "above"},
                 ]},
                {"stem": "ag_6v_23_safety", "viewport": [525, 756],
                 "caption": "분류별 비교 표 — 안전 이슈가 맨 위(2건 → 6건)",
                 "callouts": [
                     {"box": [19, 233, 404, 26], "label": "2. 주간 분류별 문의 건수 비교", "pos": "above"},
                     {"box": [26, 445, 464, 63], "label": "안전 이슈 2건 → 6건 (+200.0%)", "pos": "above"},
                 ]},
                {"stem": "ag_6v_24_query_result", "viewport": [525, 756],
                 "caption": "합계 79건 → 91건, 마지막 줄의 데이터 출처 · 기준일",
                 "callouts": [
                     {"box": [26, 429, 464, 46], "label": "합계 79건 → 91건 (+12건, +15.2%)", "pos": "above"},
                     {"box": [18, 493, 476, 45], "label": "데이터 출처: BigQuery … | 기준일: 2026-10-25",
                      "pos": "below"},
                 ]},
            ],
            "tip": "MCP 도구를 쓰면 숫자를 *에이전트가 눈으로 세는 것*이 아니라 **BigQuery가 SQL로 계산**합니다. Lab 3에서 "
                   "python으로 검증했던 것처럼, 보고서에 들어갈 숫자는 이렇게 도구가 계산하게 하세요.",
            "note": "승인 카드는 Lab 3의 명령 실행 승인과 같은 원리입니다. 처음에는 **Yes, allow this time**으로 하나씩 "
                    "확인하고, `Tool arguments`에 엉뚱한 프로젝트나 테이블이 보이면 **No**를 고르고 바로잡아 주세요.",
        },
        {
            "title": "데이터에서 원인 찾기",
            "body": [
                "분류별 표에서는 **앱 연결** 문의가 가장 많았습니다. 왜 늘었는지 데이터에서 찾아봅니다. 새 대화에서 아래 "
                "프롬프트를 보냅니다(`<내 프로젝트 ID>`는 내 값으로).",
                "에이전트는 MCP 도구의 사용법(도구 설명)부터 확인한 뒤 테이블 정보 → 일자별 집계 → 문의 내용 순서로 도구를 "
                "불렀습니다. 녹화에서는 승인 카드가 **네 번** 떴고, 모두 **Yes, allow this time**으로 허용했습니다.",
                "같은 대화에서 승인이 반복되면 두 번째 **Yes, and always allow in this conversation**을 골라도 됩니다. 세 번째 "
                "**Yes, and always allow**는 이 대화가 끝나도 계속 허용되니 신중하게 고르세요.",
                "답을 쓰기 전에는 `AGENTS.md`의 팀 규칙(한국어, 개인정보 마스킹, 데이터 출처 표기 등)도 다시 확인했습니다"
                "(생각 과정에 *Focusing on the rules in AGENTS.md* 표시).",
                "약 **1분 40초** 뒤 답이 나왔습니다(**Worked for 1m**). 로봇청소기 '앱 연결' 문의는 모두 37건이고, "
                "**2026-09-28 ~ 2026-10-13에는 하루 0~1건(모두 4건)** 이던 것이 **2026-10-14 하루 6건**으로 급증한 뒤 매일 "
                "이어져 **2026-10-14 ~ 10-25에 33건**이 몰렸습니다. 아래로 내리면 이어지는 일자별 표에서도 2026-10-14가 "
                "*문의 급증 시작일*로 표시됩니다.",
                "답 아래쪽에는 급증 전후의 문의 내용 3건이 고객 이름·연락처를 가린 채 이어집니다. 그날 무엇이 바뀌었는지"
                "(앱·펌웨어 업데이트, 출시, 캠페인 등) 단서를 문의 내용에서 확인해 보세요.",
            ],
            "prompt": P_INSIGHT,
            "shots": [
                {"stem": "ag_6v_26_always", "viewport": [525, 756],
                 "caption": "반복되는 승인 — 대화 단위로 허용하려면 두 번째 옵션",
                 "callouts": [
                     {"box": [12, 489, 500, 76], "label": "Allow using this MCP tool? · bigquery/execute_sql_readonly",
                      "pos": "above"},
                     {"box": [19, 602, 281, 25], "label": "Yes, and always allow in this conversation",
                      "pos": "above"},
                 ]},
                {"stem": "ag_6v_25_insight", "viewport": [525, 756],
                 "caption": "로봇청소기 앱 연결 문의 — 2026-10-14부터 급증",
                 "callouts": [
                     {"box": [20, 342, 472, 55], "label": "1. 로봇청소기 '앱 연결' 일자별 문의 추이 · 2026-10-14부터 급증",
                      "pos": "above"},
                     {"box": [20, 424, 470, 64], "label": "2026-10-14 (급증 시작일) … 기간 내 총 33건", "pos": "below"},
                 ]},
            ],
            "tip": "원인을 찾을 때는 *주별 → 일자별 → 실제 문의 내용*처럼 단계적으로 좁혀 달라고 하세요. 날짜가 특정되면 그날 "
                   "무슨 일이 있었는지 다른 팀에 바로 물어볼 수 있습니다.",
        },
        {
            "title": "스킬을 MCP로 업그레이드하고 다시 실행",
            "body": [
                "Lab 5에서 만든 **voc-weekly-report** 스킬(`.agents/skills/voc-weekly-report/SKILL.md`)은 아직 CSV를 읽어 "
                "보고서를 만듭니다. 이제 데이터 원본을 BigQuery로 바꿉니다. 새 대화에서 아래 프롬프트를 보냅니다.",
                "에이전트는 스킬 파일과 스크립트, 지난 보고서를 읽은 뒤 `SKILL.md`를 고쳤습니다(약 **3분**, **1 file changed "
                "+57 −16**). 채팅에 정리된 변경 내용은 세 가지입니다.",
                "- **BigQuery MCP 데이터 조회 절차로 변경** — 로컬 CSV 스크립트 대신 `lab.env`의 `PROJECT_ID`를 확인하고 "
                "BigQuery MCP(`bigquery` 서버의 `execute_sql_readonly`)로 `cymbal_cx.voc_tickets`의 최신 데이터를 조회(예시 "
                "SQL 포함)",
                "- **데이터 출처 표기 변경** — 보고서 맨 아래를 `데이터 출처: BigQuery cymbal_cx.voc_tickets | 기준일: "
                "YYYY-MM-DD` 형식으로",
                "- **상대 경로 링크 적용** — 문서 안의 파일 링크를 `[lab.env](../../../lab.env)` · "
                "`[AGENTS.md](../../../AGENTS.md)`처럼 상대 경로로(다른 사람 컴퓨터에서도 링크가 깨지지 않습니다)",
                "편집기의 변경 내용을 확인하고 **Accept all**을 누릅니다.",
                "이제 업그레이드한 스킬을 실행합니다. 새 대화 입력창에 `/voc`를 입력하면 슬래시 메뉴에 **voc-weekly-report** "
                "스킬이 나옵니다. 고른 뒤 이어서 아래 **실행 프롬프트**를 입력해 보냅니다.",
                "에이전트는 스킬의 절차대로 `SKILL.md`와 `lab.env`를 읽고 BigQuery MCP 도구를 불렀습니다(녹화에서는 승인 네 "
                "번). 약 **1분 30초** 뒤 `reports/voc_weekly_report_2026-10-19.md`가 다시 만들어졌습니다. 채팅의 요약 맨 "
                "위에는 *[긴급/안전 이슈 최우선 보고]* — 안전 이슈 6건(전주 2건 대비 +4건, +200.0%), 6건 모두 공기청정기 전원 "
                "어댑터 관련, 전 건 미완료(접수 3 · 처리중 3)가 나옵니다.",
                "바뀐 줄은 **데이터 출처 한 줄**뿐입니다(**+1 −1**): `데이터 출처: data/voc_tickets.csv (또는 BigQuery …)` → "
                "`데이터 출처: BigQuery cymbal_cx.voc_tickets | 기준일: 2026-10-25`. BigQuery에 같은 데이터를 올렸기 때문에 "
                "숫자는 그대로입니다 — CSV로 만든 보고서와 숫자가 같다는 것이 곧 *데이터가 제대로 연결됐다*는 검증입니다. "
                "**Accept all**로 확정합니다.",
            ],
            "prompt": P_SKILL,
            "code": {"lang": "text", "label": "실행 프롬프트 — 새 대화에서 /voc로 voc-weekly-report를 고른 뒤 이어서 입력",
                     "text": P_RUN},
            "shots": [
                {"stem": "ag_6v_27_skill_done", "viewport": [525, 756],
                 "caption": "SKILL.md 수정 요약 — BigQuery MCP 조회 · 출처 표기 · 상대 경로 링크",
                 "callouts": [
                     {"box": [14, 133, 484, 142], "label": "1. BigQuery MCP 데이터 조회 절차로 변경", "pos": "above"},
                     {"box": [14, 278, 484, 174], "label": "2. 데이터 출처 표기 변경 · 3. 상대 경로 링크 적용",
                      "pos": "below"},
                     {"box": [412, 639, 74, 26], "label": "Accept all", "pos": "above"},
                 ]},
                {"stem": "ag_6v_28_slash", "viewport": [525, 450],
                 "caption": "/voc → 슬래시 메뉴의 voc-weekly-report 스킬",
                 "callouts": [
                     {"box": [20, 272, 482, 26], "label": "voc-weekly-report", "pos": "above"},
                     {"box": [24, 326, 40, 21], "label": "/voc", "pos": "below"},
                 ]},
                {"stem": "ag_6v_17_run_done",
                 "caption": "다시 만든 보고서 — 바뀐 줄은 데이터 출처 한 줄(CSV → BigQuery)",
                 "callouts": [
                     {"box": [104, 419, 494, 39], "label": "데이터 출처 → BigQuery cymbal_cx.voc_tickets | 기준일: 2026-10-25",
                      "pos": "below"},
                     {"box": [946, 466, 452, 132], "label": "안전 이슈 6건 · +4건(+200.0%)", "pos": "above"},
                     {"box": [1327, 669, 73, 26], "label": "Accept all", "pos": "above"},
                 ]},
            ],
            "tip": "스킬과 문서 안의 링크는 **상대 경로**로 쓰세요. `file:///…` 같은 절대 경로는 내 컴퓨터에서만 열리고, "
                   "팀원과 공유하면 깨집니다.",
            "note": "실습 데이터는 4주치 고정 데이터라 숫자가 바뀌지 않지만, 실제 운영에서는 BigQuery에 매일 새 문의가 "
                    "쌓이므로 같은 스킬을 다시 실행하기만 하면 최신 보고서가 나옵니다. Lab 7에서는 이 스킬과 BigQuery "
                    "데이터로 임원 보고 슬라이드를 만듭니다.",
        },
    ],
    "check": [
        "lab.env를 내 프로젝트 값으로 채우고 setup/load_to_bigquery.sh로 BigQuery에 300건을 올렸다",
        "MCP Store에서 BigQuery MCP를 설치하고 Tools 탭에서 도구와 켜기/끄기 스위치를 확인했다",
        "Manage MCP Servers에서 BigQuery 9 / 9 도구가 켜진 것을 확인했다",
        "Allow using this MCP tool? 카드에서 도구 이름과 Tool arguments를 보고 허용했다",
        "MCP 도구로 지난주 분류별 문의를 조회했다 (91건, 안전 이슈 6건)",
        "로봇청소기 앱 연결 문의가 2026-10-14부터 급증한 것을 데이터에서 찾았다",
        "voc-weekly-report 스킬을 BigQuery MCP로 고치고 /voc-weekly-report로 보고서를 다시 만들었다",
    ],
    "more": [
        "BigQuery MCP로 지난주(2026-10-19 ~ 2026-10-25) 공기청정기 안전 이슈 문의를 모두 조회해서 접수일 · 상태 · 문의 요약 표로 "
        "보여 주세요. 고객 이름·연락처는 가리고, 아직 미완료인 건을 맨 위에 두세요.",
        "BigQuery MCP로 에어폴 프로 문의를 주별로 조회하고, 구매 문의 안에서 어떤 질문(가격 · 출시일 · 단체 구매 등)이 많은지 "
        "문의 내용을 분류해 알려 주세요.",
        "/voc-weekly-report 지난 4주(2026-09-28 ~ 2026-10-25) 주별 보고서의 핵심 숫자를 BigQuery 데이터로 한 표에 모아 주세요. "
        "Lab 7 임원 보고 슬라이드의 재료로 쓰겠습니다.",
    ],
}
