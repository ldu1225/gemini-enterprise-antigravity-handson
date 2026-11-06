# production/content/v2 — lab content (Korean source edition)

Everything a learner reads on the portal lives here as **plain Python data** (dicts and lists). There is no CMS
and no markdown files: the site builder (`production/site_build_v2/build.py`) imports these modules, validates
them and renders HTML. The text is Korean; this README explains the format in English so the content can be
translated. The original Korean schema is [`v2/schema.md`](v2/schema.md).

```text
production/content/v2/
  site.py        SITE (dict) — portal-wide settings, hero, showcase, stage · TRACKS (list) — the two tracks
  ge.py          LABS for track "ge" — loads ge_labs/lab1.py … lab9.py (falls back to a skeleton = "coming soon" page)
  ag.py          LABS for track "ag" — loads ag_labs/lab1.py … lab10.py
  ge_labs/       one module per Gemini Enterprise lab, each defines LAB = {...}
  ag_labs/       one module per Antigravity lab
  schema.md      the format (Korean)
```

The long docstring at the top of each lab module is a **production note** (which recordings and stills are used
and why, what was cut for hygiene, facts the text relies on). It is not rendered.

## 1. Text markup (fields marked *md*)

Only these constructs are interpreted; everything else is shown literally (all text is HTML-escaped).

| Syntax | Result |
|---|---|
| `**bold**` | bold (may wrap inline code: ``**`code`**``) |
| `*emphasis*` | highlighter-style emphasis (not italic — better for Hangul). Not applied when there is a space just inside the `*`, so cron strings like `0 9 * * 1-5` stay literal |
| `` `code` `` | inline code; ≤ 22 characters never wrap, longer ones may wrap |
| `[text](https://…)` | external link, new tab — **https only**, anything else stays plain text |
| `- item` | consecutive `body` entries starting with `- ` become one bullet list |
| `1. item` (or `1)`) | consecutive numbered entries become one ordered list (starts at the first number) |

- Each string in a `body` list is one paragraph (or one list item); `\n` inside a string is handled line by line.
- Unbalanced `**` is dropped. `title`, `caption`, `check`, `more` are plain text (markup symbols removed).
- `qa.py` fails if unrendered markdown (`**`, backticks, `*…*`, `1. ` paragraphs) reaches the built HTML.

## 2. `site.py`

```python
SITE = {
    "title": "Hands-on Lab",                  # brand and <title> (required)
    "org": "Cymbal",                          # optional, footer / description
    "hero_kicker": "…",                       # optional pill above the hero title
    "hero_title": ["line 1", "line 2"],       # required, one string per line
    "hero_sub": "…",                          # required
    "description": "…",                       # optional <meta name=description> (defaults to hero_sub)
    "stats": [{"value": "19", "label": "…"}], # optional 4 hero stats; computed when omitted
    "files_src": "production/samples/v2/build",   # practice-file source folder (repo-relative)
    "video_src": "production/video_v2",       # optional: copy referenced videos into assets/video at build time
    "footer_note": "md …",                    # optional footer notice (synthetic data, real captures)
    "references": [{"title": "…", "url": "https://…"}],
    "showcase": [                             # optional home "results" bento of real captures
        {"track": "ag", "lab": "lab7", "stem": "ag_7v_21_deck_s1",
         "span": 7,                           # columns of a 12-column grid (a row sums to 12)
         "focus": "50 40", "zoom": 1.0,       # crop focus "x y" in %, zoom 1–3 (crops the real capture)
         "title": "…", "desc": "…"},
    ],
    "stage": [                                # optional rotating hero deck of real captures
        {"stem": "ge_3_32_canvas_ready", "title": "window title / dot label"},
    ],
}

TRACKS = [{
    "id": "ge",                 # lowercase id → output folder site_v2/ge/ and module ge.py
    "title": "Gemini Enterprise",
    "short": "GE",              # optional chip / narrow-screen label
    "tagline": "…",             # required, one line on the track card
    "hero_line": "…",           # optional second (gradient) line of the track hero
    "audience": "…",            # optional
    "accent": "#4285F4",        # optional track accent (defaults GE #4285F4, AG #9B72CB)
    "cover": "stem",            # optional cover still for the home track card
    "opening": {"video": "ge_opening", "title": "…", "desc": "…"},
    "prep": ["md …"],           # optional "before you start" list
    "files": [{"file": "Cymbal_….xlsx", "title": "…", "desc": "…", "labs": ["lab3"],
               "preview": "previews/….png", "bundle": False}],   # bundle=True → big download card
    "faq": [{"q": "…", "a": "md …"}],
}]
```

File paths must be relative to `files_src`; `..` or absolute paths fail the build.

## 3. A lab — `LAB` in `ge_labs/labN.py` / `ag_labs/labN.py`

```python
LAB = {
    "id": "lab1",               # [a-z0-9-] → site_v2/<track>/<id>.html
    "no": 1,                    # display number
    "title": "…", "subtitle": "…",
    "level": "입문",             # 입문 Intro | 기본 Basic | 중급 Intermediate | 심화 Advanced (see LEVELS in build.py)
    "minutes": 15,              # planned time
    "goal": "md …",
    "video": "ge1",             # assets/video/<id>.mp4 (+ .ko.vtt, .jpg, .chapters.json)
    "steps": [STEP, …],         # empty → rendered as a "coming soon" page
    "check": ["…"],             # checklist (state kept in the browser's localStorage)
    "more": ["prompt …"],       # "try more" prompts with copy buttons
}

STEP = {
    "title": "…",
    "body": ["md paragraph", "- bullet", …],
    "prompt": "text to paste" ,                     # dark prompt card + copy button
    "code": {"lang": "bash", "text": "…", "file": "optional/path"},   # or a list of such dicts
    # screenshots — one of three forms
    "shot": "stem", "caption": "…", "callouts": [CALLOUT, …],
    "shot": {"stem": "…", "caption": "…", "callouts": [...], "viewport": [1440, 810]},
    "shots": ["stem_a", {"stem": "stem_b", "caption": "…", "callouts": [...]}],   # up to 2 side by side
    "tip": "md …",
    "note": "md …",
}

CALLOUT = {"box": [x, y, w, h], "label": "text that is inside the box", "pos": "above" | "below" | "inside"}
```

- `code.lang` in `bash|sh|shell|zsh|console|terminal` renders a `$` prompt and dims `#` comments; other languages
  are shown without highlighting.
- Stills come from `production/assets/shots/<stem>.png|.jpg|.webp` and are converted to WebP at 800/1600/2400 px.
- **Callout boxes are CSS px of the capture**, not image pixels. Images ≥ 2400 px wide are treated as DPR 2
  (2880 × 1620 → 1440 × 810); otherwise DPR 1; or set `"viewport"` explicitly.
- `"step"` order defines the video chapters: `<video>.chapters.json` must have one chapter per step (build warns
  otherwise), and the lab page links each step to its chapter.

### Authoring rules that are enforced or reviewed

1. **Boxes are measured, never estimated.** Use the `targets` / `leaves` boxes saved next to the still
   (`<stem>.boxes.json`), or `python3 production/qa/find_text.py <stem> "on-screen text"` (OCR → CSS px), and
   check with `python3 production/qa/proof.py`.
2. **The label is exactly what is inside the box.** The box must not cover neighbouring rows or menu items, and
   must not cut the target in half. `pos` is only `above`, `below` or `inside`.
3. After any callout change run `build.py` (fails on out-of-range boxes / invalid `pos`), `qa.py --callouts-only`
   (≤ 1.5 px position error on desktop, mobile and lightbox; label chips not clipped) and
   `production/qa/callout_audit.py --track <ge|ag> --labs <labN>` (review every sheet).
4. Prompts and commands shown in a step must be the ones used in the recording (the AG prompts are defined in
   `production/capture/agy/agv.py`). Commands use variables from `lab.env` (`$PROJECT_ID`, `$REGION`, …), never a
   real project.
5. Show results big: labs that build something end with a step that shows the finished artifact.
6. Never use broken AI output in a still (raw `<br>`, `**`, `|---` in tables, garbled text in generated images).

## 4. Build and preview

```bash
python3 production/site_build_v2/build.py          # → site_v2/
python3 production/serve_site.py site_v2 8080      # → http://127.0.0.1:8080 (Range support for video seeking)
python3 production/site_build_v2/qa.py             # full browser QA (see production/site_build_v2/README.md)
```

For translating this content into English, see [docs/LOCALIZATION.md](../../docs/LOCALIZATION.md).
