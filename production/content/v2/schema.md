# Hands-on Lab v2 — 콘텐츠 스키마

포털 빌더(`production/site_build_v2/build.py`)가 읽는 콘텐츠 형식입니다. 콘텐츠는 **파이썬 모듈**(dict/list 리터럴)로 작성합니다.
빌더는 모든 문자열을 HTML 이스케이프하므로 HTML 태그를 넣으면 글자 그대로 보입니다.

```
production/content/v2/
  site.py        SITE(dict) · TRACKS(list)
  ge.py          LABS(list)  ← TRACKS[i]["id"] == "ge"
  ag.py          LABS(list)  ← TRACKS[i]["id"] == "ag"
  _fixture/      개발용 픽스처(같은 형식, 배포 금지) — build.py --fixture
```

빌드 명령:

```bash
python3 production/site_build_v2/build.py              # → site_v2/
python3 production/site_build_v2/build.py --fixture    # → site_v2_fixture/ (개발용 픽스처 — 이 저장소에는 포함하지 않음)
python3 production/site_build_v2/qa.py [--fixture]     # 스크린샷 + 콘솔/CSP/오버플로/챕터 검사
```

---

## 1. 텍스트 마크업 (md 문자열)

`body`, `goal`, `tip`, `note`, `prep`, FAQ 답변 등 **md**라고 표시된 필드에서만 아래 문법을 씁니다.

| 문법 | 결과 |
|---|---|
| `**굵게**` | 굵은 글씨 (`` **`코드`** ``처럼 코드를 감싸도 됩니다) |
| `*강조*` | 형광펜 강조(한글 가독성을 위해 기울이지 않습니다). `*` 바로 안쪽에 공백이 있으면 강조로 보지 않습니다(`0 9 * * 1-5` 같은 cron 식은 그대로 표시) |
| `` `코드` `` | 인라인 코드(고정폭). 22자 이하는 줄바꿈 없이, 더 길면 필요한 곳에서 줄바꿈 |
| `[글자](https://…)` | 외부 링크(새 탭). **https 주소만** 허용, 그 외는 글자로 남습니다 |
| `- 항목` (body 항목이 `- `로 시작) | 연속된 항목을 하나의 글머리표 목록으로 묶음 |
| `1. 항목` (`1)`도 가능) | 연속된 항목을 번호 목록으로 묶음(첫 번호부터 시작) |

- `body` 목록의 문자열 하나가 문단 하나(또는 목록 항목 하나)입니다. 문자열 안의 줄바꿈(`\n`)은 줄마다 따로 처리합니다.
- 짝이 맞지 않는 `**`는 화면에 표시하지 않습니다. 그 밖의 문자는 모두 그대로 표시됩니다.
- `title`, `caption`, `check`, `more`는 서식 없이 글자만 씁니다(문법 기호는 제거).
- `qa.py`가 빌드 결과에 렌더링되지 않은 마크다운(`**`, `` ` ``, `*…*`, `1. ` 문단)이 남았는지 검사합니다.

## 2. `site.py`

```python
SITE = {
    "title": "Hands-on Lab",                 # 브랜드·<title> (필수)
    "org": "Cymbal",                         # 선택: 푸터·설명에 표시
    "hero_kicker": "Hands-on Lab · 2026",    # 선택: 히어로 상단 pill
    "hero_title": ["AI와 함께 일하는 방법,", "직접 해 보며 익히세요"],  # 줄 단위(필수)
    "hero_sub": "…",                         # 히어로 설명(필수)
    "description": "…",                      # 선택: <meta description> (기본 hero_sub)
    "stats": [{"value": "19", "label": "개 Lab"}, …],  # 선택: 히어로 아래 4칸. 생략하면 자동 계산
    "files_src": "production/samples/v2/dist",   # 선택: 실습 파일 원본 폴더(저장소 기준 상대 경로)
    "video_src": None,                       # 선택: 영상 원본 폴더. 지정하면 빌드 때 assets/video/로 복사
    "footer_note": "md …",                   # 선택: 푸터 안내(가상 데이터·실제 캡처 고지)
    "references": [{"title": "…", "url": "https://…"}],  # 선택: 푸터 참고 링크(https만)
    "showcase": [                            # 선택: 홈 '결과물' 벤토(실습에서 만든 실제 결과물 캡처)
        {"track": "ag", "lab": "lab7", "stem": "ag_7v_21_deck_s1",  # stem = production/assets/shots 의 실제 캡처
         "span": 7,                          # 넓은 화면 12칸 그리드 칸 수(한 줄 합 12)
         "focus": "50 40", "zoom": 1.0,      # 잘라 보일 위치 "x y"(%) · 확대(1~3, 실제 캡처를 자르는 것)
         "title": "…", "desc": "…"},
    ],
    "stage": [                               # 선택: 홈 히어로의 움직이는 창(실제 캡처가 오른쪽 → 가운데 → 왼쪽으로 넘어감)
        {"stem": "ge_3_32_canvas_ready",     # 첫 항목이 가운데, 두 번째가 오른쪽, 마지막이 왼쪽에서 시작(스크립트 없이도 보이는 세 장)
         "title": "Gemini Enterprise · 데이터 분석 & Canvas"},   # 창 제목 표시줄 + 점 버튼의 이름
    ],                                       # 생략하면 기본 세 장. 자동 넘김은 정지 버튼·마우스 올림·키보드 포커스·동작 줄이기 설정에서 멈춤
}

TRACKS = [
    {
        "id": "ge",                          # 필수, 소문자 영숫자. 출력 폴더(site_v2/ge/)와 모듈(ge.py) 이름
        "title": "Gemini Enterprise",        # 필수
        "short": "GE",                       # 선택: 칩·좁은 화면용 약칭
        "tagline": "…",                      # 필수: 트랙 카드 한 줄 소개
        "hero_line": "…",                     # 선택: 트랙 페이지 히어로 둘째 줄(그라디언트). 없으면 오프닝 제목
        "audience": "일반 사무직(비개발자)",     # 선택
        "accent": "#4285F4",                 # 선택: 트랙 강조색(기본 GE #4285F4, AG #9B72CB)
        "cover": "ag_4_06c_browser_result",  # 선택: 홈 트랙 카드 커버 스크린샷 stem(없으면 Lab 스크린샷에서 자동 선택)
        "opening": {                         # 선택: 오프닝 발표 영상
            "video": "ge_opening",           #   assets/video/<video>.mp4 (+ .ko.vtt, .jpg, .chapters.json 선택)
            "title": "Gemini Enterprise로 일하는 방식",
            "desc": "…",
        },
        "prep": ["md …", …],                 # 선택: 준비물(순서 목록)
        "files": [                           # 선택: 실습 파일 (files_src 기준 상대 경로)
            {"file": "Cymbal_실적_가상.xlsx", "title": "…", "desc": "…",
             "labs": ["lab3"], "preview": "previews/….png", "bundle": False},
        ],
        "faq": [{"q": "…", "a": "md …"}],     # 선택
    },
    …
]
```

- `files[].bundle: True`인 항목(보통 전체 ZIP)은 큰 다운로드 카드로 따로 보여 줍니다.
- 파일 경로에 `..`나 절대 경로는 쓸 수 없습니다(빌드 실패).

## 3. `ge.py` / `ag.py` — `LABS`

```python
LABS = [
    {
        "id": "lab1",                        # 필수, [a-z0-9-]. 출력: site_v2/<track>/<id>.html
        "no": 1,                             # 필수, 표시 번호(정수 또는 "01")
        "title": "시작하기",                   # 필수
        "subtitle": "첫 화면, 언어·테마·개인화, 모델 선택",   # 선택
        "level": "입문",                      # "입문" | "기본" | "심화"
        "minutes": 15,                       # 필수: 예상 소요 시간(분)
        "goal": "md …",                      # 선택: 이번 실습의 목표
        "video": "ge_lab1",                  # 선택: 영상 id (assets/video/<id>.mp4)
        "steps": [STEP, …],                  # 비어 있으면 '준비 중' 페이지로 출력
        "check": ["…", …],                   # 선택: 체크리스트(브라우저 localStorage에 저장)
        "more": ["프롬프트 …", …],             # 선택: '더 해 보기' 프롬프트(복사 버튼)
    },
]
```

### STEP

```python
{
    "title": "기본 설정 — 테마",                # 필수
    "body": ["md 문단", "- 글머리표", …],       # 선택
    "prompt": "그대로 붙여 넣을 프롬프트" | None,   # 선택: 어두운 프롬프트 카드 + 복사 버튼
    "code": {                                # 선택: dict 하나 또는 dict 목록
        "lang": "bash",                      #   bash|sh|shell|zsh|console → 줄 앞에 $ 표시, # 주석은 흐리게
        "text": "agy --version\n…",          #   yaml|md|markdown|python|json|text …(구문 강조는 하지 않음)
        "file": ".agents/skills/x/SKILL.md", #   선택: 머리글에 파일 이름 표시
    },
    # 스크린샷 — 셋 중 한 가지 방식
    "shot": "ge_s1_12_design", "caption": "…", "callouts": [CALLOUT, …],
    "shot": {"stem": "…", "caption": "…", "callouts": [...]},
    "shots": ["stem_a", {"stem": "stem_b", "caption": "…", "callouts": [...]}],   # 최대 2장 권장(나란히)
    "tip": "md …",                           # 선택: TIP 상자
    "note": "md …",                          # 선택: 참고 상자
}
```

v1 형식(`shot2`/`caption2`/`callouts2`)도 그대로 읽습니다.

### 스크린샷과 CALLOUT 좌표

- 원본: `production/assets/shots/<stem>.png` (`.jpg`/`.webp`도 가능). 빌드 때 WebP 3종(800·1600·2400px)으로 변환합니다.
- **CALLOUT 좌표는 캡처 당시 CSS px**입니다. 빌더는 실제 이미지 크기에서 CSS 크기를 계산합니다.
  - 폭 ≥ 2400px이면 DPR 2로 봅니다: GE 2880×1620 → **1440×810**, Antigravity 2800×1800 → **1400×900**
  - 그보다 작으면 DPR 1(예: v1 1440×810)
  - 다르면 `"viewport": [w, h]`(CSS px)를 shot dict에 직접 적습니다.

```python
CALLOUT = {"box": [x, y, w, h], "label": "밝게", "pos": "above" | "below" | "inside"}  # pos 선택(기본 자동)
```

## 4. 영상 파일 (`site_v2/assets/video/`)

| 파일 | 필수 | 내용 |
|---|---|---|
| `<id>.mp4` | ✔ | H.264 + AAC |
| `<id>.ko.vtt` | | 한국어 자막(기본 켜짐). 마지막 cue로 영상 길이를 계산 |
| `<id>.jpg` | | 포스터 |
| `<id>.chapters.json` | | 단계별 구간. 있으면 '이 단계 영상 보기' 버튼·챕터 칩·재생 중 단계 표시·'이 단계만 재생'이 켜짐 |
| `<id>.chapters.vtt` | | 선택: `<track kind="chapters">` |

`chapters.json` (v1과 동일):

```json
{"video": "ge_lab7.mp4", "duration": 431.63,
 "chapters": [{"step": 1, "title": "새 에이전트 → 채팅 에이전트", "start": 26.1, "end": 37.6}, …]}
```

`step`은 1부터 시작하는 `steps` 순서입니다. 단계 수와 챕터 수가 다르면 빌드 경고가 납니다.
모든 미디어 URL에는 내용 해시(`?v=`)가 붙어 재렌더링 뒤에도 캐시된 옛 영상이 재생되지 않습니다.

## 5. 출력 구조

```
site_v2/
  index.html            홈(히어로 · 트랙 카드+Lab 목록 · 진행 방법 · 오프닝 · 데모 영상(탭) · 준비물/파일(탭) · FAQ · 마무리)
  ge/index.html         트랙 개요(진행률·이어서 하기 · 오프닝 영상 · Lab 카드 · 준비물/파일 · FAQ)
  ge/lab1.html …        Lab 페이지(사이드바 Lab 목록+단계 · 목표 · 데모 영상+구간 · 타임라인 단계 · 체크리스트)
  ag/…
  404.html  robots.txt
  assets/css/portal.css  assets/js/{theme.js,portal.js,search.json}
  assets/img/shots/*.webp  assets/fonts/…  assets/video/…  assets/files/…
```

## 6. 보안 규칙(빌더가 강제)

- 인라인 `<script>`/`style=""`/이벤트 핸들러 없음 → CSP `script-src 'self'; style-src 'self'`
- 콜아웃 위치·이미지 비율은 **빌드 때 생성한 CSS 클래스**로 적용
- 클라이언트 JS는 `createElement`/`textContent`만 사용(innerHTML 금지)
- localStorage에는 체크리스트·테마·'이 단계만 재생' 같은 UI 상태만 저장
- 외부 링크는 https만, `rel="noopener noreferrer"`
