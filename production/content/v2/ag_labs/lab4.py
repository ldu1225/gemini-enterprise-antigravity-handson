# -*- coding: utf-8 -*-
"""AG Lab 4 — VOC 대시보드 만들기 (cymbal-voc 스토리 Day 1 오후, Lab 3의 계획서를 이어받음).

REAL recordings (1440x810 CSS, Antigravity agent IDE desktop app):
  ag4v_build · ag4v_settings · ag4v_browse · ag4v_iterate · ag4v_verify
Stills ag_4v_* are 2880x1620 → CSS 1440x810. Every callout box below is measured — DOM boxes from
production/assets/shots/<stem>.boxes.json (targets / leaves), recording event boxes, Apple Vision OCR
(production/qa/find_text.py) or a pixel scan of the still (report screenshot edges). Never eyeballed.

Observed in the recordings (do not over-claim; times = recording seconds, answer = first frame of the final answer):
- BUILD (Review Policy / Auto Execution still Request Review from Lab 3): Proceed (2.9 s) → 'Proceeded with
  Implementation Plan' → 3 command approvals: ① python3 aggregation of the CSV (week/product/category/severity/status,
  21.4/22.7 s), ② python3 that writes app.js with maskName / maskPhone + pre-masked fallback data (199.8/201.1 s),
  ③ `node --check app.js && python3 …` scanning index.html · styles.css · app.js (211.2/212.6 s). Edited index.html
  +211 (66.7 s), styles.css +539 (118.9 s). Answer 'Worked for 3m' at 227.1 s (≈ 3 min 44 s after Proceed): 생성된 파일
  index.html · styles.css · app.js, 안전 이슈 총 10건(4주 차 6건), 62/68/79/91, 외부 URL 0건, 조*윤 / 010-****-8299.
  Review bar '2 Files With Changes' (index.html, styles.css — app.js is not listed there) → Accept all (282.0 s).
- SETTINGS: status-bar Settings → Auto Execution → Always Proceed, Review Policy → Always Proceed.
- BROWSE (new conversation, /browser): local server http://localhost:8123, headless browser from the terminal,
  answer 'Worked for 1m' (streams from 85 s, ≈ 1 min 20 s after the prompt): 긴급 10건(미완료 6: 접수 3·처리중 3,
  완료 4), 권*윤 / 010-****-3389, 62/68/79/91 with 긴급 1/1/2/6, 제품별 로봇청소기 91 …, 분류별 앱 연결 60 … 안전 이슈 10.
  'Dashboard Verification' artifact → report with the full-page dashboard screenshot.
- ITERATE (new conversation, Always Proceed → no approvals): answer streams at 424 s (≈ 7 min after the prompt; the
  recorder kept rolling until 483 s); edits index.html / styles.css / app.js, `node --check app.js`; answer:
  #productFilter + 🚨 긴급만 보기(#urgentOnlyToggle) synced with the list filters, updateDashboard / getFilteredTickets,
  안전 이슈 최상단 고정. Review bar '3 Files With Changes' (index.html +21 −4, styles.css +108 −1, app.js +260 −100) →
  Accept all (485.4 s).
- VERIFY (new conversation, /browser): python expected values, headless browser + node scripts, answer at ≈ 235 s
  (≈ 4 min): 공기청정기 + 긴급만 보기 → 9건 (주별 0/1/2/6), 배지 긴급 9건 / 미완료 6건, list 9건 (masked). Small fix:
  긴급 N건 badge colour/stroke (app.js +3 −2, '1 File With Changes') → Accept all (299.4 s). The later click on
  '1 file changed' only expands the changed-file list (not a new report). The 'Dashboard Verification' report visible in
  the editor during ITERATE/VERIFY is the one from BROWSE.
- Data facts: production/samples/v2/answer_keys/voc_facts.json (safety 10 = 공기청정기 9 + 홈카메라 1).

Hygiene (no local paths / internal names in customer material):
- ag_4v_02_changes shows the agent's sentence '(file://로 직접 열었을 때도 …)' (protocol word, y 550.6–568.6) →
  not used directly; derived crop of the same hi-DPR still: ag_4v_02a_summary = CSS x 700–1440, y 0–518
  ("viewport": [740, 518], boxes shifted by −700; the size keeps every WebP variant at the exact aspect ratio).
  A separate crop of the review bar was dropped: any crop that holds the whole bar is either too wide for the qa.py
  mobile stretch gate or includes that line. The bar + Accept all are shown in the video (zoom windows that exclude
  the line) and in the STEP 4/5 screenshots.
- ag_4v_01b_allow = recording frame ag4v_build @21.195 s (000198.jpg, 1920x1080 → 2880x1620 LANCZOS); boxes = the
  recording's event boxes (target 명령 승인 / click 허용 / click Submit).
- ag_4v_05_browsing / 08_verifying / 09b / 09c show local folder paths in the agent log → not used.
- The status-bar button label of the recording build stays visible (cannot be cropped) → no callout on it.

Finished-dashboard showcase (STEP 1 preview + STEP 6; production/capture/agy/ag4_dash.py take 2, 2026-10-29):
- The dashboard the agent built (index.html · styles.css · app.js + data/voc_tickets.csv), served by a local HTTP
  server like the learner does and opened in an own headless Chromium — page content only (no URL bar, no paths).
  Lab 5 later touched dates (YYYY-MM-DD) / a unit label / a data-source footer → said in the STEP 6 note.
- Stills ag_4v_20 (top, 전체 4주) · 21 (KPI + 주간 추이, 전체 4주) · 22 (제품별 · 분류별, 지난주 = after the 4주 차 bar)
  · 23 (지난주 · 공기청정기 · 긴급만 보기, top) · 24 (same filters, KPI + 주간 추이). 2880x1620 = CSS 1440x810.
  Callout boxes = targets / leaves of <stem>.boxes.json (unions of leaves where noted). The header is sticky (89 px);
  take 2 places every card below it.
- Numbers checked against data/voc_tickets.csv: 300 · 주평균 75.0 · 안전 10 (미완료 6) · 85.0% (미완료 45) · 3.87점 /
  22.8 h · 62/68/79/91 · 지난주 91 (+12, +15.2%) · 지난주 분류 앱 연결 24 … 안전 이슈 6 · 지난주 공기청정기 18 (+5) ·
  지난주 공기청정기 긴급 6 (전주 2 → +4, +200.0%, 접수 3 · 처리중 3, 완료율 0.0%) · 공기청정기 긴급 주별 0/1/2/6.
"""

P_BROWSE = ("/browser 로컬 서버를 띄우고 대시보드를 열어서, 주간 건수·제품별·분류별 차트와 긴급 문의 목록이 제대로 보이는지 "
            "확인해 주세요. 확인한 화면은 스크린샷으로 남겨 주세요.")
P_ITER = ("대시보드에 제품 선택 필터와 '긴급만 보기' 토글을 추가해 주세요. 필터를 바꾸면 차트와 목록이 함께 바뀌어야 하고, "
          "안전 이슈는 항상 맨 위에 보여야 해요.")
P_VERIFY = "/browser 제품을 '공기청정기'로 바꾸고 '긴급만 보기'를 켰을 때 목록과 차트가 맞게 바뀌는지 확인해 주세요."

LAB = {
    "id": "lab4", "no": 4, "level": "기본", "minutes": 30, "video": "ag4",
    "title": "VOC 대시보드 만들기",
    "subtitle": "Proceed · 변경 검토 · /browser 검증 · 필터 추가",
    "goal": "Lab 3에서 세운 **VOC 대시보드 계획서(Implementation Plan)** 에 이어서, 이번에는 실제로 만듭니다. "
            "**Proceed로 계획대로 만들기 → 바뀐 파일 검토(Accept all) → `/browser`로 화면 확인 → 기능 추가 → 다시 검증**까지, "
            "에이전트에게 *만들기와 확인을 함께 맡기는* 흐름을 한 바퀴 돌아 봅니다. 마지막에는 완성된 대시보드를 **직접 열어** "
            "CX팀의 질문(지난주 공기청정기 긴급 문의는 몇 건이고 처리됐는지)에 필터 몇 번으로 답해 봅니다 — 완성된 모습은 STEP 1의 "
            "첫 그림에서 먼저 볼 수 있습니다. 결과물인 대시보드(`index.html` · `styles.css` · `app.js`)는 Lab 5에서 팀 규칙과 "
            "주간 보고 스킬을 만들 때 그대로 이어서 씁니다.",
    "steps": [
        {
            "title": "계획대로 만들기 — Proceed와 변경 검토",
            "body": [
                "**먼저 완성된 모습부터 보세요.** 아래 첫 번째 그림이 이번 Lab을 마치면 나오는 대시보드입니다 — 맨 위에 안전 이슈 "
                "목록이 고정되고, 위쪽에서 기준 주차 · 제품 선택 · 긴급만 보기로 화면 전체를 거를 수 있습니다(STEP 6에서 직접 열어 "
                "써 봅니다). 지금부터 이 화면을 에이전트와 함께 만듭니다.",
                "Lab 3의 **같은 대화**를 엽니다. 마지막 답변의 Implementation Plan 카드 아래 **Proceed**를 누르면, 에이전트가 "
                "계획서대로 대시보드를 만들기 시작합니다. 채팅 맨 위에 **Proceeded with Implementation Plan**이 표시됩니다.",
                "Lab 3에서 권한을 **Request Review**로 두었기 때문에, 에이전트가 터미널 명령을 실행하려 할 때마다 "
                "**Allow running this command?** 카드가 뜹니다. 명령을 읽고 **Yes, allow this time** → **Submit**을 누르세요. "
                "녹화에서는 세 번 승인했습니다.",
                "1. 데이터 다시 집계 — `python3`로 CSV의 주별·제품별·분류별·긴급도·상태별 건수를 세어 화면에 쓸 숫자 확인",
                "2. `app.js` 만들기 — `python3` 명령 안에 이름·연락처 마스킹 함수(`maskName` · `maskPhone`)와 화면 코드가 들어 있음",
                "3. 검사 — `node --check app.js`(문법 검사)와 세 파일(`index.html` · `styles.css` · `app.js`)을 훑는 `python3` 검사",
                "그사이 에이전트는 `index.html`(+211줄)과 `styles.css`(+539줄)를 만들었습니다. Proceed부터 승인 시간을 포함해 "
                "약 4분 만에 완성되었습니다(답변 위에는 **Worked for 3m**). 답변의 **생성된 파일**에 `index.html` · `styles.css` · "
                "`app.js`가, 아래 **주요 구현 및 검증 완료 항목**에 최상단 안전 이슈 목록(총 10건, 4주 차 6건), 4주 막대 차트"
                "(62 → 68 → 79 → 91건), 외부 URL(`http://` · `https://`) 참조 0건, 이름·연락처 마스킹(`조*윤` · `010-****-8299`)이 "
                "정리됩니다.",
                "답변 맨 아래 **변경 검토 바**(**2 Files With Changes**)에서 바뀐 파일을 확인합니다. 파일 이름을 누르면 바뀐 "
                "내용을 볼 수 있고, 괜찮으면 **Accept all**, 되돌리려면 **Reject all**을 누릅니다. 녹화에서는 **Accept all**을 "
                "눌렀습니다.",
            ],
            "shots": [
                {"stem": "ag_4v_20_dash_top", "caption": "미리 보기 — 이번 Lab에서 완성할 VOC 대시보드 (STEP 6에서 직접 사용)",
                 "callouts": [
                     # union of label 기준 주차 [698.5,33.9] … toggle [1260.2,26.9,155.8,35.1] (boxes.json leaves/targets)
                     # = [698.5,26.4,717.5,36.0] + 4 px left/right, 3 px top/bottom (still inside the header bar)
                     {"box": [694.5, 23.4, 725.5, 42.0], "label": "기준 주차 · 제품 선택 · 긴급만 보기", "pos": "below"},
                     # target D 긴급·미완료 배지 (union of the two badges)
                     {"box": [318.9, 136.7, 155.3, 24.7], "label": "긴급 10건 · 미완료 6건", "pos": "above"},
                 ]},
                {"stem": "ag_4v_01_working", "caption": "Proceed 후 — 계획서대로 작업 시작, 첫 명령(데이터 집계) 실행",
                 "callouts": [
                     {"box": [725, 96, 274, 23], "label": "Proceeded with Implementation Plan", "pos": "below"},
                     {"box": [721, 184, 688, 25], "label": "Running python3 -c …", "pos": "below"},
                 ]},
                {"stem": "ag_4v_01b_allow", "caption": "Allow running this command? — 명령을 읽고 Yes, allow this time → Submit",
                 "callouts": [
                     {"box": [740, 182, 190, 24], "label": "Allow running this command?", "pos": "above"},
                     {"box": [741, 345, 124, 25], "label": "Yes, allow this time", "pos": "below"},
                     {"box": [1340, 730, 87, 38], "label": "Submit", "pos": "above"},
                 ]},
                {"stem": "ag_4v_02a_summary", "viewport": [740, 518],
                 "caption": "약 4분 뒤 완성 — 생성된 파일 3개와 구현·검증 항목",
                 "callouts": [
                     {"box": [21, 208, 688, 152], "label": "생성된 파일", "pos": "above"},
                     {"box": [21, 372, 688, 144], "label": "주요 구현 및 검증 완료 항목", "pos": "above"},
                 ]},
            ],
            "tip": "변경 검토 바에는 이번에 `index.html` · `styles.css` 두 파일이 표시되었습니다. `app.js`까지 세 파일이 "
                   "함께 표시되는 모습은 STEP 4에서 볼 수 있습니다. 어떤 파일이 바뀌었는지 모르겠다면 \"방금 바꾼 파일과 이유를 "
                   "표로 정리해 주세요\"라고 물어보세요.",
        },
        {
            "title": "설정 바꾸기 — 연습 폴더에서만 Always Proceed",
            "body": [
                "Lab 3부터 지금까지는 명령 하나하나를 내가 승인했습니다. 흐름에 익숙해졌다면, **연습 폴더에서는** 승인 없이 "
                "진행하도록 바꿔 속도를 낼 수 있습니다.",
                "화면 오른쪽 아래 상태 표시줄의 **Settings** 버튼(에이전트 설정)을 눌러 설정 창을 열고, 두 항목을 모두 "
                "**Always Proceed**로 바꿉니다. 같은 버튼을 한 번 더 누르면 창이 닫힙니다.",
                "- **Auto Execution = Always Proceed** 터미널 명령을 묻지 않고 바로 실행",
                "- **Review Policy = Always Proceed** 계획서 같은 결과물을 만든 뒤 내 검토 없이 바로 진행",
                "이제부터 에이전트는 명령 실행과 파일 수정을 스스로 진행합니다. 그래도 파일이 바뀌면 답변 아래 **변경 검토 바**"
                "(Accept all · Reject all)가 나타나므로, 결과는 여전히 확인하고 받아들일 수 있습니다(STEP 4 · 5).",
            ],
            "shot": "ag_4v_04_always", "caption": "Settings → Auto Execution · Review Policy를 Always Proceed로",
            "callouts": [
                {"box": [1092, 355, 318, 24], "label": "Auto Execution · Always Proceed", "pos": "above"},
                {"box": [1092, 389, 318, 24], "label": "Review Policy · Always Proceed", "pos": "below"},
            ],
            "note": "회사 코드 저장소나 중요한 폴더에서는 **Request Review**를 그대로 두세요. 회사 계정이라면 관리자가 정한 보안 "
                    "정책(Lab 1)이 우선 적용되어, 이 설정을 바꿀 수 없을 수도 있습니다.",
        },
        {
            "title": "/browser로 화면 확인 — 검증 보고서와 스크린샷",
            "body": [
                "만든 대시보드가 실제 브라우저에서 제대로 보이는지 에이전트에게 확인을 맡깁니다. Agent 패널 오른쪽 위 **+**(새 대화)를 "
                "눌러 **새 대화**를 시작하세요. 로컬 서버처럼 계속 실행되는 명령이 남아 있으면 같은 대화의 다음 요청이 대기열에 "
                "묶일 수 있어서, 단계마다 새 대화로 시작하는 편이 깔끔합니다.",
                "입력창 맨 앞에 `/browser`를 붙여 아래 프롬프트를 보냅니다. `/browser`는 브라우저를 다루는 에이전트를 불러 웹 화면을 "
                "열고, 살펴보고, 스크린샷을 찍게 하는 명령입니다.",
                "에이전트는 로컬 웹 서버(`http://localhost:8123`)를 띄우고 대시보드를 브라우저로 열어 확인한 뒤, 약 1분 20초 만에 "
                "결과를 정리했습니다(**Worked for 1m**). 스크린샷 이미지(`dashboard_full.png`)와 검증 결과 문서"
                "(`dashboard_verification.md`)도 만들었습니다.",
                "1. **긴급 문의(안전 이슈) 목록** 대시보드 최상단에 고정 — 총 10건(미완료 6건: 접수 3 · 처리중 3, 완료 4건), "
                "이름·연락처 마스킹(`권*윤` · `010-****-3389`)",
                "2. **주간 문의 추이** 62 → 68 → 79 → 91건(긴급 1 · 1 · 2 · 6건)",
                "3. **제품별** 로봇청소기 91건 · 공기청정기 67건 · 홈카메라 46건 · 스마트 조명 36건 · 스마트 스피커 33건 · 에어폴 프로 27건",
                "4. **분류별** 앱 연결 60건 · 불량·고장 59건 · 배송 55건 · 사용법 46건 · 구매 문의 36건 · 환불·교환 34건 · "
                "안전 이슈 10건(빨간색 강조)",
                "답변 아래 **Dashboard Verification** 카드를 누르면 편집기에 검증 보고서가 열리고, 에이전트가 찍은 **대시보드 전체 화면 "
                "스크린샷**을 볼 수 있습니다.",
            ],
            "prompt": P_BROWSE,
            "shots": [
                {"stem": "ag_4v_06_browser_result", "caption": "/browser 결과 — 확인 결과 요약과 Dashboard Verification 카드",
                 "callouts": [
                     {"box": [721, 287, 690, 215], "label": "확인 결과 요약", "pos": "above"},
                     {"box": [717, 512, 696, 60], "label": "Dashboard Verification", "pos": "below"},
                 ]},
                {"stem": "ag_4v_06b_report", "caption": "검증 보고서 — 에이전트가 찍은 대시보드 전체 화면 스크린샷",
                 "callouts": [
                     {"box": [350, 153, 331, 35], "label": "Cymbal VOC 대시보드 브라우저 검증 결과", "pos": "below"},
                     {"box": [352, 260, 327, 518], "label": "Cymbal VOC 대시보드 전체 화면", "pos": "inside"},
                 ]},
            ],
            "tip": "내 눈으로 직접 여는 방법은 STEP 6에서 다룹니다(`cymbal-voc` 폴더의 터미널에서 `python3 -m http.server 8123` → "
                   "브라우저에서 `http://localhost:8123`).",
            "note": "녹화 환경에서는 브라우저 확인이 터미널의 *헤드리스 브라우저*(화면 없이 실행되는 브라우저)로 진행되어 별도 창이 뜨지 "
                    "않았습니다. 환경에 따라 Chrome 창이 따로 열릴 수 있습니다.",
        },
        {
            "title": "기능 추가 — 제품 필터와 '긴급만 보기'",
            "body": [
                "CX팀이 제품별로, 그리고 긴급 건만 골라 보고 싶어 합니다. 다시 **새 대화**를 열고 아래 프롬프트를 보냅니다.",
                "STEP 2에서 Always Proceed로 바꿨기 때문에, 이번에는 승인 카드 없이 에이전트가 파일을 읽고 고칩니다. 녹화에서는 "
                "`index.html` · `styles.css` · `app.js`를 차례로 고치고 `node --check app.js`로 문법까지 확인한 뒤, **약 7분** 만에 "
                "끝났습니다.",
                "- **제품 선택 필터와 🚨 긴급만 보기 토글** 상단 헤더에 추가(`#productFilter` · `#urgentOnlyToggle`), 아래 전체 문의 "
                "목록의 필터와도 양방향으로 동기화",
                "- **필터를 바꾸면 함께 갱신** 주간 추이 차트 · 제품별/분류별 차트 · KPI 카드 · 문의 목록(차트의 막대를 눌러도 필터 전환)",
                "- **안전 이슈 최상단 고정** 긴급 목록 · 분류별 차트 · 전체 문의 표에서 항상 맨 위(빨간색 강조)",
                "Review Policy가 Always Proceed여도 파일 변경은 **변경 검토 바**에 모입니다. 이번에는 **3 Files With Changes** — "
                "`index.html` +21 −4 · `styles.css` +108 −1 · `app.js` +260 −100. 내용을 확인하고 **Accept all**을 누릅니다.",
            ],
            "prompt": P_ITER,
            "shot": {"stem": "ag_4v_07_iterated", "caption": "기능 추가 결과 — 안전 이슈 최상단 고정 · 바뀐 파일 3개",
                     "callouts": [
                         {"box": [720, 268, 690, 163], "label": "3. 안전 이슈 최상단 고정 표시", "pos": "above"},
                         {"box": [722, 587, 209, 74], "label": "index.html · styles.css · app.js", "pos": "above"},
                         {"box": [765, 670, 136, 24], "label": "3 Files With Changes", "pos": "below"},
                         {"box": [1326, 670, 74, 24], "label": "Accept all", "pos": "below"},
                     ]},
            "tip": "요청할 때 *무엇을*(제품 필터 · 긴급 토글)과 *어떻게 동작해야 하는지*(차트와 목록이 함께 바뀜, 안전 이슈는 항상 "
                   "맨 위)를 함께 적으면, 에이전트가 빠뜨리지 않고 구현합니다.",
        },
        {
            "title": "다시 검증 — 필터가 맞게 바뀌는지 /browser로 확인",
            "body": [
                "기능을 추가했으면 다시 확인합니다. **새 대화**에서 `/browser`로 필터 동작을 확인해 달라고 요청합니다.",
                "에이전트는 먼저 `python3`로 기대하는 숫자를 계산한 뒤, 헤드리스 브라우저와 `node` 스크립트로 **공기청정기 + 긴급만 보기**"
                "(기준 주차: 전체 4주) 조건을 확인하고, 약 4분 만에 결과를 정리했습니다.",
                "- **주차별 추이** 1주 차 0건 → 2주 차 1건 → 3주 차 2건 → 4주 차 6건(모두 긴급), 합계 **9건**",
                "- **제품별 · 분류별 차트** 공기청정기 9건 · 안전 이슈 9건 단일 막대로 바뀜",
                "- **목록** 상단 안전 이슈 배지는 긴급 9건 / 미완료 6건, 하단 전체 목록도 같은 9건만 마스킹된 채 표시",
                "전체 안전 이슈는 10건인데 왜 9건일까요? 나머지 1건은 **홈카메라** 문의라서, 공기청정기만 고르면 9건이 맞습니다. "
                "Lab 3에서 python으로 검증한 데이터와도 일치합니다.",
                "검증하면서 작은 문제도 고쳤습니다. '긴급만 보기'를 켜면 빨간 막대 안의 '긴급 N건' 배지가 잘 보이지 않아, 배지 색과 "
                "테두리를 바꿨습니다(**1 File With Changes** — `app.js` +3 −2). 확인하고 **Accept all**을 누르면 Lab 4 완성입니다.",
            ],
            "prompt": P_VERIFY,
            "shot": {"stem": "ag_4v_09_verified", "caption": "필터 검증 — 공기청정기 · 긴급만 보기 = 9건, 작은 수정 1건",
                     "callouts": [
                         {"box": [801, 163, 275, 89], "label": "1주 차 0건 → 4주 차 6건", "pos": "below"},
                         {"box": [856, 306, 183, 46], "label": "공기청정기 9건 · 안전 이슈 9건", "pos": "below"},
                         {"box": [765, 670, 127, 24], "label": "1 File With Changes", "pos": "below"},
                         {"box": [1326, 670, 74, 24], "label": "Accept all", "pos": "below"},
                     ]},
            "note": "녹화에서 편집기 왼쪽에 열려 있는 **Dashboard Verification** 보고서는 STEP 3에서 만든 보고서입니다. 이번 검증의 "
                    "결과는 오른쪽 답변에 있습니다.",
        },
        {
            "title": "완성된 대시보드 직접 써 보기",
            "body": [
                "이제 에이전트가 만든 대시보드를 **내 브라우저로 직접** 열어 봅니다. Antigravity에서 `cymbal-voc` 폴더의 터미널을 "
                "열고 아래 명령을 실행한 뒤, 브라우저 주소창에 `http://localhost:8123`을 입력하세요. 다 봤으면 터미널에서 "
                "**Ctrl+C**를 눌러 서버를 끕니다.",
                "화면은 위에서부터 **안전 이슈(긴급 문의) 목록 → 핵심 지표(KPI) 4개 → 주간 문의 추이 → 제품별 · 분류별 문의 건수 → "
                "전체 문의 목록** 순서이고, 처음에는 **전체 4주**(300건) 기준입니다.",
                "- **안전 이슈 목록** 맨 위 고정 — 긴급 10건 중 미완료 6건, 이름·연락처는 마스킹(`권*윤` · `010-****-3389`)",
                "- **핵심 지표** 문의 300건(주평균 75.0건) · 안전 이슈 10건 · 처리 완료율 85.0%(미완료 45건) · 만족도 3.87점"
                "(평균 처리 22.8시간)",
                "- **주간 문의 추이** 62 → 68 → 79 → 91건, 막대 안의 빨간 배지는 그 주의 긴급 건수(1 · 1 · 2 · 6건)",
                "**4주 차 막대**를 누르면 대시보드 전체가 지난주(10/19 주) 기준으로 바뀝니다. 지난주 문의는 **91건**으로 전주보다 "
                "12건(+15.2%) 늘었고, 분류별로는 **앱 연결 24건**이 가장 많습니다. 안전 이슈 6건은 건수가 적어도 맨 위에 고정됩니다. "
                "같은 막대를 한 번 더 누르면 전체 4주로 돌아옵니다.",
                "이제 CX팀의 질문에 답해 봅니다 — **\"지난주 공기청정기 긴급 문의는 몇 건이고, 처리는 됐나요?\"** 기준 주차가 "
                "지난주인 상태에서 위쪽의 **제품 선택**을 **공기청정기**로 바꾸고 **🚨 긴급만 보기**를 켜면 바로 답이 나옵니다.",
                "- **6건** 전주(2건)보다 4건 늘었습니다(+200.0%). 주간 추이로 보면 0 → 1 → 2 → 6건",
                "- **처리 완료율 0.0%** 6건 모두 미완료(접수 3 · 처리중 3) — 목록 맨 위에 티켓 번호와 문의 내용이 마스킹된 채 표시",
                "요청서에 적혀 있던 '긴급 문의를 하루 늦게 발견한' 일을, 이제는 대시보드를 여는 순간 확인할 수 있습니다. 전체 4주로 "
                "보면 공기청정기 긴급은 9건(STEP 5)이고, 그중 지난주 6건이 아직 처리되지 않았습니다.",
            ],
            "code": {"lang": "bash", "text": "# cymbal-voc 폴더의 터미널에서 — 끝낼 때는 Ctrl+C\npython3 -m http.server 8123"},
            "shots": [
                {"stem": "ag_4v_21_dash_kpi", "caption": "핵심 지표 4개와 주간 추이(전체 4주) — 막대를 누르면 그 주로 필터링",
                 "callouts": [
                     # target D KPI 4개 (the four KPI cards)
                     {"box": [44, 105.4, 1352, 133.6], "label": "300건 · 10건 · 85.0% · 3.87점", "pos": "below"},
                     # target D 4주 차 막대 [951.8,370.7,126.3,215.1] (91건 label → bar → 4주 차 axis label + date) + 4 px
                     {"box": [947.8, 366.7, 134.3, 223.1], "label": "4주 차 · 91건", "pos": "above"},
                 ]},
                {"stem": "ag_4v_22_dash_breakdown", "caption": "4주 차 막대를 누른 뒤 — 지난주 기준 제품별 · 분류별 문의 건수",
                 "callouts": [
                     # union of leaves h2 제품별 문의 건수 [65,126.8,444.9,25.2] + p 4주 차 … 기준 (총 91건) [65,154,444.9,19.7] + 4 px
                     {"box": [61, 122.8, 452.9, 54.9], "label": "4주 차 기준 · 총 91건", "pos": "above"},
                     # targets D 안전 이슈 막대 [814.7,205.7,472.3,22] / D 앱 연결 막대 [845.9,241.7,456.5,22] (g.hbar-row) + 3 px
                     {"box": [811.7, 202.7, 478.3, 28], "label": "안전 이슈 6건", "pos": "above"},
                     {"box": [842.9, 238.7, 462.5, 28], "label": "앱 연결 24건", "pos": "below"},
                 ]},
                {"stem": "ag_4v_23_dash_filtered", "caption": "지난주 + 공기청정기 + 긴급만 보기 — 안전 이슈 6건, 모두 미완료",
                 "callouts": [
                     # targets D 기준 주차 / D 제품 선택 / D 긴급만 보기 / D 긴급·미완료 배지
                     {"box": [758.8, 26.4, 282, 36], "label": "4주 차 (지난주)", "pos": "below"},
                     {"box": [1115.2, 26.4, 131, 36], "label": "공기청정기", "pos": "below"},
                     {"box": [1260.2, 26.9, 155.8, 35.1], "label": "긴급만 보기", "pos": "below"},
                     {"box": [318.9, 136.7, 148.9, 24.7], "label": "긴급 6건 · 미완료 6건", "pos": "above"},
                 ]},
                {"stem": "ag_4v_24_dash_filtered_kpi", "caption": "같은 필터의 핵심 지표 — 6건(전주 대비 +4건), 처리 완료율 0.0%",
                 "callouts": [
                     # targets D KPI 문의 건수 / D KPI 처리 완료율 (article.kpi-card)
                     {"box": [44, 105.4, 326, 133.6], "label": "6건 · 전주 대비 +4건", "pos": "below"},
                     {"box": [728, 105.4, 326, 133.6], "label": "0.0% · 미완료 6건", "pos": "below"},
                     # union of the four week groups: x 380.9 (1주 차 label) … 1078.1 (4주 차 label), y 395.3 (6건) … 585.8
                     # (date line) + 4 px
                     {"box": [376.9, 391.3, 705.2, 198.5], "label": "0 → 1 → 2 → 6건", "pos": "above"},
                 ]},
            ],
            "tip": "서버 실행을 에이전트에게 맡겨도 됩니다(\"이 폴더에서 로컬 서버를 8123 포트로 띄워 주세요\"). 서버처럼 계속 실행되는 "
                   "명령이 남은 대화에 다음 요청을 보내면 대기열에 묶일 수 있으니, 다음 작업은 새 대화에서 시작하세요.",
            "note": "그림과 영상은 에이전트가 만든 `index.html` · `styles.css` · `app.js`를 같은 방법(로컬 서버)으로 열어 대시보드 "
                    "화면만 담은 것입니다. 날짜 표기(예: `2026-10-20`)와 단위 표시는 Lab 5에서 팀 규칙대로 다듬은 뒤의 모습이고, "
                    "숫자와 기능은 이 Lab에서 만든 그대로입니다.",
        },
    ],
    "check": [
        "Lab 3의 같은 대화에서 Proceed를 눌러 계획대로 대시보드를 만들었다",
        "Allow running this command? 카드에서 명령을 읽고 허용했다",
        "변경 검토 바(Files With Changes)에서 바뀐 파일을 확인하고 Accept all을 눌렀다",
        "연습 폴더에서 Auto Execution · Review Policy를 Always Proceed로 바꿨다 (회사 저장소는 Request Review)",
        "새 대화에서 /browser로 대시보드를 확인하고 Dashboard Verification 보고서의 스크린샷을 봤다",
        "제품 필터와 '긴급만 보기'를 추가하고, /browser로 공기청정기 · 긴급 9건이 맞는지 검증했다",
        "완성된 대시보드를 내 브라우저로 열고, 4주 차 막대 · 공기청정기 · 긴급만 보기로 지난주 긴급 6건이 모두 미완료인 것을 확인했다",
    ],
    "more": [
        "지금까지 대시보드를 만들며 지킨 규칙(이름·연락처 마스킹, 외부 CDN 금지, 숫자는 python으로 검증, 안전 이슈 맨 위, 한국어 화면)을 이 프로젝트의 AGENTS.md 초안으로 정리해 보여 주세요. 아직 파일은 만들지 마세요.",
        "data/voc_tickets.csv로 지난주(2026-10-19 주) 주간 VOC 보고 초안을 써 주세요. 핵심 3줄 · 분류별 표 · 원인 가설 · 다음 할 일 순서로, 숫자는 python으로 계산해 주세요.",
        "/browser 대시보드에서 제품을 '로봇청소기'로 고르고 4주 차(10/19)의 분류별 차트를 확인해, '앱 연결' 문의가 몇 건인지 알려 주세요. 확인한 화면은 스크린샷으로 남겨 주세요.",
    ],
}
