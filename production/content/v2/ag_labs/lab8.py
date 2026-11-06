# -*- coding: utf-8 -*-
"""AG Lab 8 — VOC 분석 에이전트 — ADK (cymbal-voc 스토리 Week 2, Lab 7의 임원 보고 슬라이드에 이어 요청서 3번).

REAL recordings (1440x810 CSS, Antigravity agent IDE desktop app; Lab 8 agent panel x 915–1440):
  ag8v_create · ag8v_tools · ag8v_run (re-recorded 2026-10-28 11:42, 280 s) · ag8v_eval · ag8v_score
  (ag8v_score = the HTML report written by `agents-cli eval run`, opened in a headless browser, page content only,
  2880x1620 frames, css_scale 2).
Every callout box below is measured — DOM boxes from production/assets/shots/<stem>.boxes.json (targets / leaves),
recording event boxes, or Apple Vision OCR of the still / recording frame. Never eyeballed.

Observed in the recordings (times = recording seconds; do not over-claim):
- CREATE: new chat → prompt (submit 15.2 s) → Explored 1 file · `agents-cli create --help` (39–56 s) → commands that
  read the CLI's own files (65–138 s, local paths → cut) → 'Ran 7 commands' → answer 'Worked for 2m' at 155.9 s:
  lab.env PROJECT_ID · REGION used; 생성된 프로젝트 설정 요약 = 경로 cymbal-voc-agent · 템플릿 adk (app/agent.py) ·
  GCP 프로젝트 ID (.env) · 배포 대상 및 리전 agent_runtime / us-central1 (agents-cli-manifest.yaml) · 구성 모드
  프로토타입(최소 구성, --prototype). Generated folder (rec workspace): app/(agent.py, fast_api_app.py, app_utils),
  tests/(unit, integration, eval), deployment/, agents-cli-manifest.yaml, .env, GEMINI.md, README.md, Dockerfile,
  pyproject.toml, uv.lock.
- TOOLS: new chat → prompt (submit 18.2 s) → reads GEMINI.md, lab.env, voc_tickets.csv, app/agent.py, tests; searched
  google-cloud-bigquery → 'Allow using this MCP tool?' bigquery/execute_sql_readonly ① weekly counts SQL (143–146 s)
  ② ticket list SQL (207–211 s), both 'Yes, allow this time' → Submit → Edited agent.py (+422 −26), test_dummy.py
  (+60 −3) → `uv run pytest tests/unit/test_dummy.py -v` → answer 'Worked for 5m' at ≈366 s: '…가상환경 구성 및 단위
  테스트(BigQuery 도구 실행 검증)가 완료되는 대로 결과를 확인하겠습니다.' (test result itself not shown) →
  '2 Files With Changes' → Accept all (422.9 s). Code excerpt = the real app/agent.py written in this take (rec
  workspace, unchanged after 11:11): MODEL "gemini-3.7-flash", mask_name / mask_phone, get_weekly_summary,
  list_urgent_tickets, root_agent(tools=[…]).
- RUN (new take): prompt submit 15.7 s → `…/work/cymbal-voc $ agents-cli run "…"` → 'Error: No agents-cli-manifest.yaml
  found in the current directory or its parents.' (55.5 s) → re-run in cymbal-voc-agent (69 s) → local server did not
  start within 30 s (agent: '첫 번째 실행에서 로컬 서버 구동이 30초 내에 완료되지 않아 타임아웃 오류가 발생했습니다') →
  `agents-cli run --help` → run again (149 s) → 'Run agents-cli with user query finished' → answer streams 190–226 s:
  '1. 전체 CLI 실행 출력 (원문 그대로)': Local server started on port …, [user]: 지난주 긴급 문의 중 아직 처리 안 된 건
  알려 줘, [root_agent]:, [tool_call: list_urgent_tickets({"only_open": true})], [tool_response: list_urgent_tickets ->
  {"project_id": …, "only_open": true, "total_count": 6, "open_count": 6, "completed_count": 0, "tickets": […]}] →
  Markdown answer '## 🚨 [긴급/안전 이슈] 미처리 긴급 문의 현황 (총 6건)' + table CX-2610-0259 / 0235 / 0225 / 0223 /
  0211 / 0210 (masked 이*은 010-****-8470 …) + '주요 현황 요약' + '데이터 출처: BigQuery cymbal_cx.voc_tickets | 기준일:
  2026-10-25' → 'Local server stopped.' → '2. 에이전트의 답변 렌더링 화면' (same answer rendered in the chat; its 10-column
  table is squeezed to one character per line in the narrow panel → kept out of frame).
  = voc_facts open_urgent_ticket_ids (6).
- EVAL: new chat → prompt (submit 8.6 s) → reads eval_config.yaml / basic-dataset.json / response_quality.py …, checks
  tool outputs (`uv run python -c "from app.agent import get_weekly_summary …"`), `agents-cli eval run --help` →
  basic-dataset.json: template cases greeting / weather_query → weekly_summary / urgent_open_tickets (+ a 3rd case) →
  `agents-cli eval run` (173 s; the agent ended its turn at 204 s while the eval ran) → result answer at ≈494 s:
  CAUTION '🚨 [긴급/안전 이슈 최우선 확인 결과] agents-cli eval run 평가 결과, 3개 평가 케이스 모두에서 …
  6건(전주 2건 대비 +4건, +200.0% 급증, 전 건 미완료: 접수 3건·처리중 3건)이 답변 최상단에 최우선 강조되었으며,
  고객 개인정보(…) 마스킹 규칙도 100% 준수되었습니다.' → Accept all (551.5 s).
- SCORE (report HTML): Summary Metrics custom_response_quality Mean Score 5.0000, Std. Dev. 0.0000; Case #0 trace
  Function Call get_weekly_summary {"week_start": "2026-10-19"} → Tool Output → answer (91건, 전주 79건 대비 +12건
  (+15.2%), 안전 이슈 6건 …) → Evaluation Metrics custom_response_quality 5.00 + rationale; Case #1 Final Response
  총 6건(접수 3건, 처리중 3건) + masked 6-ticket table.

Hygiene (customer material shows no local paths / internal environment details):
- Cut: create 65–138 s ('Analyzed <local path>' rows, commands with local paths), tools 36–59 s, eval 21–59 s,
  run 0–8 s (previous conversation with a project number), eval 244–493 s (a retry caused by the recording machine's own network setup —
  cut, not explained anywhere). The agent sentence about that retry stays at y 387–408 in the eval panel until the end →
  every zoom window / crop of the eval result starts below y 457.
- Empty-editor product watermark (eval 0–163 s) → zoom windows start right of x 700.
- the recording's project id = the lab's test project (same precedent as Lab 6) — note in the text; commands use lab.env variables.

Derived stills (crops, 2 image px per CSS px — `viewport` = crop size; provenance in <stem>.boxes.json, recipe:
scratch/derive8b.py of the Lab 8 writer):
- ag_8v_01a_creating = ag_8v_01_creating crop x 915–1440, y 30–387 (stops above the local-path row at y 393.5)
- ag_8v_02a_created  = ag_8v_02_created crop x 915–1440, y 170–464
- ag_8v_03b_mcp      = ag8v_tools frame @145.6 s (1920x1080 → 2880x1620 LANCZOS) crop x 915–1440, y 250–775
- ag_8v_04a_tools    = ag_8v_04_tools crop x 915–1440, y 190–736
- ag_8v_05a_toollog  = ag8v_run frame @193.76 s (upscaled) crop x 915–1440, y 150–591
- ag_8v_06a_table    = ag8v_run frame @216.46 s (upscaled) crop x 915–1440, y 150–591
- ag_8v_06b_summary  = ag_8v_06_run_result crop x 915–1440, y 400–652 (the squeezed table ends at y 377.5)
- ag_8v_08a_dataset  = ag8v_eval frame @553.06 s (after Accept all — the accepted file without the inline diff
                       widget, upscaled) crop x 330–915, y 30–615
- ag_8v_08b_caution  = ag8v_eval frame @553.06 s (after Accept all, upscaled) crop x 915–1440, y 462–714
"""

P_CREATE = ("agents-cli로 cymbal-voc-agent라는 ADK 에이전트 프로젝트를 만들어 주세요. lab.env의 PROJECT_ID와 REGION을 쓰고, "
            "배포 대상은 Agent Runtime, 프로토타입(최소 구성)으로요.")
P_TOOLS = ("cymbal-voc-agent에 BigQuery cymbal_cx.voc_tickets를 조회하는 도구 2개를 넣어 주세요. "
           "get_weekly_summary(week_start): 분류별·제품별 건수와 전주 대비 증감, list_urgent_tickets(only_open): 안전 이슈 "
           "긴급 문의 목록(고객 이름·연락처 마스킹). 에이전트 지침은 한국어로, AGENTS.md 규칙을 따르게 하고, 프로젝트 ID는 "
           "lab.env에서 읽어 주세요.")
P_RUN = ("agents-cli run으로 '지난주 긴급 문의 중 아직 처리 안 된 건 알려 줘'를 보내고, 명령을 백그라운드로 돌리지 말고 "
         "끝날 때까지 기다렸다가 도구 호출 내용과 에이전트의 답변을 그대로 보여 주세요.")
P_EVAL = "평가 케이스 3개(주간 요약 · 미처리 긴급 문의 · 제품별 질문)를 만들고 agents-cli eval run으로 평가한 뒤 결과를 요약해 주세요."

PREP = """# 실습 폴더(cymbal-voc)에서 — 새 터미널을 열 때마다 변수 불러오기
source lab.env

# 1) agents-cli 설치 (uv가 필요합니다)
uv tool install google-agents-cli
agents-cli --version

# 2) Google Cloud 로그인(ADC)과 할당량 프로젝트 지정
gcloud auth application-default login
gcloud auth application-default set-quota-project "${PROJECT_ID}"

# 3) 에이전트가 Gemini 모델을 쓰도록 Vertex AI API 켜기
gcloud services enable aiplatform.googleapis.com --project "${PROJECT_ID}\""""

TREE = """cymbal-voc-agent/
├── app/
│   ├── agent.py              # 에이전트 본체 — 모델 · 지침 · 도구
│   ├── fast_api_app.py       # 로컬 실행 · 배포용 서버
│   └── app_utils/
├── tests/                    # unit · integration · eval(평가 데이터셋)
├── deployment/
├── agents-cli-manifest.yaml  # 템플릿 · 배포 대상 · 리전
├── .env                      # 프로젝트 ID 같은 실행 설정
├── GEMINI.md · README.md     # 코딩 에이전트용 안내 · 사용법
├── Dockerfile
└── pyproject.toml · uv.lock  # 파이썬 패키지 목록"""

AGENT_PY = '''MODEL = "gemini-3.7-flash"

def mask_name(name: str | None) -> str:
    """고객 이름의 가운데 글자를 '*'로 마스킹합니다. (예: 김민수 -> 김*수, 이산 -> 이*)"""
    ...

def mask_phone(phone: str | None) -> str:
    """연락처 가운데 4자리를 '****'로 마스킹합니다. (예: 010-1234-5678 -> 010-****-5678)"""
    ...

def get_weekly_summary(week_start: str = "") -> dict[str, Any]:
    """BigQuery cymbal_cx.voc_tickets 테이블에서 주간 VOC 분류별·제품별 건수와 전주 대비 증감을 조회합니다."""
    ...

def list_urgent_tickets(only_open: bool = False) -> dict[str, Any]:
    """BigQuery cymbal_cx.voc_tickets 테이블에서 안전 이슈 및 긴급 문의 목록을 조회합니다.
    고객 이름(customer_name)과 연락처(phone)는 AGENTS.md 규칙에 따라 마스킹하여 반환합니다."""
    ...

root_agent = Agent(
    name="root_agent",
    model=Gemini(model=MODEL, ...),
    instruction=AGENT_INSTRUCTION,   # 한국어 지침: AGENTS.md 규칙 6가지 + 도구 사용 지침
    tools=[get_weekly_summary, list_urgent_tickets],
)'''

RUN_MANUAL = """# 직접 실행해 보기 — 반드시 프로젝트 폴더에서
cd cymbal-voc-agent
agents-cli run "지난주 긴급 문의 중 아직 처리 안 된 건 알려 줘\""""

RUN_TABLE = """티켓 ID        접수일자    고객명  연락처          상태    채널    지역
CX-2610-0259  2026-10-22  이*은   010-****-8470  처리중  이메일  강원·제주
CX-2610-0235  2026-10-21  김*원   010-****-3634  처리중  앱      수도권
CX-2610-0225  2026-10-20  권*윤   010-****-3389  접수    이메일  수도권
CX-2610-0223  2026-10-20  정*서   010-****-3251  접수    채팅    수도권
CX-2610-0211  2026-10-19  홍*준   010-****-1007  접수    채팅    충청
CX-2610-0210  2026-10-19  김*원   010-****-5027  처리중  채팅    수도권"""

LAB = {
    "id": "lab8", "no": 8, "level": "심화", "minutes": 35, "video": "ag8",
    "title": "VOC 분석 에이전트 — ADK",
    "subtitle": "agents-cli 생성 · BigQuery 도구 · run · eval",
    "goal": "Lab 7에서 **임원 보고 슬라이드**까지 만들었습니다. 이번에는 요청서 3번 **VOC 도우미**입니다. CX팀원 누구나 "
            "*'지난주 긴급 문의 알려 줘'*처럼 물으면 BigQuery 데이터로 답하는 에이전트를 **Google ADK**로 만듭니다. "
            "**agents-cli로 프로젝트 만들기 → BigQuery 도구 2개 붙이기 → `agents-cli run`으로 실행해 도구 호출 확인 → "
            "`agents-cli eval`로 평가하고 보고서에서 점수 확인**까지, 코드는 Antigravity 에이전트에게 맡기고 우리는 *결과를 "
            "눈으로 확인*합니다. 여기서 만든 `cymbal-voc-agent`는 Lab 9에서 배포해 Gemini Enterprise에 게시합니다.",
    "steps": [
        {
            "title": "agents-cli로 ADK 에이전트 프로젝트 만들기",
            "body": [
                "**준비(처음 한 번)** 터미널에서 실습 폴더(`cymbal-voc`)로 이동해 아래 첫 번째 코드를 실행합니다. "
                "`agents-cli`(ADK 에이전트를 만들고 · 실행하고 · 평가하고 · 배포하는 명령줄 도구)를 설치하고, 에이전트가 "
                "Gemini 모델과 BigQuery를 쓸 수 있도록 Google Cloud에 로그인(ADC)한 뒤 Vertex AI API를 켭니다. 값은 Lab 6에서 "
                "채운 `lab.env`에서 읽습니다. `uv`가 없다면 [uv 설치 안내](https://docs.astral.sh/uv/getting-started/installation/)를 "
                "따라 먼저 설치하세요.",
                "Agent 패널 오른쪽 위 **+**(새 대화)를 누르고 아래 프롬프트를 보냅니다. 배포 대상(**Agent Runtime**)과 "
                "**프로토타입**(최소 구성)을 미리 적어 두면, Lab 9의 배포 설정까지 한 번에 맞춰집니다.",
                "에이전트는 먼저 `agents-cli create --help`로 쓸 수 있는 옵션을 확인하고, `lab.env`의 `PROJECT_ID` · `REGION` "
                "값으로 프로젝트를 만들었습니다. 녹화에서는 프롬프트를 보내고 **약 2분 20초** 만에 끝났습니다(답변 위에는 "
                "**Worked for 2m**). 답변의 **생성된 프로젝트 설정 요약**을 확인하세요.",
                "- **경로** `cymbal-voc-agent` — 실습 폴더 안에 새 폴더가 생김",
                "- **템플릿** `adk` — 에이전트 본체는 `app/agent.py`",
                "- **GCP 프로젝트 ID** `lab.env`의 값이 `.env`에 들어감",
                "- **배포 대상 및 리전** `agent_runtime` / `us-central1` — `agents-cli-manifest.yaml`에 기록",
                "- **구성 모드** 프로토타입(최소 구성, `--prototype`)",
                "만들어진 폴더 구조는 아래 두 번째 코드와 같습니다. 다음 STEP에서 도구를 넣을 파일은 `app/agent.py` 하나입니다.",
            ],
            "prompt": P_CREATE,
            "code": [
                {"lang": "bash", "label": "준비 — agents-cli 설치 · ADC 로그인 · Vertex AI API", "text": PREP},
                {"lang": "text", "file": "cymbal-voc-agent/ (생성된 구조)", "text": TREE},
            ],
            "shots": [
                {"stem": "ag_8v_01a_creating", "viewport": [525, 357],
                 "caption": "먼저 agents-cli create --help로 옵션을 확인",
                 "callouts": [
                     {"box": [20, 186, 224, 26], "label": "Ran agents-cli create --help", "pos": "above"},
                 ]},
                {"stem": "ag_8v_02a_created", "viewport": [525, 294],
                 "caption": "약 2분 20초 뒤 — 생성된 프로젝트 설정 요약",
                 "callouts": [
                     {"box": [20, 118, 484, 172], "label": "생성된 프로젝트 설정 요약", "pos": "above"},
                 ]},
            ],
            "tip": "명령으로 직접 만들 수도 있습니다: `source lab.env` → `export GOOGLE_CLOUD_PROJECT=\"${PROJECT_ID}\"` → "
                   "`agents-cli create cymbal-voc-agent -a adk -d agent_runtime --prototype --region \"${REGION}\"`. "
                   "녹화에서 에이전트도 같은 옵션(템플릿 adk · 배포 대상 agent_runtime · 프로토타입)으로 만들었습니다.",
            "note": "녹화 화면의 프로젝트 ID는 실습용 테스트 프로젝트 값입니다. 여러분 화면에는 `lab.env`에 적은 "
                    "**내 프로젝트 ID**가 보여야 합니다.",
        },
        {
            "title": "BigQuery 도구 2개 붙이기 — 주간 요약 · 긴급 문의",
            "body": [
                "이제 에이전트가 쓸 **도구**(tool)를 만듭니다. 도구는 에이전트가 질문에 답하려고 필요할 때 부르는 파이썬 "
                "함수입니다. **새 대화**를 열고 아래 프롬프트를 보냅니다. *도구 이름 · 인자 · 돌려줄 내용 · 지킬 규칙*"
                "(마스킹 · 한국어 · `lab.env`)을 함께 적는 것이 요령입니다.",
                "에이전트는 `GEMINI.md` · `lab.env` · `voc_tickets.csv` · `app/agent.py` · 테스트 파일을 읽고 BigQuery 파이썬 "
                "라이브러리 사용법을 찾아본 뒤, Lab 6에서 연결한 **BigQuery MCP**로 실제 테이블을 조회해 봅니다. 이때 "
                "**Allow using this MCP tool?** 카드가 뜹니다. **Tool arguments**의 SQL(주별 전체 · 안전 이슈 · 긴급 · 미완료 "
                "건수)을 읽고 **Yes, allow this time** → **Submit**을 누르세요. 녹화에서는 긴급 문의 목록을 조회하는 두 번째 "
                "카드까지 두 번 승인했습니다.",
                "확인이 끝나면 `app/agent.py`에 도구 두 개와 한국어 지침을 넣고(+422 −26), 단위 테스트 파일"
                "(`tests/unit/test_dummy.py`, +60 −3)도 고친 뒤 테스트를 실행합니다. 프롬프트를 보내고 **약 6분** 뒤 답변이 "
                "끝났습니다(**Worked for 5m**). 만들어진 코드의 뼈대는 아래와 같습니다.",
                "- `get_weekly_summary(week_start)` 주별 전체 건수, 분류별 · 제품별 건수와 전주 대비 증감",
                "- `list_urgent_tickets(only_open)` 안전 이슈 · 긴급 문의 목록 — 고객 이름 · 연락처는 도구 안에서 마스킹해서 "
                "돌려줌(`mask_name` · `mask_phone`)",
                "- **지침(instruction)** 한국어로 답하고, AGENTS.md 규칙(마스킹 · 안전 이슈 맨 위 · 데이터 출처와 기준일 표시 "
                "등)을 지키며, 질문에 맞는 도구를 골라 부르도록",
                "답변은 *\"가상환경 구성 및 단위 테스트(BigQuery 도구 실행 검증)가 완료되는 대로 결과를 확인하겠습니다\"*로 "
                "끝났습니다. 테스트가 끝나기 전에 답변이 마무리된 것이라, 도구가 실제로 동작하는지는 **STEP 3에서 직접 실행**해 "
                "확인합니다. 변경 검토 바(**2 Files With Changes**)에서 두 파일을 확인하고 **Accept all**을 누릅니다.",
            ],
            "prompt": P_TOOLS,
            "code": {"lang": "python", "file": "cymbal-voc-agent/app/agent.py (녹화에서 만들어진 코드 — 발췌)",
                     "text": AGENT_PY},
            "shots": [
                {"stem": "ag_8v_03b_mcp", "viewport": [525, 525],
                 "caption": "Allow using this MCP tool? — SQL을 읽고 Yes, allow this time → Submit",
                 "callouts": [
                     {"box": [54, 143, 425, 98], "label": "query: SELECT … total_cnt · safety_cnt · urgent_cnt · open_cnt", "pos": "above"},
                     {"box": [36, 349, 131, 27], "label": "Yes, allow this time", "pos": "below"},
                     {"box": [425, 480, 87, 38], "label": "Submit", "pos": "above"},
                 ]},
                {"stem": "ag_8v_04a_tools", "viewport": [525, 546],
                 "caption": "약 6분 뒤 — agent.py · test_dummy.py 변경, Accept all",
                 "callouts": [
                     {"box": [25, 105, 163, 26], "label": "2 files changed +490 −37", "pos": "below"},
                     {"box": [21, 423, 413, 51], "label": "agent.py +422 −26 · test_dummy.py +60 −3", "pos": "above"},
                     {"box": [410, 479, 76, 26], "label": "Accept all", "pos": "below"},
                 ]},
            ],
            "tip": "에이전트가 BigQuery에서 무엇을 읽는지는 MCP 승인 카드의 SQL로 확인할 수 있습니다(Lab 7과 같은 원리). "
                   "같은 대화에서 승인이 여러 번 반복된다면 **Yes, and always allow in this conversation**을 골라도 됩니다.",
            "note": "카드의 `projectId` 값은 녹화용 테스트 프로젝트입니다. 에이전트가 쓰는 코드는 녹화와 조금 "
                    "다를 수 있습니다 — 도구 이름과 인자가 같으면 다음 STEP을 그대로 진행할 수 있습니다.",
        },
        {
            "title": "agents-cli run으로 실행 — 도구 호출 확인",
            "body": [
                "만든 에이전트에게 실제로 물어봅니다. **새 대화**에서 아래 프롬프트를 보냅니다. `agents-cli run \"질문\"`은 "
                "에이전트를 내 컴퓨터에서 실행해 답을 받아 오는 명령입니다(로컬 서버를 띄워 질문하고, 끝나면 서버를 닫습니다). "
                "*끝날 때까지 기다렸다가 도구 호출 내용과 답변을 그대로 보여 달라*고 적어야, 에이전트가 명령을 백그라운드에 맡겨 "
                "두고 답변을 먼저 끝내지 않습니다.",
                "녹화에서는 세 번 만에 성공했습니다. 처음에는 실습 폴더 맨 위(`cymbal-voc`)에서 실행해 **Error: No "
                "agents-cli-manifest.yaml found in the current directory or its parents.** 오류가 났고, 에이전트가 오류를 읽고 "
                "프로젝트 폴더(`cymbal-voc-agent`)에서 다시 실행했습니다. 두 번째에는 로컬 서버가 30초 안에 뜨지 않아 한 번 더 "
                "실행했고, 프롬프트를 보내고 **약 3분** 만에 결과가 나왔습니다.",
                "에이전트가 보여 준 **1. 전체 CLI 실행 출력 (원문 그대로)**에서 핵심은 두 줄입니다.",
                "- `[tool_call: list_urgent_tickets({\"only_open\": true})]` — 질문을 읽은 에이전트가 *미처리 긴급 문의* 도구를 "
                "`only_open=true`로 골라 불렀습니다",
                "- `[tool_response: list_urgent_tickets -> {… \"total_count\": 6, \"open_count\": 6, \"completed_count\": 0, …}]` — "
                "BigQuery에서 6건을 받아 왔고, 고객 이름 · 연락처는 도구 응답에서부터 마스킹되어 있습니다",
                "이어서 에이전트의 답변이 나옵니다. 지침대로 **🚨 [긴급/안전 이슈] 미처리 긴급 문의 현황 (총 6건)**이 맨 위에 "
                "오고, 6건 모두 공기청정기 어댑터(발열 · 연기 · 변형) 문의입니다. 표의 주요 열은 아래 세 번째 코드와 같습니다.",
                "답변 끝에는 **주요 현황 요약**(상태별 건수: 접수 3건, 처리중 3건 (총 6건) · 주요 내용: 공기청정기 어댑터의 과열, "
                "연기 발생 및 외관 변형 · 조치 권고사항: 즉시 사용 중단 안내 및 회수 · 교환)과 **데이터 출처: BigQuery "
                "cymbal_cx.voc_tickets | 기준일: 2026-10-25**가 붙습니다. Lab 4 대시보드의 '미완료 6건(접수 3 · 처리중 3)'과 같은 "
                "숫자입니다.",
            ],
            "prompt": P_RUN,
            "code": [
                {"lang": "bash", "label": "직접 실행해 보기", "text": RUN_MANUAL},
                {"lang": "text", "file": "agents-cli run 답변 — 미처리 긴급 문의 6건 (제품 · 심각도 · 문의 내용 열 생략)",
                 "text": RUN_TABLE},
            ],
            "shots": [
                {"stem": "ag_8v_05a_toollog", "viewport": [525, 441],
                 "caption": "CLI 실행 출력 — 질문 → tool_call → tool_response(total_count 6)",
                 "callouts": [
                     {"box": [34, 292, 299, 21], "label": "[user]: 지난주 긴급 문의 중 …", "pos": "above"},
                     {"box": [30, 331, 449, 60], "label": "tool_call list_urgent_tickets → total_count 6", "pos": "below"},
                 ]},
                {"stem": "ag_8v_06a_table", "viewport": [525, 441],
                 "caption": "에이전트의 답변 — 미처리 긴급 문의 6건 표(이름 · 연락처 마스킹)",
                 "callouts": [
                     {"box": [31, 100, 450, 326], "label": "CX-2610-0259 … 0210 — 6건", "pos": "above"},
                 ]},
                {"stem": "ag_8v_06b_summary", "viewport": [525, 252],
                 "caption": "답변 끝 — 주요 현황 요약과 데이터 출처 · 기준일",
                 "callouts": [
                     {"box": [20, 13, 478, 158], "label": "주요 현황 요약 · 데이터 출처", "pos": "below"},
                 ]},
            ],
            "tip": "`agents-cli run`은 `agents-cli-manifest.yaml`이 있는 **프로젝트 폴더**(`cymbal-voc-agent`)에서 실행하세요. "
                   "여러 번 물어볼 때는 `agents-cli run --start-server \"질문\"`으로 로컬 서버를 켜 둔 채 쓰면 다음 실행이 "
                   "빨라지고, 다 쓰면 `agents-cli run --stop-server`로 끕니다.",
            "note": "에이전트는 마지막에 같은 답변을 채팅용으로 한 번 더 그려 주는데(2. 에이전트의 답변 렌더링 화면), 열이 많은 "
                    "표는 좁은 Agent 패널에서 글자가 세로로 늘어서 보일 수 있습니다. 그럴 때는 패널을 넓히거나 위의 CLI 실행 "
                    "출력(원문)을 보세요.",
        },
        {
            "title": "agents-cli eval로 평가 — 케이스 3개",
            "body": [
                "한 번 맞게 답했다고 끝이 아닙니다. 지침이나 도구를 고칠 때마다 *같은 질문에 여전히 잘 답하는지* 확인하려면 "
                "**평가(eval)**를 만들어 둡니다. **새 대화**에서 아래 프롬프트를 보냅니다.",
                "에이전트는 `tests/eval/eval_config.yaml` · `tests/eval/datasets/basic-dataset.json` · `response_quality.py`를 "
                "읽고, 도구가 내놓는 숫자를 직접 확인한 뒤(`uv run python -c \"from app.agent import get_weekly_summary …\"`), "
                "템플릿의 예시 케이스(`greeting` · `weather_query`)를 VOC 케이스로 바꿨습니다. 케이스마다 **질문(prompt)**과 "
                "**기대 답변(reference)**이 들어갑니다.",
                "1. `weekly_summary` 지난주(2026-10-19 주간) VOC 전체 건수와 전주 대비 증감, 분류별 건수 요약",
                "2. `urgent_open_tickets` 현재 미처리(미완료) 상태인 긴급 · 안전 이슈 문의 목록",
                "3. 제품별 질문 — 프롬프트에서 요청한 세 번째 케이스",
                "`agents-cli eval run`은 데이터셋의 질문으로 에이전트를 실행(추론)한 뒤 답변을 채점합니다. 기본 지표 "
                "`custom_response_quality`는 **LLM이 채점자**가 되어 답변을 기대 답변과 비교해 1~5점을 매깁니다(LLM-as-judge).",
                "평가에는 몇 분이 걸립니다. 녹화에서는 에이전트가 평가를 실행해 두고 먼저 답변을 마친 뒤, 평가가 끝나자 결과를 "
                "정리했습니다(평가 실행부터 결과 요약까지 **약 5분**). 결과 요약 맨 위 **CAUTION** 상자에는 *3개 평가 케이스 "
                "모두에서 지난주(2026-10-19 ~ 2026-10-25) 공기청정기 어댑터 안전 이슈(긴급) 6건(전주 2건 대비 +4건, +200.0%, "
                "전 건 미완료: 접수 3건 · 처리중 3건)이 답변 최상단에 강조되었고, 고객 개인정보 마스킹 규칙도 100% "
                "지켜졌다*고 정리되었습니다.",
                "평가 데이터셋(`basic-dataset.json`) 등 바뀐 파일을 확인하고 **Accept all**을 누릅니다. 점수는 다음 STEP의 "
                "평가 보고서에서 확인합니다.",
            ],
            "prompt": P_EVAL,
            "shots": [
                {"stem": "ag_8v_08a_dataset", "viewport": [585, 585],
                 "caption": "basic-dataset.json — VOC 평가 케이스(질문 + 기대 답변)",
                 "callouts": [
                     {"box": [116, 109, 249, 24], "label": "eval_case_id: weekly_summary", "pos": "above"},
                     {"box": [174, 360, 335, 23], "label": "\"text\": \"[긴급/안전 이슈 최우선 안내] 지난주…\"", "pos": "below"},
                     {"box": [116, 487, 285, 24], "label": "eval_case_id: urgent_open_tickets", "pos": "above"},
                 ]},
                {"stem": "ag_8v_08b_caution", "viewport": [525, 252],
                 "caption": "약 5분 뒤 — 3개 케이스 평가 결과 요약(CAUTION)",
                 "callouts": [
                     {"box": [33, 43, 446, 150], "label": "CAUTION — 3개 케이스 결과 요약", "pos": "below"},
                 ]},
            ],
            "tip": "평가 케이스는 *팀원들이 실제로 물어볼 질문*으로 만드세요. Lab 7의 '더 해 보기'에서 뽑은 자주 묻는 질문이 "
                   "있다면 그대로 케이스로 쓸 수 있습니다.",
            "note": "점수는 LLM 채점자가 매기므로 실행할 때마다 조금 달라질 수 있습니다.",
        },
        {
            "title": "평가 보고서 열어 점수 확인",
            "body": [
                "`agents-cli eval run`은 채점 결과를 프로젝트 안 `artifacts/grade_results/` 폴더에 JSON과 **HTML 보고서**"
                "(`results_<날짜>_<시각>.html`)로 남깁니다. Explorer에서 `cymbal-voc-agent/artifacts/grade_results/results_….html`"
                "을 오른쪽 클릭 → **Reveal in Finder**로 폴더를 연 뒤, 파일을 브라우저로 여세요.",
                "맨 위 **Evaluation Report → Summary Metrics**에 `custom_response_quality` **Mean Score 5.0000 · Std. Dev. "
                "0.0000**이 보입니다. 5점 만점의 평균이 5.0이므로, 3개 케이스 모두 5점을 받았다는 뜻입니다.",
                "아래 **Detailed Results**에서 케이스별로 확인합니다.",
                "- **Case #0 (주간 요약)** Conversation Trace에 `Function Call: get_weekly_summary` "
                "`{\"week_start\": \"2026-10-19\"}` → `Tool Output` → 답변(전체 91건 · 전주 79건 대비 +12건(+15.2%) · 🚨 안전 "
                "이슈 6건(전주 2건, +4건 / +200.0%) · 앱 연결 24건 …)이 차례로 보이고, **Evaluation Metrics**에 "
                "`custom_response_quality` **5.00**과 채점 이유가 적혀 있습니다",
                "- **Case #1 (미처리 긴급 문의)** Final Response — 🚨 [긴급/안전 이슈] 미처리(미완료) 문의 현황: **총 6건**"
                "(접수 3건, 처리중 3건), 모두 공기청정기 어댑터 발열 · 연기 · 변형 관련. 마스킹된 6건 표(`이*은` · "
                "`010-****-8470` …)까지 STEP 3의 결과와 같습니다",
                "숫자도 직접 맞춰 보세요. 지난주 91건 · 전주 79건 · 안전 이슈 6건(전주 2건)은 Lab 4~7에서 확인한 숫자와 "
                "같습니다. 이것으로 Lab 9에서 배포할 VOC 분석 에이전트가 준비되었습니다.",
            ],
            "shots": [
                {"stem": "ag_8v_09_scores",
                 "caption": "Evaluation Report — Summary Metrics: custom_response_quality 평균 5.0000",
                 "callouts": [
                     {"box": [117, 241, 1206, 50], "label": "custom_response_quality · Mean 5.0000", "pos": "below"},
                 ]},
                {"stem": "ag_8v_10_trace",
                 "caption": "Case #0 — get_weekly_summary 호출과 채점 결과 5.00",
                 "callouts": [
                     {"box": [212, 19, 457, 118], "label": "Function Call · get_weekly_summary", "pos": "below"},
                     {"box": [166, 686, 1108, 27], "label": "custom_response_quality 5.00", "pos": "above"},
                 ]},
                {"stem": "ag_8v_11_case1",
                 "caption": "Case #1 — 미처리 긴급 문의 총 6건과 마스킹된 목록",
                 "callouts": [
                     {"box": [144, 188, 1152, 48], "label": "총 6건 — 접수 3건 · 처리중 3건", "pos": "above"},
                     {"box": [147, 405, 1146, 405], "label": "CX-2610-0259 · 0235 · 0225 · 0223 · 0211 …", "pos": "above"},
                 ]},
            ],
            "tip": "Evaluation Metrics 아래의 채점 이유를 읽으면 감점 이유를 알 수 있습니다. 점수가 낮은 케이스가 있으면 "
                   "\"Case #N의 채점 이유를 읽고 지침을 고쳐 줘\"처럼 에이전트에게 맡긴 뒤 다시 평가하세요.",
            "note": "보고서의 도구 출력에 보이는 `project_id` 값은 녹화용 테스트 프로젝트입니다. 녹화에서는 "
                    "보고서 파일을 브라우저로 열어 페이지 내용만 캡처했습니다.",
        },
    ],
    "check": [
        "agents-cli를 설치하고 ADC 로그인과 Vertex AI API를 준비했다",
        "agents-cli로 cymbal-voc-agent 프로젝트(템플릿 adk · 배포 대상 agent_runtime · 프로토타입)를 만들었다",
        "get_weekly_summary · list_urgent_tickets 도구를 넣고, MCP 승인 카드의 SQL을 읽고 허용했다",
        "agents-cli run 출력에서 tool_call(list_urgent_tickets)과 미처리 긴급 문의 6건을 확인했다",
        "평가 케이스 3개로 agents-cli eval run을 실행하고 결과 요약을 확인했다",
        "HTML 평가 보고서에서 custom_response_quality 평균 5.0과 케이스별 채점 이유를 확인했다",
    ],
    "more": [
        "agents-cli run으로 '지난주 VOC 요약해 줘'를 보내고, 끝날 때까지 기다렸다가 어떤 도구가 어떤 인자로 호출됐는지와 에이전트의 답변을 그대로 보여 주세요.",
        "cymbal-voc-agent에 '제품 × 분류' 주별 건수를 조회하는 도구를 하나 더 넣고, '로봇청소기 앱 연결 문의가 4주 동안 어떻게 늘었는지 알려 줘' 평가 케이스를 추가해서 agents-cli eval run으로 다시 평가해 주세요.",
        "다음 Lab에서 이 에이전트를 Agent Runtime에 배포하려고 합니다. agents-cli deploy 전에 확인할 것(프로젝트 · 리전 · 권한 · 비용)을 체크리스트로 정리해 주세요. 아직 배포는 하지 마세요.",
    ],
}
