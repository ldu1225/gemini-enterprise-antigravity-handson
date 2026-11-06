# -*- coding: utf-8 -*-
"""AG Lab 9 — 배포 + Gemini Enterprise 게시 (cymbal-voc 스토리 Week 2, Lab 8의 cymbal-voc-agent에 이어서).

REAL recordings (Antigravity agent IDE desktop app, window 1440x810 CSS, Always Proceed since Lab 4):
ag9v_deploy (2026-10-28) · ag9v_iam (2026-10-29) · ag9v_publish (2026-10-28) — each a NEW conversation — and the REAL
Gemini Enterprise web app in Chrome (ag9v_ge_use, 2026-10-29, 1440x810 @2x). Stills ag_9v_* are 2880x1620 → CSS 1440x810.
Every callout box is measured: DOM leaves of production/assets/shots/<stem>.boxes.json (unions of leaves for blocks) or
Apple Vision OCR (production/qa/find_text.py). Never eyeballed.

Derived stills (real pixels, crops only — scratch/make_l9_stills.py of the writer conversation):
- ag_9v_07c_ge_answer      = ag_9v_07_ge_answer crop [455, 88, 780, 512]   (viewport 780x512, boxes = leaves − origin)
- ag_9v_08c_ge_answer_more = ag_9v_08_ge_answer_more crop [455, 104, 780, 520]
- ag_9v_02d_iam_done       = ag9v_iam frame @175.79 s (004044.jpg, 1920x1080 → 2880x1620 LANCZOS) crop [340, 0, 1100, 585]
  (no 2x still of the IAM answer is usable: ag_9v_02b shows an 'Analyzed <local path>' row, ag_9v_02c shows another lab's
  leftover files in the change list + explorer and a red label under the input box; the frame @175.79 is the last one
  before the service-account address streams in, and after the raw markdown link (174.68–175.02 s) was rendered.)

Observed in the recordings (do not over-claim):
- DEPLOY (prompt P_DEPLOY, submit 19.6 s): agent read lab.env · 요청서 · cymbal-voc-agent, ran `agents-cli deploy --help`,
  `agents-cli deploy --status && agents-cli deploy --list …` ('현재 배포 상태를 확인하고 있습니다'), read
  deployment_metadata.json · Dockerfile · deployment/terraform · fast_api_app.py · agent.py, `agents-cli deploy --list`
  ('기존 Agent Runtime 배포 목록을 조회하고 있습니다'), `agents-cli deploy --dry-run …` + GET of the existing reasoningEngine
  ('배포 설정과 Agent Runtime 리소스 정보를 확인하고 있습니다'), then ~263 s `source ../lab.env && agents-cli deploy --project
  "$PROJECT_ID" --region "$REGION" --no-confirm-project`. ~281 s (≈ 4분 20초 after the request) its last message:
  '… agents-cli deploy 명령을 실행하여 cymbal-voc-agent를 Agent Runtime에 배포하고 있습니다. 배포가 완료될 때까지 대기한 뒤
  필요한 BigQuery IAM 권한을 부여하겠습니다.' — and the turn ENDED there; the deploy kept running in a terminal (blue dot on
  the terminal icon of the agent panel toolbar). The IAM part was therefore asked in a new conversation (take 2).
  deployment_metadata.json (lead): remote_agent_runtime_id projects/<number>/locations/us-central1/reasoningEngines/<id>,
  deployment_target agent_runtime. The deploy's own completion output is NOT in the recording → never shown/claimed.
- IAM (P_IAM, submit 15.7 s): read deployment_metadata.json, lab.env, README, GEMINI.md, agents-cli-manifest.yaml,
  terraform (iam.tf, service.tf, variables.tf …); `gcloud projects add-iam-policy-binding` ×2 (dataViewer, jobUser) for
  the runtime's effectiveIdentity service-<number>@gcp-sa-aiplatform-re.iam.gserviceaccount.com; a dataset-level try
  (`bq add-iam-policy-binding`) failed with 'This feature requires allowlisting' → it checked the dataset ACL instead
  (projectReaders READER); `Edited variables.tf +2 −0` (app_sa_roles). Answer from ~174 s: '… IAM 권한 부여 및 확인을
  완료했습니다' → 1) Agent Runtime·서비스 계정 확인 2) 부여 명령(bash) 3) get-iam-policy 결과 표 + 데이터셋 ACL.
  Then Accept all (240.4 s) — NOT shown: the change list there also lists another lab's leftover files.
- PUBLISH (P_PUBLISH, submit 23.9 s): `agents-cli publish gemini-enterprise --help`, read lab.env ·
  deployment_metadata.json · agent.py · GEMINI.md · agents-cli-manifest.yaml · README, ~166 s `source ../lab.env &&
  agents-cli publish gemini-enterprise --gemini-enterprise-app-id "projects/${PROJECT_NUMBER}/locations/${GE_LOCATION}/
  collections/default_collection/engines/${GE_APP_ID}" --display-name "${GE_DISPLAY_NAME}" --description "Cymbal
  고객경험(CX)팀의 VOC(고객의 소리) 분석 에이전트입니다. …"` (rest of the block is cut off on screen), ~210 s 'Publish
  cymbal-voc-agent to Gemini Enterprise finished', ~216 s result table: GE 앱 리소스 · 연결된 Agent Runtime ·
  등록된 에이전트 리소스 이름 (…/agents/11781391963813115024) · 등록 방식 adk (상태: created) · 콘솔 확인 URL.
- GE (Q_GE): 에이전트 → 조직의 에이전트 'Cymbal VOC 분석가' → agent home (description = the --description above) →
  question → thinking shows the tool 'List Urgent Tickets' (~42 s) → answer after ~32 s (visible from ~50.3 s; static until the scroll at 61.2 s): '🚨 [긴급/안전 이슈] 미처리
  문의 현황 (총 6건)', table CX-2610-0259 · 0235 (처리중) · 0225 · 0223 · 0211 (접수) · 0210 (처리중), all 공기청정기,
  names/phones masked, '데이터 출처: BigQuery cymbal_cx.voc_tickets | 기준일: 2026-10-25' (= voc_facts.json
  open_urgent_ticket_ids, 접수 3 · 처리중 3).
Hygiene: local paths ('Analyzed <local path>' rows, transient raw markdown links), the build status-bar label, another
lab's leftovers in the IAM take (explorer 'tests', change list, bottom bar) and the red label under the input box are
never shown in crops/zooms and never named in text.
"""

P_DEPLOY = ("lab.env의 PROJECT_ID와 REGION으로 agents-cli deploy를 써서 cymbal-voc-agent를 Agent Runtime에 배포해 주세요. "
            "배포 명령은 백그라운드로 돌리지 말고 끝날 때까지 기다린 뒤, 배포된 에이전트가 BigQuery를 읽을 수 있도록 "
            "필요한 IAM 권한(BigQuery 데이터 보기·작업 실행)도 부여하고 결과를 알려 주세요.")
P_IAM = ("배포된 cymbal-voc-agent(Agent Runtime)가 BigQuery의 cymbal_cx 데이터를 읽을 수 있도록 IAM 권한"
         "(roles/bigquery.dataViewer, roles/bigquery.jobUser)을 부여하고, 부여된 결과를 확인해서 알려 주세요. "
         "명령은 백그라운드로 돌리지 말고 끝날 때까지 기다려 주세요.")
P_PUBLISH = ("배포한 cymbal-voc-agent를 agents-cli publish gemini-enterprise로 Gemini Enterprise 앱에 등록해 주세요. "
             "앱 ID·위치·표시 이름은 lab.env의 GE_APP_ID, GE_LOCATION, GE_DISPLAY_NAME 값을 그대로 쓰면 되니 "
             "앱 목록은 조회하지 말고 바로 등록해 주세요.")
Q_GE = "지난주(2026-10-19 ~ 2026-10-25) 안전 이슈 긴급 문의 중 아직 처리되지 않은 건을 알려 줘"

IAM_CMDS = """# 녹화에서 에이전트가 실행한 권한 부여 명령 (답변 2번 항목) — 실습 폴더(cymbal-voc)에서
source lab.env
SA_EMAIL="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \\
  --member="serviceAccount:${SA_EMAIL}" \\
  --role="roles/bigquery.dataViewer"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \\
  --member="serviceAccount:${SA_EMAIL}" \\
  --role="roles/bigquery.jobUser\""""

METADATA = """{
  "remote_agent_runtime_id": "projects/<PROJECT_NUMBER>/locations/<REGION>/reasoningEngines/<ID>",
  "deployment_target": "agent_runtime",
  …
}"""

CMD_DEPLOY = """# 0) 변수 불러오기 — 실습 폴더(cymbal-voc)에서
source lab.env
cd cymbal-voc-agent

# 1) 배포 — 녹화에서 에이전트가 실행한 명령과 같습니다. 결과는 deployment_metadata.json에 저장됩니다
agents-cli deploy --project "${PROJECT_ID}" --region "${REGION}" --no-confirm-project

# 미리 점검만(실행하지 않음) · 배포 목록 · --no-wait로 시작한 배포의 상태
agents-cli deploy --dry-run --project "${PROJECT_ID}" --region "${REGION}" --no-confirm-project
agents-cli deploy --list
agents-cli deploy --status"""

CMD_IAM = """# 2) 권한 — Agent Runtime 서비스 에이전트에게 BigQuery 데이터 보기 · 작업(쿼리) 실행
SA_EMAIL="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
for ROLE in roles/bigquery.dataViewer roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \\
    --member="serviceAccount:${SA_EMAIL}" --role="${ROLE}"
done

# 확인 — 이 서비스 에이전트에 붙은 역할 목록
gcloud projects get-iam-policy "${PROJECT_ID}" \\
  --flatten="bindings[].members" \\
  --filter="bindings.members:serviceAccount:${SA_EMAIL}" \\
  --format="table(bindings.role)\""""

CMD_PUBLISH = """# 3) Gemini Enterprise 게시 — ADK 방식. cymbal-voc-agent 폴더에서 실행하면
#    Agent Runtime ID는 deployment_metadata.json에서 자동으로 읽습니다
GE_APP="projects/${PROJECT_NUMBER}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}"
agents-cli publish gemini-enterprise \\
  --registration-type adk \\
  --gemini-enterprise-app-id "${GE_APP}" \\
  --display-name "${GE_DISPLAY_NAME}" \\
  --description "Cymbal 고객경험(CX)팀의 VOC(고객의 소리) 분석 에이전트입니다."

# 프로젝트의 Gemini Enterprise 앱 목록(앱 ID · 위치 확인용)
agents-cli publish gemini-enterprise --list"""

LAB = {
    "id": "lab9", "no": 9, "level": "심화", "minutes": 30, "video": "ag9",
    "title": "배포 + Gemini Enterprise 게시",
    "subtitle": "Agent Runtime 배포 · 권한 · GE 게시 · GE에서 질문",
    "goal": "Lab 8에서 만든 **cymbal-voc-agent**(BigQuery 도구 `get_weekly_summary` · `list_urgent_tickets`를 가진 ADK "
            "에이전트)에 이어서, 이번에는 요청서의 마지막 3번 **VOC 도우미** — \"팀원 누구나 Gemini Enterprise에서 '지난주 "
            "긴급 문의 알려 줘'처럼 물어볼 수 있게\" — 를 완성합니다. 지금까지 내 컴퓨터에서만 돌던 에이전트를 Google Cloud의 "
            "에이전트 실행 환경인 **Agent Runtime**에 **배포**하고, 배포된 에이전트가 BigQuery를 읽을 수 있게 **권한(IAM)** 을 "
            "준 뒤, 회사의 **Gemini Enterprise 앱에 게시**합니다. 세 가지 모두 Antigravity에게 한국어로 맡깁니다. 마지막에는 "
            "CX팀원이 되어 Gemini Enterprise 화면에서 질문해 봅니다 — BigQuery에서 찾아낸 **안전 이슈 미처리 문의 6건**이 "
            "이름·연락처가 가려진 표로 돌아오면 성공입니다.",
    "steps": [
        {
            "title": "Agent Runtime에 배포하기 — agents-cli deploy",
            "body": [
                "**준비** Lab 8의 `cymbal-voc` 폴더(안에 `cymbal-voc-agent` 프로젝트), 결제가 연결된 Google Cloud 프로젝트, "
                "그리고 배포 권한(Vertex AI · Cloud Build 사용)이 필요합니다. 이번 Lab에서는 `lab.env`의 값을 모두 씁니다 — "
                "`PROJECT_ID` · `PROJECT_NUMBER` · `REGION`과 게시용 `GE_APP_ID` · `GE_LOCATION` · `GE_DISPLAY_NAME`"
                "(기본 `Cymbal VOC 분석가`)을 내 환경 값으로 채워 두세요. 앱 ID와 위치는 Google Cloud 콘솔의 Gemini "
                "Enterprise 앱 화면에서 확인합니다.",
                "**Agent Runtime**은 ADK 에이전트를 올려 두고 API로 부르는 Google Cloud의 실행 환경입니다. 배포하면 내 컴퓨터가 "
                "꺼져 있어도 에이전트가 동작하고, Gemini Enterprise 같은 다른 서비스가 이 에이전트를 부를 수 있게 됩니다.",
                "`cymbal-voc` 폴더에서 Agent 패널의 **+**로 **새 대화**를 열고 아래 프롬프트를 보냅니다. 녹화에서 에이전트는 "
                "바로 배포하지 않고 먼저 확인부터 했습니다.",
                "1. `lab.env` · 요청서 · `cymbal-voc-agent` 폴더를 읽고 `agents-cli deploy --help`로 옵션 확인",
                "2. `agents-cli deploy --status`와 `--list`로 지금 배포 상태와 기존 배포 목록 확인",
                "3. `deployment_metadata.json` · `Dockerfile` · `deployment/terraform` 등 배포 설정을 읽고, "
                "`agents-cli deploy --dry-run`으로 실행될 내용을 미리 점검",
                "4. 실제 배포 — `source ../lab.env && agents-cli deploy --project \"$PROJECT_ID\" --region \"$REGION\" "
                "--no-confirm-project`",
                "오래 걸리는 명령은 터미널에 맡겨 두고 **Worked for 1m** 아래에 \"현재 배포 상태를 확인하고 있습니다\"처럼 진행 "
                "상황을 알린 뒤 차례를 마칩니다. 명령이 끝나면 **… finished** 줄(예: *Check existing deployment status and list "
                "finished*)과 함께 결과를 받아 다음 일을 이어 갑니다. 녹화에서는 상태 확인 → 목록 조회 → dry-run 점검까지 이 "
                "흐름이 세 번 이어졌습니다.",
                "요청부터 약 4분 20초 뒤 에이전트는 \"`agents-cli deploy` 명령을 실행하여 cymbal-voc-agent를 Agent Runtime에 "
                "**배포하고 있습니다**. 배포가 완료될 때까지 대기한 뒤 필요한 BigQuery IAM 권한을 부여하겠습니다\"라고 알리고 "
                "**차례를 마쳤습니다.** 배포 명령은 터미널에서 계속 실행됩니다(Agent 패널 아래쪽 터미널 아이콘에 파란 점). "
                "녹화는 이 시점에서 끝났고, 권한 부여는 STEP 2에서 새 대화로 따로 요청했습니다.",
                "배포가 끝나면 결과가 `cymbal-voc-agent/deployment_metadata.json`에 기록됩니다. 다음 단계들(권한 · 게시)은 이 "
                "파일에서 배포된 에이전트의 **Agent Runtime ID**(`…/reasoningEngines/<ID>`)를 읽어 씁니다.",
            ],
            "prompt": P_DEPLOY,
            "shots": [
                {"stem": "ag_9v_01_deploying", "caption": "새 대화에서 배포 요청 → 먼저 agents-cli deploy --help로 옵션 확인",
                 "callouts": [
                     {"box": [940, 97, 474, 73], "label": "lab.env의 PROJECT_ID와 REGION으로 agents-cli deploy", "pos": "below"},
                     {"box": [937, 236, 221, 22], "label": "Ran agents-cli deploy --help", "pos": "below"},
                 ]},
                {"stem": "ag_9v_02_deployed", "caption": "상태 · 목록 · dry-run 확인 뒤 배포 명령 실행 — \"배포하고 있습니다\"",
                 "callouts": [
                     {"box": [933, 188, 474, 254], "label": "배포 상태 · 배포 목록 확인 → dry-run 점검", "pos": "above"},
                     {"box": [933, 481, 474, 90], "label": "agents-cli deploy 명령을 실행 — 배포하고 있습니다", "pos": "below"},
                 ]},
            ],
            "code": {"lang": "json", "file": "cymbal-voc-agent/deployment_metadata.json (배포 후, 일부)", "text": METADATA},
            "tip": "배포는 소스를 컨테이너로 빌드한 뒤 Agent Runtime에 올리는 과정이라 몇 분 이상 걸립니다. 기다리지 않으려면 "
                   "`agents-cli deploy --no-wait`로 시작하고 `agents-cli deploy --status`로 상태를 확인하면 됩니다. 끝났는지 "
                   "궁금하면 같은 대화에 \"배포가 끝났는지 agents-cli deploy --status로 확인해 주세요\"라고 물어보세요.",
            "note": "프롬프트에 \"백그라운드로 돌리지 말고 기다려 달라\"고 적었는데도, 오래 걸리는 명령은 에이전트가 터미널에 맡겨 두고 "
                    "먼저 답할 수 있습니다. 실행 중인 명령이 남아 있는 대화에 새 프롬프트를 보내면 지금 일이 끝난 뒤로 미뤄질 수 "
                    "있으니(Queued Messages), 다음 단계는 **새 대화**에서 시작하세요.",
        },
        {
            "title": "배포된 에이전트에 BigQuery 권한 주기 — IAM",
            "body": [
                "Lab 8에서 내 컴퓨터로 실행할 때 에이전트는 **내 로그인 정보**(`gcloud auth application-default login`)로 "
                "BigQuery를 읽었습니다. 배포된 에이전트는 다릅니다. Agent Runtime이 자기 **서비스 에이전트**(Google이 관리하는 "
                "서비스 계정, `service-<프로젝트 번호>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`)의 이름으로 실행하므로, "
                "이 계정에 BigQuery 권한을 줘야 질문에 답할 수 있습니다.",
                "- `roles/bigquery.dataViewer` — 테이블 데이터 **보기**(cymbal_cx.voc_tickets 읽기)",
                "- `roles/bigquery.jobUser` — 쿼리 **작업 실행**(BigQuery 조회는 프로젝트 안에서 '작업'으로 실행됩니다)",
                "배포가 끝난 뒤(보통 몇 분) **새 대화**를 열고 아래 프롬프트를 보냅니다. 녹화에서 에이전트는 이렇게 일했습니다.",
                "1. `deployment_metadata.json` · `lab.env` · Terraform 파일(`iam.tf` · `variables.tf` 등)을 읽고, 배포된 "
                "Agent Runtime의 **실행 주체(effectiveIdentity)** — 위의 서비스 에이전트 — 를 찾아냄",
                "2. `gcloud projects add-iam-policy-binding`으로 두 역할을 부여(아래 코드가 답변에 정리된 실제 명령)",
                "3. 데이터셋 단위 권한(`bq add-iam-policy-binding`)도 시도했지만 *This feature requires allowlisting* 오류가 나자, "
                "대신 `cymbal_cx` 데이터셋의 접근 목록(ACL)에 **projectReaders(READER)** 가 있어 프로젝트 단위 두 역할로 바로 "
                "조회된다는 것을 확인",
                "4. 같은 역할을 Terraform `variables.tf`의 `app_sa_roles`에도 추가(**Edited variables.tf +2 −0**) — 나중에 "
                "인프라를 코드로 다시 만들어도 권한이 빠지지 않게",
                "약 2분 40초 뒤 \"…IAM 권한 부여 및 확인을 완료했습니다\"라는 답이 나옵니다. 답변은 1) 배포된 Agent Runtime과 "
                "서비스 계정 2) 수행한 권한 부여 명령 3) `gcloud projects get-iam-policy`로 확인한 결과 표(역할 · 부여 대상 · "
                "용도) 순서입니다. 표에서 `roles/bigquery.dataViewer`와 `roles/bigquery.jobUser`를 찾으세요. 변경 검토 바의 "
                "`variables.tf`를 확인하고 **Accept all**을 누릅니다.",
            ],
            "prompt": P_IAM,
            "shot": {"stem": "ag_9v_02d_iam_done", "viewport": [1100, 585],
                     "caption": "권한 부여 완료 — variables.tf에도 반영, 실행 주체(effectiveIdentity)를 찾아 두 역할 부여 "
                                "(왼쪽 편집기는 요청서 3번 'VOC 도우미')",
                     "callouts": [
                         {"box": [596, 325, 173, 21], "label": "Edited variables.tf +2 −0", "pos": "above"},
                         {"box": [592, 361, 480, 134], "label": "IAM 권한 부여 및 확인을 완료 · 실행 주체(effectiveIdentity)",
                          "pos": "below"},
                     ]},
            "code": {"lang": "bash", "text": IAM_CMDS},
            "tip": "STEP 1에서 에이전트가 권한 부여까지 마쳤다면 이 단계는 결과 확인만 하면 됩니다 — \"배포된 에이전트의 서비스 "
                   "계정에 BigQuery 역할이 있는지 확인해 주세요\"라고 물어보세요.",
            "note": "녹화 프로젝트의 결과 표에는 이전 실습에서 붙은 다른 역할(Vertex AI · Storage 등)도 함께 나왔습니다. 여러분의 "
                    "표는 다를 수 있습니다. 권한은 꼭 필요한 것만 주는 것이 원칙입니다 — 이 에이전트는 읽기와 쿼리 실행이면 "
                    "충분합니다.",
        },
        {
            "title": "Gemini Enterprise에 게시하기 — agents-cli publish gemini-enterprise",
            "body": [
                "배포한 에이전트를 회사의 Gemini Enterprise 앱에 등록합니다. **새 대화**에서 아래 프롬프트를 보냅니다. 앱 ID · "
                "위치 · 표시 이름은 `lab.env`에서 읽으므로 프롬프트는 그대로 붙여 넣으면 됩니다.",
                "에이전트는 `agents-cli publish gemini-enterprise --help`로 옵션을 확인하고, `deployment_metadata.json`과 "
                "`agent.py`를 읽은 뒤 등록 명령을 실행했습니다.",
                "- `--gemini-enterprise-app-id` 앱의 전체 리소스 이름 — `projects/${PROJECT_NUMBER}/locations/${GE_LOCATION}/"
                "collections/default_collection/engines/${GE_APP_ID}`",
                "- `--display-name` Gemini Enterprise에 보일 이름 — `${GE_DISPLAY_NAME}`(Cymbal VOC 분석가)",
                "- `--description` 에이전트 설명 — \"Cymbal 고객경험(CX)팀의 VOC(고객의 소리) 분석 에이전트입니다. …\" "
                "이 문장이 STEP 4의 에이전트 목록 카드와 첫 화면에 그대로 보입니다.",
                "Agent Runtime ID는 따로 적지 않아도 `deployment_metadata.json`에서 읽습니다. 요청부터 약 3분 뒤 **등록 결과**가 "
                "표로 나옵니다.",
                "- **연결된 Agent Runtime** `projects/<번호>/locations/<리전>/reasoningEngines/<ID>` — STEP 1에서 배포한 그 에이전트",
                "- **등록된 에이전트 리소스 이름** `…/engines/<앱 ID>/assistants/default_assistant/agents/<ID>`",
                "- **등록 방식** `adk`(상태: created) · **Google Cloud 콘솔 확인 URL**",
            ],
            "prompt": P_PUBLISH,
            "shots": [
                {"stem": "ag_9v_03_publishing", "caption": "게시 요청 → publish 옵션 확인, 배포 정보(deployment_metadata.json) 읽기",
                 "callouts": [
                     {"box": [936, 236, 372, 22], "label": "Ran agents-cli publish gemini-enterprise --help", "pos": "above"},
                     {"box": [947, 393, 303, 58], "label": "Analyzed deployment_metadata.json · agent.py", "pos": "below"},
                 ]},
                {"stem": "ag_9v_04_published", "caption": "등록 결과 — 연결된 Agent Runtime, 등록 방식 adk(created), 콘솔 확인 URL",
                 "callouts": [
                     {"box": [949, 214, 444, 58], "label": "연결된 Agent Runtime", "pos": "above"},
                     {"box": [947, 376, 279, 57], "label": "등록 방식 (registration_type) adk (상태: created)", "pos": "above"},
                     {"box": [949, 447, 444, 76], "label": "Google Cloud 콘솔 확인 URL", "pos": "below"},
                 ]},
            ],
            "tip": "등록 방식은 두 가지입니다. Agent Runtime에 배포한 ADK 에이전트는 **ADK 방식**(`--registration-type adk`), "
                   "Cloud Run · GKE에 배포한 에이전트는 에이전트 카드 URL로 등록하는 **A2A 방식**(`--registration-type a2a`)을 "
                   "씁니다. 옵션을 생략하면 `deployment_metadata.json`을 보고 정합니다.",
            "note": "등록한 에이전트를 누가 볼 수 있는지(공유 범위)와 사용 권한은 Gemini Enterprise 관리자가 관리합니다(GE 트랙 "
                    "Lab 9 참고). 등록 직후에는 목록에 나타나기까지 몇 분 걸릴 수 있습니다.",
        },
        {
            "title": "Gemini Enterprise에서 써 보기 — CX팀원의 질문",
            "body": [
                "이제 CX팀원이 되어 봅니다. 평소 쓰는 **Gemini Enterprise 웹앱**을 열고 왼쪽 메뉴에서 **에이전트**를 누릅니다. "
                "에이전트 화면의 **조직의 에이전트**에 방금 게시한 **Cymbal VOC 분석가** 카드가 보입니다. 카드 설명이 STEP 3의 "
                "`--description`과 같습니다.",
                "카드를 누르면 에이전트 첫 화면이 열립니다. 입력창(**Cymbal VOC 분석가에게 질문하기**)에 아래 질문을 그대로 "
                "붙여 넣고 보냅니다.",
                "답이 나오는 동안 생각 과정에 **List Urgent Tickets**가 잠깐 보입니다. Lab 8에서 붙인 도구 `list_urgent_tickets`가 "
                "배포된 Agent Runtime 안에서 STEP 2의 권한으로 BigQuery를 조회하고 있다는 뜻입니다. 약 30초 뒤 답이 나왔습니다.",
                "**🚨 [긴급/안전 이슈] 미처리 문의 현황 (총 6건)** — 지난주 접수된 안전 이슈 긴급 문의 중 아직 끝나지 않은 "
                "건입니다. 모두 **공기청정기 전원 어댑터** 과열 · 연기 · 변형 문의라 즉각 조치가 필요하다는 요약이 붙습니다.",
                "- 처리중 3건 — `CX-2610-0259`(10-22) · `CX-2610-0235`(10-21) · `CX-2610-0210`(10-19)",
                "- 접수 3건 — `CX-2610-0225`(10-20) · `CX-2610-0223`(10-20) · `CX-2610-0211`(10-19)",
                "- 고객 이름과 연락처는 `이*은` · `010-****-8470`처럼 가려져 있고, 맨 아래에 **데이터 출처: BigQuery "
                "cymbal_cx.voc_tickets | 기준일: 2026-10-25**가 붙습니다. Lab 5의 팀 규칙을 Lab 8에서 에이전트 지침에 넣었기 "
                "때문입니다.",
                "Lab 7 임원 보고 슬라이드의 숫자(안전 이슈 긴급 6건 전량 미완료 — 접수 3 · 처리중 3)와 같습니다. 이제 CX팀은 Antigravity 없이도 "
                "Gemini Enterprise에서 한국어로 물어 같은 답을 얻습니다 — 요청서 3번 **VOC 도우미** 완성입니다.",
            ],
            "prompt": Q_GE,
            "shots": [
                {"stem": "ag_9v_05_ge_agents", "caption": "Gemini Enterprise → 에이전트 → 조직의 에이전트에 나타난 Cymbal VOC 분석가",
                 "callouts": [
                     {"box": [8, 268, 272, 32], "label": "에이전트", "pos": "below"},
                     {"box": [394, 625, 204, 164], "label": "Cymbal VOC 분석가", "pos": "above"},
                 ]},
                {"stem": "ag_9v_06_ge_agent_open", "caption": "에이전트 첫 화면 — 이름과 설명(게시할 때 넣은 description), 질문 입력창",
                 "callouts": [
                     {"box": [579, 299, 568, 118], "label": "Cymbal VOC 분석가", "pos": "above"},
                     {"box": [494, 647, 726, 60], "label": "Cymbal VOC 분석가에게 질문하기", "pos": "above"},
                 ]},
                {"stem": "ag_9v_07c_ge_answer", "viewport": [780, 512],
                 "caption": "답변 — 미처리 안전 이슈 6건, 이름 · 연락처는 마스킹 (위 2건)",
                 "callouts": [
                     {"box": [311, 12, 458, 48], "label": "아직 처리되지 않은 건을 알려 줘", "pos": "below"},
                     {"box": [19, 148, 297, 24], "label": "🚨 [긴급/안전 이슈] 미처리 문의 현황 (총 6건)", "pos": "above"},
                     {"box": [174, 345, 121, 161], "label": "이*은 010-…-8470 · 김*원 010-…-3634", "pos": "above"},
                 ]},
                {"stem": "ag_9v_08c_ge_answer_more", "viewport": [780, 520],
                 "caption": "나머지 4건과 맨 아래 데이터 출처 · 기준일",
                 "callouts": [
                     {"box": [18, 10, 50, 341], "label": "CX-2610-0225 · 0223 · 0211 · 0210", "pos": "below"},
                     {"box": [19, 448, 471, 24], "label": "데이터 출처: BigQuery cymbal_cx.voc_tickets | 기준일: 2026-10-25",
                      "pos": "above"},
                 ]},
            ],
            "tip": "후속 질문도 해 보세요. 예: \"그중 처리중인 건만 접수일 순으로 보여 줘\", \"지난주 VOC를 분류별로 요약해 줘\"(이번에는 "
                   "`get_weekly_summary` 도구를 씁니다).",
            "note": "답변의 표현과 표 모양은 물을 때마다 조금씩 다를 수 있지만, 숫자와 티켓 번호는 BigQuery 조회 결과라 같아야 "
                    "합니다. 다르면 STEP 2의 권한과, 질문한 기간(2026-10-19 ~ 2026-10-25)을 확인하세요.",
        },
        {
            "title": "명령으로 직접 해 보기 · 정리(비용)",
            "body": [
                "Antigravity가 실행한 명령은 터미널에서 직접 실행할 수도 있습니다. `lab.env`의 변수로 그대로 동작합니다. 옵션은 "
                "`agents-cli deploy --help`, `agents-cli publish gemini-enterprise --help`로 확인하세요.",
                "`--gemini-enterprise-app-id`에는 앱의 **전체 리소스 이름**을 넣습니다. 아래 명령은 `lab.env`의 변수로 "
                "`projects/${PROJECT_NUMBER}/locations/${GE_LOCATION}/collections/default_collection/engines/${GE_APP_ID}`를 "
                "만들어 씁니다.",
                "**정리(비용)** 배포된 Agent Runtime은 질문이 없어도 계속 남아 있고 비용이 생길 수 있습니다. 모든 실습을 마치고 "
                "더 쓰지 않을 때 정리하세요.",
                "- `agents-cli deploy --list`로 남아 있는 배포를 확인합니다.",
                "- Google Cloud 콘솔의 **Agent Runtime(에이전트 엔진)** 화면에서 `cymbal-voc-agent`를 삭제합니다.",
                "- Gemini Enterprise 앱의 **에이전트** 목록에서 **Cymbal VOC 분석가** 등록을 지웁니다(관리자 권한).",
                "- 필요하면 `gcloud projects remove-iam-policy-binding`으로 STEP 2의 두 역할도 회수합니다.",
            ],
            "code": [
                {"lang": "bash", "text": CMD_DEPLOY},
                {"lang": "bash", "text": CMD_IAM},
                {"lang": "bash", "text": CMD_PUBLISH},
            ],
            "note": "**지우기 전에 확인하세요.** Agent Runtime을 지우면 Gemini Enterprise의 Cymbal VOC 분석가도 더 이상 답하지 "
                    "못합니다. Lab 10(운영 자동화)을 이어서 할 예정이라면 그 뒤에 정리해도 됩니다.",
        },
    ],
    "check": [
        "agents-cli deploy로 cymbal-voc-agent를 Agent Runtime에 배포하고 deployment_metadata.json의 Agent Runtime ID를 확인했다",
        "에이전트가 배포 명령을 터미널에 맡기고 먼저 차례를 마칠 수 있다는 것과, 다음 단계는 새 대화에서 한다는 것을 안다",
        "배포된 에이전트는 내 계정이 아니라 Agent Runtime 서비스 에이전트로 실행된다는 것을 설명할 수 있다",
        "서비스 에이전트에 roles/bigquery.dataViewer와 roles/bigquery.jobUser를 주고 결과 표로 확인했다",
        "agents-cli publish gemini-enterprise로 ADK 방식 등록(adk · created)을 마쳤다",
        "Gemini Enterprise에서 Cymbal VOC 분석가에게 물어 미처리 안전 이슈 6건(접수 3 · 처리중 3)을 받았다",
        "실습 후 Agent Runtime 배포와 Gemini Enterprise 등록을 정리하는 방법을 안다",
    ],
    "more": [
        "(Gemini Enterprise의 Cymbal VOC 분석가에게) 지난주(2026-10-19 ~ 2026-10-25) VOC를 분류별로 요약하고, 전주보다 많이 늘어난 분류와 그 이유를 알려 줘",
        "agents-cli deploy --list로 현재 배포 목록을 보여 주고, cymbal-voc-agent의 Agent Runtime ID가 deployment_metadata.json과 같은지 확인해 주세요. 삭제는 하지 마세요.",
        "매주 월요일 아침 CX팀이 Gemini Enterprise에 직접 묻지 않아도, voc-weekly-report 스킬로 지난주 보고서가 자동으로 만들어지게 하려면 어떻게 하면 좋을지 계획만 세워 주세요. 아직 아무것도 실행하거나 예약하지 마세요.",
    ],
}
