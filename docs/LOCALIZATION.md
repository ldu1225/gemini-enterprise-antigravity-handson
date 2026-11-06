# Producing the English edition

The pipeline is language-neutral; the **content, the recordings and the narration are Korean**. An English
edition therefore means: translate the text, re-record the product UI in English, re-render the videos with
English narration, and switch a handful of hard-coded locale settings. This guide lists every place that has to
change and a sensible order of work.

## 1. What changes and what stays

| Layer | Stays as is | Must change |
|---|---|---|
| Lab content (`production/content/v2/`) | structure, step order, prompts' intent, callout *targets* | all text (≈ 1,640 strings / 168k Korean characters), prompts, `level` keys, file names referenced in `site.py` |
| Practice files (`production/samples/v2/`) | data model, seeds, stories, verification | all strings and file names; holiday calendar if you change the locale; PDF body font |
| Stills and recordings | capture scripts, coordinate system (1440×810, DPR 2) | every still and recording (the product UI must be English); **all callout boxes re-measured** |
| Videos (`production/render/scripts/v2/`) | segment structure, chapters map, encode settings | narration `text` (≈ 1,410 sentences / 43k characters), `say`, on-screen titles/cards/labels (≈ 19k characters), callout boxes and `at` times (new recordings) |
| Portal UI (`production/site_build_v2/`) | design, CSS, security model | hard-coded Korean UI strings, `lang`, caption track language |
| QA (`production/qa/`, `site_build_v2/qa.py`) | gates and thresholds | OCR language order, Korean-specific text checks |

## 2. Recommended order of work

1. **Text-only portal first.** Translate `production/content/v2/` and the builder's UI strings, then
   `python3 production/site_build_v2/build.py` — the builder produces all 23 pages without stills or videos
   (warnings only), so reviewers can read the English edition before anything is recorded.
2. **Practice files.** Translate the generators in `production/samples/v2/`, rebuild (`build_all.py`), update file
   names in `site.py` (`TRACKS[i]["files"]`) and in the lab text.
3. **Recording environment in English.** Your own Gemini Enterprise app with fictional Cymbal content, browser and
   account language English; the Antigravity desktop app; a Google Cloud project for BigQuery / Agent Runtime.
4. **Re-capture** every still and recording (`production/capture/`), with English prompts. Re-measure all callouts
   (`targets` in `boxes.json`, `production/qa/find_text.py`).
5. **Re-render** each video with English narration (`production/render/`), then run the video audits.
6. **QA and deploy** as a separate service (`SERVICE=… deploy/deploy.sh`) or a separate build directory
   (`build.py --out site_en`).

## 3. Touchpoints

### 3.1 Content and practice files

| Where | What to change |
|---|---|
| `production/content/v2/site.py` | `SITE` hero / footer / references, `TRACKS[*]` tagline, prep, files (titles, descriptions, **file names**), FAQ, `showcase` / `stage` titles |
| `production/content/v2/ge_labs/*.py`, `ag_labs/*.py` | `title`, `subtitle`, `goal`, step `title` / `body` / `prompt` / `code` comments / `caption` / callout `label` / `tip` / `note`, `check`, `more`. Callout labels must match the **English** UI text inside the box. |
| `level` values (`입문`, `기본`, `중급`, `심화`) | they are keys of `LEVELS` in `build.py` — either keep the keys and translate the displayed label in the builder, or change both together |
| GE lab text mentioning `?hl=ko` (e.g. GE Lab 1 tip, GE track prep) | replace with the English equivalent (`?hl=en`) |
| `production/capture/agy/agv.py` (`L3_*` … `L10_*` prompt constants) | the exact Antigravity prompts typed on camera — translate them and keep them identical to the prompts shown in the lab pages. Two encode the language on purpose: `L5_RULES` (team rule 1 "screens and documents in Korean") and `L8_TOOLS` ("agent instructions in Korean") |
| `production/samples/v2/build_voc_starter.py` | starter README, CX request memo (`요청서_CX팀.md` → e.g. `request_cx_team.md`, including its "screens and reports in Korean" requirement), `lab.env` comments, ticket categories/products/messages/names, the deck template text |
| `production/samples/v2/data_*.py`, `build_*_pdf.py`, `build_marketing_pdfs.py`, `build_skill.py`, `build_bundle.py` | all document text, sheet/column names, skill name/description, bundle read-me, output file names |
| `production/samples/v2/calendar_kr.py` | Korean public holidays used by the policy deadline questions — replace if your edition changes the locale, and update `answer_keys/policies_qa.md` via `write_answer_keys.py` |
| `production/samples/v2/doccss.py`, `verify.py` | PDF body font (NanumGothic, Korean) → a static Latin font that embeds as Type0; the font check in `verify.py`; `BANNED` brand list (keep it) |
| `html lang="ko"` in generated HTML (`build_*_pdf.py`, `build_previews.py`, `build_voc_previews.py`, `render/out/openings/make_slides.py`) | `lang="en"` |

### 3.2 Capture (`production/capture/`)

| Where | What to change |
|---|---|
| `?hl=ko` appended to `APP_HOME` in every GE script (`capture/v2/*.py`, `capture/agy/ge_voc_agent.py`) | `?hl=en` |
| Locators by visible Korean text / aria-labels (`vis_text("…")`, `vis_label("…")`, `click(..., label="…")`) | the English UI strings; `label=` values become the names used by `"at": "click:<label>"` in render scripts — keep both in sync |
| `wait_answer_done`, brand scans and other text heuristics | re-check for English UI wording |
| `shot()` `targets` labels | English labels (they become callout labels) |

*(Detailed per-file list: see [§ 4](#4-file-by-file-notes-from-the-code-review).)*

### 3.3 Render (`production/render/`)

| Where | What to change |
|---|---|
| `production/render/scripts/v2/*.json` | `title`, `brand`, segment `kicker` / `title` / `subtitle` / `bullets`, label `kicker` / `text`, callout `text`, narration `text`; `say` only where English pronunciation needs help (most `say` fields exist to make Korean TTS read English product names — drop them) |
| `production/render/lexicon.json` | Korean pronunciations of English terms — replace with an English lexicon (or empty) |
| `production/render/engine/voice.py` (+ `tts.py`) | voice name, `STYLE` prompt, ASR transcription checks and text normalisation (Korean-specific rules such as filler words "어/아", numerals and dates read in Korean), comma-pause shaping thresholds |
| `production/render/engine/typo.py`, `common.py` | caption / card fonts (Pretendard covers Latin, but you may prefer a Latin face), caption line-length limits tuned for Hangul |
| `production/render/render.py` | output caption file name `<id>.ko.vtt` |
| `production/render/out/openings/make_slides.py` | all slide text, `lang` |

### 3.4 Portal (`production/site_build_v2/`)

| Where | What to change |
|---|---|
| `build.py` page shell | `<html lang="ko">` → `en` |
| `build.py` video tags | `<track kind="captions" srclang="ko" label="한국어" …>` and the chapters track label; the `.ko.vtt` file name it looks for |
| `build.py` UI strings | every Korean label rendered by the builder (navigation, buttons, section headings, empty states, level names …) — see § 4 |
| `static/js/portal.js` | Korean strings created at runtime (copy feedback, search placeholder/results, dock labels …) — see § 4 |
| `static/css/portal.css` | Hangul-specific typography (e.g. `word-break: keep-all`, line heights) and the font stack |
| `qa.py` | the two search queries typed into the command palette (`"에이전트"`, `"프롬프트"`); all other checks are language-neutral |

### 3.5 QA (`production/qa/`)

| Where | What to change |
|---|---|
| `vision_ocr.js` | `recognitionLanguages = ['ko-KR', 'en-US']` → `['en-US']` (or English first) |
| `callout_audit.py`, `ring_band_audit.py` | nothing — their text normalisation is language-neutral |
| `production/render/tools/ocr.py` | nothing — it already uses Tesseract `eng`, which becomes fully usable on an English UI |

## 4. File-by-file notes from the code review

Line numbers refer to the files as committed. *Recommendation* is what we would do for a clean English edition.

### 4.1 Narration engine — `production/render/engine/`

| Location | Korean-specific behaviour | Recommendation |
|---|---|---|
| `voice.py` `ASR_PROMPT` (≈ l. 460) | the transcription instruction is Korean ("transcribe this Korean speech …") | English prompt |
| `voice.py` `normalize_ko()` (≈ l. 189) | keeps only Hangul before computing the character error rate — **with English narration the CER is always 0 and the ASR gate silently passes** | add `normalize_en()` (lower-case alphanumerics, number words) and select by language |
| `voice.py` `FILLERS` (l. 45), `fillers()` (≈ l. 501) | Korean filler syllables, `[가-힣]` regex | English fillers (uh, um, er …) |
| `voice.py` `_CRITICAL` (l. 49), `missing_critical()` (≈ l. 507) | Korean numerals and month names that must be heard correctly | English equivalents ("three point eight", month names) |
| `voice.py` `comma_weights()` (≈ l. 127) and the rate bounds in `best_take()` | pacing tuned per Hangul syllable (Latin letter weighted 0.45) | recalibrate for English |
| `voice.py` Sino-Korean number reading and `_lexicon()` (≈ l. 137–186) | adds Korean readings such as AI → 에이아이, % → 퍼센트 | drop or replace |
| `voice.py` `VOICE`, `common.py` `DEFAULT_VOICE`, `tts.py` `normalize_voice()` | voice "Kore", chosen as a Korean instructor voice | pick an English voice; `STYLE` is already English |
| `production/render/lexicon.json` | maps English terms to Korean phonetics | English lexicon (VOC, CSV, GE, MCP, ADK, slash commands) or disable it in the scripts |
| `timeline.py` (l. 588) | fast-forward badge text `빨리 감기 ×N` is hard-coded | "Fast-forward ×N" (ideally a script option) |
| `tts.py` sentence splitter (≈ l. 74) | splits after `.`/`!`/`?` — English abbreviations ("e.g.", "Dr.") would split | protect abbreviations or use explicit narration items |
| `timeline.py` `caption_max_w`, caption size; `typo.py` keep-all wrapping, Hangul tracking clamp, fallback font `AppleSDGothicNeo` | caption layout tuned for Hangul | review caption chunking with English (longer lines), consider a Latin font such as Inter |
| `render.py` (l. 237) | writes `<id>.ko.vtt` | `<id>.en.vtt` — and update `build.py` (below) at the same time |
| `production/render/tools/chapters.py` | chapter titles come from the content modules | follows the content translation automatically |
| `production/render/out/openings/make_slides.py` | `<html lang="ko">`, all slide strings (two of them state "Korean" as a team rule), level keys | translate; `lang="en"` |
| `production/render/scripts/v2/*.json` | `brand` ("… 핸즈온 랩"), titles, kickers, subtitles, bullets, label texts (e.g. "미리 보기"), callout chip texts, narration `text`, ≈ 435 Korean `say` overrides; event references such as `click:시작하기`, `target:명령 승인` | translate; drop most `say`; event references must equal the labels logged by the new English recordings |

### 4.2 Capture — `production/capture/`

| Location | Korean-specific behaviour | Recommendation |
|---|---|---|
| `?hl=ko` in `v2/*.py` (all GE scripts, `probe.py`, `chats.py`), `v2/ge7_refine.py` / `v2/ge8_refine.py` (`/r/agents?hl=ko`), `agy/ge_voc_agent.py` | forces the Korean GE UI | one constant / env var set to `hl=en` |
| Korean aria-label and visible-text selectors (≈ 45 distinct strings): `helpers.py` `submit()` (`[aria-label="제출"]`), `chats.py`, `v2/ge1e_answer_tools.py`, `v2/ge1bcd.py`, `v2/ge3.py`, `v2/ge4.py`, `v2/ge5.py`, `v2/ge7*.py`, `v2/ge8*.py`, `v2/ge9.py` | locate buttons by Korean labels (e.g. 파일 추가, 도구 선택, 새 에이전트, 테스트) | a locale table of UI strings; `ge.py` `ensure_sidebar` and the busy regex already have English fallbacks |
| Korean text regexes: `v2/ge3.py` / `v2/ge4.py` error toast (`문제가 발생했습니다`), `v2/ge3.py` file chip, `v2/ge5.py` studio pending (`생성 중`) and citation filter | detect UI states by Korean wording | English UI wording |
| Korean practice-file names matched by glob (`v2/ge3.py` 월별매출, `v2/ge4.py` 브리프, `ge5.py`, `ge6.py`, `ge7.py`, `ge7_refine.py`, `ge8_refine.py`) | find the upload file | rename together with the practice files |
| On-camera prompts: all prompt constants in `v2/*.py` (e.g. `ge2.py`, `ge4.py` — which asks for a Korean paragraph —, `ge5.py`, `ge9.py`), `agy/agv.py` `L3_*` … `L10_*`, `agy/ge_voc_agent.py` `Q` | Korean prompts | translate and keep identical to the lab pages |
| `agy/agv.py` workspace names used as selectors (`요청서_CX팀.md`, `@요청서`, heading "운영 가이드") | starter file names | follow the renamed starter files |
| Event labels (`agy/agrec.py` e.g. "새 대화", "허용"; `ge.click(..., label="시작하기")`; `mark_target("명령 승인")`) | Korean labels referenced by the render scripts | rename in lock-step with the scripts (English labels for new takes) |
| `agy/ge_voc_agent.py` `AGENT = "Cymbal VOC 분석가"`, `vis_label("에이전트")` | display name of the agent published in AG Lab 9 | the English display name (also `GE_DISPLAY_NAME` in the starter `lab.env`) |
| Showcase selectors: `agy/ag4_dash.py` (KPI cards, titles, `data-name` values, option "공기청정기"), `agy/ag7_deck.py` (slide labels, presenter buttons), `agy/ag8_eval.py` ("총 6건"; a run-specific report file name) | depend on the Korean artifacts the agent built | regenerate the English artifacts, then update the selectors |
| `agy/ag1r_console.py` target labels (partly Korean; referenced by `ag1.json`) | console selectors themselves are English | translate the labels |
| `ge.py` `BRANDS` | brand-leak deny-list centred on Korean brands | extend for the target market |

### 4.3 Portal — `production/site_build_v2/`

| Location | Korean-specific behaviour | Recommendation |
|---|---|---|
| `build.py` l. 768 `<html lang="ko">`; l. 640 / 644 caption and chapter `<track srclang="ko" label="한국어" / "단계">`; l. 557 / 631 `.ko.vtt`; video meta "한국어 내레이션" | locale baked into markup and file names | derive from a `SITE["locale"]` setting (`lang`, `srclang`, label, `<id>.<lang>.vtt`) |
| `build.py` l. 56 `LEVELS` keys 입문/기본/중급/심화 (warning text at l. 401 lists only three) | content uses Korean level names as keys | language-neutral level codes in content + localized labels |
| `build.py` units and counters (`fmt_minutes` 분/시간, "N분 SS초", "{n}단계", "N개 구간", "완료", hero fact labels such as 개 Lab / 시간 분량 / 편 데모 영상 / 종 실습 파일 / 내 진행률) | Korean counters | a plural-aware formatter (1 lab / 9 labs) |
| `build.py` chrome strings: skip link, brand aria, search button and palette (placeholder, key hints), theme toggle, top navigation and CTA "실습 시작", drawer, lightbox, "(새 탭)", "공식 문서", trademark line, breadcrumbs "홈", "준비 중", copy button "복사", demo-video section ("이 단계만 재생", chapter aria), prompt card label/hint, note label "참고", step-play, "더 해 보기", checklist, pager, goal kicker, mobile bar, step dock "다음", opening card, empty states, bundle card, hero buttons, section headings and leads, CTA bands, page `<title>`s and the 404 page, default stage titles, deck controls, bento, track and "how it works" cards, search-index labels | ≈ 200 lines contain Hangul | move to one locale dictionary (e.g. `production/site_build_v2/i18n/<lang>.json`) used through `t()` / `plural()` helpers; English labels already used: STEP, LAB, TRACK, TIP |
| `build.py` checklist keys (hash of the item text) | translating an item resets saved ticks | expected; no action |
| `static/js/portal.js` theme announcements, copy feedback, default caption "스크린샷", checklist-complete announcement, resume labels 시작하기 / 이어서 하기 / 다시 보기 (l. 327; must match `build.py`), step-only end message, "더 해 보기" / "체크리스트" (l. 585, 620), palette group names, empty result `‘…’에 대한 결과가 없습니다` (l. 761, different word order), audio-stall notice, deck toggle aria | runtime strings | inject a string table at build time into `portal.js` (like the dark-mode token injection) so the `?v=` hash changes; **never** emit an inline `<script>` (CSP + the static QA check would fail) |
| `static/js/portal.js` search | lower-case + whitespace tokenisation, no stemming | fine for English |
| `static/css/portal.css` `--font-sans` (Pretendard / Apple SD Gothic Neo / Malgun Gothic first), `word-break: keep-all` on body, prompt text and "try more", `em` rendered as a highlighter (no italics) | Hangul typography | scope keep-all to `:lang(ko)`, put a Latin face first, consider italics for `em` |
| `static/css/portal.css` width-sensitive rules: search button min-width, the ≤ 1439 px rule that hides section links, `nowrap` on top-nav links, buttons, tabs, segment control, chips, callout chips | tuned to Korean label widths | re-check every breakpoint with English labels |
| `qa.py` l. 586 / 608 | types `에이전트` / `프롬프트` into the palette | locale-driven query |
| `production/content/v2/site.py` references | documentation links end in `?hl=ko` | `?hl=en` |

## 5. Gotchas

- **Text length.** English labels are often longer than Korean; check callout label chips (`qa.py --callouts-only`
  fails on clipped chips), cards in the videos, and the step dock.
- **UI differences by locale.** Menu names, button order and available models can differ between UI languages,
  regions and editions. Re-verify every step against the English UI; never translate a screenshot's label without
  re-capturing it.
- **AI output differs on every run.** Re-capture until the answer is clean (no raw markdown, no garbled text in
  generated images) and update the facts quoted in the text and narration accordingly.
- **Numbers and dates.** The synthetic data uses KRW, Korean regions and Korean holidays. Decide whether the English
  edition keeps the Korean setting (simplest: keep data, translate labels) or localizes the data too.
- **Narration timing.** English speech has a different pace; keep `"at"` anchors on recording events
  (`"at": "click:<label>"`) rather than fixed seconds so the timeline adapts.
- **Privacy.** Use only your own demo app and project; run `tools/check_sensitive.py` with your own denylist and
  OCR-scan rendered frames before publishing.
