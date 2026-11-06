# -*- coding: utf-8 -*-
"""AG Lab 10 — 운영 자동화 (cymbal-voc 스토리 마지막 Lab, Lab 9의 Gemini Enterprise 게시에 이어서).

REAL recordings (Antigravity agent IDE desktop app, window 1440x810 CSS, 2026-10-29), each a NEW
conversation in the cymbal-voc folder: ag10v_schedule (13:38) and ag10v_sub (14:02). Stills ag_10v_* are 2880x1620
(CSS 1440x810). Every callout box is measured — DOM leaves of production/assets/shots/<stem>.boxes.json (crops: leaves
shifted by the crop origin) or Apple Vision OCR (production/qa/find_text.py) for the recording-frame still. Never eyeballed.

Derived stills (real pixels, crops only — scratch/make_l10_stills.py of the writer conversation):
- ag_10v_01p_scheduled = ag_10v_01_scheduled      crop [916, 36, 524, 588]
- ag_10v_01bp_card     = ag_10v_01b_schedule_card crop [916, 36, 524, 440]
- ag_10v_01cp_status   = ag_10v_01c_status        crop [916, 71, 524, 385]
- ag_10v_02p_subagents = ag_10v_02_subagents      crop [916, 36, 524, 340]
- ag_10v_03t_tests     = ag10v_sub frame @255.21 s (1920x1080 → 2880x1620 LANCZOS) crop [916, 71, 524, 625]
- ag_10v_03p_sub_done  = ag_10v_03_sub_done       crop [916, 186, 524, 510]
- ag_10v_05r_request   = ag_10v_01_scheduled      crop [342, 182, 573, 278] (editor: 요청서_CX팀.md)
(ag_10v_04_readme_guide is NOT used: the explorer click opened cymbal-voc-agent/README.md, not the root README.)

Observed in the recordings (do not over-claim):
- SCHEDULE (submit 16.6 s): '/' → slash menu 'schedule — Run an instruction on a recurring schedule or as a one-time
  timer.' → '/schedule' chip + L10_SCHEDULE_REST. 'Thought for 8s' → chip 'Scheduled 30 8 * * 1' (~30 s) → answer
  (~35–40 s, 'Worked for 18s'): '매주 월요일 오전 8시 30분에 주간 VOC 보고서를 자동으로 생성하도록 예약했습니다.' +
  예약 설정 요약 (실행 주기 · 적용 스킬 · 데이터 소스 · 저장 경로 · 주요 처리 규칙) + 데이터 출처 line (기준일 2026-10-29).
  Card click 98.6 s → the agent's rewritten scheduled prompt + 'Status: Active'. Status question (L10_STATUS) 109.1 s →
  'Queued Messages 1 · Sends after agent finishes working' → Send Now 113.9 s → 'Exploring 1 artifact, 1 task',
  '예약 작업 로그 조회' → answer (~134 s): 현재 상태 정상 대기 중 (실행 중 / RUNNING) · 반복 주기 매주 월요일 오전 08:30
  (30 8 * * 1) · 다음 실행 시각 2026-11-02 오전 08:30:00 (KST, 2026-11-02T08:30:00+09:00).
  Cancel was verified OFF camera by the lead (text only): '예약한 작업을 취소해 주세요' → queued → Send Now →
  '상태: 정상 취소 완료 (cancelled)', '현재 실행 중인 예약/백그라운드 작업: 없음 (0건)'. Nothing is claimed about the app
  being closed at fire time.
- SUBAGENTS (submit 17.3 s): two cards 'Weekly Stats Unit Tester' / 'README Operations Guide Writer' ('Invoked self
  subagent', ~38 s) → 'Worked for 48s' + '두 개의 서브에이전트를 동시에 실행하여 작업을 시작했습니다 … 완료되면 결과를
  종합하여 알려드리겠습니다' (turn ends ~70 s) → ~3분 (200.8 s): 'Message from Weekly Stats Unit Tester (self)' → '…
  tests/test_weekly_stats.py 작성 및 6개 단위 테스트 통과를 완료했습니다' + changes (+265 −0 tests/test_weekly_stats.py,
  +74 −2 README.md) → ~4분: 'Message from README Operations Guide Writer (self)' → '두 서브에이전트의 작업이 모두
  완료되었습니다. 종합 결과는 다음과 같습니다.' → merged report finished ~4분 30초 (… 2. 데이터 확인 방법 · 3. 장애 시
  대처 방법 · 데이터 출처). Accept all at 850.7 s → '0 Files With Changes'.
  README excerpt below = the real root README.md written in that take (mtime 14:05:50), quoted verbatim with '…' cuts.
Hygiene: transient raw markdown links with local paths flash while answers stream (all-frames OCR scan: ag10v_schedule
~34.3 s; ag10v_sub ~63.8–65.0, ~224.4 and 268.9–283.2 s) — those stretches are never shown; the status-bar label,
explorer, input placeholder and model menu stay outside crops/zooms; MCP is not mentioned (not used in this Lab).
"""

P_SCHEDULE = ("/schedule 매주 월요일 오전 8시 30분에 voc-weekly-report 스킬로 지난주 보고서를 BigQuery 최신 데이터로 만들어 "
              "reports/에 저장하고, 안전 이슈 긴급 건이 있으면 맨 위에 요약하도록 예약해 주세요.")
P_STATUS = "방금 예약한 작업의 상태와 다음 실행 시각을 알려 주세요."
P_CANCEL = "예약한 작업을 취소해 주세요."
P_SUB = ("서브에이전트 두 개에게 나눠서 동시에 진행해 주세요: (1) .agents/skills/voc-weekly-report/scripts/weekly_stats.py의 "
         "단위 테스트 작성·실행 (2) README.md에 '매주 운영 가이드'(월요일 자동 보고 흐름, 데이터 확인, 장애 시 대처) 섹션 추가. "
         "끝나면 결과를 합쳐서 알려 주세요.")

CRON = """30 8 * * 1
│ │ │ │ └─ 요일   1 = 월요일 (0·7 = 일요일)
│ │ │ └─── 월     * = 매월
│ │ └───── 일     * = 매일
│ └─────── 시     8시
└───────── 분     30분      → 매주 월요일 08:30"""

README_GUIDE = """## 매주 운영 가이드

> [!CAUTION]
> **🚨 [최우선 운영 원칙 — 안전 이슈(긴급) 최우선 배치 및 즉시 대응]**
> - 미완료(`접수`·`처리중`) 상태인 안전 이슈가 확인되면 정기 보고 마감(월요일 08:30)을 기다리지 않고 즉시 품질안전팀 및 CX팀장에게 공유하여 …
> - 모든 운영 문서·보고서·로그·질의 응답에서 고객 개인정보는 반드시 마스킹하여 표기합니다 …

### 1. 월요일 자동 보고 흐름
| 시각 / 단계 | 수행 주체 | 상세 작업 내용 | 산출물 / 확인처 |
|---|---|---|---|
| **월요일 08:00** (자동 트리거) | 스케줄러 (`/schedule` · 크론 `0 8 * * 1`) | 매주 월요일 08:00(KST)에 주간 VOC 자동 보고 작업을 시작합니다. | 백그라운드 태스크 실행 |
| **1단계: 실데이터 조회** | … | … | BigQuery 읽기 전용 쿼리 결과 |
| **2단계: 주간 보고서 생성** | 에이전트 (`SKILL.md` 4단계 양식) | … | `reports/voc_weekly_report_YYYY-MM-DD.md` |
| **3단계: 팀 규칙 검증** | CX팀 담당자 / 자동 체크리스트 | … | `AGENTS.md` 체크리스트 통과 |
| **월요일 08:30** (임원 보고) | CX팀장 · 유관 부서 | … Gemini Enterprise의 **Cymbal VOC 분석가**(`cymbal-voc-agent`)로 응답합니다. | … |

### 2. 데이터 확인 방법
1. **🚨 안전 이슈 및 미완료 긴급 문의 최우선 점검 (필수 1순위)**
2. **BigQuery 원본 테이블 직접 확인 (운영 기준)**
3. **로컬 CSV 백업 및 주간 통계 스크립트 검증**

### 3. 장애 시 대처 방법
| 장애 유형 | 증상 | 즉시 대처 및 복구 방법 |
|---|---|---|
| **🚨 안전 이슈 수동 선발송 (공통 최우선)** | 자동 보고 지연·시스템 장애 발생 시 | … |
| **1) 월요일 자동 스케줄 미실행** | 월요일 08:10까지 신규 보고서 파일이 생성되지 않음 | 1. 스케줄/백그라운드 작업 상태를 확인합니다. … |
| **2) BigQuery 연결 오류 / 데이터 누락** | … | … `bash setup/load_to_bigquery.sh`를 실행해 CSV 원본을 재적재합니다. … |
| **3) VOC 에이전트(`cymbal-voc-agent`) 오류** | … | … `agents-cli deploy` 및 `agents-cli publish gemini-enterprise`로 재배포합니다. |
| **4) 팀 규칙(`AGENTS.md`) 위반 발견** | 마스킹 누락, 외부 CDN 포함, 날짜 형식 불일치 등 | … |"""

TEST_CMD = """# 실습 폴더(cymbal-voc)에서 — 서브에이전트가 만든 단위 테스트 6개를 직접 다시 실행
python3 -m unittest tests/test_weekly_stats.py -v

# README의 '데이터 확인 방법' 3번 — 로컬 CSV로 주간 통계 교차 확인
python3 .agents/skills/voc-weekly-report/scripts/weekly_stats.py --csv data/voc_tickets.csv --week 2026-10-19"""

LAB = {
    "id": "lab10", "no": 10, "level": "심화", "minutes": 25, "video": "ag10",
    "title": "운영 자동화",
    "subtitle": "/schedule 주간 예약 · 서브에이전트 병렬 작업",
    "goal": "Lab 9에서 VOC 에이전트를 Gemini Enterprise에 게시한 데 이어, 이번이 **cymbal-voc 스토리의 마지막 Lab**입니다. "
            "요청서 2번의 마지막 조건 — \"**매주 월요일 08:30까지** 지난주 요약이 **자동으로** 나오게\" — 을 Antigravity의 "
            "**/schedule**로 해결합니다. 매주 월요일 오전 8시 30분에 Lab 5의 `voc-weekly-report` 스킬이 BigQuery 최신 데이터로 "
            "보고서를 만들도록 예약하고, 예약 상태와 다음 실행 시각을 확인하는 법, 멈추는 법까지 익힙니다. 이어서 일을 둘로 나눠 "
            "**서브에이전트 두 개**에게 동시에 맡깁니다 — 하나는 통계 스크립트의 **단위 테스트**, 다른 하나는 README의 **매주 "
            "운영 가이드**. 마지막으로 처음 받은 요청서 3가지가 어느 Lab에서 어떻게 해결됐는지 정리하고, 운영할 때 챙길 권한·"
            "비용·예약 정리를 점검합니다.",
    "steps": [
        {
            "title": "/schedule로 매주 월요일 08:30 보고 예약하기",
            "body": [
                "**준비** Lab 5의 팀 규칙(`AGENTS.md`)과 `voc-weekly-report` 스킬, Lab 6의 BigQuery 연결이 있는 `cymbal-voc` "
                "폴더를 엽니다. 예약은 그 예약을 만든 **대화에 묶이므로**, Agent 패널의 **+**로 **새 대화**를 열고 시작하세요.",
                "입력창에 **/** 를 입력하면 명령 목록이 나옵니다. `/sch`까지 치면 **schedule — Run an instruction on a recurring "
                "schedule or as a one-time timer.**(반복 예약 또는 한 번만 실행하는 타이머)가 남습니다. 고르면 입력창에 "
                "`/schedule` 칩이 들어가고, 그 뒤에 **언제 · 무엇을** 할지 한국어로 적습니다(아래 프롬프트).",
                "에이전트는 약 20초 만에 이 대화에 **반복 예약 작업**을 만듭니다. 답변 위에 **Scheduled 30 8 * * 1** 카드가 "
                "생기고, 답변에 **예약 설정 요약**이 정리됩니다.",
                "- **실행 주기** 매주 월요일 오전 08:30 (`30 8 * * 1`) — 아래 크론 식 풀이 참고",
                "- **적용 스킬** `voc-weekly-report` · **데이터 소스** BigQuery 최신 데이터(`cymbal_cx.voc_tickets`) · "
                "**저장 경로** `reports/`",
                "- **주요 처리 규칙** 안전 이슈·긴급 문의가 있으면 보고서 **최상단에 빨간색 경고**로 요약, 그리고 팀 규칙(한국어, "
                "`customer_name`·`phone` 마스킹, `YYYY-MM-DD`, 하단 데이터 출처·기준일)",
                "예약 프롬프트에 \"팀 규칙을 지켜 달라\"고 따로 쓰지 않았는데도 규칙이 들어간 것은 Lab 5의 `AGENTS.md`를 "
                "에이전트가 함께 읽었기 때문입니다.",
            ],
            "prompt": P_SCHEDULE,
            "shot": {"stem": "ag_10v_01p_scheduled", "viewport": [524, 588],
                     "caption": "약 20초 만에 예약 완료 — Scheduled 30 8 * * 1 카드와 예약 설정 요약",
                     "callouts": [
                         {"box": [21, 173, 129, 21], "label": "Scheduled 30 8 * * 1", "pos": "above"},
                         {"box": [21, 234, 472, 239],
                          "label": "예약 설정 요약 — 실행 주기 · 적용 스킬 · 데이터 소스 · 저장 경로 · 주요 처리 규칙",
                          "pos": "below"},
                     ]},
            "code": {"lang": "text", "label": "크론 식 읽는 법", "text": CRON},
            "tip": "요청서는 \"08:30**까지**\"입니다. 08:30에 시작하면 보고서는 몇 분 뒤에 나오므로, 실제 운영에서는 \"매주 월요일 "
                   "오전 8시\"처럼 조금 앞당겨 예약하세요(`0 8 * * 1`). STEP 3에서 서브에이전트가 쓴 README의 흐름표도 "
                   "**08:00 자동 시작 → 08:30 임원 보고**로 적혀 있습니다.",
            "note": "한 번만 실행할 일은 같은 `/schedule`로 \"30분 뒤에 …\", \"오늘 오후 6시에 한 번 …\"처럼 적으면 됩니다(명령 "
                    "설명의 *one-time timer*).",
        },
        {
            "title": "예약 확인 · 상태 묻기 · 멈추기",
            "body": [
                "**Scheduled 30 8 * * 1** 카드를 누르면 펼쳐집니다. 안에는 에이전트가 내 요청을 **다시 정리한 예약 "
                "프롬프트** — \"voc-weekly-report 스킬을 사용하여 BigQuery 최신 데이터(cymbal_cx.voc_tickets)를 기반으로 "
                "지난주 주간 VOC 보고서를 작성하고 reports/ 디렉터리에 저장해 주세요. 안전 이슈 및 긴급 안전 관련 문의가 "
                "있는 경우 보고서 최상단에 빨간색 경고와 함께 최우선으로 요약하고, 팀 규칙(…)을 준수해 주세요.\" — 와 "
                "**Status: Active**가 보입니다. 매주 실제로 실행되는 것은 이 문장이니, 빠진 조건이 없는지 읽어 보세요.",
                "같은 대화에 상태를 물어봅니다(아래 프롬프트). 메시지가 바로 가지 않고 입력창 위 **Queued Messages 1 · Sends "
                "after agent finishes working**에 대기합니다. 이 대화에는 예약 작업이 계속 살아 있어서 에이전트가 **일하는 "
                "중**으로 보이기 때문입니다. 대기 메시지 오른쪽의 **Send Now**(→)를 누르면 바로 보냅니다.",
                "에이전트는 예약 작업과 로그를 확인하고(**Exploring 1 artifact, 1 task** · **예약 작업 로그 조회**) 약 20초 뒤 "
                "답합니다.",
                "- **현재 상태** 정상 대기 중 (실행 중 / `RUNNING`)",
                "- **반복 주기** 매주 월요일 오전 08:30 (`30 8 * * 1`)",
                "- **다음 실행 시각** **2026-11-02 오전 08:30:00** (KST) — 녹화한 날(2026-10-29, 목)의 다음 월요일",
                "**멈추기** 같은 대화에 \"" + P_CANCEL + "\"라고 보내고(역시 Queued → **Send Now**), 답에 **정상 취소 완료 "
                "(cancelled)** 와 \"현재 실행 중인 예약/백그라운드 작업: 없음 (0건)\"이 나오면 끝입니다. 이 취소 과정은 "
                "영상에는 없고, 같은 환경에서 따로 확인한 결과입니다.",
            ],
            "prompt": P_STATUS,
            "shots": [
                {"stem": "ag_10v_01bp_card", "viewport": [524, 440],
                 "caption": "카드를 펼치면 — 에이전트가 다시 쓴 예약 프롬프트와 Status: Active",
                 "callouts": [
                     {"box": [60, 231, 416, 131], "label": "voc-weekly-report 스킬을 사용하여 … 준수해 주세요.",
                      "pos": "above"},
                     {"box": [40, 377, 93, 19], "label": "Status: Active", "pos": "below"},
                 ]},
                {"stem": "ag_10v_01cp_status", "viewport": [524, 385],
                 "caption": "Send Now로 보낸 상태 질문의 답 — 정상 대기 중, 다음 실행 2026-11-02 오전 08:30",
                 "callouts": [
                     {"box": [21, 159, 374, 124], "label": "예약 작업 상태 — 현재 상태 · 반복 주기 · 다음 실행 시각",
                      "pos": "below"},
                 ]},
            ],
            "tip": "예약을 만든 대화는 앞으로도 메시지가 계속 Queued로 대기합니다. 예약을 확인·변경·취소할 때만 그 대화를 쓰고, "
                   "**다른 일은 새 대화**에서 하세요.",
            "note": "예약은 그 대화에 들어 있습니다. 예약이 잘 있는지는 그 대화의 카드(Status)와 상태 질문으로 확인하세요. 같은 "
                    "일을 두 번 예약하면 보고서도 두 번 만들어지니, 바꾸고 싶으면 먼저 취소하고 다시 예약합니다.",
        },
        {
            "title": "서브에이전트 두 개로 테스트와 운영 가이드를 동시에",
            "body": [
                "자동 보고가 매주 돌아가려면 두 가지가 더 있으면 좋습니다. 보고서 숫자를 만드는 통계 스크립트가 맞게 동작하는지 "
                "확인하는 **단위 테스트**, 그리고 팀원 누구나 따라 할 수 있는 **운영 가이드**입니다. 서로 관계없는 일이라 "
                "**서브에이전트**에게 나눠 맡기면 동시에 진행됩니다. **새 대화**에서 아래 프롬프트를 보냅니다.",
                "메인 에이전트는 약 20초 만에 서브에이전트 두 개 — **Weekly Stats Unit Tester**와 **README Operations Guide "
                "Writer** — 를 시작합니다(**Invoked self subagent** = 메인 에이전트와 같은 설정의 에이전트). 그리고 \"두 "
                "서브에이전트의 작업이 모두 완료되면 결과를 종합하여 알려드리겠습니다\"라고 알린 뒤 **차례를 마칩니다**"
                "(Worked for 48s). 서브에이전트는 뒤에서 계속 일합니다.",
                "요청부터 약 3분 뒤 **Message from Weekly Stats Unit Tester (self)** — 메인 에이전트가 \"첫 번째 "
                "서브에이전트가 `tests/test_weekly_stats.py` 작성 및 **6개 단위 테스트 통과**를 완료했습니다\"라고 전하고, "
                "변경 검토 바에 **+265 −0 test_weekly_stats.py** · **+74 −2 README.md** 두 파일이 올라옵니다.",
                "- 테스트 6개: 이름 마스킹 · 연락처 마스킹 · 증감 표시 형식 · CSV 읽기(빈 파일·정상 파일) · 합성 데이터로 팀 규칙 "
                "검증(안전 이슈 맨 위 등) · 실제 `data/voc_tickets.csv`와 명령줄 실행",
                "약 4분 뒤 **Message from README Operations Guide Writer (self)** 가 도착하고, 메인 에이전트가 \"두 "
                "서브에이전트의 작업이 모두 완료되었습니다. 종합 결과는 다음과 같습니다\"로 시작하는 **종합 보고**를 씁니다"
                "(요청부터 약 4분 30초). 보고의 마지막 부분이 README에 추가된 가이드의 요약입니다.",
                "- **2. 데이터 확인 방법** ① 안전 이슈 및 미완료 긴급 문의 1순위 점검 ② BigQuery 원본 테이블 SQL 조회 명령 "
                "③ 로컬 CSV와 `weekly_stats.py` 교차 검증 명령",
                "- **3. 장애 시 대처 방법** 맨 위에 🚨 **안전 이슈 수동 선발송** 절차, 이어서 자동 스케줄 미실행 · BigQuery 연결 "
                "실패 · `cymbal-voc-agent` 응답 오류 · `AGENTS.md` 규칙 위반 때 할 일",
                "변경 검토 바에서 두 파일을 확인하고 **Accept all**을 누르면 **0 Files With Changes**가 됩니다. 아래는 "
                "서브에이전트가 실제로 `README.md`에 추가한 섹션의 일부입니다.",
            ],
            "prompt": P_SUB,
            "shots": [
                {"stem": "ag_10v_02p_subagents", "viewport": [524, 340],
                 "caption": "메인 에이전트가 서브에이전트 두 개를 동시에 시작",
                 "callouts": [
                     {"box": [21, 172, 236, 42], "label": "Weekly Stats Unit Tester · Invoked self subagent",
                      "pos": "above"},
                     {"box": [21, 238, 236, 42], "label": "README Operations Guide Writer · Invoked self subagent",
                      "pos": "below"},
                 ]},
                {"stem": "ag_10v_03t_tests", "viewport": [524, 625],
                 "caption": "첫 번째 서브에이전트 완료 — 6개 단위 테스트 통과, 변경 파일 2개(+265 −0 · +74 −2)",
                 "callouts": [
                     {"box": [20, 298, 462, 75],
                      "label": "Message from Weekly Stats Unit Tester · 6개 단위 테스트 통과를 완료했습니다",
                      "pos": "above"},
                     {"box": [20, 536, 360, 50], "label": "+265 −0 test_weekly_stats.py · +74 −2 README.md",
                      "pos": "above"},
                 ]},
                {"stem": "ag_10v_03p_sub_done", "viewport": [524, 510],
                 "caption": "종합 보고의 끝부분 — README에 추가된 데이터 확인 방법 · 장애 시 대처 방법",
                 "callouts": [
                     {"box": [60, 4, 430, 264], "label": "2. 데이터 확인 방법 · 3. 장애 시 대처 방법", "pos": "below"},
                     {"box": [411, 485, 72, 22], "label": "Accept all", "pos": "above"},
                 ]},
            ],
            "code": [
                {"lang": "markdown", "file": "README.md — 서브에이전트가 추가한 '매주 운영 가이드' (일부, … 는 생략)",
                 "text": README_GUIDE},
                {"lang": "bash", "text": TEST_CMD},
            ],
            "tip": "서브에이전트에게는 **서로 겹치지 않는 일**을 맡기세요. 같은 파일을 둘이 동시에 고치게 하면 충돌이 납니다. "
                   "\"끝나면 결과를 합쳐서 알려 달라\"고 적어 두면 메인 에이전트가 종합 보고까지 써 줍니다.",
            "note": "메인 에이전트가 먼저 차례를 마쳐도 기다리면 됩니다. 서브에이전트의 결과가 도착할 때마다 메인 에이전트가 "
                    "이어서 답합니다. 녹화에서는 첫 결과가 약 3분, 종합 보고가 약 4분 30초 뒤에 나왔습니다.",
        },
        {
            "title": "마무리 — 요청서 3가지 체크와 운영할 때 주의할 점",
            "body": [
                "Lab 3에서 받은 `요청서_CX팀.md`를 다시 열어 봅니다. 요청 사항 3가지가 모두 해결되었습니다.",
                "- ✅ **1. VOC 대시보드** — **Lab 4** `index.html`: 핵심 지표 4개 · 주간 추이 · 제품별·분류별 · **긴급 문의 "
                "목록**을 한 화면에, 제품·긴급 필터까지(외부 CDN 없이 직접 그린 차트)",
                "- ✅ **2. 주간 보고 자동화** — **Lab 5** 팀 규칙과 `voc-weekly-report` 스킬(핵심 3줄 · 표 · 원인 · 다음 할 일) → "
                "**Lab 6** BigQuery 실데이터 연결 → **Lab 7** 임원 보고 슬라이드 6장 → **Lab 10** 매주 월요일 08:30 자동 실행 예약",
                "- ✅ **3. VOC 도우미** — **Lab 8** ADK 에이전트 `cymbal-voc-agent` → **Lab 9** Agent Runtime 배포 · Gemini "
                "Enterprise 게시. CX팀원 누구나 **Cymbal VOC 분석가**에게 \"지난주 긴급 문의 알려 줘\"라고 묻습니다.",
                "**지켜야 할 것** 4가지(마스킹 · 외부 CDN 금지 · 한국어 · 안전 이슈 맨 위)는 Lab 4부터 요청서를 따라 지켰고, "
                "Lab 5에서 `AGENTS.md` 팀 규칙으로 굳힌 뒤로는 보고서 · 슬라이드 · GE 답변(Lab 8에서 에이전트 지침에 넣음) · "
                "이번 예약 프롬프트에도 따로 말하지 않아도 들어갔습니다.",
                "**운영할 때 주의할 점**",
                "- **권한** 배포된 에이전트(Agent Runtime 서비스 에이전트)에는 BigQuery **데이터 보기 · 작업 실행** 두 역할만 "
                "둡니다(Lab 9). 사람이 쓰는 계정과 섞지 마세요.",
                "- **비용** Agent Runtime 배포는 질문이 없어도 남아 있고, BigQuery 조회는 쓴 만큼 비용이 듭니다. 실습만 하고 더 "
                "쓰지 않는다면 Lab 9 STEP 5대로 배포와 Gemini Enterprise 등록을 정리하세요.",
                "- **예약 정리** 실습이 끝나면 예약 대화에서 \"" + P_CANCEL + "\" → **cancelled** 확인. 남겨 두면 매주 월요일마다 "
                "보고서가 만들어집니다.",
                "- **결과 검토** 자동으로 나온 결과도 사람이 확인합니다. 예를 들어 README 흐름표의 크론(`0 8 * * 1`, 08:00 시작)은 "
                "STEP 1의 예약(`30 8 * * 1`)과 다릅니다. 운영 전에 둘 중 하나로 맞추세요(요청서 기준이면 08:00 쪽).",
            ],
            "shots": [
                {"stem": "ag_10v_05r_request", "viewport": [573, 278],
                 "caption": "요청서_CX팀.md — 요청 사항 3가지와 지켜야 할 것 (Antigravity 편집기 화면)",
                 "callouts": [
                     {"box": [64, 25, 380, 109], "label": "1. VOC 대시보드 · 2. 주간 보고 자동화 · 3. VOC 도우미",
                      "pos": "below"},
                 ]},
                {"stem": "ag_4v_21_dash_kpi",
                 "caption": "요청 1 ✅ Lab 4 대시보드 — 핵심 지표 4개와 주간 추이(외부 CDN 없이 직접 그린 차트)",
                 "callouts": [
                     {"box": [44, 105.4, 1352, 133.6], "label": "300건 · 10건 · 85.0% · 3.87점", "pos": "below"},
                 ]},
                {"stem": "ag_7v_21_deck_s1",
                 "caption": "요청 2 ✅ Lab 5–7 주간 보고 스킬 → 임원 보고 슬라이드(표지) — 주간 보고서는 이제 Lab 10의 예약으로 매주 월요일 자동 생성",
                 "callouts": [
                     {"box": [148.8, 181.1, 684.3, 50.6], "label": "안전 이슈(긴급) 6건 · 6건 미완료", "pos": "below"},
                 ]},
                {"stem": "ag_9v_07c_ge_answer", "viewport": [780, 512],
                 "caption": "요청 3 ✅ Lab 9 Gemini Enterprise의 Cymbal VOC 분석가 — 미처리 안전 이슈 6건, 이름 · 연락처 마스킹",
                 "callouts": [
                     {"box": [19, 148, 297, 24], "label": "🚨 [긴급/안전 이슈] 미처리 문의 현황 (총 6건)", "pos": "above"},
                 ]},
            ],
            "tip": "새 요청이 오면 같은 순서를 되풀이하면 됩니다 — 요청서를 에이전트와 함께 읽고(/plan) → 만들고 검증하고 → "
                   "규칙과 스킬로 굳히고 → 회사 데이터에 연결하고 → 배포·게시하고 → 예약으로 자동화합니다.",
        },
    ],
    "check": [
        "/schedule로 매주 월요일 08:30(30 8 * * 1) 주간 보고 예약을 만들고, 예약 설정 요약을 읽어 확인했다",
        "예약 카드를 펼쳐 에이전트가 다시 쓴 예약 프롬프트와 Status: Active를 확인했다",
        "예약 대화의 새 메시지는 Queued Messages로 대기하고 Send Now로 바로 보낸다는 것을 안다",
        "예약 상태와 다음 실행 시각(2026-11-02 08:30)을 묻고, 필요하면 '예약한 작업을 취소해 주세요'로 멈출 수 있다",
        "서브에이전트 두 개로 단위 테스트(6개 통과)와 README '매주 운영 가이드'를 동시에 받고 Accept all 했다",
        "요청서 3가지가 각각 어느 Lab에서 해결됐는지 설명할 수 있다",
        "운영 전 권한 · 비용 · 예약 정리 · 결과 검토(크론 시각 맞추기)를 점검했다",
    ],
    "more": [
        "/schedule 매일 오전 9시에 BigQuery cymbal_cx.voc_tickets에서 전날 접수된 안전 이슈 긴급 문의가 있는지 확인하고, 있으면 "
        "고객 정보를 마스킹해서 reports/alerts_YYYY-MM-DD.md로 요약해 주세요. 없으면 파일을 만들지 마세요.",
        "README의 '매주 운영 가이드' 흐름표(크론 0 8 * * 1)와 지금 예약(30 8 * * 1)이 다릅니다. 요청서의 '월요일 08:30까지'에 "
        "맞추려면 어느 쪽을 어떻게 고치면 좋을지 제안만 해 주세요. 아직 아무것도 바꾸거나 예약하지 마세요.",
        "서브에이전트 세 개에게 나눠서 동시에 진행해 주세요: (1) index.html 대시보드의 지난주 숫자를 BigQuery와 대조 "
        "(2) slides/의 최신 임원 보고 슬라이드 숫자를 BigQuery와 대조 (3) 두 결과가 다르면 원인 추정. 파일은 고치지 말고, "
        "끝나면 결과를 표로 합쳐서 알려 주세요.",
    ],
}
