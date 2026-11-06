# production/capture — real product UI → recordings and stills

The scripts in this folder drive the **real** products over the Chrome DevTools Protocol (CDP) and save what they see:

- the **Gemini Enterprise web app** and the **Google Cloud console** in a demo Chrome (CDP port 9222),
- the **Antigravity desktop app** in an isolated recording instance (CDP port 9334; a legacy instance uses 9333),
- **agent-built files** (dashboard, slide deck, evaluation report) in a private headless Chromium ("showcase" captures).

Nothing is mocked up. The fictional company is **Cymbal**; all lab data is synthetic.
The end-to-end process, including how these recordings become videos, is described in
[docs/VIDEO_PRODUCTION.md](../../docs/VIDEO_PRODUCTION.md) (§3 covers this folder in depth).

> [!IMPORTANT]
> The outputs (`production/assets/recordings/`, `production/assets/shots/`) are **not in the repository**. Run the scripts
> against your own Gemini Enterprise app, Antigravity install and Google Cloud project to create them.

## Prerequisites

| Need | Used by | Notes |
|---|---|---|
| Python 3.9+ with `playwright` | everything | `connect_over_cdp` for live apps; `showcase.py` also needs `playwright install chromium` |
| Google Chrome started with `--remote-debugging-port=9222` | `ge.py`, `v2/*`, `agy/gconsole.py`, `agy/ag1r_console.py`, `agy/ge_voc_agent.py` | use a dedicated profile, signed in to **your own** GE app that contains only Cymbal demo content, e.g. `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir=<chrome-profile-dir>` |
| Your GE app's config id | `ge.py` | `GE_APP_CID`; the app URL is `https://vertexaisearch.cloud.google.com/us/home/cid/<GE_APP_CID>` (location `us` is hard-coded) |
| Antigravity desktop app (macOS) | `agy/launch_ag_rec_voc.sh`, `agy/launch_rec.sh`, `agy/agrec.py`, `agy/agv.py`, `agy/agy.py` | the launchers use macOS app-bundle paths, the login keychain and `lsof` |
| gcloud CLI, account logged in with `gcloud auth login <account>` | `agy/launch_ag_rec_voc.sh` | the launcher builds ADC for the recording instance from that login |
| A Google Cloud project for the AG storyline | `agy/agv.py` Labs 6–9, `agy/ag1r_console.py` | BigQuery (MCP), Agent Runtime, GE publishing; `agents-cli` installed (the agent runs it on camera in Labs 8–9) |
| Sample files | GE Labs 3–8, AG workspace | `production/samples/v2/build/` (in the repo): workbook, PDFs, skill ZIP, `cymbal-voc` starter project |

The GE scripts record the Korean UI (`?hl=ko`) and select many elements by Korean `aria-label`s and visible texts; see
[docs/LOCALIZATION.md](../../docs/LOCALIZATION.md) before recording another language.

## Environment variables

| Variable | Read by | Default | Purpose |
|---|---|---|---|
| `GE_CDP_URL` | `ge.py` (and every driver built on it) | `http://localhost:9222` | CDP endpoint of the demo Chrome |
| `GE_APP_CID` | `ge.py` | `YOUR_GE_APP_CID` | your GE app's config id |
| `AG_CDP_URL` | `agy/agrec.py` | `http://localhost:9334` | CDP endpoint of the Antigravity recording instance |
| `AGY_CDP_URL` | `agy/agy.py` | `http://localhost:9333` | CDP endpoint of the legacy recording instance |
| `AG_REC_HOME` | `agy/launch_ag_rec_voc.sh`, `agy/agv.py`, `agy/ag4_dash.py`, `agy/ag7_deck.py`, `agy/ag8_eval.py` | a folder in your home directory (see the scripts) | root of the recording instance: `home/`, `profile/`, `work/cymbal-voc/`, `app.log`. Set it explicitly and use the same value for every script |
| `REC_ACCOUNT` | `agy/launch_ag_rec_voc.sh` | **required** | gcloud account used for MCP / ADC inside the recording instance |
| `LAB_PROJECT_ID` | `agy/launch_ag_rec_voc.sh` (**required**), `agy/agv.py`, `agy/gconsole.py`, `agy/ag1r_console.py`, `agy/ag8_eval.py` | `your-project-id` | lab project: gcloud project and ADC quota project of the instance, console URLs, and a value **typed on camera** in AG Lab 6 |
| `LAB_PROJECT_NUMBER` | `agy/agv.py` | `123456789012` | typed on camera in AG Lab 6 |
| `LAB_GE_APP_ID` | `agy/agv.py` | `your-ge-app-id` | typed on camera in AG Lab 6 |
| `AG_APP` | `agy/launch_ag_rec_voc.sh` | `/Applications/Antigravity.app` | app bundle to launch |
| `AG_PROFILE_SRC` | `agy/launch_ag_rec_voc.sh` | your app's Electron profile (standard macOS location) | source of the sign-in state copied into the recording profile |
| `AG_DATA_DIR` | `agy/launch_ag_rec_voc.sh` | your app's data directory (standard location) | only `installation_id` and `user_settings.pb` are copied |
| `AG_BLOCK_UPDATER_HOST` | `agy/launch_rec.sh` | — | updater host to block with `--host-resolver-rules` (an update mid-take shut down the language server) |
| `AG7_DECK` | `agy/ag7_deck.py` | the deck in the recording workspace | override the HTML deck to film (dry runs) |
| `LEAK_DENYLIST` | `agy/showcase.py` (`ag4_dash.py`, `ag7_deck.py`, `ag8_eval.py`) | — | comma-separated terms that abort a showcase capture (your username, project id, real customer names …) |

`launch_ag_rec_voc.sh` also exports `GOOGLE_API_USE_CLIENT_CERTIFICATE=false` for every process the agent starts.

## Scripts

### Core

| File | What it does |
|---|---|
| `ge.py` | `GE` driver: CDP attach, 1440×810 CSS viewport at DPR 2, demo cursor + click ripple, visible-element finders, `click`/`type_text`/`insert_text` with events and DOM boxes, `wait_answer_done`, `shot` (2880×1620 PNG), `brand_scan`, screencast `start_recording`/`set_rate`/`stop_recording`, `mark` |
| `helpers.py` | shared JS snippets (`DUMP_JS`, `FIND_TEXT_JS`, `MEDIA_JS`) and helpers `type_prompt`, `smooth_scroll`, `click_xy`, `click_text`, `submit` |
| `media_wait.py` | `wait_media(ge, kind, count)`: wait until N generated images/videos are rendered (`wait_start`/`wait_end` events) |
| `nb_explore.py` | off-camera explorer for the Gemini Notebook iframe — one action per call (`--text`, `--contains`, `--label`, `--css`, `--upload`, `--type`, `--enter`, `--wait`, `--nth`), prints controls, writes a low-res JPEG to `production/assets/shots/_explore/<name>.jpg` |

### Gemini Enterprise labs — `v2/`

Run from the repository root, e.g. `python3 production/capture/v2/ge3.py a b`. Letters select clips; no argument runs the
default set.

| Script | Args (default) | Recordings |
|---|---|---|
| `chats.py` | `list` · `delete <substr>…` · `scan <substr>` | none — chat housekeeping and brand scan of an existing chat |
| `probe.py` | `home` · `goto URL` · `menu LABEL` · `clicktext TEXT` · `clickxy X Y` · `key KEY` · `js EXPR` · `texts`, plus `--texts`, `--shot NAME` | none — off-camera probing |
| `ge1a_welcome.py` | — | `ge1a_welcome` (first-visit welcome dialog; one-shot) |
| `ge1bcd.py` | `b c d` | `ge1b_tour`, `ge1c_settings`, `ge1d_firstchat` |
| `ge1e_answer_tools.py` | — | `ge1e_answer_tools` |
| `ge2.py` | `a b e c d` | `ge2a_vague`, `ge2b_good`, `ge2e_sources`, `ge2c_followup`, `ge2d_share` |
| `ge3.py` | `a b c d` | `ge3a_upload`, `ge3b_analysis`, `ge3c_chart`, `ge3d_canvas` |
| `ge4.py` | `a b c d` | `ge4a_brief`, `ge4b_image`, `ge4c_edit`, `ge4d_video` |
| `ge5.py` | `a2 b c s` (`c s`) | `ge5a2_dr_go`, `ge5b_dr_result` (`--probe` prints scroll targets only), `ge5c_notebook`, `ge5d_studio` |
| `ge6.py` | `a b c` | `ge6a_skill_upload`, `ge6b_skill_use`, `ge6c_tips_tour` |
| `ge7.py` | `a b c d` | `ge7a_build`, `ge7b_test`, `ge7c_create`, `ge7d_use` |
| `ge7_refine.py` | `open instr model know starter sub sub2 schedule preview` (all) | `ge7e_open_edit`, `ge7f_node_instructions`, `ge7f2_model_menu`, `ge7g_node_knowledge`, `ge7g2_starter_prompt`, `ge7h_subagent`, `ge7h2_subagent2`, `ge7h3_schedule`, `ge7i_preview_update` |
| `ge8.py` | `a b c` | `ge8a_build`, `ge8b_edit`, `ge8c_test` |
| `ge8_refine.py` | `enable trigger step step_file_schema flow_menu approval branch reject_branch test update` (all) | `ge8c2_enable`, `ge8d_trigger`, `ge8e_step`, `ge8e2_step_file_schema`, `ge8f0_flow_menu`, `ge8f_approval`, `ge8g_branch`, `ge8g2_reject_branch`, `ge8h_test_approval` (or `ge8h_test_noapproval`), `ge8i_update` |
| `ge9.py` | `a b c` | `ge9a_gallery`, `ge9b_manage`, `ge9c_combo` |

What each clip shows is listed in [docs/VIDEO_PRODUCTION.md §3.4](../../docs/VIDEO_PRODUCTION.md#34-ge-lab-scripts--capturev2).
`ge2.py`, `ge3.py` and `ge4.py` run the brand scan after their clips and exit with code **3** if a real brand name is
visible. `ge3.py`, `ge4.py` and `ge5.py` keep the URL of the conversation in
`production/assets/recordings/<name>_session.txt` so later clips can reopen it.

Known gaps: the render scripts also use `ge5a_dr_start` (GE Lab 5; `ge5.py` parts `a2`/`b` read its conversation URL from
`ge5_dr_session.txt`) and `ag7v_before` / `ag7v_template` (AG Lab 7 showcase takes); no command-line entry point in this
folder records them.

### Antigravity and showcase — `agy/`

| File | Usage | What it does |
|---|---|---|
| `launch_ag_rec_voc.sh` | `REC_ACCOUNT=<account> LAB_PROJECT_ID=<id> AG_REC_HOME=<dir> bash production/capture/agy/launch_ag_rec_voc.sh [fresh]` | starts the isolated recording instance for AG Labs 3–10 on CDP 9334: own HOME and Electron profile, gcloud + ADC refreshed on every launch, window pinned to 1440×810 at zoom 0, workspace copied once from `production/samples/v2/build/cymbal-voc`; `fresh` wipes `AG_REC_HOME` first; exits with `already running` if 9334 is in use |
| `agrec.py` | library; `python3 production/capture/agy/agrec.py [name]` = probe still + page text | `AGRec` driver for the app's workbench window: viewport check and box scaling, resilient recording (reconnect, `<name>_aborted`), `shot(targets=…)` + `boxes.json`, `mark_target`, command approval, `wait_agent` |
| `agv.py` | `python3 production/capture/agy/agv.py <step> [<step> …]` | the "cymbal-voc" storyline: steps `l3_open` … `l10_sub` → recordings `ag3v_*` … `ag10v_*` and stills `ag_3v_*` … `ag_10v_*` ([step table](../../docs/VIDEO_PRODUCTION.md#35-antigravity-desktop-app-ag-labs-310)) |
| `launch_rec.sh` | `bash production/capture/agy/launch_rec.sh [fresh]` | legacy isolated instance on CDP 9333 (fixed recording folder in your home directory; optional `AG_BLOCK_UPDATER_HOST`) |
| `agy.py` | library | `AGY` driver for the legacy instance (`AGY_CDP_URL`), `refresh_page()` re-attaches after the app switches pages |
| `ag2a_signin.py` | `python3 production/capture/agy/ag2a_signin.py` | AG Lab 2 sign-in clip `ag2a_signin`: clicks "Continue with Google", waits up to 15 min for a person to finish sign-in in the browser (`WAITING_FOR_HUMAN_LOGIN` / `LOGIN_DONE`), stills `ag_2_01…03` |
| `showcase.py` | library | `Showcase`: private headless Chromium at 2×, screenshot-based recording (`frames.json`, `events.json`, `meta.json`), `still()` + `boxes.json`, `scan()` leak check |
| `ag4_dash.py` | `python3 production/capture/agy/ag4_dash.py [rec\|stills\|all]` | films the dashboard the agent built (served from the workspace on a temporary `127.0.0.1` port) → `ag4v_dash`, stills `ag_4v_20…24` |
| `ag7_deck.py` | `… ag7_deck.py [rec\|stills\|all]` | films the 6-slide deck in presentation mode → `ag7v_deck`, stills `ag_7v_21…26_deck_s1…s6` |
| `ag8_eval.py` | `… ag8_eval.py [rec\|stills\|all]` | films the `agents-cli eval` HTML report → `ag8v_score`, stills `ag_8v_09…11` |
| `gconsole.py` | library | `GC` driver for the Cloud console in its own Chrome window (id kept in `agy/.gc_target`), DOM-measured box helpers (`lb`, `rb`, `union`), `shot(targets=…)`, eased scrolling |
| `ag1r_console.py` | `python3 production/capture/agy/ag1r_console.py stills\|record` | AG Lab 1 admin screens (AI developer tools settings, Developer tools metrics), read-only → stills `gc_ag_1r_01…08`, recording `ag1r_console` |
| `ge_voc_agent.py` | `python3 production/capture/agy/ge_voc_agent.py [agents\|ask\|all]` | AG Lab 9: the published agent in the GE web app → `ag9v_ge_agents` (with `agents`) or `ag9v_ge_use`, stills `ag_9v_05…08` |

## Outputs

```text
production/assets/recordings/<id>/
  frames/000000.jpg …   screencast frames, 1440×810 or 1920×1080 (showcase: 2880×1620 screenshots)
  frames.json           [{"file", "ts"}]              ts = epoch seconds
  events.json           [{"t", "wall", "kind", ...}]  click / hover / type_start / type_end / paste / submit /
                                                      wait_start / wait_end / target / shot / select / key / scroll /
                                                      cut_start / cut_end / rec_start / rec_stop …
  meta.json             showcase only: {"css_width": 1440, "css_height": 810, "dpr": 2, "source"}
production/assets/shots/<stem>.png         2880×1620 still (prefixes ge_, ag_, gc_)
production/assets/shots/<stem>.boxes.json  {"viewport": [1440, 810], "targets": {label: [x, y, w, h]},
                                            "leaves": [{"t", "a", "tag", "role", "b": [x, y, w, h]}], "source"?}
```

All boxes are CSS px of the 1440×810 viewport. `boxes.json` is written by `AGRec.shot`, `GC.shot`, `Showcase.still` and the
`shot()` wrapper in `ge_voc_agent.py`; the plain `GE.shot()` writes only the PNG (measure those stills with
`production/qa/find_text.py`). Inspect a recording with `production/render/inspect_rec.py <id>` or
`production/render/tools/rec_summary.py <id>`.

## Hygiene rules

1. **Real UI only.** No mock-ups; fictional Cymbal; synthetic data; no real customer names in prompts or data.
2. **Measure, don't guess.** Mark the things you will highlight: `mark_target(label, loc)` for video callouts,
   `shot(name, targets={...})` for stills. Labels must name what is visibly inside the box.
3. **Capture only through CDP or the headless showcase browser** — never OS screenshots or screen recordings of your desktop.
4. **Keep the demo app clean.** Only Cymbal content; delete or rename stray chats (`v2/chats.py`); the sidebar shows titles.
5. **Run the leak scans.** `GE.brand_scan()` (exit code 3 in `ge2`/`ge3`/`ge4`), `Showcase.scan()` with `LEAK_DENYLIST`.
   Never show local paths, e-mail addresses or real brands; bracket unavoidable moments with `cut_start`/`cut_end` and cut them.
6. **Antigravity instance discipline.** One launcher at a time; window exactly 1440×810 at zoom 0 (`AGRec.measure_viewport`
   warns otherwise); a new conversation per step (background commands queue the next prompt under "Queued Messages");
   `/schedule` conversations stay busy — use **Send Now**; a red "MCP Error" under the input means expired auth —
   `gcloud auth login <account>` and relaunch; if a subagent never starts, restart the app with the launcher and retake.
7. **Typed values are visible.** `LAB_PROJECT_ID`, `LAB_PROJECT_NUMBER` and `LAB_GE_APP_ID` are typed on camera in AG Lab 6 —
   use a dedicated demo project.
8. **Check generated output before you keep a take.** No raw `<br>`, `**`, `|---` in tables, no garbled text in generated
   images; re-prompt and retake (`v2/ge5.py` stops on broken markdown).
9. **Never commit captures or local state**: `production/assets/`, `*_session.txt`, `agy/.gc_target`, the recording
   instance folder. Run `python3 tools/check_sensitive.py` (with `SENSITIVE_DENYLIST`) before publishing.

## Quick start

```bash
# GE: demo Chrome on :9222 signed in to your app
export GE_APP_CID=<GE_APP_CID>
python3 production/capture/v2/probe.py home --texts          # check the connection
python3 production/capture/v2/ge2.py a b                     # record two clips

# Antigravity storyline
export AG_REC_HOME=<dir> LAB_PROJECT_ID=your-project-id
REC_ACCOUNT=<gcloud-account> bash production/capture/agy/launch_ag_rec_voc.sh
python3 production/capture/agy/agv.py l3_open l3_setup
python3 production/capture/agy/ag4_dash.py stills            # after Lab 4 has built the dashboard
```
