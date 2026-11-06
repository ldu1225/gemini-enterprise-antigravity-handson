# Hands-on Lab v2 — 공통 디자인/팩트 가이드 (Single Source of Truth)

> v2는 **모든 고객사 대상 범용 랩**입니다. 특정 고객사 관련 내용은 사용하지 않습니다.

## 0. 절대 원칙
- **가짜 화면 금지**: 제품 UI가 보이는 이미지·영상은 모두 실제 앱을 녹화·캡처한 것입니다.
  - Gemini Enterprise: Chrome CDP(:9222), Cymbal 데모 앱(cid는 환경 변수 `GE_APP_CID`, location us)
  - Antigravity: 녹화 전용 인스턴스(CDP :9334, `production/capture/agy/launch_ag_rec_voc.sh`, HOME·프로필 격리. 로그인 화면은 CDP :9333, `production/capture/agy/launch_rec.sh`)
  - Google Cloud 콘솔(관리자 화면): Chrome CDP(:9222)
- **가상 회사 Cymbal(심벌)**: Google 공식 가상 브랜드. 모든 실습 데이터는 가상이며, 파일과 표지에 "실습용 가상 데이터"를 표기합니다.
- **대상**
  - GE 트랙: 일반 사무직(비개발자)
  - Antigravity 트랙: 개발자와 기술 친화적 현업. Lab 1~3은 비개발자도 따라올 수 있게 만듭니다.
- **톤**: 친절하고 명료한 존댓말, 전문용어 최소화. 처음 쓰는 용어는 한 번 풀어서 설명합니다.
- **로고**: 고객사 로고 사용 금지. Google·Gemini·Antigravity 로고를 직접 그리지 않습니다(실제 화면에 보이는 것은 OK).
  포털 헤더·푸터·파비콘은 **Google Cloud 공식 로고 파일만** 씁니다(`production/site_build_v2/static/brand/`, gstatic 원본 — `SOURCE.md`).
  다크 배경에는 'Cloud' 글자만 흰색으로 바꾼 반전 로고를 씁니다. 그 밖의 변형(재작도·늘이기·효과)은 금지.

## 1. 디자인 토큰 (포털 · 영상 · 슬라이드 공통)
- **폰트**: Pretendard(한글), Inter(숫자·영문), JetBrains Mono(코드). 모두 자체 호스팅합니다.
- **컬러**

  | 용도 | 값 |
  |---|---|
  | Ink | `#0E1116` |
  | 보조 텍스트 | `#5B6472` |
  | 라인 | `#E5E7EB` |
  | 라이트 배경 | `#F7F8FA` |
  | 카드 | `#FFFFFF` |
  | 다크 배경 | `#0B0F17` |
  | 다크 카드 | `rgba(255,255,255,.04)` + 1px `rgba(255,255,255,.08)` |
  | 포인트 그라디언트 | `linear-gradient(135deg,#4285F4 0%,#9B72CB 55%,#D96570 100%)` (아껴서 사용) |
  | GE 트랙 액센트 | `#4285F4` |
  | Antigravity 트랙 액센트 | `#9B72CB` → `#34A853` 보조 |
  | 상태색 | 성공 `#1E8E3E` · 경고 `#F29900` · 정보 `#1A73E8` · 위험 `#D93025` |

- **형태**: 카드 radius 16px, 버튼 10px, 칩 999px. 그림자 `0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(15,23,42,.06)`. 여백은 넉넉하게.
- **포털 UI (2026-11 전면 개편 — `production/site_build_v2/static/css/portal.css`가 기준)**
  - 브랜드: 헤더 = Google Cloud 공식 로고 │ 포털 제목, 파비콘 = Google Cloud 공식 아이콘, 푸터 = 항상 다크(반전 로고).
  - 색: CTA는 Google Blue `#0B57D0`(다크 `#8AB4F8`), 장식은 Google 4색 `#4285F4 · #EA4335 · #FBBC04 · #34A853` + 보라 `#A142F4`,
    트랙 액센트는 `site.py`의 `accent`(GE 파랑 · AG 보라)에서 대비 보정 토큰을 자동 생성합니다.
  - 형태: Material 3 Expressive — 버튼·탭·칩은 pill(999px), 카드 18–32px, 히어로 뒤 추상 도형(원·둥근 삼각형·꽃 모양·반원·알약)은 SVG 장식(로고 아님).
  - 홈: 가운데 히어로(도형) → 실제 캡처가 움직이는 스테이지 → 트랙 카드 → 결과물 벤토(`SITE['showcase']`) → 진행 방식 → 오프닝 → 데모 영상 → 준비물 → FAQ → 마무리 → CTA 밴드.
    - 스테이지(`SITE['stage']`, 사용자: "좌우로 움직이는 멋진 애니메이션"): 실제 캡처 창이 오른쪽 → 가운데 → 왼쪽으로 넘어가는 3D 덱입니다.
    - 움직임은 CSS(translate · scale · rotate · opacity)만, JS는 `data-pos`만 바꿉니다. 활성 점의 채움 애니메이션이 타이머입니다.
    - 정지 버튼이 있고, 마우스 올림 · 키보드 포커스 · 화면 밖 · 동작 줄이기에서 멈춥니다(WCAG 2.2.2). JS가 없으면 가운데 + 양옆 세 장이 고정으로 보입니다.
  - 트랙: 홈과 같은 히어로 + 오프닝 영상 스테이지 + 학습 경로(번호 노드가 이어진 가로 카드) + 준비물 · FAQ · CTA 밴드.
    Lab: 홈 히어로 언어의 헤더 카드(도형 · 킥커 칩), 타임라인 단계, 그라디언트 테두리 프롬프트, 다크 코드 블록,
    플로팅 **단계 도크**(이전 · 현재 단계 + 진행 막대 · 다음).
  - 스크린샷 콜아웃 기하(`.fig-stage`, `.co`, `.co-tag`) 규칙은 그대로 — qa.py가 1.5px 이내로 검사합니다.
  - **모든 페이지가 같은 룩** (사용자: "메인에 맞춰서 모든 탭 똑같이"): 상단 바는 모든 페이지에서 똑같고, 트랙 페이지는 홈 히어로를 그대로 씁니다
    (도형 · 배경 · 킥커 칩 · 두 줄 제목 · CTA · 큰 숫자 · 영상 스테이지). Lab 헤더도 같은 언어의 카드입니다.
    색은 어느 페이지든 브랜드 파랑이 기준이고, 트랙 색(`.t-<id>`)은 점 · 킥커 · 홈 트랙 카드 같은 **식별 표시에만** 씁니다(페이지 전체를 물들이지 않음).
- **영상**
  - 1920×1080, 30fps, H.264 + AAC
  - 자막: 하단 중앙 pill
  - 하이라이트 링·박스: **측정한 좌표만** 씁니다(캡처 이벤트·DOM 박스·OCR). 추적 검사(`render.py --strict-callouts`) +
    의미 검사(`production/qa/video_callout_audit.py`, 스크린샷은 `production/qa/callout_audit.py`) 시트를 전수 확인합니다 — `AGENTS.md` §1.
- **내레이션**: Gemini 3.8 Flash TTS(Kore), 쉼표 쉼, ASR 검수. 모듈은 `production/render/engine/voice.py`

## 2. 확인된 팩트 (공개 문서 기준, 2026-10-26)
- **GE 기능**: v1 DESIGN §2를 그대로 씁니다(Gemini 4 Argon, 3.8 Flash, Claude Opus/Sonnet 5.5, Workflow Builder, Skills, Canvas, Nano Banana, Veo 3.1, Deep Research, Gemini Notebook, Projects).
- **Gemini 4 Carbon**: Gemini 4 Argon과 함께 나온 Gemini 4 세대의 새 고성능 모델. 녹화한 GE · Antigravity 모델 메뉴에는 보이지 않으므로
  "목록에 보이면 Argon 자리에서 골라도 된다(조직 · 요금제 · 허용 모델에 따라 다름)"로만 안내합니다(트랙 FAQ, GE Lab 1, AG Lab 1 · 3). 화면에 없는 메뉴를 있다고 쓰지 않습니다.
- **Gemini Notebook 스튜디오** *(실제 화면으로 확인함, 2026-11-02)*: AI 오디오 오버뷰(언어 · 길이 짧게/기본값 · 집중할 내용), 슬라이드 자료,
  동영상 개요, 마인드맵, 보고서(브리핑 문서 · 학습 가이드 · FAQ · 타임라인), 플래시카드 · 퀴즈(개수 · 난이도), 인포그래픽(방향 · 시각적 스타일 · 세부정보 수준).
  여러 개를 동시에 생성할 수 있고 백그라운드에서 완성됩니다(보고서 · 퀴즈 1분 안팎, 인포그래픽 · 오디오 약 3분, 동영상 · 슬라이드 5~8분).
  GE Lab 5는 마인드맵이 아니라 **동영상 개요 · 오디오 · 슬라이드 · 인포그래픽**을 주인공으로 보여 줍니다(사용자 지시).
  - 캡처 주의: ① 표 답변은 "열 이름 + 한 칸에 한 문장"으로 요청합니다(그냥 요청하면 칸 안에 날 `<br>`가 찍힘 — `ge5.py`가 `<br>` · `**` · `|---`가 보이면 중단).
    ② 슬라이드 · 인포그래픽은 이미지 모델이 글자를 그리므로 **장마다 확대해서 오타 · 깨진 영어를 확인**합니다(첫 시도 표지에 깨진 영어 부제, 인포그래픽에 '에어플' 오타 → 설명란에 표기 지시를 넣어 다시 생성).
    ③ 노트북 홈 둘째 줄에 실제 회사명이 들어간 예전 노트북 카드가 있습니다 → 홈 스틸은 노트북 영역 첫 줄까지만 잘라 찍고(`ge_5_13`, 1152×420), 영상은 홈이 그려지기 전에 오른쪽 위로 줌해 둡니다.
- **Antigravity**: 공개 문서 조사 노트(저장소 밖)가 출처 목록입니다. 요점:
  - 제품: Antigravity 2.0(데스크톱 앱), Antigravity CLI(`agy`), Antigravity for IDEs, Antigravity SDK(`pip install google-antigravity`)
  - 로그인 화면은 **Continue with Google**(개인 계정)과 **Use Business Account**(조직·GE 라이선스) 두 가지입니다. *실제 화면으로 확인함.*
  - GE 라이선스 조건과 관리자 설정:
    - Standard·Plus·Pay-as-you-go·Emerging Market 에디션, 인보이스 결제 계정 필요
    - 관리자 경로: 콘솔 **Gemini Enterprise > Settings > AI developer tools**
      - 사용 on/off
      - 보안 정책(파일 접근·터미널 명령)
      - 허용 모델(Antigravity authorized models)
      - Boost·Teamwork 제어
    - 사용 지표: Developer tools metrics(Preview)
  - GE 웹앱 사이드바에도 **Explore Antigravity** 진입점이 있습니다. *실제 화면으로 확인함.*
  - 개인 계정 요금제와 모델:

    | 요금제 | 할당량 | 사용 가능 모델 |
    |---|---|---|
    | 무료 | 주간 할당량 | Gemini 3.8 Flash |
    | Google AI Pro | 5시간마다 갱신 | Gemini 4 Argon, Claude 포함 |
    | Google AI Ultra | 가장 높음 | |

  - 기능:
    - Plan 모드(`/plan`)와 아티팩트(Implementation Plan, Walkthrough, Task list)
    - 권한 프리셋: Request Review, Default(sandbox), Turbo
    - 브라우저 사용, Remote Control, 슬래시 명령: `/goal`, `/schedule`, `/browser`, `/learn`, `/boost`, `/teamwork-preview`, `/grill-me`
  - Skills와 규칙:
    - 형식: `SKILL.md`(YAML `name`/`description`, `scripts/` · `examples/` · `resources/`)
    - 위치: 워크스페이스 `.agents/skills/<name>/`, 전역 `~/.gemini/config/skills/`
    - 규칙 파일: `AGENTS.md`, `GEMINI.md`, `.agents/rules/*.md`
    - Workflows는 2026-10-19부터 deprecated입니다. `/migrate-workflows`로 스킬로 옮깁니다.
  - ADK와 배포:
    - `agents-cli scaffold create` → `agents-cli run`/`playground` → `agents-cli eval` → `agents-cli deploy`(Agent Runtime)
    - GE 등록: `agents-cli publish gemini-enterprise --registration-type adk`
  - **슬라이드**: Antigravity의 별도 "기능"은 아닙니다. 에이전트에게 HTML 슬라이드 생성·PDF 내보내기를 맡기는 **실습 시나리오**로 다룹니다. 기능이라고 쓰지 않습니다.

## 3. 커리큘럼
### GE 트랙 (Cymbal)
| Lab | 제목 | 부서 시나리오 |
|---|---|---|
| 0 | 오프닝 발표 — Gemini Enterprise로 일하는 방식 | — |
| 1 | 시작하기 — 첫 화면, 언어·테마·개인화, 모델 선택 | 공통 |
| 2 | 프롬프트로 답 얻기 — 4요소 프롬프트, 웹 검색·출처, 후속 질문, 공유 | 마케팅 |
| 3 | 데이터 분석 + Canvas — 영업 실적 엑셀 → 차트 → 보고 슬라이드 | 영업 |
| 4 | 이미지·동영상 — 캠페인 비주얼(Nano Banana) + 티저(Veo 3.1) | 마케팅 |
| 5 | Deep Research & Gemini Notebook — 시장 조사 → 노트북 근거 질문 → 스튜디오(동영상 개요·오디오 오버뷰·슬라이드·인포그래픽·보고서·퀴즈·플래시카드) | 전략 |
| 6 | 생산성 — 스킬 · 프로젝트 · 라이브러리 · 커넥터 | 공통 |
| 7 | 채팅 에이전트(심화) — Cymbal 사내 지원 데스크 | HR·재무·IT |
| 8 | 워크플로(심화) — 고객 문의 자동 분류·답변 초안(조건 분기·정보 요청·승인/거부) | CS |
| 9 | 에이전트 공유·갤러리·관리 | 공통 |

### Antigravity 트랙 — 스토리라인 "Cymbal CX팀 VOC 프로젝트" (Lab 3~10은 같은 `cymbal-voc` 폴더를 이어서 키웁니다)
| Lab | 제목 | 스토리 속 할 일 |
|---|---|---|
| 0 | 오프닝 발표 — 에이전트와 함께 만드는 개발 | — |
| 1 | 시작하기 A — GE 라이선스(관리자 콘솔 설정 + Use Business Account 로그인) | — |
| 2 | 시작하기 B — 개인 Google 계정(Continue with Google), 요금제 차이 | — |
| 3 | 프로젝트 받기 — 화면 구성과 기본 사용(@멘션 · 명령 승인 · /plan) | 요청서·데이터 파악, 숫자 검증, 대시보드 계획 |
| 4 | VOC 대시보드 만들기(Proceed · 변경 검토 · /browser · 필터) | 계획대로 구현 → 실행 → 검증 → 기능 추가 |
| 5 | 팀 규칙과 주간 보고 스킬(AGENTS.md · SKILL.md) | 개인정보 마스킹 규칙, 주간 보고 스킬 |
| 6 | **MCP로 회사 데이터 연결 — BigQuery** | MCP Store 설치, MCP 도구 호출로 실데이터 분석 |
| 7 | 임원 보고 슬라이드(HTML → PDF) | 스킬 + BigQuery 데이터로 주간 보고 6장 |
| 8 | VOC 분석 에이전트 — ADK(agents-cli 생성 · 도구 · 실행 · 평가) | 누구나 묻는 VOC 에이전트 |
| 9 | 배포 + Gemini Enterprise 게시 | Agent Runtime 배포, CX팀이 GE에서 사용 |
| 10 | 운영 자동화(/schedule · 서브에이전트 · Remote Control) | 매주 월요일 자동 보고, 테스트·문서 병렬 작업 |

- 실습 파일: `Cymbal_VOC_스타터.zip`(`production/samples/v2/build_voc_starter.py`) — 요청서, 고객 문의 300건(4주), `lab.env`, BigQuery 적재 스크립트. 팩트는 `production/samples/v2/answer_keys/voc_facts.json`.
- 녹화: `production/capture/agy/launch_ag_rec_voc.sh` + `production/capture/agy/agv.py`(창은 정확히 1440×810 CSS px — DOM 박스·스틸·영상 좌표가 하나).

## 4. 경로 규칙
- **캡처**
  - 스틸: `production/assets/shots/` — 접두어 `ge_`, `ag_`, `gc_`(Cloud 콘솔)
  - 녹화: `production/assets/recordings/<id>/`(id 접두어 동일)
- **콘텐츠**: `production/content/v2/ge.py`, `ag.py`, `site.py`
- **렌더 스크립트**: `production/render/scripts/v2/<id>.json`
- **실습 파일 원본**: `production/samples/v2/`, 배포본은 `site_v2/assets/files/`
- **포털 빌더**: `production/site_build_v2/`, 출력은 `site_v2/`
