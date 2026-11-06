# `production/site_build_v2` — portal builder and browser QA

[`build.py`](build.py) turns the lab content in [`../content/v2/`](../content/v2/) into the static Hands-on Lab
portal (`site_v2/`). [`qa.py`](qa.py) checks a built portal in real browsers. Why the UI looks and behaves the way it
does is explained in [docs/UI_DESIGN.md](../../docs/UI_DESIGN.md); the content format is described in
[production/content/README.md](../content/README.md) (English) and [schema.md](../content/v2/schema.md) (Korean
original).

## Requirements

| Tool | Needed for | Notes |
|---|---|---|
| Python 3 + Pillow | `build.py` | `build.py` imports `PIL.Image` even when no screenshots exist; WebP encoding must be available (the standard Pillow wheels include it). Versions: [`requirements.txt`](../../requirements.txt) at the repository root. |
| Playwright for Python + its Chromium | `qa.py` | `python3 -m pip install -r requirements.txt` and `python3 -m playwright install chromium` |
| Playwright WebKit **or** Google Chrome | `qa.py` media checks | Playwright's Chromium cannot play H.264, so the chapter checks try WebKit first and then Chrome (`channel="chrome"`). Without either, use `--no-media` (otherwise the run records a failure). |

## Quick start

```bash
python3 production/site_build_v2/build.py              # production/content/v2 → site_v2/
python3 production/serve_site.py site_v2 8080          # preview at http://127.0.0.1:8080/ (Range requests, no-store HTML)
python3 production/site_build_v2/qa.py --callouts-only # fast gate: callout geometry only
python3 production/site_build_v2/qa.py                 # full browser QA → production/site_build_v2/qa/
```

Both scripts locate the repository from their own path (two directories up), so they work from any working
directory. `serve_site.py` changes into the site directory you pass, so give it a path that is valid from where you
run it.

## `build.py`

### Usage

| Flag | Default | Effect |
|---|---|---|
| *(none)* | — | Build `production/content/v2/` into `site_v2/` at the repository root. |
| `--out DIR` | `site_v2/` (`site_v2_fixture/` with `--fixture`) | Output directory. A relative path is resolved against the current directory. It must be inside the repository, must not be the repository root, and must not be named `site`, `production`, `deploy` or `archive`. |
| `--fixture` | off | Read `production/content/v2/_fixture/` instead and write a `FIXTURE_DO_NOT_DEPLOY` marker into the output. The fixture is **not** part of this repository. |
| `-h`, `--help` | | Prints the module docstring. |

Exit status: `0` when the pages were written (warnings do not change it); `2` on a build error (`build failed: …` on
stderr); an unexpected exception (for example a syntax error in a content module) ends with a Python traceback and
status `1`.

### What a build does

In the order of `build()`:

1. Check the output directory, load and validate the content (`load_content()`).
2. Delete stale `*.html` files in the first-level subdirectories of the output (for example `site_v2/ge/*.html`);
   nothing under `assets/` is ever deleted.
3. Optionally copy the referenced videos from `SITE["video_src"]` (`sync_videos()`), collect the practice files
   (`collect_files()`), copy the fonts (`ensure_fonts()`) and the official brand files (`copy_brand()`), and generate
   the accent tokens (`accent_css()`).
4. Build the search index (`search_index()`).
5. Render every page once with placeholder asset URLs. This "dry run" registers all generated CSS (aspect ratios,
   bento crops, callout geometry) and converts screenshots to WebP.
6. Write `assets/css/portal.css`, `assets/js/theme.js`, `assets/js/portal.js` and `assets/js/search.json`; each URL
   gets a `?v=` content hash (`write_static()`).
7. Render and write every page with the final asset URLs (warnings are not repeated in this pass).
8. Write `robots.txt` (`Disallow: /`) and print a summary line, for example
   `wrote 23 pages → site_v2/ · 0 screenshots · css 144 KB · js 43 KB`, followed by `N warning(s)` if there were any.

Step 2 runs before the practice-file, brand and callout checks, so a build that fails at one of those can leave the
output without its track and lab pages. Fix the error and build again; never deploy the output of a failed build. For a completely clean output (for
example after renaming screenshots), delete the output directory before building.

### Inputs

| Input | Location | If it is missing |
|---|---|---|
| Content | `production/content/v2/site.py` (`SITE`, `TRACKS`) and one `<track id>.py` per track (`LABS`); `ge.py` / `ag.py` load `ge_labs/<lab>.py` / `ag_labs/<lab>.py` and fall back to a "coming soon" skeleton | build error |
| Static assets | [`static/`](static/) — see [the folder map](#static-and-vendor-folders) | build error for missing brand files; Python error otherwise |
| Pretendard font | [`vendor/fonts/pretendard.css`](vendor/fonts/pretendard.css) + `vendor/fonts/pretendard/*.woff2` (a legacy `site/assets/fonts/` directory is also searched) | warning; system fonts are used |
| Screenshots | `production/assets/shots/<stem>.png` (or `.jpg`, `.jpeg`, `.webp`) — **not included in this repository** | warning per stem; the figure is left out |
| Practice files | `SITE["files_src"]` (here `production/samples/v2/build/`, included) | warning per file; preview images likewise |
| Videos | `site_v2/assets/video/<id>.mp4` (+ `.ko.vtt`, `.jpg`, `.chapters.json`, `.chapters.vtt`); filled from `SITE["video_src"]` (here `production/video_v2/`, **not included**) when that directory exists | warning per lab/opening video; a placeholder card is shown |

### Output

```text
site_v2/
├── index.html                      home
├── 404.html                        served by nginx for missing paths (absolute URLs)
├── robots.txt                      Disallow: /
├── ge/index.html, ge/lab1.html … ge/lab9.html
├── ag/index.html, ag/lab1.html … ag/lab10.html
├── assets/
│   ├── css/portal.css              Pretendard @font-face + portal.css (dark tokens inserted) + generated rules
│   ├── js/theme.js, js/portal.js, js/search.json
│   ├── fonts/                      Inter, JetBrains Mono (+ licences), pretendard/*.woff2 (+ LICENSE.txt)
│   ├── img/brand/                  google-cloud.svg, google-cloud-dark.svg, favicon.ico, cloud-192.png
│   ├── img/shots/<stem>-800.webp, -1600.webp, -2400.webp
│   ├── img/files/<hash>.webp       practice-file previews (720 px)
│   ├── files/…                     practice files, same relative paths as in files_src
│   └── video/<id>.mp4 …            demo and opening videos with captions, posters and chapters
└── FIXTURE_DO_NOT_DEPLOY           fixture builds only
```

With the current content that is 23 pages: home, 2 track pages, 9 + 10 lab pages and the 404 page. Fonts, videos and
practice files are hard-linked from their sources (copied where hard links are not possible) and replaced only when
the source is newer or differs in size; WebP variants are regenerated only when the source image is newer.

### Warnings and build errors

**Build errors** stop the build with exit status 2:

| Error | Raised by |
|---|---|
| `content module not found` (`site.py` or a `<track>.py`) | `load_module()` |
| `SITE['title']`, `SITE['hero_title']` or `SITE['hero_sub']` missing | `load_content()` |
| invalid or duplicate track id (pattern `^[a-z0-9][a-z0-9-]{0,40}$`) | `load_content()` |
| invalid or duplicate lab id, or a lab called `index` | `load_content()` |
| invalid video id for a lab or an opening (pattern `^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$`) | `load_content()` |
| unsafe practice-file path (absolute, `..`, backslash) | `collect_files()` |
| brand asset missing in `static/brand/` | `copy_brand()` |
| callout without a four-number `box` | `figure()` |
| callout box outside the capture, or `pos` not `above` / `below` / `inside` | `callout_css()` |
| callout class collision (two different geometries with the same hash) | `callout_css()` |
| output directory outside the repository or with a reserved name | `build()` |

**Warnings** are printed as `  ! …` (each distinct message once) and do not change the exit status:

| Warning | Meaning |
|---|---|
| `unknown level '…' (입문\|기본\|심화)` | `level` is not a key of `LEVELS` (`입문`, `기본`, `중급`, `심화`); the chip falls back to the middle style |
| `invalid screenshot stem` / `screenshot not found: <stem>` | the stem breaks the allowed pattern / no source image exists |
| `stage item skipped …` / `showcase item skipped …` | a hero-deck or bento item's screenshot (or track) was not found |
| `video_src not found or outside repo` | `SITE["video_src"]` does not point to a directory inside the repository |
| `<track>/<lab>: video '<id>' not found in assets/video` / `<track>: opening video … not found` | the MP4 is missing |
| `<id>.chapters.json unreadable` / `missing 'chapters' list` / `no valid chapters` | a chapters file could not be used |
| `<id>.chapters.json has no chapter for step(s) [...]` | the number of chapters does not match the steps |
| `files_src missing — skipped …` / `practice file not found` / `file preview missing` | practice files are incomplete |
| `Pretendard not found — falling back to system fonts` | no Pretendard source directory |

An invalid track accent colour falls back to the default without a warning. The repository's working rules require
**0 warnings** for a finished lab ([AGENTS.md](../../AGENTS.md)); because warnings do not affect the exit status, a CI
job has to check the output, for example `python3 production/site_build_v2/build.py | tee build.log` followed by
`! grep -q 'warning(s)' build.log`.

### Building without media (this repository as published)

Screenshots and videos are not part of the repository, but the build still writes all 23 pages. A build of this
repository reports `0 screenshots` and 283 warnings: 255 `screenshot not found` (including 7 hero-deck items),
6 skipped bento items, 19 lab videos and 2 opening videos not found, and 1 for the missing `video_src`
directory. The practice files are present, so the file lists and previews are complete.

What changes on the pages:

- **Home:** no hero deck, no "What you'll build" bento, no opening and demo-video sections, no track-card covers; the
  hero's second button becomes "download practice files"; the video count is hidden from the hero facts.
- **Track pages:** no opening-video stage, the second hero button becomes "download files", the video fact shows 0,
  and lab cards show an hourglass placeholder instead of a thumbnail.
- **Lab pages:** a "demo video in preparation" card instead of the player and chapter list, no "watch this step"
  buttons and no figures; text, prompts, code blocks, tips, "try more", the checklist, the pager and the step dock are
  complete.

## `static/` and `vendor/` folders

```text
static/
├── css/portal.css          design system in cascade layers; contains the /*@DARK_TOKENS@*/ placeholder
├── css/tokens-dark.css     dark-theme token declarations, inserted by dark_wrap()
├── js/theme.js             applies a pinned theme before first paint (blocking <script> in <head>)
├── js/portal.js            all client behaviour (deferred): palette, lightbox, copy, checklist, chapters, scrollspy, dock, deck …
├── icons.svg               inline SVG sprite (36 line icons), inserted at the top of <body> on every page
├── favicon.svg             not referenced by build.py
├── fonts/                  Inter and JetBrains Mono (variable, Latin subsets) + OFL licence files
└── brand/                  official Google Cloud logo (light and reversed), favicon.ico, cloud-192.png, SOURCE.md
vendor/fonts/
├── pretendard.css          92 @font-face rules with unicode-range subsets
└── pretendard/             PretendardVariable.subset.0–91.woff2 + LICENSE.txt (SIL OFL 1.1)
```

Edit the files in `static/`; never edit `site_v2/assets/` — it is regenerated on every build and the content hashes
in the URLs change automatically. Keep the class names that `portal.js` and `qa.py` depend on (`.fig-stage`, `.co`,
`.co-tag`, `.steps > .step`, `.nav-step`, `.chapter`, `.step-play`, `[data-checks]` …). Generated class names must stay
content-addressed: callout classes are hashes of their geometry and must never be derived from lab or step ids (both
tracks have `lab1` … `lab9`).

## `qa.py`

`qa.py` serves the built site itself (a threaded server on `127.0.0.1` with a free port and HTTP `Range` support), so
no preview server is needed.

### Usage

| Flag | Default | Effect |
|---|---|---|
| `--site DIR` | `site_v2/` (`site_v2_fixture/` with `--fixture`) | built site to test |
| `--out DIR` | `production/site_build_v2/qa/` | screenshots and `report.json` |
| `--fixture` | off | test the fixture build (not included in this repository) |
| `--no-media` | off | skip the video/chapter checks |
| `--callouts-only` | off | run only the callout-geometry gate and print its JSON result |

Exit status: `0` when nothing gating failed, `1` otherwise.

> [!NOTE]
> A full run also works on a build **without screenshots or videos** (this repository as published): the lightbox
> checks are skipped (`"lightbox_open": "skipped: no screenshots in this build"` in `report.json`), no lab page has a
> chapter list, and the callout gate reports `"checked": 0`. Verified on a fresh build of this repository: exit status
> 0 with 0 static problems, console errors, failed requests, broken images, overflow pages and contrast failures.

### What a full run checks

1. **Static checks** of every built HTML file: inline `style` attributes, inline `<script>`, inline event handlers,
   `<style>` elements, external `src`, external links without `target="_blank"` and `rel="noopener noreferrer"`,
   `javascript:` / `data:` links, and unrendered markdown (`**`, backticks, `*…*`, `[text](url)`, paragraphs that start
   with `1. `). The shipped JavaScript must not contain `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
   `document.write`, `eval(` or `new Function`.
2. **Page sample** (`pick_pages()`): the home page, the first track page in alphabetical order, the lab page with the
   most "watch this step" buttons, callouts and chapters, and the first lab page with code blocks.
3. **Viewports:** desktop 1440 × 900 (light and dark), tablet 820 × 1180 (light) and mobile 390 × 844 at device scale
   2 (light and dark, touch), all with reduced motion. For each sampled page: scroll through to load lazy images, then
   record horizontal overflow, broken images, console errors, failed requests (HTTP ≥ 400) and — except on tablet —
   text contrast against WCAG AA (4.5 : 1, or 3 : 1 for large text); take screenshots (plus full-page shots, a lab
   step, a code block, the home files section and the mobile drawer).
4. **Interactions** (desktop, light, motion allowed): open the palette with ⌘K / Ctrl+K, type a query, move with the
   arrow keys and navigate with Enter; pin the dark theme and check that it survives a reload and updates
   `<meta name="color-scheme">`, then reset it; switch the home video tabs by click and by keyboard; copy a prompt and
   read the clipboard; open the lightbox (callouts are cloned) and step through a gallery with → ; tick a checklist item,
   reload, and check the percentage, the sidebar progress, the progress ring and the home "continue" button; check the
   sidebar's current step after scrolling to step 3.
5. **Callout geometry gate** — the same as `--callouts-only`, below.
6. **Media checks** (unless `--no-media`), on every lab page with a chapter list: the number of "watch this step"
   buttons must equal the number of steps that have a chapter; clicking a chapter button and the last step button must
   seek to the chapter start (±0.5 s), show the right "STEP n" chip and mark the right step; the video must be scrolled
   into view; once per run, "play this step only" must pause within 0.6 s of the chapter end (played at 4× speed).

**What decides the exit status:** static problems, broken images, horizontal overflow, failed requests, console or
page errors, chapter failures and callout failures. Contrast results, interaction results and callout warnings are
reported only — read them in `report.json`.

### `--callouts-only`

For every lab page that contains callouts, at 1440 × 900 (device scale 1) and 390 × 844 (device scale 2): load the
page, scroll through it, wait for all screenshots, then compare each `.co` box with the position computed from its
`data-box` / `data-cap` attributes and the rendered image. Failures: an edge more than 1.5 px off, a stretched image
(aspect skew > 0.01), a label chip cut off by the screenshot edge, a box that is not rendered, or a callout outside a
screenshot. On desktop the same check runs inside the lightbox for every figure with callouts. A chip that covers more
than 25 % of another box is a warning. The result is printed as JSON:

```json
{"checked": 0, "failures": [], "warnings": []}
```

(`checked` is 0 for this repository as published, because no screenshots are included.)

### Outputs

- `production/site_build_v2/qa/*.png` — screenshots named `<viewport>_<scheme>_<page>.png` plus the interaction shots
  (`desktop_light_cmdk.png`, `desktop_light_lightbox.png`, `desktop_chapters.png` …). A full run deletes the old PNG
  files first.
- `production/site_build_v2/qa/report.json` — `pages`, `problems`, `console`, `failed_requests`, `broken_images`,
  `layout`, `contrast`, `interactions`, `callouts`, `chapters` and a `summary`.
- The console shows the report (without screenshots, layout and contrast details) and the first contrast failures per
  page.

## Localization pointers

The builder and the client script carry the Korean UI strings of the source edition, `<html lang="ko">`, Korean
caption-track settings (`srclang="ko"`, `.ko.vtt`), Korean level names (`LEVELS`), Korean counter words and
Hangul-oriented typography; `qa.py` types Korean search queries. See [docs/LOCALIZATION.md](../../docs/LOCALIZATION.md)
and [§ 15 of UI_DESIGN.md](../../docs/UI_DESIGN.md#15-locale-specific-behaviour).
