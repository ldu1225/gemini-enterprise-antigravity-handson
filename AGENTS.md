# AGENTS.md — working rules for this repository

These rules apply to every AI coding agent (and human) working here. They were written after real mistakes in
the Korean edition; keep them when you build the English edition. Design principles and facts live in
`production/DESIGN_v2.md` (Korean), the content format in `production/content/README.md`.

## 1. Callout boxes must be exact — absolute rule

Boxes that miss their target, cover the neighbouring row, or drift in a video were the most frequent defect.

1. **No eyeballed coordinates.** Measure every box.
   - New capture: `shot(name, targets={"label": locator, ...})` (Antigravity / console / showcase helpers) saves the
     DOM boxes to `production/assets/shots/<stem>.boxes.json` (CSS px).
   - Existing still: `python3 production/qa/find_text.py <stem> "on-screen text"` → Apple Vision OCR returns the
     CSS-px box.
   - Proof image: `python3 production/qa/proof.py <stem> x,y,w,h --box x,y,w,h --out <jpg>`.
2. **Label = what is visibly inside the box.** The box must not cover other elements (next row, next menu item)
   or only half of the target. `pos` is `above | below | inside` only.
3. **After adding or changing a still callout, all three must pass:**
   1. `python3 production/site_build_v2/build.py` — fails on out-of-range boxes, invalid `pos`, class clashes.
   2. `python3 production/site_build_v2/qa.py --callouts-only` — real browser (desktop, mobile, lightbox): box
      position error ≤ 1.5 px, no clipped label chips.
   3. `python3 production/qa/callout_audit.py --track <ge|ag> --labs <labN>` — look at **every**
      `production/qa/out/stills/sheet_*.jpg`.
4. **Video callouts:** prefer `"at": "click:<label>"` / `"target:<label>"` (boxes recorded with the capture events)
   over hand-typed `box_css`. Before and after rendering:
   - `python3 production/render/render.py <script> --strict-callouts` (tracking check)
   - `TTS_REUSE=1 python3 production/qa/video_callout_audit.py <script>` → review every
     `production/qa/out/video/<id>/sheet_*.jpg`
   - `python3 production/qa/ring_band_audit.py <script>` → **FAIL 0** (inspect `production/qa/out/ring/<id>/fail_*.jpg`).
     The drawn ring band (default pad 6 CSS px + 4.5 px stroke) must not cross text in the visible frame, be clipped
     at the frame edge, or sit under the captions. Fix by re-measuring on the visible frame's text lines, `"pad": 0`
     with 1–2 px margin, or moving the zoom when the ring touches the edge / caption band.
   - Mistakes that already happened — do not repeat:
     - A callout's / label's `"say"` is a **0-based** sentence index. Counting from 1 shows the ring on the wrong
       screen; an out-of-range index shows it at the segment start (during the cross-fade).
     - Narration `"rec_at"` is **not read** by the engine. To sync with the screen use `"at": <recording seconds or
       event>` with `"align": 0`.
     - Click callouts once followed the demo cursor baked into the reference frame. The engine
       (`engine/callout_track.py`) masks the cursor area out of the template and only follows axis-aligned motion —
       do not revert that. If in doubt, `track: false`.
     - After a `TTS_REUSE=1` render, check the `TTS reuse (ratio)` log lines. If a different sentence's audio was
       reused (caption ≠ voice), re-synthesize that sentence without reuse.
5. **Portal callout CSS classes must not be derived from lab/step ids.** Both tracks have lab1…lab9, and id-based
   classes once drew Antigravity boxes on Gemini Enterprise pages. `build.py` uses geometry-hash class names — keep it.

## 2. Other fixed rules

- **No fake screens.** Product UI only from real recordings / captures. Fictional company **Cymbal** only; no real
  customer or company names, no real people.
- **Show results big.** Labs that build something (dashboards, slides, reports, evaluation reports, GE answers)
  show the finished artifact large on the page and in the video: a short preview right after the title and a
  result scene in the last step. Headless-Chromium 2× captures of the real files the agent built
  (`production/capture/agy/showcase.py`, e.g. `ag4_dash.py`, `ag7_deck.py`, `ag8_eval.py`) count as real results
  (page content only — no address bar, no local paths).
- **Never ship broken AI output.** Zoom in on every captured answer: raw `<br>`, `**`, `|---` in tables, garbled
  text or typos inside generated images. If broken, fix the prompt (e.g. "column names + one sentence per cell",
  explicit product spelling), regenerate, recapture — and re-render the video if the scene is in it.
- **Images you inspect** should be ≤ 1280 px per side (use contact sheets / crops of the 2880 × 1620 originals).
- **Never change global `gcloud` configuration.** Pass the account per command (`CLOUDSDK_CORE_ACCOUNT=…`) and the
  project via environment variables (`TTS_PROJECT`, `LAB_PROJECT_ID`, `PROJECT`, …). For re-renders that only
  change boxes or zoom, use `TTS_REUSE=1` to reuse existing narration.
- **Never screenshot a person's real desktop.** Capture only the recording browser / app window over CDP.
- **Privacy before publishing.** No project IDs or numbers, app IDs, accounts, e-mails, local paths or internal
  names in code, docs, stills or frames. Run `python3 tools/check_sensitive.py` (add your own terms with
  `SENSITIVE_DENYLIST=…`) before every push, and OCR-scan rendered videos for paths and names.

## 3. Recording the Antigravity desktop app

`production/capture/agy/agv.py` drives an isolated recording copy of the app over CDP :9334, launched by
`production/capture/agy/launch_ag_rec_voc.sh`.

- The window must be exactly **1440 × 810 at zoom 0** (the launcher pins it) so DOM boxes match pixels. Never run
  two launchers at once.
- If the agent leaves a background command running (e.g. a local server), the next prompt in the same conversation
  is queued — start a **new conversation per step** (`new=True`).
- A conversation with a `/schedule` job stays busy; its new messages are queued → use **Send Now**.
- A sub-agent can stall before starting; restart the app with the launcher and retake.
- When MCP authentication (ADC) expires, a red *MCP Error* appears under the input. Re-authenticate and relaunch
  for takes that use MCP; for takes that do not, remove the server from the recording HOME's MCP config (back it up
  and restore it afterwards).

## 4. Definition of done (per lab)

`build.py` warnings 0 · `qa.py` passes · every callout sheet reviewed · `ring_band_audit.py` FAIL 0 · video chapters =
lab steps · the finished result is shown big.
