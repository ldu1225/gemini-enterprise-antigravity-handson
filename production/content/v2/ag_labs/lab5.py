# -*- coding: utf-8 -*-
"""AG Lab 5 — 팀 규칙과 주간 보고 스킬 (cymbal-voc 스토리 Day 2, Lab 4의 VOC 대시보드에 이어서).

REAL recordings (1440x810 CSS, Antigravity agent IDE desktop app, Auto Execution / Review Policy =
Always Proceed since Lab 4): ag5v_rules · ag5v_rules_file · ag5v_check · ag5v_skill · ag5v_skill_file · ag5v_use ·
ag5v_slash · ag5v_custom. Stills ag_5v_* are 2880x1620 → CSS 1440x810. Every callout box below is measured — DOM boxes
from production/assets/shots/<stem>.boxes.json (targets / leaves), Apple Vision OCR (production/qa/find_text.py) or a
pixel scan of the still (Accept all button bg [1329.5, 673, 67.5, 18]; + Global / + Workspace button borders
x 1242.5–1314 / 1322–1423, y 184.5–212.5). Never eyeballed.

Observed in the recordings (do not over-claim):
- RULES (new conversation): the agent read README.md + 요청서_CX팀.md, then wrote AGENTS.md (Edited +29, '1 file changed
  +30 −0', 'Worked for 57s', ~1 min); answer '포함된 규칙 요약' 1–6. Accept all. AGENTS.md = 30 lines, sections
  ## 1. 언어 규칙 … ## 6. 데이터 출처 및 기준일 명시 (code block below = the real file).
- CHECK (same conversation, ~3 min): Analyzed index.html #L1-228 · styles.css #L1-646 · app.js #L1-663; thinking found
  MM/DD dates (WEEK_LABELS / WEEK_SHORT_LABELS), a date without the year (index.html line 23), prevWeek.slice(5).
  Answer table '점검 결과 요약': 1) 언어 — 영문 단위 h → 처리 시간(시간) 수정, 2) 마스킹 ✅ (maskName 홍*동 · maskPhone
  010-****-1234), 3) 외부 CDN ✅, 4) 날짜 — 10-25 · 09/28 · 9/28 혼재 → YYYY-MM-DD, 5) 안전 이슈 ✅ (.urgent-section),
  6) 푸터에 데이터 출처·기준일 누락 → index.html <footer> 추가. '2 files changed +18 −17' (index.html +6 −5, app.js
  +12 −12) → Accept all. (index.html footer now: '데이터 출처: data/voc_tickets.csv | 기준일: 2026-10-25 …')
- SKILL (new conversation, ~2 min 30 s): wrote scripts/weekly_stats.py (+242), ran it once, wrote SKILL.md (+71);
  '2 files changed +315 −0'; answer lists the stats and the run command. Accept all. SKILL.md front matter
  name: voc-weekly-report / description: '…주간 VOC 보고서, 지난주 문의 요약, 주간 VOC 통계 비교 … 요청할 때 활성화'.
- USE (new conversation, skill NOT named): first 'Analyzed voc-weekly-report/SKILL.md #L1-71' (rec 27 s), then
  'Ran python3 .agents/skills/voc-weekly-report/scripts/weekly_stats.py --csv data/voc_tickets.csv --week 2026-10-19'
  (32 s); ~2 min (answer header 'Worked for 1m') → reports/voc_weekly_report_2026-10-19.md (+95); answer '주요 반영 사항
  (AGENTS.md 및 SKILL.md 준수)', 안전 이슈 6건 (전주 2건, +4건), 김*원 … 010-****-5027, 'data/voc_tickets.csv (또는 BigQuery
  cymbal_cx.voc_tickets) | 기준일: 2026-10-25'. The report file itself: 91건 vs 79건 (+12, +15.2%), 로봇청소기 앱 연결
  13 → 20 (= answer_keys/voc_facts.json).
- SLASH (new conversation): '/voc' → Mentions menu shows voc-weekly-report + its description → Enter → chip →
  ' 2026-10-12 주간 보고서도 같은 형식으로 만들어 주세요.' (~3 min; the agent also opened last week's report for the format)
  → reports/voc_weekly_report_2026-10-12.md (+91), same footer line. No Accept all click in that take.
- CUSTOM: status-bar Settings → Customizations 'Manage' → Customizations view: Rules / Workflows tabs, '+ Global' /
  '+ Workspace', rule item '# Cymbal VOC 프로젝트 팀 규칙 (AGENTS.md) …' · 'Project · AGENTS.md'. Skills are NOT listed
  in this view (the take's 'voc-weekly-report' target hit an editor tab — not used).

Name / local-path hygiene (lead, 2026-10-28):
- The agent wrote absolute file:/// links into SKILL.md, so from ag5v_skill_file on the editor shows a local path at CSS
  y ≥ 701 (x 406–640). Portal stills use top crops of the real captures (CSS y < 699, same CSS coordinates, boxes.json
  filtered): ag_5v_06c / 08c / 09c / 10c / 11c (production/assets/shots/*.boxes.json → "derived").
- ag_5v_07_using shows 'Analyzed <local folder>' in the chat → replaced by recording frames of ag5v_use (1920x1080 →
  2880x1620 LANCZOS, same top crop): ag_5v_07f_skill_read = @30.0 s (frame 000371), ag_5v_07g_script_run = @32.0 s
  (frame 000387, the last frame before that row appears at 32.05 s). Their boxes: Apple Vision OCR on the derived still.
- The status-bar button label of the recording build is visible in some stills → no callout on it; never named in text.
"""

P_RULES = ("이 프로젝트의 팀 규칙 파일 AGENTS.md를 만들어 주세요. 1) 화면과 문서는 한국어 2) 고객 이름은 가운데 글자, "
           "연락처는 가운데 4자리를 *로 가려서 표시 3) 외부 CDN·외부 스크립트 금지 4) 날짜는 YYYY-MM-DD 5) 안전 이슈는 "
           "항상 맨 위에, 빨간색으로 강조 6) 모든 화면과 보고서 맨 아래에 데이터 출처와 기준일 표시.")
P_CHECK = "AGENTS.md 규칙에 맞는지 대시보드 코드를 점검하고, 어긋난 곳이 있으면 고쳐 주세요."
P_SKILL = ("주간 VOC 보고서를 만드는 스킬을 만들어 주세요. 위치는 .agents/skills/voc-weekly-report/ 입니다. SKILL.md에는 "
           "지난주와 그 전주를 비교해 '핵심 3줄 → 분류별 표 → 원인 추정 → 다음 할 일' 형식으로 쓰라는 지침을 넣고, "
           "scripts/weekly_stats.py에는 CSV에서 주별·분류별·제품별 건수와 긴급 건을 계산하는 코드를 넣어 주세요.")
P_USE = "지난주(2026-10-19 ~ 2026-10-25) VOC 주간 보고서를 만들어서 reports/ 폴더에 저장해 주세요."
P_SLASH = "/voc-weekly-report 2026-10-12 주간 보고서도 같은 형식으로 만들어 주세요."

AGENTS_MD = """# Cymbal VOC 프로젝트 팀 규칙 (AGENTS.md)

이 프로젝트의 모든 코드, 화면(UI), 보고서, 문서를 작성하거나 수정할 때는 아래 6가지 팀 규칙을 반드시 준수합니다.

## 1. 언어 규칙
- **모든 화면(UI)과 문서, 보고서는 한국어**로 작성합니다.
- 레이블, 버튼, 차트 제목, 표 머리글, 안내 문구 등 사용자에게 노출되는 텍스트는 한국어를 기본으로 사용합니다.

## 2. 개인정보 마스킹 (PII 보호)
고객 개인정보(`customer_name`, `phone`)는 화면, 보고서, 로그, 슬라이드 등 어디에 표시하든 반드시 마스킹 처리합니다.
- **고객 이름**: 가운데 글자를 `*`로 가려서 표시합니다. (예: `김민수` → `김*수`, 2글자인 경우 `이산` → `이*`, 4글자 이상인 경우 첫 글자와 끝 글자를 제외한 가운데 글자를 `*` 처리)
- **연락처**: 가운데 4자리를 `****`로 가려서 표시합니다. (예: `010-1234-5678` → `010-****-5678`)

## 3. 외부 CDN 및 외부 스크립트 금지
- 사내 보안 정책상 **외부 CDN, 외부 스크립트, 외부 폰트/스타일시트 로드를 전면 금지**합니다.
- 모든 HTML, CSS, JavaScript 및 차트/시각화(SVG, Canvas 등)는 외부 라이브러리 없이 로컬 코드로 직접 구현합니다.

## 4. 날짜 표기 형식
- 모든 날짜는 **`YYYY-MM-DD`** 형식으로 통일하여 표기합니다. (예: `2026-10-25`)
- 일시(Timestamp)에서 날짜만 표시하거나 기간을 표시할 때도 `YYYY-MM-DD ~ YYYY-MM-DD` 형식을 따릅니다.

## 5. 안전 이슈 최우선 강조
- **`안전 이슈` 분류 또는 `긴급` 안전 관련 문의는 건수가 적더라도 항상 화면과 보고서의 맨 위(최상단)에 배치**합니다.
- 시각적으로 즉시 인지할 수 있도록 **빨간색(경고 색상, 배지, 테두리 등)으로 강조**하여 표시합니다.

## 6. 데이터 출처 및 기준일 명시
- **모든 화면과 보고서의 맨 아래(푸터 또는 하단 영역)에 데이터 출처와 기준일을 반드시 표시**합니다.
- 예시: `데이터 출처: data/voc_tickets.csv (또는 BigQuery cymbal_cx.voc_tickets) | 기준일: 2026-10-25`"""

SKILL_MD = """---
name: voc-weekly-report
description: >-
  Cymbal CX팀의 주간 VOC(고객의 소리) 보고서를 작성할 때 사용하는 스킬입니다.
  사용자가 주간 VOC 보고서, 지난주 문의 요약, 주간 VOC 통계 비교 또는 임원 보고용 주간 요약을 요청할 때 활성화합니다.
---

# 주간 VOC 보고서 작성 스킬 (`voc-weekly-report`)

## 1. 사전 준비 및 통계 스크립트 실행
   python3 .agents/skills/voc-weekly-report/scripts/weekly_stats.py --csv data/voc_tickets.csv
   (특정 주를 기준으로 할 때는 --week YYYY-MM-DD 추가)

## 2. 보고서 필수 구성 형식 (4단계 구조)
### ① 핵심 3줄        — 첫 줄은 🚨 안전 이슈·긴급 문의 현황
### ② 분류별 표       — 🚨 안전 이슈 행을 표의 맨 위에
### ③ 원인 추정
### ④ 다음 할 일 (Action Items)

## 3. 팀 규칙 (AGENTS.md) 준수 체크리스트
1. 한국어 작성  2. 개인정보 마스킹  3. 외부 CDN/스크립트 금지
4. 날짜 YYYY-MM-DD  5. 안전 이슈 최우선 강조  6. 맨 아래 데이터 출처와 기준일
(일부 생략)"""

LAB = {
    "id": "lab5", "no": 5, "level": "기본", "minutes": 25, "video": "ag5",
    "title": "팀 규칙과 주간 보고 스킬",
    "subtitle": "AGENTS.md · SKILL.md · 자동 선택 · 슬래시 호출",
    "goal": "Lab 4에서 만든 **VOC 대시보드**(`cymbal-voc` 폴더)에 이어서, 이번에는 **우리 팀이 일하는 방식**을 에이전트에게 "
            "가르칩니다. 지금까지는 \"이름은 가려 주세요, 날짜는 YYYY-MM-DD로…\"를 프롬프트마다 다시 적었습니다. 이런 약속은 "
            "**AGENTS.md**(팀 규칙 파일)에 한 번 적어 두면 **모든 대화에 항상** 적용됩니다. 그리고 CX팀이 매주 월요일 손으로 "
            "만들던 **주간 VOC 보고**는 **스킬**(SKILL.md 작업 설명서 + 계산 스크립트)로 묶어, 누가 요청해도 같은 형식으로 "
            "나오게 합니다. 마지막으로 스킬이 **알아서 골라지는지**, **`/`로 직접 부를 수 있는지** 확인합니다. 여기서 만든 "
            "규칙과 스킬은 Lab 6에서 회사 BigQuery 데이터를 연결한 뒤에도 그대로 씁니다.",
    "steps": [
        {
            "title": "팀 규칙 파일 AGENTS.md 만들기",
            "body": [
                "먼저 두 가지를 구분해 둡시다.",
                "- **규칙 — AGENTS.md** 팀이 *항상* 지키는 약속입니다. 프로젝트 폴더 맨 위의 `AGENTS.md`에 적어 두면, 에이전트가 "
                "이 폴더에서 나누는 **모든 대화에 자동으로** 적용합니다. 예: 화면은 한국어로, 고객 이름은 가려서.",
                "- **스킬 — SKILL.md** *특정 작업*을 할 때만 꺼내 쓰는 작업 설명서입니다. 에이전트는 평소에는 스킬의 **이름과 설명"
                "(description)** 만 알고 있다가, 요청이 그 설명과 맞을 때 본문을 읽고 따릅니다. 계산용 스크립트를 함께 넣어 둘 "
                "수도 있습니다(STEP 3).",
                "Lab 4의 `cymbal-voc` 폴더에서 Agent 패널 오른쪽 위 **+**(새 대화)를 눌러 새 대화를 열고, 아래 프롬프트를 보냅니다. "
                "요청서_CX팀.md의 *지켜야 할 것*에 Lab 4까지 확인한 내용을 더해 규칙 6가지로 정리했습니다.",
                "에이전트는 `README.md`와 `요청서_CX팀.md`를 먼저 읽은 뒤, 프로젝트 맨 위에 `AGENTS.md`를 만들었습니다(약 1분, "
                "답변 위에 **Worked for 57s**). 편집기에는 새 파일 내용이 초록색(새로 추가된 줄)으로 표시되고, 답변에는 **포함된 "
                "규칙 요약** 6가지가 정리됩니다.",
                "답변 아래 변경 검토 바(**1 File With Changes**)에서 **Accept all**을 누른 뒤, Explorer에서 `AGENTS.md`를 열어 "
                "보세요. 제목 아래에 `## 1. 언어 규칙` · `## 2. 개인정보 마스킹 (PII 보호)` …처럼 규칙이 번호별로 정리되어 "
                "있습니다(전체 30줄, 아래 코드).",
            ],
            "prompt": P_RULES,
            "shots": [
                {"stem": "ag_5v_01_rules", "caption": "AGENTS.md 생성 — 편집기에 새 파일, 답변에 규칙 요약 6가지",
                 "callouts": [
                     {"box": [342, 35, 150, 30], "label": "AGENTS.md", "pos": "below"},
                     {"box": [720, 247, 538, 163], "label": "포함된 규칙 요약", "pos": "above"},
                     {"box": [1326, 670, 74, 24], "label": "Accept all", "pos": "above"},
                 ]},
                {"stem": "ag_5v_02_agents_md", "caption": "Explorer에서 연 AGENTS.md — 규칙이 번호별로 정리됨",
                 "callouts": [
                     {"box": [42, 224, 299, 22], "label": "AGENTS.md", "pos": "below"},
                     {"box": [404, 373, 213, 274], "label": "## 2. 개인정보 마스킹 (PII 보호)", "pos": "above"},
                 ]},
            ],
            "code": {"lang": "md", "file": "AGENTS.md (녹화에서 만들어진 파일)", "text": AGENTS_MD},
            "tip": "규칙은 **지켰는지 확인할 수 있는 문장**으로 쓰세요. \"개인정보 조심\"보다 \"고객 이름은 가운데 글자를 `*`로 가린다"
                   "(`김민수` → `김*수`)\"처럼 예시까지 적으면 에이전트가 정확히 따릅니다.",
            "note": "AGENTS.md는 그냥 텍스트 파일이라 직접 고쳐도 됩니다. 저장한 뒤 새 대화를 시작하면 바뀐 규칙으로 일합니다. "
                    "규칙 파일의 내용과 순서는 만들 때마다 조금씩 다를 수 있습니다.",
        },
        {
            "title": "규칙대로 점검·수정하기",
            "body": [
                "규칙을 만들었으면, 규칙이 생기기 *전에* 만든 대시보드가 규칙을 지키는지 확인해야 합니다. **같은 대화**에 아래 "
                "프롬프트를 보냅니다.",
                "Lab 4에서 권한을 **Always Proceed**로 바꿔 두었기 때문에 승인 카드 없이 진행됩니다. 에이전트는 `index.html` · "
                "`styles.css` · `app.js`를 끝까지 읽고(**Analyzed**), 규칙과 하나씩 비교한 뒤 어긋난 곳을 고쳤습니다. 생각 기록"
                "(Thinking)을 펼쳐 보면 `MM/DD` 형식의 주차 이름(`WEEK_LABELS`)처럼 규칙과 다른 날짜를 찾아내는 과정이 보입니다. "
                "약 3분 걸렸습니다.",
                "답변의 **점검 결과 요약** 표에 규칙별 결과와 조치 내용이 정리됩니다.",
                "1. **언어(한국어)** 표 머리글의 영문 단위 `h` → `처리 시간(시간)`으로 수정",
                "2. **개인정보 마스킹** ✅ 준수 중 — `maskName`(`홍*동`) · `maskPhone`(`010-****-1234`)이 데이터를 읽을 때와 표를 "
                "그릴 때 모두 적용",
                "3. **외부 CDN·스크립트 금지** ✅ 준수 중 — 로컬 CSS와 순수 SVG 차트만 사용",
                "4. **날짜 표기** `10-25` · `09/28` · `9/28`처럼 섞여 있던 날짜를 모두 `YYYY-MM-DD`로 통일"
                "(예: `2026-09-28 ~ 10-25` → `2026-09-28 ~ 2026-10-25`)",
                "5. **안전 이슈 최상단·빨간색** ✅ 준수 중 — 최상단 빨간색 경고 영역(`.urgent-section`)",
                "6. **데이터 출처·기준일** 빠져 있던 것을 `index.html` 맨 아래 `<footer>`에 추가"
                "(`데이터 출처: data/voc_tickets.csv | 기준일: 2026-10-25`)",
                "변경 검토 바에 **2 Files With Changes**(`index.html` +6 −5 · `app.js` +12 −12)가 표시됩니다. 확인하고 "
                "**Accept all**을 누릅니다.",
            ],
            "prompt": P_CHECK,
            "shots": [
                {"stem": "ag_5v_03_checking", "caption": "세 파일을 읽고 규칙과 비교 — 날짜 형식 불일치를 찾아냄",
                 "callouts": [
                     {"box": [734, 180, 204, 126], "label": "Analyzed index.html · styles.css · app.js", "pos": "above"},
                     {"box": [746, 375, 634, 66], "label": "WEEK_LABELS · MM/DD → YYYY-MM-DD", "pos": "below"},
                 ]},
                {"stem": "ag_5v_04_checked", "caption": "점검 결과 — 날짜 형식 통일 · 데이터 출처와 기준일 푸터 추가",
                 "callouts": [
                     {"box": [728, 158, 676, 186], "label": "4) 날짜 표기 (YYYY-MM-DD)", "pos": "above"},
                     {"box": [728, 398, 676, 55], "label": "6) 하단 데이터 출처 및 기준일", "pos": "below"},
                     {"box": [1326, 670, 74, 24], "label": "Accept all", "pos": "above"},
                 ]},
            ],
            "tip": "규칙을 새로 만들거나 바꿨다면 \"규칙에 맞는지 점검해 주세요\"를 한 번 요청하세요. 이미 만든 결과물은 규칙이 생기기 "
                   "전에 만들어졌기 때문에 저절로 바뀌지 않습니다.",
            "note": "Lab 4의 `python3 -m http.server 8123`으로 대시보드를 다시 열면, 맨 아래에 데이터 출처와 기준일이 보입니다. "
                    "점검 결과와 고친 위치는 실행할 때마다 조금씩 다를 수 있습니다.",
        },
        {
            "title": "주간 보고 스킬 만들기 — SKILL.md + 스크립트",
            "body": [
                "이제 CX팀의 *주간 VOC 보고*를 스킬로 만듭니다. **새 대화**를 열고 아래 프롬프트를 보냅니다.",
                "스킬은 **폴더 하나**입니다. 작업 폴더의 `.agents/skills/<스킬 이름>/` 안에 다음을 둡니다.",
                "- `SKILL.md` — 맨 위 `---` 사이에 **name**(스킬 이름, 소문자와 하이픈)과 **description**(언제 이 스킬을 쓰는지)을, "
                "그 아래 본문에 작업 순서와 보고서 형식을 적습니다.",
                "- `scripts/` — 작업에 쓰는 도우미 스크립트. 여기서는 CSV에서 주별·분류별·제품별 건수와 긴급 건을 계산하는 "
                "`weekly_stats.py`입니다. AI가 표를 *눈으로 세지* 않고 스크립트로 계산하게 하는 장치입니다(Lab 3에서 본 "
                "숫자 검증과 같은 생각).",
                "에이전트는 `weekly_stats.py`를 먼저 만들고 **직접 한 번 실행해** 결과를 확인한 뒤 `SKILL.md`를 썼습니다. 약 2분 "
                "30초 뒤 **2 files changed +315 −0**(`weekly_stats.py` +242 · `SKILL.md` +71)과 함께, 답변에 스크립트가 내는 통계"
                "(주별 접수 건수 요약, 분류별·제품별 비교, 안전 이슈·긴급 문의 목록 — 이름·연락처 자동 마스킹)와 **실행 방법**이 "
                "정리됩니다. **Accept all**을 누릅니다.",
                "Explorer에서 `.agents/skills/voc-weekly-report`를 펼쳐 `SKILL.md`를 열어 보세요. 맨 위 **description**에 "
                "\"주간 VOC 보고서, 지난주 문의 요약 … 요청할 때 활성화\"라고 적혀 있습니다. 에이전트가 스킬을 고를 때 보는 "
                "문장이 바로 이것입니다. 본문에는 **핵심 3줄 → 분류별 표 → 원인 추정 → 다음 할 일** 형식과 팀 규칙 체크리스트가 "
                "들어 있습니다.",
            ],
            "prompt": P_SKILL,
            "shots": [
                {"stem": "ag_5v_05_skill", "caption": "스킬 완성 — weekly_stats.py · SKILL.md 두 파일과 실행 방법",
                 "callouts": [
                     {"box": [790, 385, 472, 38], "label": "python3 … weekly_stats.py --csv data/voc_tickets.csv",
                      "pos": "above"},
                     {"box": [742, 614, 464, 50], "label": "weekly_stats.py · SKILL.md", "pos": "above"},
                     {"box": [1326, 670, 74, 24], "label": "Accept all", "pos": "below"},
                 ]},
                {"stem": "ag_5v_06c_skill_md", "caption": "SKILL.md — 맨 위 name · description, 본문은 보고서 형식",
                 "callouts": [
                     {"box": [42, 246, 299, 66], "label": "voc-weekly-report", "pos": "above"},
                     {"box": [404, 86, 212, 200], "label": "name · description", "pos": "above"},
                     {"box": [404, 302, 213, 182], "label": "핵심 3줄 → 분류별 표 → 원인 추정 → 다음 할 일",
                      "pos": "below"},
                 ]},
            ],
            "code": {"lang": "md", "file": ".agents/skills/voc-weekly-report/SKILL.md (앞부분 요약)", "text": SKILL_MD},
            "tip": "녹화에서는 에이전트가 SKILL.md 안의 링크(스크립트, AGENTS.md)를 **내 컴퓨터의 전체 경로**로 적었습니다. 팀원과 "
                   "함께 쓸 스킬이라면 \"SKILL.md의 링크를 상대 경로로 바꿔 주세요\"라고 요청해 `scripts/weekly_stats.py`처럼 "
                   "바꿔 두세요.",
            "note": "스킬 폴더에는 `scripts/` 말고도 `examples/`(예시) · `resources/`(템플릿·데이터)를 둘 수 있습니다. 위 코드는 "
                    "녹화에서 만들어진 SKILL.md(71줄)의 앞부분을 줄인 것입니다.",
        },
        {
            "title": "스킬이 알아서 쓰이는지 확인 — 자동 선택",
            "body": [
                "스킬이 정말 *알아서* 쓰이는지 봅니다. **새 대화**를 열고, 스킬 이름은 말하지 않은 채 아래처럼만 요청합니다.",
                "녹화에서 에이전트가 가장 먼저 한 일은 `voc-weekly-report/SKILL.md`를 읽는 것이었습니다(**Analyzed "
                "voc-weekly-report/SKILL.md**). 요청(\"VOC 주간 보고서\")이 스킬의 **description**과 맞았기 때문에 스스로 골라 "
                "읽은 것입니다.",
                "이어서 SKILL.md 1단계 지침대로 스킬 폴더의 스크립트를 실행했습니다 — `python3 .agents/skills/voc-weekly-report/"
                "scripts/weekly_stats.py --csv data/voc_tickets.csv --week 2026-10-19`. 숫자를 도구로 계산하는 습관까지 스킬에 "
                "담겨 있는 셈입니다.",
                "약 2분 뒤(답변 위에는 **Worked for 1m**) `reports/voc_weekly_report_2026-10-19.md`가 만들어졌습니다. 답변의 "
                "**주요 반영 사항 (AGENTS.md 및 SKILL.md 준수)** 에 두 파일을 함께 지켰다고 정리되어 있습니다.",
                "- **스킬(SKILL.md)** 핵심 3줄 → 분류별 표 → 원인 추정 → 다음 할 일 순서",
                "- **규칙(AGENTS.md)** 🚨 안전 이슈 6건(전주 2건 대비 +4건)을 맨 위에, 고객 이름·연락처 마스킹(`김*원` · "
                "`010-****-5027`), 날짜 `YYYY-MM-DD`, 맨 아래 **데이터 출처: data/voc_tickets.csv … | 기준일: 2026-10-25**",
                "보고서 파일을 열어 보면 핵심 3줄에 전체 접수 **91건(전주 79건 대비 +12건, +15.2%)**, 로봇청소기 '앱 연결' 문의 "
                "**13건 → 20건** 같은 숫자가 들어 있습니다. 확인하고 **Accept all**을 누릅니다.",
            ],
            "prompt": P_USE,
            "shots": [
                {"stem": "ag_5v_07f_skill_read", "caption": "스킬 이름 없이 요청 → 에이전트가 먼저 SKILL.md를 읽음",
                 "callouts": [
                     {"box": [722, 94, 538, 25], "label": "VOC 주간 보고서를 만들어서 reports/ 폴더에 저장",
                      "pos": "above"},
                     {"box": [731, 181, 313, 26], "label": "Analyzed voc-weekly-report/SKILL.md", "pos": "below"},
                 ]},
                {"stem": "ag_5v_07g_script_run", "caption": "이어서 스킬 폴더의 weekly_stats.py 실행",
                 "callouts": [
                     {"box": [721, 183, 695, 78], "label": "Run python3 .agents/skills/voc-weekly-report/scripts/weekly_stats.py",
                      "pos": "below"},
                 ]},
                {"stem": "ag_5v_08c_report", "caption": "보고서 저장 — AGENTS.md와 SKILL.md를 함께 지킴, 맨 아래 데이터 출처",
                 "callouts": [
                     {"box": [722, 156, 298, 25], "label": "reports/voc_weekly_report_2026-10-19.md", "pos": "above"},
                     {"box": [721, 190, 331, 26], "label": "AGENTS.md 및 SKILL.md 준수", "pos": "below"},
                     {"box": [721, 472, 586, 26], "label": "데이터 출처 … 기준일: 2026-10-25", "pos": "below"},
                 ]},
            ],
            "tip": "스킬이 골라지지 않을 때는 SKILL.md의 `description`에 사람들이 실제로 쓰는 표현(\"주간 보고서\", \"지난주 요약\")을 "
                   "넣어 보세요. 에이전트는 이 설명을 보고 스킬을 고릅니다.",
            "note": "보고서의 원인 추정 · 담당 부서 · 기한은 에이전트가 데이터를 바탕으로 쓴 **실습용 가상 내용**입니다. 실제 "
                    "보고서라면 사실과 맞는지 꼭 확인하세요.",
        },
        {
            "title": "슬래시(/)로 직접 부르기와 Customizations",
            "body": [
                "스킬은 직접 부를 수도 있습니다. **새 대화**에서 입력창에 `/voc`를 입력하면 메뉴에 **voc-weekly-report** 스킬이 "
                "설명(description)과 함께 나타납니다. **Enter**로 고르면 입력창에 스킬이 들어가고, 이어서 할 일을 적어 보냅니다"
                "(아래 프롬프트에서 `/voc-weekly-report` 부분은 메뉴에서 고르세요).",
                "`/스킬 이름`으로 부르면 에이전트가 그 스킬을 **반드시** 씁니다. 자동 선택을 기다리지 않고 확실하게 쓰고 싶을 때 "
                "편리합니다.",
                "녹화에서는 에이전트가 스킬 지침대로 스크립트를 실행하고, 형식을 맞추려고 지난주 보고서도 열어 본 뒤, 약 3분 만에 "
                "`reports/voc_weekly_report_2026-10-12.md`를 만들었습니다. 맨 아래 데이터 출처와 기준일도 그대로 들어갔습니다.",
                "마지막으로 규칙을 관리하는 화면을 봅니다. 상태 표시줄 오른쪽 아래 **Settings** 버튼을 누르고, 설정 창의 "
                "**Customizations** 줄에서 **Manage**를 누르면 **Customizations** 화면이 열립니다.",
                "- **Rules** 탭 — 이 폴더의 `AGENTS.md`가 **Project · AGENTS.md** 규칙으로 보입니다.",
                "- **+ Global** · **+ Workspace** — 모든 프로젝트에 쓸 규칙, 이 폴더에만 쓸 규칙을 새로 추가합니다.",
                "이 화면의 Rules 탭에서는 **규칙**을 관리합니다. 스킬은 `.agents/skills/` 폴더 안의 파일로 관리합니다 — Explorer에서 "
                "열어 고치거나, 폴더째 복사해 다른 프로젝트로 가져갈 수 있습니다.",
            ],
            "prompt": P_SLASH,
            "shots": [
                {"stem": "ag_5v_09c_slash", "caption": "/voc 입력 → 메뉴에 voc-weekly-report 스킬과 설명",
                 "callouts": [
                     {"box": [717, 296, 706, 36], "label": "voc-weekly-report", "pos": "above"},
                     {"box": [725, 353, 36, 24], "label": "/voc", "pos": "below"},
                 ]},
                {"stem": "ag_5v_10c_slash_done", "caption": "슬래시로 부른 결과 — 10-12 주 보고서도 같은 형식으로 저장",
                 "callouts": [
                     {"box": [727, 93, 444, 24], "label": "voc-weekly-report 2026-10-12 주간 보고서도 같은 형식으로",
                      "pos": "below"},
                     {"box": [721, 474, 557, 26], "label": "데이터 출처 … 기준일: 2026-10-25", "pos": "above"},
                     {"box": [742, 640, 509, 24], "label": "voc_weekly_report_2026-10-12.md", "pos": "above"},
                 ]},
                {"stem": "ag_5v_11c_customizations", "caption": "Settings → Customizations → Manage: Rules 탭의 Project · AGENTS.md",
                 "callouts": [
                     {"box": [712, 139, 155, 31], "label": "Rules · Workflows", "pos": "above"},
                     {"box": [1242, 184, 182, 29], "label": "+ Global · + Workspace", "pos": "below"},
                     {"box": [722, 254, 697, 41], "label": "Project · AGENTS.md", "pos": "below"},
                 ]},
            ],
            "tip": "자주 쓰는 스킬은 이름을 짧고 알아보기 쉽게 지으세요. `/` 뒤에 앞글자 몇 개만 입력해도 메뉴에서 바로 찾을 수 "
                   "있습니다. **제약은 규칙, 여러 단계의 절차는 스킬**로 나누는 것이 기본입니다.",
            "note": "저장 위치 — 규칙: 작업 폴더의 `AGENTS.md`(또는 `GEMINI.md`, `.agents/rules/*.md`), 모든 프로젝트용은 "
                    "`~/.gemini/AGENTS.md` · 스킬: 작업 폴더의 `.agents/skills/<이름>/`, 모든 프로젝트용(데스크톱 앱)은 "
                    "`~/.gemini/config/skills/<이름>/`. 작업 폴더의 규칙과 스킬을 Git으로 함께 관리하면 팀원 모두가 같은 방식으로 "
                    "에이전트를 씁니다. **Workflows** 탭의 워크플로는 2026-10-19부터 지원이 끝났으니, 기존 워크플로가 있다면 "
                    "`/migrate-workflows`로 스킬로 옮기세요.",
        },
    ],
    "check": [
        "규칙(AGENTS.md, 항상 적용)과 스킬(SKILL.md, 필요할 때 꺼내 씀)의 차이를 설명할 수 있다",
        "규칙 6가지를 담은 AGENTS.md를 만들고 Explorer에서 내용을 확인했다",
        "규칙대로 대시보드를 점검해 날짜 형식과 데이터 출처·기준일 푸터를 고쳤다",
        "voc-weekly-report 스킬(SKILL.md + scripts/weekly_stats.py)을 만들고 name · description을 확인했다",
        "스킬 이름 없이 요청해도 에이전트가 SKILL.md를 읽고 스크립트를 실행해 주간 보고서를 만든 것을 확인했다",
        "/voc로 스킬을 직접 불러 10-12 주 보고서를 만들고, Customizations에서 Project · AGENTS.md 규칙을 확인했다",
    ],
    "more": [
        "AGENTS.md에 '보고서와 대시보드의 숫자는 반드시 스크립트나 쿼리로 계산하고, 눈으로 센 숫자는 쓰지 않는다' 규칙을 7번으로 추가해 주세요.",
        "voc-weekly-report 스킬의 SKILL.md 안에 있는 링크를 모두 상대 경로(예: scripts/weekly_stats.py)로 바꿔 주세요. 팀원 컴퓨터에서도 그대로 쓸 수 있게요.",
        "지금 스킬은 data/voc_tickets.csv만 읽습니다. 같은 데이터가 회사 BigQuery 테이블 cymbal_cx.voc_tickets에도 있는데, 다음 실습에서 MCP로 연결하면 weekly_stats.py와 SKILL.md를 어떻게 바꾸면 좋을지 계획만 세워 주세요. 아직 아무것도 설치하거나 고치지 마세요.",
    ],
}
