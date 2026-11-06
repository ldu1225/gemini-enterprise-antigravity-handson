# -*- coding: utf-8 -*-
"""AG Lab 3 — 프로젝트 받기 (cymbal-voc 스토리 Day 1 오전).

REAL recordings (1440x810 CSS, Antigravity agent IDE desktop app):
  ag3v_open · ag3v_setup · ag3v_ask · ag3v_verify · ag3v_plan · ag3v_plandoc
Stills ag_3v_* are 2880x1620 → CSS 1440x810. Every callout box below is measured — DOM boxes from
production/assets/shots/<stem>.boxes.json (targets / leaves) or Apple Vision OCR (production/qa/find_text.py)
or a pixel scan of the still for table/alert borders. Never eyeballed.

Observed in the recordings (do not over-claim):
- Trust dialog → 'Yes, I trust the authors'. Request file: 요청 사항 3개, 지켜야 할 것 4개. CSV header = 열 이름.
- Settings popover (status bar button): Auto Execution options Always Proceed / Request Review; Review Policy options
  Always Proceed / Agent Decides / Request Review. Both were Always Proceed and were changed to Request Review.
- @요청서 → Mentions list shows 요청서_CX팀.md and its heading '# [요청서] 주간 VOC 보고 자동화'.
- First answer (~45 s; agent 'Analyzed' 요청서 #L1-27 and the CSV #L1-100, #L101-302): weekly 62/68/79/91 (=300),
  safety 1/1/2/5 (=9) — the last week is WRONG (truth: 6, total 10 — answer_keys/voc_facts.json).
- Verify prompt → 'Allow running this command?' (4 options) → approved two python3 -c commands (weekly + urgent counts,
  then the urgent ticket list) → 'Worked for 32s' → 2026-10-19 urgent 6건 (정정), total 10건 (정정).
- /plan → 'Worked for 52s' → Implementation Plan card + Proceed in the chat (the editor in that take still shows the
  CSV). Feedback → 'Worked for 53s' → updated plan (4주 SVG 세로 막대 차트, 긴급 목록에 created_at · status).
- Implementation Plan tab: 1. 핵심 준수 사항 (Guardrails), 2. 생성할 파일 구성, 필수 표시 열, KPI 카드, 차트 3종.
  Proceed was NOT pressed (Lab 4 continues the same conversation).

Name hygiene (lead, 2026-10-27 — no non-public info in customer material):
- ag_3v_01_trust (dialog text with the app build name + local path) and ag_3v_05_models (non-public model names) are NOT used;
  the video also skips those moments (trust dialog, empty-editor watermark, model dropdown).
- ag_3v_02_request has a hover tooltip with a local path → replaced by ag_3v_02f_request = the real recording frame
  ag3v_open @10.79 s (frames/000178.jpg, 1920x1080 → 2880x1620 LANCZOS; editor scrolled ~148.5 px, no tooltip).
  Its boxes: Apple Vision OCR on that still ('## 요청 사항' y173.5 · '수 있게' bottom 295 · '## 지켜야 할 것' y316 ·
  '## 데이터' y424) + the DOM line pitch of ag_3v_02_request shifted by the measured scroll.
- The status bar button label of the recording build stays visible in every frame (cannot be cropped) → no callout on it.
"""

P_ASK = ("@요청서_CX팀.md 를 읽고 CX팀이 원하는 것을 3줄로 요약해 주세요. "
         "그리고 data/voc_tickets.csv의 열 구성과 주별 문의 건수를 알려 주세요.")
P_VERIFY = "표의 숫자는 눈으로 세지 말고, 터미널에서 python으로 다시 계산해서 검증해 주세요."
P_PLAN = ("/plan 요청서 1번 VOC 대시보드를 만들 계획을 세워 주세요. HTML·CSS·JavaScript만 쓰고 외부 CDN은 쓰지 마세요. "
          "안전 이슈 긴급 문의는 맨 위에 보여 주세요.")
P_FEEDBACK = "좋아요. 주간 추이는 4주 막대 차트로, 긴급 문의 목록에는 접수 일시와 상태도 넣어 주세요."

LAB = {
    "id": "lab3", "no": 3, "level": "입문", "minutes": 20, "video": "ag3",
    "title": "프로젝트 받기 — 화면 구성과 기본 사용",
    "subtitle": "요청서·데이터 파악 · @멘션 · 명령 승인 · /plan",
    "goal": "여러분은 **Cymbal 디지털혁신팀 개발자**입니다. 월요일 아침, CX팀장에게서 *매주 손으로 하던 VOC(고객의 소리) "
            "집계를 자동화해 달라*는 요청서가 도착했습니다. Lab 1·2에서 로그인한 Antigravity로 실습 폴더 `cymbal-voc`를 열고, "
            "**요청서와 데이터 파악 → 숫자는 도구로 검증 → `/plan`으로 VOC 대시보드 계획 세우기**까지 진행합니다. "
            "에이전트가 무엇을 하기 전에 **내가 언제 승인하고 검토하는지** 익히는 것이 핵심입니다. "
            "여기서 세운 계획은 Lab 4에서 같은 대화를 이어 실제 대시보드로 만듭니다.",
    "steps": [
        {
            "title": "실습 폴더 열기와 요청서 읽기",
            "body": [
                "포털 **실습 파일**에서 `Cymbal_VOC_스타터.zip`을 내려받아 압축을 풉니다. 안에 든 `cymbal-voc` 폴더 하나를 "
                "Lab 3부터 Lab 10까지 계속 키워 갑니다.",
                "Antigravity에서 `cymbal-voc` 폴더를 엽니다. 처음 여는 폴더라면 **Do you trust the authors of the files in this "
                "folder?** 창이 뜹니다. 폴더 안의 파일이 자동으로 실행될 수도 있어서, 믿을 수 있는 폴더인지 묻는 것입니다. "
                "내가 받은 실습 폴더이므로 **Yes, I trust the authors**를 누릅니다(No를 고르면 일부 기능이 꺼진 제한 모드로 열립니다).",
                "화면은 크게 세 영역입니다. 왼쪽 **Explorer**(파일 목록), 가운데 **편집기**(파일과 계획서 보기), "
                "오른쪽 **Agent 패널**(에이전트와 대화)입니다.",
                "Explorer에서 이번 프로젝트의 출발점인 `요청서_CX팀.md`를 열어 읽어 보세요.",
                "- **요청 사항** ① VOC 대시보드(주간 문의 건수, 제품별·분류별 건수, 주간 추이, 긴급 문의 목록) "
                "② 주간 보고 자동화(매주 월요일 08:30) ③ VOC 도우미(팀원이 Gemini Enterprise에서 질문)",
                "- **지켜야 할 것** 고객 이름·연락처 마스킹, 외부 CDN·외부 스크립트 금지(차트도 직접 그리기), 한국어, "
                "안전 이슈는 건수가 적어도 맨 위에",
                "이어서 `data` 폴더의 `voc_tickets.csv`를 엽니다. 2026-09-28부터 10-25까지 4주 동안 들어온 "
                "**가상 고객 문의 300건**이 한 줄에 하나씩 들어 있고, 첫 줄(머리글)이 열 이름입니다 "
                "(`ticket_id`, `created_at`, `week_start`, `channel`, `product`, `category`, `severity`, `status` …).",
            ],
            "shots": [
                {"stem": "ag_3v_02f_request", "caption": "요청서_CX팀.md — 요청 사항과 지켜야 할 것",
                 "callouts": [
                     {"box": [400, 166, 576, 136], "label": "요청 사항", "pos": "above"},
                     {"box": [400, 310, 552, 101], "label": "지켜야 할 것", "pos": "below"},
                 ]},
                {"stem": "ag_3v_03_data", "caption": "data/voc_tickets.csv — 첫 줄이 열 이름",
                 "callouts": [
                     {"box": [42, 180, 299, 22], "label": "voc_tickets.csv", "pos": "below"},
                     {"box": [406, 87, 628, 18], "label": "열 이름 — ticket_id, created_at, week_start …", "pos": "below"},
                 ]},
            ],
            "note": "이 트랙의 화면은 녹화 당시의 Antigravity 빌드로 녹화했습니다. 앱 이름이나 아이콘이 조금 다르게 보일 수 "
                    "있지만 에이전트 기능과 사용 방법은 같습니다. 실습 데이터는 모두 가상입니다.",
        },
        {
            "title": "권한 · 패널 · 모델 준비",
            "body": [
                "일을 맡기기 전에, **에이전트가 무엇을 하기 전에 내 확인을 받을지**부터 정합니다. 화면 오른쪽 아래 상태 표시줄의 "
                "**Settings** 버튼(에이전트 설정)을 누르면 설정 창이 열립니다.",
                "- **Auto Execution** 에이전트가 터미널 명령을 실행할 때 — **Always Proceed**(바로 실행) 또는 "
                "**Request Review**(실행 전에 내 승인)",
                "- **Review Policy** 계획서 같은 결과물을 만든 뒤 — **Always Proceed**(바로 진행) · **Agent Decides**"
                "(에이전트가 판단) · **Request Review**(내 검토 후 진행)",
                "녹화에서는 둘 다 **Always Proceed**였던 것을 **Request Review**로 바꿨습니다. 처음에는 이렇게 두고, 에이전트가 "
                "하려는 일을 하나씩 확인하며 익히세요. 같은 버튼을 한 번 더 누르면 설정 창이 닫힙니다.",
                "표와 계획서를 읽기 편하도록 **Agent 패널을 넓힙니다**. 편집기와 Agent 패널 사이의 경계선을 왼쪽으로 끌면 됩니다.",
                "입력창 아래 **모델 선택**을 눌러 **Gemini 4 Argon Medium**을 고릅니다. 고른 모델은 입력창 아래에 표시됩니다"
                "(STEP 3 화면 참고). 목록에 새 모델 **Gemini 4 Carbon**이 보이면 Carbon을 골라도 같은 흐름으로 진행됩니다"
                "(요금제 · 관리자 허용 모델에 따라 보이지 않을 수 있음).",
            ],
            "shot": "ag_3v_04_settings", "caption": "Settings → Auto Execution · Review Policy를 Request Review로",
            "callouts": [
                {"box": [1092, 355, 323, 24], "label": "Auto Execution · Request Review", "pos": "above"},
                {"box": [1092, 389, 323, 24], "label": "Review Policy · Request Review", "pos": "below"},
            ],
            "note": "공개 Antigravity 앱에서는 권한 프리셋(**Request Review** · **Default**(샌드박스) · **Auto** · **Turbo**)으로 "
                    "같은 내용을 고르며, 메뉴 이름과 위치는 버전에 따라 조금 다를 수 있습니다. 모델 목록도 계정·요금제에 따라 "
                    "다르게 보입니다. 회사 계정이라면 관리자가 정한 보안 정책(Lab 1)이 우선 적용됩니다.",
        },
        {
            "title": "@멘션으로 요청서와 데이터 파악하기",
            "body": [
                "Agent 패널 입력창에 `@`와 파일 이름 앞부분(`요청서`)을 입력하면 **멘션 후보**가 뜹니다. 후보에는 파일 "
                "`요청서_CX팀.md`와 그 파일의 제목 줄(`# [요청서] 주간 VOC 보고 자동화`)이 함께 보입니다. "
                "**요청서_CX팀.md**를 고르면(Enter) 에이전트가 *어느 파일을 보고 답해야 하는지* 정확히 알 수 있습니다.",
                "이어서 나머지 질문을 쓰고 보냅니다. 아래 프롬프트를 통째로 붙여 넣기보다, `@요청서`까지는 직접 입력해 후보를 "
                "고른 뒤 나머지 문장을 붙여 넣으세요.",
                "에이전트는 요청서(27줄)와 CSV를 끝까지 읽은 뒤(**Analyzed** 표시) 답합니다. 실습에서는 약 45초 걸렸습니다.",
                "답에는 ① CX팀 요청 3줄 요약 ② 열 구성 표(이름·연락처 열은 *마스킹 대상*으로 표시) ③ **주별 문의 건수 표**가 "
                "들어 있습니다. 주별 문의는 **62 → 68 → 79 → 91건**(합계 300건)으로 4주 내내 늘었고, 맨 오른쪽 열에는 "
                "**긴급(안전 이슈) 건수 1 · 1 · 2 · 5건(합계 9건)** 도 세어 주었습니다.",
                "그런데 이 숫자를 그대로 믿어도 될까요? 다음 단계에서 확인합니다.",
            ],
            "prompt": P_ASK,
            "shots": [
                {"stem": "ag_3v_06_mention", "caption": "@요청서 입력 → 멘션 후보에서 요청서_CX팀.md 고르기",
                 "callouts": [
                     {"box": [724, 278, 122, 21], "label": "요청서_CX팀.md", "pos": "above"},
                     {"box": [753, 387.2, 156.1, 28], "label": "Gemini 4 Argon Medium", "pos": "below"},
                 ]},
                {"stem": "ag_3v_08_answer", "caption": "첫 답 — 주별 문의 건수와 긴급(안전 이슈) 건수",
                 "callouts": [
                     {"box": [725, 336, 329, 215], "label": "주별 문의 건수", "pos": "above"},
                     {"box": [1214, 336.5, 190, 214], "label": "긴급(안전 이슈) 건수", "pos": "above"},
                 ]},
            ],
            "tip": "질문할 때 파일을 `@`로 짚어 주면, 에이전트가 엉뚱한 파일을 찾느라 헤매지 않고 답도 더 정확해집니다.",
        },
        {
            "title": "숫자는 도구로 검증 — 명령 실행 승인",
            "body": [
                "AI가 300줄을 *읽고 세어서* 만든 표는 틀릴 수 있습니다. 같은 대화에서 **터미널에서 python으로 다시 계산해 "
                "검증**해 달라고 요청합니다.",
                "에이전트가 python 명령을 실행하려 하면, STEP 2에서 **Auto Execution = Request Review**로 해 두었기 때문에 "
                "**Allow running this command?** 카드가 먼저 나타납니다. 실행할 명령이 그대로 보이니 읽어 보고 고릅니다.",
                "1. **Yes, allow this time** 이번 한 번만 허용",
                "2. **Yes, and always allow '…' in this conversation** 이 대화에서는 같은 명령을 계속 허용",
                "3. **Yes, and always allow '…'** 앞으로 같은 명령을 항상 허용",
                "4. **No (tell the agent what to do instead)** 거절하고 대신 할 일을 알려 주기",
                "**Yes, allow this time**을 고르고 **Submit**을 누릅니다. 녹화에서는 에이전트가 ① 주별·긴급 건수 집계 "
                "② 긴급 문의 목록 출력, 두 개의 명령을 차례로 요청해 두 번 승인했고, 약 30초 만에 결과가 나왔습니다.",
                "결과: 주별 문의 건수(62 · 68 · 79 · 91건, 합계 300건)는 같았지만 **2026-10-19 주 긴급 건수가 5건 → 6건(정정)**, "
                "**합계 9건 → 10건(정정)** 으로 바뀌었습니다. 첫 답은 눈으로 세다가 한 건을 놓쳤던 것입니다.",
            ],
            "prompt": P_VERIFY,
            "shots": [
                {"stem": "ag_3v_07_allow", "caption": "Allow running this command? — 명령을 읽고 허용",
                 "callouts": [
                     {"box": [718, 255, 704, 150], "label": "Allow running this command?", "pos": "above"},
                     {"box": [722, 417, 142, 26], "label": "Yes, allow this time", "pos": "below"},
                     {"box": [1343, 733, 81, 32], "label": "Submit", "pos": "above"},
                 ]},
                {"stem": "ag_3v_08b_verified", "caption": "python으로 다시 계산 — 긴급 건수 정정(5 → 6, 9 → 10)",
                 "callouts": [
                     {"box": [724, 146, 668, 96], "label": "다시 집계해 검증했습니다", "pos": "above"},
                     {"box": [1214, 441, 190, 71], "label": "6건 (정정) · 10건 (정정)", "pos": "below"},
                 ]},
            ],
            "tip": "**AI 답의 숫자는 도구로 검증하게 하세요.** 보고서나 대시보드에 들어갈 숫자라면 \"python으로 다시 계산해서 "
                   "확인해 주세요\"를 습관처럼 붙이세요. 매번 말하지 않아도 되도록 팀 규칙으로 만드는 방법은 Lab 5에서 다룹니다.",
            "note": "모르는 명령이 보이면 **No**를 고르고 \"이 명령이 무슨 일을 하는지 먼저 설명해 주세요\"라고 적어 보세요. "
                    "승인하기 전에는 언제든 물어볼 수 있습니다.",
        },
        {
            "title": "/plan으로 대시보드 계획 세우고 피드백하기",
            "body": [
                "이제 요청 사항 1번 **VOC 대시보드**의 계획을 세웁니다. 입력창 맨 앞에 `/plan`을 붙이면 에이전트가 바로 만들지 "
                "않고 먼저 **Implementation Plan**(구현 계획서)을 씁니다. 요청서의 *지켜야 할 것* 가운데 중요한 조건"
                "(HTML·CSS·JavaScript만, 외부 CDN 금지, 안전 이슈 맨 위)을 프롬프트에 함께 적었습니다.",
                "실습에서는 약 50초 뒤 채팅에 **Implementation Plan** 카드와 **Proceed** 버튼이 나타났습니다. Proceed는 "
                "*계획대로 만들기 시작*하는 버튼입니다. 아직 누르지 말고 고칠 점부터 말합니다.",
                "같은 대화에 아래 **피드백 프롬프트**를 보냅니다. 약 50초 뒤 계획이 업데이트되고, 채팅에 바뀐 내용"
                "(**주간 문의 추이** 4주 SVG 세로 막대 차트, **최상단 긴급 문의 목록**에 접수 일시·상태 열)이 요약됩니다.",
                "편집기 위쪽의 **Implementation Plan** 탭을 누르면 계획서 전체를 읽을 수 있습니다. **1. 핵심 준수 사항(Guardrails)**"
                "에 안전 이슈 최상단 고정 · 외부 CDN 금지 · 개인정보 마스킹(예: `조*윤`, `010-****-8299`) · 한국어 UI가, "
                "**2. 생성할 파일 구성**에 `index.html` · `styles.css` …가 정리되어 있습니다. 아래로 내리면 긴급 문의 목록의 "
                "**필수 표시 열**과 KPI 카드, 차트 3종까지 적혀 있습니다.",
                "**Proceed는 누르지 않고** 여기서 마칩니다. Lab 4에서 *같은 대화*를 이어 Proceed를 누르고 대시보드를 만듭니다.",
            ],
            "prompt": P_PLAN,
            "code": {"lang": "text", "label": "피드백 프롬프트 — 같은 대화에 이어서 보내기", "text": P_FEEDBACK},
            "shots": [
                {"stem": "ag_3v_09_plan", "caption": "/plan 결과 — 채팅의 Implementation Plan 카드와 Proceed",
                 "callouts": [
                     {"box": [726, 258, 678, 62], "label": "Implementation Plan", "pos": "above"},
                     {"box": [726, 327.5, 60.4, 26.2], "label": "Proceed", "pos": "below"},
                 ]},
                {"stem": "ag_3v_10_plan_updated", "caption": "피드백 반영 — 4주 막대 차트 · 접수 일시와 상태 열",
                 "callouts": [
                     {"box": [726, 209, 669, 42], "label": "주간 문의 추이 · 최상단 긴급 문의 목록", "pos": "above"},
                     {"box": [726, 367.4, 60.4, 26.2], "label": "Proceed", "pos": "below"},
                 ]},
                {"stem": "ag_3v_11_plan_doc", "caption": "Implementation Plan 탭 — 핵심 준수 사항과 생성할 파일",
                 "callouts": [
                     {"box": [54, 246.6, 623, 294], "label": "1. 핵심 준수 사항 (Guardrails)", "pos": "above"},
                     {"box": [54, 581.4, 623, 206.6], "label": "2. 생성할 파일 구성", "pos": "above"},
                     {"box": [620, 73, 64, 32], "label": "Proceed", "pos": "below"},
                 ]},
                {"stem": "ag_3v_12_plan_doc_more", "caption": "계획서 아래쪽 — 긴급 문의 목록의 필수 표시 열과 4주 막대 차트",
                 "callouts": [
                     {"box": [68, 140, 432, 194], "label": "필수 표시 열", "pos": "below"},
                     {"box": [68, 565, 610, 75], "label": "주간 문의 추이 (4주 막대 차트)", "pos": "below"},
                 ]},
            ],
            "tip": "계획서 위쪽의 **Review** 메뉴로 계획서에 댓글을 남길 수도 있습니다. 채팅이든 댓글이든, 만들기 전에 "
                   "고치는 편이 만든 뒤에 고치는 것보다 훨씬 빠릅니다.",
            "note": "계획서의 파일 구성 · 차트 모양 · 마스킹 예시는 만들 때마다 조금씩 달라질 수 있습니다. 요청서의 "
                    "*지켜야 할 것*이 빠지지 않았는지만 확인하세요.",
        },
    ],
    "check": [
        "cymbal-voc 폴더를 열고 Yes, I trust the authors로 신뢰했다",
        "요청서의 요청 사항 3가지와 지켜야 할 것을 확인했다",
        "Auto Execution과 Review Policy를 Request Review로 바꿨다",
        "@멘션으로 요청서를 짚어 요약과 주별 문의 건수를 받았다",
        "명령 실행 승인 카드에서 명령을 읽고 허용해, python으로 숫자를 검증했다",
        "/plan으로 Implementation Plan을 받고 피드백으로 계획을 고쳤다 (Proceed는 Lab 4에서)",
    ],
    "more": [
        "@요청서_CX팀.md 의 '지켜야 할 것' 4가지가 Implementation Plan에 모두 반영됐는지 표로 점검해 주세요. 빠진 항목이 있으면 계획서에 추가해 주세요.",
        "data/voc_tickets.csv에서 지난주(2026-10-19 주) 분류별 문의 건수를 python으로 계산해 표로 보여 주세요. 전주보다 가장 많이 늘어난 분류도 알려 주세요.",
        "계획서의 KPI 카드 4개에 실제로 어떤 값이 들어갈지, data/voc_tickets.csv를 python으로 계산해 미리 알려 주세요. 아직 파일은 만들지 마세요.",
    ],
}
