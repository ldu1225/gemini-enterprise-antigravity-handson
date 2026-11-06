# -*- coding: utf-8 -*-
"""AG Lab 7 — 임원 보고 슬라이드 (cymbal-voc 스토리 Day 4) — 회사 템플릿으로 다시 녹화 (2026-11-02).

REAL recordings (1440x810 CSS, Antigravity agent IDE desktop app):
  ag7v_slides · ag7v_pdf · ag7v_edit   (production/capture/agy/agv.py l7_slides / l7_pdf / l7_edit)
Headless showcase captures of REAL files (production/capture/agy/ag7_deck.py — page content only, no browser chrome):
  ag7v_deck / ag_7v_21…26_deck_s1…s6 = slides/weekly_2026-10-19.html after the STEP 3 edit (the agent's file)
  ag7v_before / ag_7v_13_s2_before · ag_7v_14_s3_before = the same file before the STEP 3 edit (byte copy at 13:37)
  ag7v_template / ag_7v_00_template = templates/exec_deck_template.html (starter file: company template)
Stills ag_7v_* are 2880x1620 → CSS 1440x810. Every callout box below is measured — DOM boxes from
production/assets/shots/<stem>.boxes.json (targets / leaves; union targets = every visible match of one selector),
Apple Vision OCR (production/qa/find_text.py, ÷2 for the 2x crops) or a pixel scan of card borders. Never eyeballed.

Derived stills (crops, 2 image px per CSS px — `viewport` = crop size; provenance in <stem>.crop.json /
<stem>.boxes.json "derived"), made by scratch/make_l7_stills.py:
- ag_7v_01c_mcp     = ag7v_slides frame @78.6 s, crop [916, 36, 524, 742]: 3rd MCP card (query with customer_name, phone)
- ag_7v_02p_answer  = ag_7v_02_slides crop [916, 180, 524, 520]: Worked for 5m · 슬라이드별 주요 반영 내용 · Accept all
- ag_7v_03c_check   = ag7v_pdf frame @205 s, crop [916, 36, 524, 600]: Playwright run · Analyzed Slide 01–06 · PDF
- ag_7v_03p_done    = ag_7v_03b_pdf_done crop [916, 148, 524, 552]: screenshots · 데이터 출처 · Walkthrough · +2 −0
- ag_7v_05p_walk    = ag_7v_05_report_more crop [344, 66, 566, 700]: Walkthrough artifact (slide 1 image, file table)
- ag_7v_06c_changes = ag7v_edit frame @478.98 s, crop [916, 186, 524, 440]: 주요 변경 내역 (the frames right after
  stream raw markdown image links with local paths — 479.1–482.5 s; this frame has none, OCR-checked)
- ag_7v_13c_s2_before / ag_7v_22c_s2_after = crop [130, 196, 1180, 516] of the before / final slide 2
- ag_7v_14c_s3_before / ag_7v_23c_s3_after = crop [130, 343, 677, 399] of the before / final slide 3 (chart card)

Not used: ag_7v_01_making / ag_7v_03_browser / ag_7v_06_editing ('Analyzed <local path>' rows), ag_7v_04_report (full
window), the full-window end shots (status bar). Leak windows the video skips (scratch/scan_all.py, every frame OCR'd):
ag7v_slides 49.5–68.6 s ('Analyzed <local path>' row) and 364.0–366.0 s (raw links while the answer streams); ag7v_pdf and
ag7v_edit: see scratch/l7_pdf_scan.txt / l7_edit_scan.txt (edit 110–150 s row, 479.1–482.5 s raw image links).

Observed in the recordings (do not over-claim):
- SLIDES (new chat, submit 18.6 s): read voc-weekly-report/SKILL.md, exec_deck_template.html, the BigQuery tool schema,
  요청서_CX팀.md, lab.env, reports/ → 4 × 'Allow using this MCP tool?' (bigquery/execute_sql_readonly; Tool arguments =
  projectId + query): ① weekly total/safety/urgent/open/status counts ② week × category × product counts ③ last-week
  safety/urgent/앱 연결 tickets incl. customer_name, phone, message ④ 로봇청소기 앱 연결 daily counts. Each 'Yes, allow
  this time' → Submit (69.6 / 73.8 / 78.0 / 149.0 s). Read last week's reports, wrote slides/weekly_2026-10-19.html
  (+456), grep'd for leftover [brackets]. Answer at 375.7 s ('Worked for 5m'), Accept all 432.2 s.
- PDF (new chat, '/browser …', submit 14.0 s): no built-in browser window in this build → the agent drove headless
  Chrome with Playwright (python3 -c): 6 slide PNGs + full-page PNG + PDF, opened its own PNGs and the PDF, read the
  template's print styles (L230–260) and added 2 print rules to the deck (+2 −0: print-color-adjust exact · cover
  stays a grid), re-exported, wrote a 'Walkthrough' artifact (rule check · 6-slide carousel · file table). Answer
  ≈ 6 min after submit; Accept all 435.7 s; Walkthrough opened 439.1 s. PDF = 6 pages, 960×540 pt (16:9).
- EDIT (new chat, submit 14.0 s): read the deck, its slide_02/03 PNGs, the template, reports, the CSV; 'Thinking for
  39s' (white stroke halo so the numbers stay legible on the orange bar); Edited weekly_2026-10-19.html +7 −3 (≈330 s);
  the first re-export failed (Playwright's own Chromium not installed → 'playwright install' message), re-run with the
  installed Chrome; viewed the new PNGs; answer with 주요 변경 내역 + both changed slides embedded (≈476–490 s);
  1 file changed +7 −3; Accept all 537.3 s.
Data check (production/samples/v2/answer_keys/voc_facts.json + data/voc_tickets.csv): 91 vs 79 (+12, +15.2%); weekly
62 · 68 · 79 · 91; safety 1 · 1 · 2 · 6, last week 6 = all 공기청정기 adapter (과열·타는 냄새 2 · 변형 2 · 연기 2), all open
(접수 3 · 처리중 3); open last week 45 (접수 23 · 처리중 22); 앱 연결 8 · 9 · 19 · 24; 로봇청소기 앱 연결 3 · 1 · 13 · 20
(+53.8%, 20/91 = 22.0%, 20/24 = 83.3%), daily 0–1 until 10-14 (6 on 10-14); last-week 20 = 연결 끊김 8 · 오프라인 6 ·
예약 기능 3 · 페어링 3, open 9 (접수 4 · 처리중 5); safety last 3 weeks 9 (all adapter). Every number in the deck matches.
Not in the data (told to the learner in STEP 4): the '2026-10-14 앱 업데이트' cause (inferred from messages such as
'앱 업데이트 후 … 예약 기능이 사라졌어요' + the daily spike), owners/dates on slide 6, and slide 3's category chart shows
5 of 7 categories (사용법 11 · 환불·교환 8 left out) under the note '많은 순'.
"""

P_SLIDES = ("voc-weekly-report 스킬과 BigQuery MCP로 지난주(2026-10-19 ~ 2026-10-25) 데이터를 확인해서, "
            "templates/exec_deck_template.html 회사 템플릿으로 임원 보고 슬라이드 6장을 slides/weekly_2026-10-19.html로 "
            "만들어 주세요. 템플릿의 CSS와 발표 모드는 그대로 두고 [대괄호] 자리만 실제 데이터로 채워 주세요. "
            "1 표지 2 핵심 3줄 3 주간 추이 4 안전 이슈 긴급 문의(미완료 강조) 5 로봇청소기 앱 연결 급증 6 다음 할 일. "
            "AGENTS.md 규칙을 지켜 주세요.")
P_PDF = ("/browser slides/weekly_2026-10-19.html을 열어 6장이 잘 보이는지 확인하고, 한 장에 한 슬라이드씩 "
         "slides/weekly_2026-10-19.pdf로 내보내 주세요. 확인한 화면은 스크린샷으로 남겨 주세요.")
P_EDIT = ("2번 슬라이드 핵심 3줄은 문장이 길어서 한 줄로 읽히게 짧게 줄여 주세요. 3번 슬라이드 주별 접수 차트의 "
          "빨간 안전 이슈 선에는 주별 건수를 숫자로 표시해 주세요. "
          "고친 뒤 PDF를 다시 내보내고, 바뀐 두 장의 스크린샷을 보여 주세요.")

LAB = {
    "id": "lab7", "no": 7, "level": "기본", "minutes": 25, "video": "ag7",
    "title": "임원 보고 슬라이드",
    "subtitle": "회사 템플릿 + 스킬 + BigQuery 데이터 → 슬라이드 6장 → /browser · PDF → 피드백 반영",
    "goal": "Lab 6에서 **BigQuery MCP**를 연결하고 `voc-weekly-report` 스킬이 BigQuery 데이터를 읽도록 바꿨습니다. "
            "이번에는 요청서 2번의 남은 조각, **임원 보고 슬라이드**입니다. CX팀장이 *월요일 임원 회의에 띄울 주간 VOC "
            "보고 6장*을 부탁했고, 회사에는 정해진 **임원 보고 템플릿**(`templates/exec_deck_template.html`)이 있습니다. "
            "에이전트에게 *디자인은 템플릿 그대로, 내용만 실제 데이터로* 채우게 하면 STEP 1 첫 그림 같은 **16:9 슬라이드 "
            "6장**이 나오고, 브라우저에서 **발표 모드**로 한 장씩 넘겨 볼 수 있습니다(STEP 4). **템플릿 + 스킬 + MCP "
            "데이터로 슬라이드 만들기 → `/browser`로 확인하고 PDF로 내보내기 → 팀장 피드백 반영 → 완성된 6장 검토**까지 "
            "진행합니다. 핵심은 세 가지입니다. *디자인은 템플릿에, 데이터는 에이전트에* 맡기는 것, MCP 승인 카드의 SQL로 "
            "*어떤 데이터를 가져오는지* 확인하는 것, 그리고 보고 전에 *숫자를 내 눈으로 검증*하는 것입니다.",
    "steps": [
        {
            "title": "회사 템플릿 + 스킬 + BigQuery MCP로 슬라이드 만들기",
            "body": [
                "완성하면 아래 첫 그림처럼 임원 회의에 바로 띄울 16:9 슬라이드 6장이 나옵니다. 6장 모두는 STEP 4에서 "
                "발표 모드로 넘겨 봅니다.",
                "먼저 회사 템플릿을 봅니다. 스타터 폴더의 `templates/exec_deck_template.html`은 CX팀의 **임원 보고 "
                "템플릿**입니다. 둘째 그림처럼 디자인은 완성되어 있고, 숫자와 문장 자리는 `[N]건`, `[YYYY-MM-DD]`처럼 "
                "**대괄호**로 비어 있습니다. 6장 구성(표지 · 핵심 3줄 · 주간 추이 · 안전 이슈 · 급증 분석 · 다음 할 일), "
                "차트 그리는 법, 발표 모드, 인쇄 설정까지 들어 있고, 파일 맨 위 주석에 *채우는 규칙*이 적혀 있습니다. "
                "외부 CDN 없이 파일 하나로 되어 있어 사내 보안 규칙(`AGENTS.md`)에도 맞습니다.",
                "Lab 6에 이어 같은 `cymbal-voc` 폴더에서 작업합니다. Agent 패널 오른쪽 위 **+**(새 대화)를 눌러 새 대화를 "
                "엽니다. 하는 일이 바뀌면 새 대화로 시작해야 앞 대화의 내용이 섞이지 않습니다.",
                "아래 프롬프트를 붙여 넣고 보냅니다. **쓸 스킬**(`voc-weekly-report`)과 **데이터 출처**(BigQuery MCP), "
                "**기간**, **템플릿 파일**과 *CSS · 발표 모드는 그대로 두고 [대괄호] 자리만 채우라*는 규칙, **슬라이드 6장의 "
                "순서**, `AGENTS.md` 규칙을 한 번에 적었습니다.",
                "에이전트는 스킬 설명서(`SKILL.md`), 템플릿, 요청서, `lab.env`를 읽은 뒤 BigQuery MCP 도구 "
                "`execute_sql_readonly`를 부르려 합니다. 그때마다 **Allow using this MCP tool?** 카드가 뜨고, 바로 위 "
                "**Tool arguments**에 에이전트가 실행할 **SQL**(`query`)이 그대로 보입니다. 녹화에서는 네 번 물었습니다.",
                "1. 주별 전체 · 안전 이슈 · 긴급 · 미완료 · 상태별 건수",
                "2. 주 · 분류 · 제품별 건수",
                "3. 지난주 안전 이슈 · 긴급 · 앱 연결 문의 목록 — 고객 이름(`customer_name`)과 연락처(`phone`) 열도 "
                "가져옵니다(셋째 그림)",
                "4. 로봇청소기 앱 연결 문의의 **날짜별** 건수 — 급증이 시작된 날을 찾는 쿼리입니다",
                "네 번 모두 SQL을 읽어 보고 **Yes, allow this time** → **Submit**으로 허용했습니다. 이름 그대로 읽기 전용 "
                "쿼리를 실행하는 도구입니다. 3번처럼 개인정보 열을 가져온 경우에는, 슬라이드에 **마스킹**되어 나오는지 "
                "STEP 4에서 꼭 확인하세요.",
                "에이전트는 지난주 보고서(`reports/`)도 읽고, 템플릿을 바탕으로 대괄호 자리를 채운 파일을 쓴 뒤 남은 "
                "`[대괄호]`가 없는지 직접 검색까지 했습니다. 녹화에서는 약 6분 뒤 답이 나왔습니다(**Worked for 5m**). "
                "`slides/weekly_2026-10-19.html`이 새로 생기고(+456줄), 답변에 **슬라이드별 주요 반영 내용**이 정리됩니다.",
                "- **1 표지** 맨 위 안전 경보 배너(안전 이슈(긴급) 6건 · 공기청정기 전원 어댑터 발열 · 변형 · 연기 — 6건 "
                "미완료), 오른쪽 핵심 지표 4개(안전 이슈 6건 · 총 접수 91건 +15.2% · 로봇청소기 앱 연결 20건 +53.8% · "
                "미완료 45건)",
                "- **2 핵심 3줄** ① 공기청정기 어댑터 문의 6건(전주 2건의 3배, 전 건 미완료: 접수 3 · 처리중 3) ② 총 "
                "91건(전주 79건 대비 +12건, +15.2%), 3주 연속 증가 ③ 로봇청소기 앱 연결 13 → 20건(+53.8%), 전체의 22.0%",
                "- **3 ~ 6** 주간 추이 차트 2개 · 안전 이슈 6건 표(미완료 강조, 고객명 · 연락처 마스킹) · 앱 연결 주별 "
                "추이와 2026-10-14 시점 표시 · 다음 할 일 3단계(담당 · 기한)",
                "답변 끝의 **AGENTS.md 규칙 준수 확인**(한국어 · 마스킹 · 외부 CDN 금지 · 날짜 형식 · 안전 이슈 최우선 · 데이터 "
                "출처 표기)까지 읽고, 답변 아래 변경 검토 바(**1 File With Changes**)에서 **Accept all**을 누릅니다.",
            ],
            "prompt": P_SLIDES,
            "shots": [
                {"stem": "ag_7v_21_deck_s1",
                 "caption": "완성하면 이런 6장이 나옵니다 — 1번 표지 (회사 템플릿 디자인 + BigQuery 데이터. STEP 4에서 6장을 "
                            "모두 넘겨 봅니다)"},
                {"stem": "ag_7v_00_template",
                 "caption": "회사 임원 보고 템플릿(templates/exec_deck_template.html) — 디자인은 완성, 숫자 · 문장 자리는 "
                            "[대괄호]",
                 "callouts": [
                     {"box": [148.8, 181.1, 684.3, 50.6], "label": "안전 이슈(긴급) [N]건 · [제품·증상 한 줄] — [N]건 미완료",
                      "pos": "below"},
                     {"box": [928.3, 156.3, 386.8, 335.2], "label": "[N]건 × 4 — 핵심 지표 자리", "pos": "below"},
                 ]},
                {"stem": "ag_7v_01c_mcp", "viewport": [524, 742],
                 "caption": "Allow using this MCP tool? — Tool arguments의 SQL(고객 이름 · 연락처 열 포함)을 읽고 "
                            "Yes, allow this time → Submit",
                 "callouts": [
                     {"box": [56, 338, 424, 110], "label": "query: SELECT … customer_name, phone …", "pos": "above"},
                     {"box": [7.5, 485.5, 507, 104.5], "label": "Allow using this MCP tool? · 1 Yes, allow this time",
                      "pos": "above"},
                     {"box": [429, 697, 77, 32], "label": "Submit", "pos": "above"},
                 ]},
                {"stem": "ag_7v_02p_answer", "viewport": [524, 520],
                 "caption": "답변 — 회사 템플릿의 CSS · 발표 모드를 유지한 6장, 슬라이드별 주요 반영 내용 → Accept all",
                 "callouts": [
                     {"box": [21, 153, 470, 133], "label": "슬라이드 1 — 표지: 안전 경보 배너 · 지표 4개", "pos": "above"},
                     {"box": [35, 291, 458, 156], "label": "슬라이드 2 — 핵심 3줄", "pos": "inside"},
                     {"box": [409, 490, 76, 24], "label": "Accept all", "pos": "above"},
                 ]},
            ],
            "tip": "회사에 정해진 양식이 있다면 **템플릿 파일을 주고 '자리만 채워 달라'** 고 하세요. 디자인을 매번 새로 "
                   "만들지 않으니 결과가 고르고, 다음 주에도 같은 모양의 보고서가 나옵니다. 같은 대화에서 비슷한 조회가 "
                   "계속된다면 **Yes, and always allow in this conversation**을 골라도 됩니다.",
            "note": "문장과 세부 배치는 만들 때마다 조금씩 달라집니다. 숫자(91건, +15.2%, 안전 이슈 6건 …)는 같은 데이터에서 "
                    "나오므로 같아야 합니다. 녹화 화면의 `projectId`는 데모 프로젝트이며, 여러분의 화면에는 Lab 6에서 연결한 "
                    "프로젝트가 보입니다.",
        },
        {
            "title": "/browser로 확인하고 PDF로 내보내기",
            "body": [
                "다시 **+**로 새 대화를 열고, 입력창 맨 앞에 `/browser`를 붙여 확인과 PDF 내보내기를 맡깁니다. "
                "`/browser`는 에이전트가 *브라우저로 직접 열어 보고* 확인하게 하는 명령입니다(Lab 4에서 대시보드를 확인할 "
                "때와 같습니다). **한 장에 한 슬라이드**, **스크린샷 남기기**처럼 결과물 조건도 함께 적었습니다.",
                "에이전트는 슬라이드 파일과 스킬 설명서를 읽고, 화면 없이 실행되는 **헤드리스 브라우저**(Chrome)를 "
                "Playwright로 띄웠습니다. 슬라이드별 스크린샷 6장과 PDF를 만든 뒤, **자기가 만든 스크린샷과 PDF를 직접 "
                "열어** 확인합니다(첫 그림 — **Analyzed Slide 01 ~ Slide 06**, `weekly_2026-10-19.pdf`).",
                "PDF를 본 에이전트는 템플릿의 인쇄용 설정(`@media print`)을 확인하고, 슬라이드 HTML에 인쇄 규칙 두 줄을 "
                "더했습니다(**+2 −0**). 인쇄할 때도 배경색을 그대로 찍는 설정(`print-color-adjust: exact`)과, 표지의 "
                "2단 배치를 유지하는 설정입니다. 그리고 PDF를 다시 내보냈습니다. 녹화에서는 약 6분 뒤 답이 나왔습니다.",
                "- **내보낸 PDF** `slides/weekly_2026-10-19.pdf` — 1~6페이지, 한 페이지에 한 슬라이드(16:9), 배경 색상 · "
                "SVG 차트 · 표지 2단 레이아웃 포함",
                "- **스크린샷** 전체 화면 `weekly_2026-10-19_screenshot.png`, 슬라이드별 `weekly_2026-10-19_slide_01.png` "
                "~ `_slide_06.png`",
                "- **Walkthrough** 카드 — 규칙 준수 확인, 6장 스크린샷(넘겨 보기), 저장된 파일 목록을 모은 확인 문서",
                "답변 끝에는 **데이터 출처: BigQuery cymbal_cx.voc_tickets | 기준일: 2026-10-25**가 적혀 있습니다. 점검하면서 "
                "HTML이 바뀌었으므로(**1 File With Changes**) 확인하고 **Accept all**을 누릅니다.",
                "**Walkthrough** 카드를 누르면 가운데에 확인 문서가 열립니다(셋째 그림). **Next** / **Previous**로 6장의 "
                "스크린샷을 넘겨 보고, 아래 **저장된 파일 목록**에서 PDF와 스크린샷 파일을 확인합니다.",
            ],
            "prompt": P_PDF,
            "shots": [
                {"stem": "ag_7v_03c_check", "viewport": [524, 600],
                 "caption": "헤드리스 브라우저로 스크린샷 6장과 PDF를 만든 뒤, 에이전트가 직접 열어 확인",
                 "callouts": [
                     {"box": [20, 245, 482, 26], "label": "Ran python3 -c ' import os from playwright…", "pos": "above"},
                     {"box": [30, 309, 296, 236], "label": "Analyzed Slide 01 ~ 06 · weekly_2026-10-19.pdf",
                      "pos": "below"},
                 ]},
                {"stem": "ag_7v_03p_done", "viewport": [524, 552],
                 "caption": "답변 끝 — 스크린샷 · 데이터 출처 · Walkthrough 카드 · 인쇄 규칙 2줄(+2 −0) → Accept all",
                 "callouts": [
                     {"box": [35, 34, 392, 190], "label": "스크린샷 — 전체 화면 · 슬라이드별 01~06", "pos": "above"},
                     {"box": [16, 268, 480, 82], "label": "Walkthrough", "pos": "inside"},
                     {"box": [24, 365, 130, 24], "label": "1 file changed +2 −0", "pos": "below"},
                     {"box": [409, 522, 76, 24], "label": "Accept all", "pos": "above"},
                 ]},
                {"stem": "ag_7v_05p_walk", "viewport": [566, 700],
                 "caption": "Walkthrough — 6장 스크린샷을 넘겨 보는 확인 문서와 저장된 파일 목록",
                 "callouts": [
                     {"box": [10, 45, 538, 304], "label": "1번 슬라이드 스크린샷 — 주간 VOC 임원 보고", "pos": "inside"},
                     {"box": [9, 445, 539, 214], "label": "3. 저장된 파일 목록 — PDF · 전체 스크린샷 · 슬라이드 1~6",
                      "pos": "above"},
                 ]},
            ],
            "tip": "PDF처럼 *보는 사람*이 있는 결과물은 '16:9', '한 장에 한 슬라이드'처럼 **출력 조건**을 프롬프트에 "
                   "적어 주세요. 에이전트가 그 조건으로 직접 확인하고, 어긋나면 스스로 고칩니다.",
            "note": "녹화 환경에서는 에이전트가 python 스크립트로 헤드리스 브라우저(Playwright)를 띄워 확인했습니다. 환경에 "
                    "따라 브라우저 창이 직접 열리거나, 브라우저 사용 권한을 먼저 물어볼 수 있습니다. 회사 계정이라면 관리자의 "
                    "브라우저 정책(Lab 1)이 우선 적용됩니다. 녹화에서 고친 인쇄 규칙은 이후 스타터 템플릿에 반영되어 있어, "
                    "여러분의 PDF 점검 결과는 다르게 나올 수 있습니다.",
        },
        {
            "title": "피드백 반영 — 핵심 3줄은 한 줄로 · 안전 이슈에 숫자 → 다시 PDF",
            "body": [
                "PDF를 본 CX팀장이 두 가지를 부탁했습니다. *핵심 3줄은 문장이 길어서 한눈에 안 읽혀요*, *빨간 안전 이슈 "
                "선은 몇 건인지 바로 보이게 해 주세요*.",
                "새 대화에서 아래 프롬프트를 보냅니다. 고칠 **슬라이드 번호**와 **무엇을 어떻게**를 짝지어 적고, 고친 뒤 할 "
                "일(PDF 다시 내보내기, 바뀐 두 장의 스크린샷 보여 주기)까지 함께 적었습니다.",
                "에이전트는 슬라이드 HTML과 *지난번에 찍어 둔 2 · 3번 스크린샷*, 템플릿, 데이터를 읽은 뒤 어떻게 고칠지 "
                "39초 동안 생각했습니다(주황색 막대 위의 빨간 숫자는 잘 안 보이니 흰 테두리를 두르기로 했습니다). "
                "HTML을 한 번 고치고(**+7 −3**) PDF와 스크린샷을 다시 내보냈습니다. 처음 내보낼 때 Playwright 전용 "
                "브라우저가 없어 오류가 났지만, 에이전트가 PC에 설치된 Chrome으로 바꿔 다시 실행했습니다.",
                "녹화에서는 약 8분 뒤 답이 나왔습니다(첫 그림). **주요 변경 내역**에 바뀐 세 문장과 3번 슬라이드의 숫자"
                "(1 · 1 · 2 · 6)가 정리되고, 아래 **변경된 슬라이드 스크린샷**에 2번 · 3번 슬라이드가 그대로 붙습니다.",
                "- **2번 슬라이드** 두 줄로 넘어가던 세 문장을 한 줄씩으로 — 예: '공기청정기 어댑터 과열 · 연기 문의가 "
                "6건(전주 2건)으로 3배 급증, 전 건 미완료입니다.' (둘째 · 셋째 그림)",
                "- **3번 슬라이드** 빨간 안전 이슈 선의 점 위에 주별 건수 1 · 1 · 2 · 6 (넷째 · 다섯째 그림)",
                "답변 속 스크린샷으로 바뀐 부분을 확인한 뒤 **Accept all**을 누릅니다(**1 file changed +7 −3**).",
            ],
            "prompt": P_EDIT,
            "shots": [
                {"stem": "ag_7v_06c_changes", "viewport": [524, 440],
                 "caption": "답변 — 주요 변경 내역: 2번 슬라이드 세 문장 · 3번 슬라이드 주별 건수(1, 1, 2, 6)",
                 "callouts": [
                     {"box": [22, 114, 470, 179], "label": "2번 슬라이드 — 세 문장 모두 한 줄로", "pos": "above"},
                     {"box": [22, 299, 468, 40], "label": "3번 슬라이드 — 빨간 선에 주별 건수 1 · 1 · 2 · 6",
                      "pos": "below"},
                 ]},
                {"stem": "ag_7v_13c_s2_before", "viewport": [1180, 516],
                 "caption": "고치기 전 2번 슬라이드 — 세 문장이 모두 두 줄로 넘어감",
                 "callouts": [
                     {"box": [113, 65.3, 819.1, 56.2], "label": "두 줄", "pos": "below"},
                     {"box": [113, 233, 819.1, 56.2], "label": "두 줄", "pos": "below"},
                     {"box": [113, 400.7, 819.1, 56.2], "label": "두 줄", "pos": "below"},
                 ]},
                {"stem": "ag_7v_22c_s2_after", "viewport": [1180, 516],
                 "caption": "고친 뒤 2번 슬라이드 — 세 문장 모두 한 줄",
                 "callouts": [
                     {"box": [113, 65.3, 819.1, 28.1], "label": "한 줄", "pos": "below"},
                     {"box": [113, 204.9, 819.1, 28.1], "label": "한 줄", "pos": "below"},
                     {"box": [113, 344.5, 819.1, 28.1], "label": "한 줄", "pos": "below"},
                 ]},
                {"stem": "ag_7v_14c_s3_before", "viewport": [677, 399],
                 "caption": "고치기 전 3번 슬라이드 차트 — 빨간 안전 이슈 선에 숫자가 없음",
                 "callouts": [
                     {"box": [122.9, 226.3, 442.3, 85.3], "label": "빨간 안전 이슈 선 (숫자 없음)", "pos": "above"},
                 ]},
                {"stem": "ag_7v_23c_s3_after", "viewport": [677, 399],
                 "caption": "고친 뒤 — 빨간 선의 점 위에 주별 건수 1 · 1 · 2 · 6 (흰 테두리로 주황 막대 위에서도 보임)",
                 "callouts": [
                     {"box": [122.9, 203.4, 442.3, 108.2], "label": "안전 이슈 1 · 1 · 2 · 6건", "pos": "above"},
                 ]},
            ],
            "tip": "고칠 점은 **슬라이드 번호 + 대상 + 원하는 모양**으로 짝지어 말하세요. '보기 좋게 고쳐 주세요'보다 "
                   "'2번 핵심 3줄은 한 줄로', '3번 빨간 선에 숫자'가 한 번에 원하는 결과를 줍니다.",
        },
        {
            "title": "완성된 6장 — 발표 모드로 넘겨 보며 숫자 검토",
            "body": [
                "이제 완성된 슬라이드를 직접 열어 봅니다. Explorer에서 `slides` 폴더를 펼치고 `weekly_2026-10-19.html`을 "
                "오른쪽 클릭 → **Reveal in Finder**(Windows는 **Reveal in File Explorer**)를 누릅니다. 열린 폴더에서 "
                "파일을 더블클릭하면 기본 브라우저에서 열립니다.",
                "외부 CDN 없이 파일 하나로 된 슬라이드라서 인터넷 연결 없이도 그대로 열립니다. 위쪽 도구 막대는 회사 "
                "템플릿에 들어 있던 기능입니다.",
                "- **슬라이드 발표 모드** 한 장씩 크게 봅니다. 누르면 버튼이 **전체 보기**로 바뀌고, 다시 누르면 6장을 "
                "위아래로 이어 보는 화면으로 돌아갑니다.",
                "- **◀ 이전 / 다음 ▶** 버튼이나 키보드 **← / →** 로 넘깁니다. 가운데 숫자(**1 / 6**)가 지금 장입니다.",
                "발표 모드로 6장을 넘겨 보며 숫자를 데이터와 대조합니다. 이번 실습 데이터의 정답은 아래와 같습니다.",
                "- **1 표지** 보고 기간 2026-10-19 ~ 2026-10-25, 안전 이슈(긴급) 6건(전주 2건) 전량 미완료(접수 3 · "
                "처리중 3), 총 접수 91건(+12건, +15.2%), 로봇청소기 앱 연결 20건(전주 13건, +53.8%), 미완료 45건(접수 "
                "23 · 처리중 22)",
                "- **2 핵심 3줄** 안전 이슈 2 → 6건, 총 91건(+15.2%), 로봇청소기 앱 연결 13 → 20건(+53.8%)",
                "- **3 주간 추이** 주별 62 · 68 · 79 · 91건, 안전 이슈 1 · 1 · 2 · 6건, 지난주 앱 연결 24건(전주 대비 +5건)",
                "- **4 안전 이슈** 6건 모두 공기청정기 전원 어댑터, 6건 전부 미완료(빨간 행), 고객 이름 · 연락처는 "
                "`홍*준` · `010-****-1007`처럼 마스킹",
                "- **5 로봇청소기 앱 연결** 주별 3 → 1 → 13 → 20건, 지난주 20건 = 연결 끊김 8 · 오프라인 표시 6 · 예약 "
                "기능 3 · 페어링 실패 3, 미완료 9건(접수 4 · 처리중 5)",
                "- **6 다음 할 일** 안전 이슈 6건 회수 · 교체가 1단계(맨 앞)에 있는지",
                "녹화에서 만든 6장을 이 정답과 대조해 보니 **숫자는 모두 맞았습니다**. 그래도 보고 전에 꼭 짚을 곳이 세 "
                "군데 있습니다.",
                "- **5번의 '2026-10-14 앱 업데이트'** 데이터에는 업데이트 날짜가 없습니다. 10월 14일 하루 6건으로 급증한 "
                "것과 '앱 업데이트 후 … 예약 기능이 사라졌어요' 같은 문의 내용을 보고 에이전트가 *추정*한 것이므로, 앱 개발팀에 "
                "사실인지 확인합니다.",
                "- **6번의 담당 팀과 기한**(2026-10-27 · 10-28 · 10-30)은 에이전트의 *제안*입니다. 실제 담당과 일정으로 "
                "바꿔서 보고합니다.",
                "- **3번 오른쪽 '지난주 분류별 건수'** '많은 순'이라고 적혀 있지만 7개 분류 중 5개만 있습니다(사용법 11건 · "
                "환불 · 교환 8건이 빠짐). 전체처럼 보이지 않게 고치거나 '주요 분류'로 이름을 바꾸게 하세요.",
                "고칠 곳은 STEP 3처럼 *슬라이드 번호 + 무엇을 어떻게*로 다시 부탁하면 됩니다. 이렇게 검토한 6장이 월요일 "
                "임원 회의용 보고 자료입니다.",
            ],
            "shots": [
                {"stem": "ag_7v_21_deck_s1",
                 "caption": "1번 표지 — 안전 이슈(긴급) 6건 · 6건 미완료 경보, 이번 주 핵심 지표 4개(6건 · 91건 · 20건 · 45건)",
                 "callouts": [
                     {"box": [148.8, 181.1, 684.3, 50.6], "label": "안전 이슈(긴급) 6건 · 6건 미완료", "pos": "below"},
                     {"box": [928.3, 156.3, 386.8, 335.2], "label": "6건 · 91건 · 20건 · 45건", "pos": "below"},
                 ]},
                {"stem": "ag_7v_22_deck_s2",
                 "caption": "2번 핵심 3줄 — ① 안전 이슈 2 → 6건, 전 건 미완료 ② 총 91건(+15.2%) ③ 로봇청소기 앱 연결 "
                            "13 → 20건(+53.8%)",
                 "callouts": [
                     {"box": [144.8, 212.3, 1150.3, 402.9], "label": "핵심 1 안전 이슈 · 2 전체 접수량 · 3 앱 연결 급증",
                      "pos": "below"},
                 ]},
                {"stem": "ag_7v_23_deck_s3",
                 "caption": "3번 주간 추이 — 지표 타일 4개, 주별 62 → 68 → 79 → 91건과 안전 이슈 1 · 1 · 2 · 6건, 지난주 "
                            "분류별 건수",
                 "callouts": [
                     {"box": [144.8, 212.3, 1150.3, 126.9], "label": "안전 이슈 6건 · 91건 · 앱 연결 24건 · 미완료 45건",
                      "pos": "above"},
                     {"box": [252.9, 546.4, 442.3, 108.2], "label": "안전 이슈 1 · 1 · 2 · 6건", "pos": "above"},
                 ]},
                {"stem": "ag_7v_24_deck_s4",
                 "caption": "4번 안전 이슈 — 미완료 긴급 문의 6건(접수 3 · 처리중 3) 빨간 행, 고객 이름 · 연락처는 "
                            "마스킹(홍*준 · 010-****-1007)",
                 "callouts": [
                     {"box": [144.8, 212.3, 1150.3, 50.6], "label": "미완료 긴급 문의 6건 — 접수 3건 · 처리중 3건",
                      "pos": "above"},
                     {"box": [144.8, 278.8, 1150.3, 287.6], "label": "6건 전부 미완료(빨간 행) · 고객명 · 연락처 마스킹",
                      "pos": "below"},
                 ]},
                {"stem": "ag_7v_25_deck_s5",
                 "caption": "5번 로봇청소기 앱 연결 — 주별 3 → 1 → 13 → 20건(+53.8%), 2026-10-14 시점 표시. 오른쪽 "
                            "원인은 에이전트의 추정입니다",
                 "callouts": [
                     {"box": [393.7, 281.7, 158.7, 23.8], "label": "2026-10-14 앱 업데이트 (에이전트 추정)",
                      "pos": "above"},
                     {"box": [814.9, 212.3, 480.2, 327.3], "label": "무엇이 · 언제부터 · 원인 추정 · 영향",
                      "pos": "below"},
                 ]},
                {"stem": "ag_7v_26_deck_s6",
                 "caption": "6번 다음 할 일 — STEP 1 안전 이슈 6건 회수 · 교체부터, 담당 · 기한, 임원 결정 요청과 다음 주 "
                            "확인 지표",
                 "callouts": [
                     {"box": [144.8, 212.3, 1150.3, 103.1],
                      "label": "STEP 1 안전 이슈 회수 · 교체 → STEP 2 로트 조사 → STEP 3 앱 핫픽스", "pos": "above"},
                     {"box": [144.8, 333.3, 1150.3, 127.9], "label": "CX팀 · CS현장팀 … 2026-10-27 — 담당 · 기한 (에이전트 제안)",
                      "pos": "inside"},
                 ]},
            ],
            "tip": "**숫자는 보고 전에 한 번 더.** 에이전트가 만든 표와 차트도 결국 *데이터를 옮겨 적은 것*입니다. 핵심 "
                   "숫자와 내역 몇 개를 정답(또는 BigQuery 조회 결과)과 대조하고, *추정*과 *제안*은 사실 확인을 거쳐 "
                   "보고하세요.",
        },
    ],
    "check": [
        "회사 템플릿(templates/exec_deck_template.html)의 [대괄호] 자리와 6장 구성을 확인했다",
        "새 대화에서 템플릿 + 스킬 + BigQuery MCP로 임원 보고 슬라이드 6장을 만들었다",
        "Allow using this MCP tool? 카드에서 Tool arguments의 SQL을 읽고 허용했다",
        "/browser로 확인하고, 한 장에 한 슬라이드씩 PDF와 슬라이드별 스크린샷을 받았다",
        "피드백(핵심 3줄 한 줄로 · 안전 이슈 선에 숫자)을 반영하고 PDF를 다시 내보냈다",
        "완성된 HTML을 발표 모드로 넘겨 보며 숫자 · 마스킹을 확인하고, 추정 · 제안을 구분했다",
    ],
    "more": [
        "voc-weekly-report 스킬의 SKILL.md에 '임원 보고 슬라이드' 절차를 추가해 주세요. templates/exec_deck_template.html 회사 템플릿을 쓰고, 이번에 쓴 6장 구성, 한 장에 한 슬라이드 PDF, 데이터 출처·기준일 표기를 단계로 정리해서, 다음 주에는 주차만 바꿔 요청할 수 있게 해 주세요.",
        "slides/weekly_2026-10-19.html의 숫자가 BigQuery 데이터와 맞는지 MCP로 다시 조회해서, 슬라이드별로 표로 대조해 주세요. 다른 숫자나 데이터에 없는 내용(추정·제안)이 있으면 알려만 주고 아직 고치지는 마세요.",
        "CX팀원들이 이 보고서를 보고 자주 물어볼 만한 질문 10개를 뽑고, BigQuery로 각 질문의 정답을 구해 표로 정리해 주세요. 다음 Lab에서 만들 VOC 분석 에이전트의 평가 질문으로 쓰겠습니다.",
    ],
}
