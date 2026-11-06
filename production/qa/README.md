# production/qa — callout and ring audits

Tools that prove every highlight box (portal stills) and highlight ring (videos) sits on the thing its label names, and
that video rings do not cut through neighbouring text. They complement the build-time gates in `production/site_build_v2/`
and the tracking check in `production/render/render.py`. Background and rules: [docs/VIDEO_PRODUCTION.md §1.2 and
§6](../../docs/VIDEO_PRODUCTION.md#6-video-qa).

| Tool | Checks | Input | Output |
|---|---|---|---|
| `find_text.py` | where a text is on a still (to author a box) | still stem or image path | CSS-px boxes on stdout |
| `proof.py` | a box by eye, zoomed | still stem + region + boxes | one JPEG (≤ 1280 px wide) |
| `callout_audit.py` | portal still callouts: OCR inside the box vs. label | `production/content/v2/{ge,ag}.py` | `production/qa/out/stills/report.json`, `sheet_*.jpg` |
| `video_callout_audit.py` | video rings: OCR inside the ring vs. chip text | edit scripts | `production/qa/out/video/<id>/report.json`, `sheet_*.jpg` |
| `ring_band_audit.py` | video rings: stroke band vs. visible glyphs, frame edge, captions | edit scripts | `production/qa/out/ring/<id>/report.json`, `fail_*.jpg`; exit code |
| `vision_ocr.js` | OCR engine used by all of the above | image files | JSON lines |

## Requirements

- **macOS** — OCR runs Apple Vision through `osascript -l JavaScript` (`vision_ocr.js`); no compiler or extra packages.
- Python 3 with Pillow; the video tools also need the render engine's dependencies (numpy, OpenCV, SciPy) and existing
  recordings in `production/assets/recordings/`.
- Stills in `production/assets/shots/` (`.png`, `.jpg`, `.jpeg` or `.webp`). A still at least 2400 px wide is treated as
  DPR 2 (CSS = pixels ÷ 2) unless the content entry declares an explicit `viewport`.
- `video_callout_audit.py` and `ring_band_audit.py` rebuild the render plan, which needs the narration durations: run them
  with cached narration (`TTS_REUSE=1`; `ring_band_audit.py` sets it by default) so no speech is synthesized.
- Generated output in `production/qa/out/` is not part of the repository.

## `vision_ocr.js` — Apple Vision OCR

```bash
osascript -l JavaScript production/qa/vision_ocr.js <image> [<image> …]
```

Prints one JSON line per recognized line: `{"file", "text", "conf", "box": [x, y, w, h]}` in image pixels, top-left
origin. Accurate recognition level, language correction off, languages `ko-KR` + `en-US`. The Python tools call it in
batches (40 images per call in `callout_audit.py`, 16 per call on several threads in `ring_band_audit.py`).

## `find_text.py` — measure a box on an existing still

```bash
python3 production/qa/find_text.py <stem|image> "text" ["more text" …]
python3 production/qa/find_text.py <stem> --all
```

Prints every OCR line whose text matches one of the needles (normalised, fuzzy match ≥ 0.8) as
`[x, y, w, h] conf=… text`, in CSS px. Use these numbers for still callouts and `box_css` instead of estimating.
Exit code 2 without arguments, 1 if the still is not found.

## `proof.py` — zoomed proof image

```bash
python3 production/qa/proof.py <stem> x,y,w,h --box x,y,w,h [--box x,y,w,h …] --out <file.jpg>
```

Crops the region (CSS px) from the still, scales it to fit 1280×900 (enlarging at most 2×), draws each `--box` in a
different colour with its index, and saves a JPEG (quality 80). Use it to compare a candidate box with the screen before
and after a fix.

## `callout_audit.py` — portal still callouts

```bash
python3 production/qa/callout_audit.py                                   # both tracks
python3 production/qa/callout_audit.py --track ge --labs lab4 lab8       # --track is repeatable: ge, ag
python3 production/qa/callout_audit.py --track ag --labs lab6 --out <dir>
```

For every callout of every step (`shot`, `shot2`, `shots`) in `production/content/v2/<track>.py`:

1. OCR inside the box plus a 6 CSS px margin, compared with the label (share of label tokens found, fuzzy ≥ 0.8) → `score`;
2. if the score is below 0.6, OCR of the whole still to find where the label text actually is (`label_elsewhere`);
3. contact sheets: each box drawn on a zoomed crop, 6 tiles per sheet, green or red header.

Writes `report.json` and `sheet_NN.jpg` (old sheets are deleted first) and prints the callouts that need attention
(score < 0.6, or "screenshot missing"). The exit code is always 0.

**Pass** = no callout needs attention (or each flagged one is justified, e.g. a label that describes an icon) **and every
sheet has been looked at**. It runs after `build.py` and `site_build_v2/qa.py --callouts-only`, which prove the box is
*drawn* where the content says; this tool checks the coordinates themselves against the real screenshot.

## `video_callout_audit.py` — video rings: content

```bash
TTS_REUSE=1 python3 production/qa/video_callout_audit.py production/render/scripts/v2/<id>.json [more.json …] [--out <dir>]
```

`render.py --strict-callouts` proves a ring stays on the same pixels while it is shown; this tool checks that those pixels
are what the chip says. For every callout it renders the frame in the middle of the callout with the real compositor,
crops around the ring and its chip, OCRs the source frame inside the box and compares the text with the chip.

Writes `production/qa/out/video/<id>/report.json` and `sheet_NN.jpg` (6 tiles per sheet) and prints the rings that "need a
look": OCR score < 0.6 or ring visibility ≤ 0.5. Rings without chip text score 1.0. The exit code is always 0.

**Pass** = every flagged ring explained or fixed **and every sheet looked at**.

## `ring_band_audit.py` — video rings: stroke band

```bash
python3 production/qa/ring_band_audit.py production/render/scripts/v2/<id>.json [more.json …] \
    [--out <dir>] [--workers 3] [--min-depth 0.75]
```

The compositor pads every callout box (default 6 CSS px) and draws a 4 px stroke reaching 4.5 output px outside it. In
dense UI that band can land on the next line. For each callout, at three moments while it is fully shown, the tool
computes the band exactly like the compositor (including the 4 px clamp at the frame edge), finds glyph ink in the frame
actually shown (OCR lines refined to high-contrast word/row blobs; the demo cursor and the next click target's cursor
position are masked) and the caption pills on screen:

| Verdict | When |
|---|---|
| **FAIL** | the band crosses a glyph blob by more than `--min-depth` output px (reported as "cuts target text" or "crosses neighbour text"), the ring is clamped at the frame edge, or the ring overlaps a caption |
| **WARN** | the only crossings are next to the demo cursor, or the tracker hides the ring (visibility < 0.3) |
| **PASS** | none of the above |

Writes `production/qa/out/ring/<id>/report.json` (verdict, reasons and samples per callout) and `fail_NN.jpg` (FAIL and
WARN rings, crossings boxed in red); OCR results are cached in `production/qa/out/ring/_ocr/`. **Exit code 1 if any
callout FAILs.**

**Pass** = **FAIL 0**, with every WARN looked at. To fix a FAIL: re-measure the box on the frame that is actually shown
(glyph rows, not OCR boxes), set `"pad": 0` (or a small value) on the callout and keep 1–2 CSS px between box and glyphs,
move the camera (`zoom`) if the ring touches the frame edge or the caption band, re-render with
`TTS_REUSE=1 … --strict-callouts`, then run this tool and `video_callout_audit.py` again.

## Related gates (documented elsewhere)

- `production/site_build_v2/build.py` — fails the portal build on still callouts outside the capture, unknown `pos`
  (only `above` | `below` | `inside`) or CSS class collisions.
- `production/site_build_v2/qa.py --callouts-only` — real-browser geometry gate for still callouts: desktop and mobile,
  inline and lightbox; box error ≤ 1.5 px, no clipped label chips.
- `production/render/render.py --callout-qa | --strict-callouts` — tracking check of video rings
  ([render/README.md](../render/README.md)).

## Typical order

```bash
# still callouts
python3 production/qa/find_text.py ge_5_01_dr_home "Deep Research"      # measure (example from the tool's docstring)
python3 production/qa/proof.py ge_4_13_image_full 470,330,720,70 --box 480,344,700,46 --out production/qa/out/proof.jpg
python3 production/site_build_v2/build.py && python3 production/site_build_v2/qa.py --callouts-only
python3 production/qa/callout_audit.py --track ge --labs lab4

# video rings
python3 production/render/render.py production/render/scripts/v2/ge4.json --strict-callouts --out production/video_v2
TTS_REUSE=1 python3 production/qa/video_callout_audit.py production/render/scripts/v2/ge4.json
python3 production/qa/ring_band_audit.py production/render/scripts/v2/ge4.json
```
