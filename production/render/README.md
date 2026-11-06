# production/render — recordings → finished tutorial videos

Turns capture recordings (`production/assets/recordings/<id>/frames/*.jpg` + `frames.json` + `events.json`, optional
`meta.json`) and the opening-slide pseudo recordings into **1920×1080 / 30 fps H.264 + AAC** tutorial videos with eased
zoom/pan, a device-frame look, measured callouts, burned-in captions, Gemini TTS narration, a Lyria music bed, a WebVTT
caption file, a poster and per-step chapters. **Only real recordings are used for product UI** (`production/DESIGN_v2.md`
§0); everything drawn on top is graphics.

The full production process (capture → render → QA → portal) is in [docs/VIDEO_PRODUCTION.md](../../docs/VIDEO_PRODUCTION.md);
this README is the engine reference.

```bash
python3 production/render/render.py production/render/scripts/v2/<id>.json --out production/video_v2
#  -> <out>/<id>.mp4     H.264 High yuv420p BT.709 (crf/preset from "encode", default crf 24 / slow), AAC 48 kHz stereo, +faststart
#  -> <out>/<id>.ko.vtt  captions
#  -> <out>/<id>.jpg     poster
#  -> <out>/<id>.chapters.json / .chapters.vtt   (if the script has "chapters")
# Without --out the files go to site/assets/video (engine/common.py SITE_VIDEO_DIR);
# the v2 portal reads production/video_v2 (production/content/v2/site.py "video_src").
```

| Option | Purpose |
|---|---|
| `--dry-run` | build the plan (new TTS is synthesized and cached) and print the timeline: segment times, rec ranges, time-remap pieces, sync points, badges, callouts, sentence times |
| `--stills 3,8.5,12` / `--stills-every 1` | render only those frames (global seconds) as PNG → `production/render/out/<id>/still_<t>s_f<frame>.png` |
| `--callout-qa` | contact sheet + JSON report of every callout (`production/render/out/<id>/<id>_callouts.jpg/.json`), then exit |
| `--strict-callouts` | run the callout QA first and abort the render if any callout fails |
| `--fast` | quick preview encode (x264 `veryfast`, crf 23, no size loop) |
| `--no-bgm` | skip the music bed |
| `--workers N` | parallel frame renderers (default `max(2, min(8, cpu_count − 4))`) |
| `--out DIR` | output directory (default `site/assets/video`) |

## Requirements

- Python 3.9+ with numpy, OpenCV (`cv2`), Pillow and SciPy; `ffmpeg` on the PATH.
- gcloud CLI: the engine calls `gcloud auth print-access-token` for TTS, ASR and Lyria (Vertex AI) in your quota project.
- Recordings in `production/assets/recordings/` (not in the repository — see `production/capture/`).
- Optional: `tesseract` (English model) for `tools/ocr.py`.

| Environment variable | Default | Purpose |
|---|---|---|
| `TTS_PROJECT` | `GOOGLE_CLOUD_PROJECT`, else the placeholder `your-project-id` | quota project for TTS, ASR and Lyria (`X-Goog-User-Project` header and endpoint path) |
| `TTS_REUSE` | unset | `1` = on a TTS cache miss reuse the most similar cached take instead of synthesizing |
| `TTS_REUSE_MIN` | `0.85` | minimum text similarity for a reused take |
| `TTS_REUSE_STRICT` | `1` | with `TTS_REUSE=1`: abort when no close take exists (`0` = synthesize instead) |
| `CLOUDSDK_CORE_ACCOUNT` | active gcloud account | standard gcloud variable — selects the account per command without changing your global config |

## Authoring helpers (text first, image-budget friendly)

* `python3 production/render/inspect_rec.py <rec_id> [--every 0.5] [--cols 5]` — every event in **rec time** with its box
  (frame px), the static (no-repaint) intervals, and a timestamped contact sheet with event boxes outlined in
  `production/render/out/inspect_<rec_id>.jpg`.
* `python3 production/render/tools/rec_summary.py <rec…> [--gap 1.0]` — events (CSS-px boxes), long repaint gaps and frame
  density per 10 s, no images.
* `python3 production/render/tools/ocr.py <rec>@t1,t2 [--crop x,y,w,h] [--min-conf 55] [--lines]` — English/number OCR
  (tesseract `eng`) with CSS-px boxes.
* `python3 production/render/tools/sheet.py --out out/x.jpg --tile 320 --cols 4 [--grid] <rec>@t1,t2[x,y,w,h] --video <mp4>@t… --images …`
  — small contact sheets (≤ 1280 px wide, JPEG q ≤ 70); click/hover boxes within ±0.8 s are outlined.
* `python3 -u production/render/tools/chapters.py production/render/scripts/v2/<id>.json [--out DIR]` — (re)write
  `<id>.chapters.json/.vtt` from the script's plan without re-rendering (default `--out` is `site/assets/video`).
* `python3 production/render/tools/regiondiff.py <rec> --ref 11.0 --t 11:17:0.25 --box toast=8,754,345,48 …` — mean pixel
  change of CSS-px regions against a reference time, as text: find exactly when a toast / page / panel appears (useful for
  UI text that the English-only OCR cannot read).

Recommended loop: `rec_summary` / `inspect_rec` / `ocr` → write script → `--dry-run` → `--stills …` → `--callout-qa` →
full render with `--strict-callouts` → QA tools in `production/qa/`.

Recordings: frames whose JPEG size differs from the recording's majority size, and short same-size "glitch" runs right
around `shot` events (the capture driver's DPR-2 screenshots briefly re-lay the page out), are dropped at load.

---

## Edit script (JSON)

Scripts live in `production/render/scripts/v2/` (21 files). Real examples: `ge1.json` (short: title → card → five screen
segments → outro), `ag4.json` (event-anchored narration, `target:` callouts, explicit speed ranges), `ge_opening.json`
(designed slides interleaved with lab clips).

```jsonc
{
  "id": "ge1",                              // output basename (required)
  "track": "ge", "lab": "lab1",             // content module + lab id → chapter titles
  "title": "GE LAB 01 · …",                 // VTT NOTE
  "brand": "Gemini Enterprise Hands-on Lab",// text-only brand line on title/card/outro (v2 scripts use the Korean wording)
  "voice": "Kore",                          // Gemini TTS voice (default Kore); per-segment "voice" overrides
  "bgm": true,                              // true | false | {"prompt","negative_prompt","seed","bed_db":-10,"duck_db":-22,"fade_in":1.5,"fade_out":2.5}
  "captions": true,                         // burned-in captions + VTT
  "transition": 0.5,                        // crossfade between segments (s)
  "poster": 2.6,                            // optional poster time (s)
  "encode": {"crf": 24, "preset": "slow", "audio_kbps": 160, "max_mb": 60},
  "chapters": [{"step": 1, "seg": 2}, {"step": 2, "seg": 3}, {"step": 3, "seg": 3, "say": 4}],
  "segments": [ … ]
}
```

Optional global tunables (names in *italics* can also be set per screen segment): `fps` 30, *`gap`* 0.42 (pause between
sentences), *`lead`*/*`tail`* 0.30 (narration padding, + half of each adjacent transition), *`max_speed`* 8,
*`min_speed`* 0.8, *`type_speed`* 1.6, *`idle_speed`* 2.0, *`max_zoom`* 1.6, `frame_scale` 0.84, `frame_top` 40,
`caption_band` 150, `caption_max_w` 1500; plus `fade_in` 0.4 / `fade_out` 0.8 (picture fades).

Script-level keys used by the lab scripts:

| key | meaning |
|---|---|
| `brand` | text-only brand line drawn top-left on title/card/outro (red accent bar + text, no logos). v2 values: "Gemini Enterprise 핸즈온 랩" / "Antigravity 핸즈온 랩" ("… Hands-on Lab"). Stays fixed across consecutive title/card/outro segments. Per-segment `brand` overrides (`false` hides). |
| `voice` | Gemini TTS voice name. Default `Kore`; legacy Chirp 3 names (`ko-KR-Chirp3-HD-…`), `Despina`, `Charon` and `default` map to `Kore`. No v2 script sets it. |
| `speaking_rate` | accepted and part of the TTS cache key, but not sent to the model — no audible effect. |
| `lexicon` | `true` (default) applies `lexicon.json` to the **spoken** text only (captions keep the on-screen spelling): `Gemini` → 제미나이, `PDF` → 피디에프; `re:` keys are regexes applied first; literal keys longest-first; ASCII keys match whole words; `_` keys are comments. `false` disables; a repo-relative path or an inline dict selects another lexicon. A narration item's `say` replaces the spoken text completely and bypasses the lexicon (file names, `/commands`, numbers). |
| `encode` | `{"crf": 24, "preset": "slow", "audio_kbps": 160, "max_mb": 30}` (defaults). If the mp4 is larger than `max_mb`, it is re-encoded at crf + 2 (at most twice). v2 scripts use crf 24 or 26 and `max_mb` 40–90. |
| `chapters` | `[{"step": 1, "seg": 2, "say"?: 0, "lead"?: 0.4, "offset"?: 0}]` — one entry per lab step (1-based, every step exactly once or `tools/chapters.py` exits). Chapter start = start of sentence `say` of segment `seg` − `lead` (never before the segment's visible start), or the segment's visible start, + `offset`, rounded to 0.1 s; end = next start; the last ends where the outro becomes visible. Titles come from `production/content/v2/<track>.py` (`LABS[lab]['steps']`). Writes `<id>.chapters.json` (`{"video","duration","chapters":[{"step","title","start","end"}]}`) and `<id>.chapters.vtt` (`STEP n · title`). |
| `track`, `lab` | select the content module and lab for chapter titles. |
| `transition` (per segment) | crossfade length *into* that segment (overrides the global value; `0` = hard cut). |

### Segment types

| type | fields | notes |
|---|---|---|
| `title` | `kicker`, `title`, `subtitle`, `duration` (3.5), `narration`? | dark #0B0F17 + drifting Gemini-gradient glow, staggered fade-up, slow push-in, gradient rule under the kicker |
| `card` | `kicker`?, `title`, `bullets` [..], `narration`?, `duration`? (2.5 + 1.0 × bullets) | numbered bullets; if the narration has exactly one sentence per bullet, bullet *i* appears as sentence *i* starts |
| `outro` | `kicker`?, `title`, `subtitle`, `narration`?, `duration` (4; with checklist 3.8 + 0.9 × rows), `checklist`? [..], `check_at`?, `center_y`? | check-mark ring + text; video fades to black. With `checklist` the rows slide in one by one: synced to narration when it has one sentence per row (or an intro sentence + one per row), else at explicit sentence indices `check_at`, else staggered. `center_y` moves the block (default (1080 − 120)/2) |
| `screen` | see below | a clip of a recording |

Text on title/card/outro enters after the incoming dissolve and leaves before the outgoing one (no double exposure).

### `screen` segment

Illustrative example based on `ge1.json` segment 2 (narration translated; event labels are what the recording logged —
here the Korean UI's "Start" button):

```jsonc
{
  "type": "screen",
  "rec": "ge1a_welcome",                  // recording id (folder under production/assets/recordings, or a path relative to it)
  "from": 0, "to": 12.6,                  // rec time (s) or event refs; default whole recording
  "labels": [{"kicker": "STEP 1", "text": "First visit — the welcome screen", "at": 0.6, "dur": 3.4}],
  "narration": [
    "The first time you open the app, a welcome screen appears.",
    {"text": "Click Start in the lower right to go to the home screen.", "at": "click:시작하기", "align": 0.55}
  ],
  "zoom": [
    {"from": 1.0, "to": "click:시작하기 -1.3", "box_css": [400, 110, 640, 590]},
    {"from": "click:시작하기 -1.3", "to": "click:시작하기 +0.7", "box": "click:시작하기"}
  ],
  "callouts": [
    {"at": "click:시작하기", "lead": -1.1, "dur": 1.6, "text": "Start", "spotlight": 0.22}
  ],
  // the remaining keys are not in ge1.json segment 2; shown for reference with their meaning
  "speed": "auto",                        // "auto" | number (uniform) | [{"from":12,"to":40,"x":6}]
  "keep": [[20.0, 23.5]],                 // rec-time ranges that must play at 1x
  "badge": true,                          // automatic fast-forward badge
  "intro": "settle"                       // gentle push-in at start ("none" to disable; default when previous segment is not a screen)
}
```

**Rec time** = seconds since the recording's first frame (`frames.json` ts − ts0). Event times use `wall − ts0`; older
recordings without `wall` use `t`. `inspect_rec.py` prints everything in rec time.

**Event references** (anywhere a time or box is accepted): `"<kind>"`, `"<kind>:<label>"` (exact, else substring),
`"<kind>#2"` / `"<kind>:<label>#2"` (2nd matching event in the recording), `"event:<index in events.json>"`, or a dict
`{"event", "label", "n", "offset"}`, with an optional trailing signed offset in rec seconds: `"click:Proceed -1.2"`.
Kinds include `click`, `hover`, `target`, `submit`, `type_start`, `type_end`, `paste`, `wait_start`, `wait_end`, `select`,
`key`, `scroll`, `shot`, `rec_stop`. Without `#n`, references inside a segment use the first match inside the segment's
range (±0.5 s), else the one nearest to the reference point; a segment's own `from`/`to` use the first match in the
recording.

**Narration** — a string (split into sentences at `.`/`!`/`?`/`。`/`…` + whitespace) or a list of strings (split) /
objects (never split) `{"text", "say"?, "at"?, "align"?=0, "offset"?=0, "pause"?, "caption"?}`. Each sentence is synthesized
separately (cached by spoken text) so captions are timed exactly. `at` makes a **sync point**: the recording is
time-remapped so that the moment `at` is on screen when the narration reaches `align` (0 = sentence start, 1 = end) +
`offset` seconds of that sentence. Sentences are delayed automatically if the visuals cannot be compressed enough.
`caption` overrides the burned-in text (e.g. to shorten it). Other keys are ignored — `rec_at` in particular is **not
read**; use `at` (with `align: 0` to tie the sentence start to the screen).

**Time remapping (`speed: "auto"`)** — visual length = max(narration + lead + tail, shortest acceptable clip):
* *needs more time*: unchanging (no-repaint) stretches are held longer (invisible); if there are none, slow to `min_speed`
  and hold the last frame;
* *needs less time*: unchanging stretches are compressed first (down to 0.2 s each), then motion is time-lapsed with caps —
  1× around `click` (−1.0/+0.7 s), `hover` (−0.6/+0.5 s), `submit`/`paste` (−0.4/+0.9 s) and `keep` ranges; ≤ `type_speed`
  while typing; ≤ `max_speed` (8×) inside `wait_start…wait_end` (AI generation); other motion ≤ `max_speed`, or ≤
  `idle_speed` (2×) when the recording marks its waits;
* *no narration*: the shortest acceptable clip (waits time-lapsed, interactions at 1×, unchanging stretches kept ≥ 0.5 s).
  Use `"speed": 1` or `"duration"` for natural pacing of silent clips;
* a number = uniform speed; a list `[{"from", "to", "x"}]` = explicit speed per rec range (1× elsewhere);
* speed changes are smoothed (0.1 s Gaussian, `speed_smooth`) and frames are resampled to constant 30 fps by timestamp
  (each output frame shows the latest source frame at that rec time);
* a fast-forward badge ("▶▶ 빨리 감기 ×N" — Korean for "fast-forward") appears automatically while visibly changing content
  plays ≥ 1.9× for ≥ 0.8 s (N = 90th-percentile speed of that stretch; brisk 1.5× playback or compressed idle screens get no
  badge). The badge text is hard-coded in `engine/timeline.py`.

**Zoom** — `{"from", "to"?, "box" | "box_css", "scale"?, "max"?, "dur"?, "dur_out"?, "lead"?, "lead_out"?, "from_say"?,
"to_say"?, "min_w"?, "min_h"?, "overscan"?, "overscan_px"?}`. The move starts at `from` (cubic ease-in-out, 0.75–1.4 s
depending on the zoom ratio, zoom about the fixed point so the target "pushes in" without swaying) and zooms back out at
`to` (omit to stay zoomed). Zooms less than 0.3 s apart chain directly (pan + zoom). `box` = `[x,y,w,h]` in **recording frame
px**, or `"auto:click"` (default) / `"click:<label>"` / any event with a box (context padding is added: max(40 % of the box,
60 CSS px) per side, at least 27 % × 28 % of the frame). `box_css` = CSS px of the 1440×810 viewport (same units as
`events.json`), resolution-independent. Targets are framed above the caption band; magnification ≤ `max_zoom` × "fills the
frame"; `scale` forces a magnification (same units).

**Callouts** — `{"at", "lead"?=0, "dur"?=2.4, "box" | "box_css", "text"?, "spotlight"?=true, "position"?="auto", "pad"?,
"radius"?=14, "say"?, "track"?=true}`. `at` is rec time / event ref, `lead` and `dur` are output seconds (e.g.
`lead: -1.4` = appear 1.4 s before a click). Without `box`, the `at` event's own box is highlighted when it has one (e.g.
`"at": "target:Proceed"`), else the first click from about 1 s before `at`. `pad` (recording-frame px, default 6 CSS px) is
added on every side. Draws an animated gradient ring with glow (gentle pulse, kept ≥ 4 px inside the frame), dims the rest by
28 % (`spotlight: false` or a number to change), and a Gemini-gradient label chip above the target (below if there is no
room, inside for tall targets; `position: "top" | "bottom"` forces a side). Callouts follow the camera and, with `track`, the
target itself ([Callout tracking](#callout-tracking-and-qa)).

**Anchoring to narration (`say`)** — callouts, labels and zooms can be timed to a sentence instead of a rec time:
`"say": k` (callout/label) or `"from_say": k` / `"to_say": k` (zoom) = the output time sentence *k* of this segment
starts, plus `lead` (zoom-out: `lead_out`). *k* is **0-based** and indexes the **sentence list after splitting**: a plain
string item containing two sentences becomes two items, dict items are never split — re-check indices after editing
narration. An out-of-range index is silently ignored (the callout falls back to `at`, by default the segment start).

**Step labels** — `"label"` (one) or `"labels": [{"kicker": "STEP 2", "text": "…", "at"?: 0.55, "at_rec"?, "say"?,
"lead"?, "dur"?: 3.6}]`: `at` = output seconds into the segment, `at_rec` = rec time / event ref, `say` = sentence index
(wins). Overlapping labels are trimmed so the earlier one leaves 0.25 s before the next appears.

**Zoom near the bottom** — targets are framed above the 150 px caption band; for UI in the bottom ~15 % of the page
(toasts, input box) add `"overscan": true` (optionally `"overscan_px"`, default caption band + 40) so the camera may move
past the recording's bottom edge instead of hiding the target under the captions.

**Captions** — one cue per sentence; a cue that would end within a short gap of the next is extended to it (no flicker),
and cues fade only at real pauses (clean cuts between back-to-back sentences).

**Badges** — fast-forward stretches separated by < 1.2 s are merged into one badge.

**Recording hygiene** (`engine/recording.py`) — frames whose JPEG size differs from the recording's majority size (DPR-2
stills taken during a screencast) and same-size "glitch" frames right around `shot` events are dropped at load
(`[render] <rec>: dropped N off-size frames`); the time base (ts0) still comes from all frames. `css_scale` = frame width ÷
`meta.json` `css_width` (default 1440).

---

## Pipeline

1. **Plan** (`engine/timeline.py`): TTS per sentence (`engine/tts.py` + `engine/voice.py`, cached in `cache/tts/`),
   narration scheduling + sync points, time-remap → per-frame rec time, camera track (`S, tx, ty` per frame), callouts with
   tracking (`engine/callout_track.py`), badges, labels, caption cues (Pretendard SemiBold 40 px, line breaks at spaces,
   balanced 2 lines, long sentences split at punctuation and timed by character share).
2. **Sprites** (`engine/typo.py`): captions, chips, badges, labels, brand line and title/card text are rendered once with
   Pretendard (SIL OFL, `fonts/`) + SDF-antialiased shapes and cached as PNGs in `cache/sprites/`.
3. **Frames** (`engine/compositor.py`, multiprocess, chunks of 8 frames): dithered gradient background → two-layer soft
   shadow → recording warped with a float affine (bicubic, sub-pixel, adaptive unsharp mask when magnified) inside a rounded
   device mask with a 1 px inner highlight → spotlight/ring/chip → badge → glass step label → segment crossfades → captions
   (glass pill) → global fades. Raw BGR frames stream into a single ffmpeg (libx264 preset/crf from `encode`, High profile,
   yuv420p, aq-mode 3, BT.709 tags, 2 s GOP; re-encoded at crf + 2 if the file exceeds `max_mb`) with bounded back-pressure.
4. **Audio** (`engine/music.py`): narration placed sample-accurately at 48 kHz; Lyria (`lyria-002`, REST, cached in
   `cache/music/`) looped with equal-power crossfades, ducked to −22 dB under narration (−10 dB bed otherwise, smoothed
   envelope that merges short pauses), faded in/out; two-pass EBU R128 loudnorm to −16 LUFS / −1.5 dBTP. If Lyria fails the
   video renders without music.
5. **Outputs**: mp4 written to `<id>.part.mp4` then renamed; VTT from the same cues; poster rendered directly by the
   compositor (JPEG q92); chapter files via `tools/chapters.py` when the script has `chapters`.

Caches (`cache/`) are safe to delete, but regenerating them calls paid APIs (TTS; music becomes a new Lyria take), and
`TTS_REUSE=1` needs the TTS cache.

## Narration

* Model `gemini-3.8-flash-tts` (Vertex AI `generateContent`, location `global`), voice `Kore`, one constant English style
  instruction for every line ("Clear, warm and engaging instructor narration at a steady, moderate pace, with a brief natural
  pause at every comma").
* Every take is transcribed back with Gemini ASR (`gemini-3.8-flash`, fallbacks `gemini-3.5-flash`, `gemini-2.5-flash`) and
  rejected if words are added/dropped/changed (CER > 0.08 or > 2 consecutive edits), a filler or a pause tag is heard, a
  version number or month is misread, a comma pause is missing or the pacing is off; up to 4 takes, the best one wins.
  Comma pauses are then shaped to 0.30–0.40 s and other inner silences capped at 0.62 s.
* Cache key = engine version, model, style, comma bounds, voice, rate, spoken text, sample rate → `cache/tts/<key>.wav/.json`.
* `TTS_REUSE=1` (re-renders that do not change narration) reuses the closest cached take and logs
  `TTS reuse (<ratio>): <text>`. Check those lines: a reused take of a different sentence means caption ≠ voice — re-render
  that sentence without `TTS_REUSE`.

Details: [docs/VIDEO_PRODUCTION.md §5.4](../../docs/VIDEO_PRODUCTION.md#54-narration-tts).

## Callout tracking and QA

A callout box is resolved at its anchor (event box or measured `box_css`) and then **verified on the frames actually shown**
(`engine/callout_track.py`): the unpadded target region is template-matched in every output frame of the callout
(grayscale, 2× downscaled, ±220 px search). An axis-aligned strong match (≥ 0.80) elsewhere → the ring follows (scroll,
panel shift); the original spot still similar (≥ 0.45) → it stays; lost for 4+ frames → the ring fades out. The demo cursor
is masked out of the template (when it covers most of a small target the ring stays static at the measured event box);
featureless targets are only verified; `"track": false` disables tracking.

`--callout-qa` renders the in / middle / out frame of every callout into `out/<id>/<id>_callouts.jpg` (+ `.json` with
`mode`, `vis_frac`, `score_min`, `score_med`, `drift_px`, problems). A callout fails if the target is not on screen in the
first ~0.6 s, is visible for less than 30 % of the callout, extends outside the recording, matches poorly (median < 0.5) or
is cut off by the output frame edge at the current zoom (> 6 %). `--strict-callouts` aborts the render on any failure.
After rendering, run `production/qa/video_callout_audit.py` (does the ring show what the chip says?) and
`production/qa/ring_band_audit.py` (does the ring stroke cut through text? must be FAIL 0) — see
[production/qa/README.md](../qa/README.md).

## Limitations / notes

* Screencast recordings are 1440×810 or 1920×1080 depending on the target (the screencast is capped at 1920×1080). At
  1440×810 the overview is upscaled 1.12× and zooms go up to ~2.1×, so zoomed text is slightly soft; 1920×1080 sources and the
  2880×1620 showcase recordings (`capture/agy/showcase.py`, with `meta.json`) stay sharper. The renderer adapts to any frame
  size (`css_scale` = frame width ÷ `css_width`).
* Spotlight dims the whole frame outside the target; every v2 callout sets `"spotlight"` between 0.12 and 0.25 (mostly 0.15–0.2).
* Narration anchors must be in increasing rec-time order; out-of-range anchors are ignored with a warning.
* The TTS input is a verbatim transcript plus one style string — there is no SSML/phoneme control. Pronunciation is fixed in
  text: add global rules to `lexicon.json` (spoken text only; captions keep the on-screen spelling) or a per-sentence `say`.
* Korean-specific parts (ASR prompt and normalisation in `engine/voice.py`, `lexicon.json`, the badge text, the `.ko.vtt`
  file name) are listed in [docs/LOCALIZATION.md](../../docs/LOCALIZATION.md).
* The OS cursor is not in CDP screencasts — the cursor and click ripple come from the capture driver's injected demo cursor
  (`capture/ge.py` `install_cursor`).
