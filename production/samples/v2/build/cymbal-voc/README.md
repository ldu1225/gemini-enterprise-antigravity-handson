# cymbal-voc — Cymbal 고객의 소리(VOC) 인사이트 프로젝트

> 실습용 가상 데이터 — Cymbal(심벌)은 가상의 회사이며 실제 기업·인물과 무관

Cymbal CX(고객경험)팀의 주간 VOC 업무를 자동화하는 실습 프로젝트입니다. Antigravity 핸즈온 랩 Lab 3부터 Lab 10까지
**이 폴더 하나를 계속 키워 갑니다.**

| 단계 | 하는 일 |
|---|---|
| Lab 3 | 요청서와 데이터를 파악하고, 대시보드 계획(Implementation Plan)을 세웁니다 |
| Lab 4 | VOC 대시보드를 만들고 브라우저로 검증합니다 |
| Lab 5 | 팀 규칙(AGENTS.md)과 주간 보고 스킬(SKILL.md)을 만듭니다 |
| Lab 6 | MCP로 회사 BigQuery에 연결해 실데이터를 씁니다 |
| Lab 7 | 임원 보고용 슬라이드를 만듭니다 |
| Lab 8 | 누구나 물어볼 수 있는 VOC 분석 에이전트(ADK)를 만듭니다 |
| Lab 9 | 에이전트를 배포하고 Gemini Enterprise에 게시합니다 |
| Lab 10 | 매주 자동 보고(/schedule)와 서브에이전트로 운영을 자동화합니다 |

## 폴더
- `요청서_CX팀.md` — 출발점. CX팀장이 보낸 요청서
- `data/voc_tickets.csv` — 고객 문의 300건 (2026-09-28 ~ 2026-10-25, 4주). 열 설명은 아래 표
- `lab.env` — 실습 환경 변수(프로젝트 ID·리전·BigQuery·Gemini Enterprise 앱). **여기 값만 바꾸면** 모든 명령을 그대로 복사해 쓸 수 있습니다
- `setup/load_to_bigquery.sh` — Lab 6 준비: 같은 데이터를 내 프로젝트 BigQuery에 올리는 스크립트(lab.env 값을 읽습니다)
- `templates/exec_deck_template.html` — Lab 7 준비: 회사 임원 보고 슬라이드 템플릿(16:9, 외부 CDN 없음). 에이전트가 이 디자인으로 슬라이드를 만듭니다

## 데이터 열
| 열 | 뜻 |
|---|---|
| ticket_id | 문의 번호 |
| created_at | 접수 일시 (KST) |
| week_start | 접수 주의 월요일 |
| channel | 접수 채널 (전화·이메일·채팅·앱) |
| product | 제품 |
| category | 분류 (배송·불량·고장·앱 연결·사용법·환불·교환·구매 문의·안전 이슈) |
| severity | 긴급도 (긴급·높음·보통·낮음) — 안전 이슈는 모두 긴급 |
| status | 상태 (접수·처리중·완료) |
| region | 지역 |
| customer_name, phone | 고객 이름·연락처 (가상, **개인정보로 취급**) |
| message | 문의 내용 |
| resolution_hours | 처리 시간(시간, 완료 건만) |
| csat | 만족도 1~5 (완료 건만) |
