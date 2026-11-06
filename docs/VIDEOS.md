# Video catalog

21 narrated tutorial videos: one opening talk per track and one demo video per lab. Every lab video has
**one chapter per lab step** (`<id>.chapters.json`), so the portal can jump to "this step" and play a single step.
The rendered media files (`.mp4`, `.ko.vtt`, posters, chapter files) are **not** in this repository — they are
produced by the scripts in `production/render/scripts/v2/` (see [VIDEO_PRODUCTION.md](VIDEO_PRODUCTION.md)).

Common format: 1920×1080, 30 fps, H.264 + AAC 48 kHz, burned-in Korean captions plus a Korean WebVTT track,
Korean narration synthesized with Gemini TTS (`gemini-3.8-flash-tts`, voice *Kore*; every take is transcribed
back with Gemini and re-generated if words, pauses or pacing are off — `production/render/engine/voice.py`),
a quiet generated music bed (Lyria, `engine/music.py`), a title card, optional agenda cards, real screen
recordings with zoom/pan, callout rings and labels, and an outro card with the checklist and the next lab.

Total running time: **107:20** (GE labs 33:23, AG labs 56:35, openings).

| Video | Title | Length | Chapters | Segments | Callouts | Narration sentences |
|---|---|---|---|---|---|---|
| `ge_opening` | GE opening · How you work with Gemini Enterprise | 7:46 | — | 18 | 7 | 68 |
| `ge1` | GE Lab 1 · Getting started | 3:39 | 7 | 8 | 11 | 71 |
| `ge2` | GE Lab 2 · Getting answers with prompts | 3:06 | 5 | 8 | 5 | 57 |
| `ge3` | GE Lab 3 · Data analysis + Canvas | 2:44 | 4 | 6 | 4 | 46 |
| `ge4` | GE Lab 4 · Images & video | 3:33 | 5 | 11 | 14 | 60 |
| `ge5` | GE Lab 5 · Deep Research & Gemini Notebook | 4:14 | 6 | 10 | 20 | 79 |
| `ge6` | GE Lab 6 · Skills, projects, library | 1:49 | 3 | 5 | 1 | 57 |
| `ge7` | GE Lab 7 · Chat agent — internal help desk | 5:55 | 10 | 16 | 0 | 93 |
| `ge8` | GE Lab 8 · Workflow — inquiry triage & reply drafts | 6:22 | 12 | 16 | 0 | 95 |
| `ge9` | GE Lab 9 · Sharing, gallery & managing agents | 2:00 | 5 | 7 | 0 | 58 |
| `ag_opening` | AG opening · Building software with agents | 9:37* | — | 35 | 49 | 108 |
| `ag1` | AG Lab 1 · Getting started A — GE license | 3:45 | 9 | 10 | 23 | 84 |
| `ag2` | AG Lab 2 · Getting started B — personal Google account | 1:48 | 5 | 7 | 2 | 61 |
| `ag3` | AG Lab 3 · Taking on the project | 5:00 | 5 | 14 | 30 | 46 |
| `ag4` | AG Lab 4 · Build the VOC dashboard | 7:32 | 6 | 28 | 44 | 77 |
| `ag5` | AG Lab 5 · Team rules & weekly-report skill | 6:22 | 5 | 25 | 41 | 52 |
| `ag6` | AG Lab 6 · Connect company data with MCP — BigQuery | 6:51 | 5 | 29 | 48 | 68 |
| `ag7` | AG Lab 7 · Executive report slides | 6:43 | 4 | 29 | 54 | 60 |
| `ag8` | AG Lab 8 · VOC analysis agent — ADK | 6:02 | 5 | 22 | 29 | 52 |
| `ag9` | AG Lab 9 · Deploy + publish to Gemini Enterprise | 6:06 | 5 | 21 | 29 | 59 |
| `ag10` | AG Lab 10 · Operations automation | 6:27 | 4 | 25 | 30 | 59 |

\* last published render; see the note under `ag_opening`.

*Segments* are the units of a render script (title / card / screen / outro). *Callouts* are rings drawn around
a UI element at a narration sentence; *labels* are short kicker + text overlays.

---

### `ge_opening` — GE opening · How you work with Gemini Enterprise

- Script: `production/render/scripts/v2/ge_opening.json` · 18 segments (1 title, 2 card, 14 screen, 1 outro) · 68 narration sentences · 7 callouts · 5 on-screen labels · size budget 90 MB
- Slide recordings (6): `ge_s_features`, `ge_s_gate`, `ge_s_labs`, `ge_s_prompt`, `ge_s_safety`, `ge_s_shift` — HTML slides built by `production/render/out/openings/make_slides.py`
- Real-UI clips (8): `ge1a_welcome`, `ge1b_tour`, `ge1d_firstchat`, `ge2b_good`, `ge2e_sources`, `ge3a_upload`, `ge3c_chart`, `ge3d_canvas`

### `ge1` — GE Lab 1 · Getting started

- Lab page: `production/content/v2/ge_labs/lab1.py` · script: `production/render/scripts/v2/ge1.json`
- 8 segments (1 title, 1 card, 5 screen, 1 outro) · 71 narration sentences · 11 callouts · 7 on-screen labels · size budget 60 MB
- Recordings used (5): `ge1a_welcome`, `ge1b_tour`, `ge1c_settings`, `ge1d_firstchat`, `ge1e_answer_tools`
- Opens with: Agenda card, then the real welcome screen on first sign-in
- Ends with: Answer tools: copy, table download, follow-ups, chat management

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:24 | First visit — the welcome screen |
| 2 | 0:44 | The layout at a glance — the sidebar |
| 3 | 1:19 | Buttons in the input box — files · tools · sources · model |
| 4 | 1:46 | Change the theme — design |
| 5 | 2:05 | Personalization and memory — answers tailored to you |
| 6 | 2:35 | Pick a model and ask your first question |
| 7 | 3:09 | Working with answers — copy · table download · follow-ups · managing chats |

### `ge2` — GE Lab 2 · Getting answers with prompts

- Lab page: `production/content/v2/ge_labs/lab2.py` · script: `production/render/scripts/v2/ge2.json`
- 8 segments (1 title, 1 card, 5 screen, 1 outro) · 57 narration sentences · 5 callouts · 5 on-screen labels · size budget 60 MB
- Recordings used (5): `ge2a_vague`, `ge2b_good`, `ge2c_followup`, `ge2d_share`, `ge2e_sources`
- Opens with: Agenda card, then a deliberately vague question
- Ends with: A 4-element prompt answer with sources and the reasoning panel; share link

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:26 | Start with a vague question — what is missing? |
| 2 | 0:48 | The four elements of a good prompt — role · task · context · format |
| 3 | 1:44 | Check the sources — always verify the evidence |
| 4 | 2:06 | Ask follow-up questions — refine the result |
| 5 | 2:32 | Tidy up and share — rename · share link |

### `ge3` — GE Lab 3 · Data analysis + Canvas

- Lab page: `production/content/v2/ge_labs/lab3.py` · script: `production/render/scripts/v2/ge3.json`
- 6 segments (1 title, 4 screen, 1 outro) · 46 narration sentences · 4 callouts · 4 on-screen labels · size budget 40 MB
- Recordings used (4): `ge3a_upload`, `ge3b_analysis`, `ge3c_chart`, `ge3d_canvas`
- Opens with: Uploading the sales workbook straight after the title
- Ends with: 5-slide Canvas report and its export

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:04 | Upload the Excel file and get analysis ideas |
| 2 | 0:36 | Quarterly results and target attainment by product, with hypotheses |
| 3 | 1:18 | Chart the online-sales share trend |
| 4 | 1:42 | Build a 5-slide report in Canvas and export it |

### `ge4` — GE Lab 4 · Images & video

- Lab page: `production/content/v2/ge_labs/lab4.py` · script: `production/render/scripts/v2/ge4.json`
- 11 segments (1 title, 2 card, 7 screen, 1 outro) · 60 narration sentences · 14 callouts · 4 on-screen labels · size budget 60 MB
- Recordings used (4): `ge4a_brief`, `ge4b_image`, `ge4c_edit`, `ge4d_video`
- Opens with: Agenda card, then uploading the product brief PDF
- Ends with: Edited key visual and the Veo 3.1 teaser; 'check before use' card

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:28 | Upload the brief and get an image prompt first |
| 2 | 1:11 | Create the key visual with the image tool |
| 3 | 1:49 | Edit by talking — change only the time of day and lighting |
| 4 | 2:24 | Make a teaser with the video tool (Veo 3.1) |
| 5 | 2:57 | Check before you use it — brand guide and cautions |

### `ge5` — GE Lab 5 · Deep Research & Gemini Notebook

- Lab page: `production/content/v2/ge_labs/lab5.py` · script: `production/render/scripts/v2/ge5.json`
- 10 segments (1 title, 8 screen, 1 outro) · 79 narration sentences · 20 callouts · 7 on-screen labels · size budget 45 MB
- Recordings used (5): `ge5a2_dr_go`, `ge5a_dr_start`, `ge5b_dr_result`, `ge5c_notebook`, `ge5d_studio`
- Opens with: Result preview: Studio infographic, slides and video overview made from one brief PDF
- Ends with: Step 6 opens the finished Studio outputs

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:16 | Open Deep Research from the sidebar and request research |
| 2 | 0:42 | Review the research plan, then click *Start research* |
| 3 | 1:02 | Review the finished report · comparison table · sources · audio summary |
| 4 | 1:20 | Upload the brief PDF to Gemini Notebook and ask evidence-based questions |
| 5 | 1:58 | Create audio · video · slides · infographic in the Studio at once |
| 6 | 2:37 | Open the finished outputs — video overview · audio · slides · infographic |

### `ge6` — GE Lab 6 · Skills, projects, library

- Lab page: `production/content/v2/ge_labs/lab6.py` · script: `production/render/scripts/v2/ge6.json`
- 5 segments (1 title, 3 screen, 1 outro) · 57 narration sentences · 1 callouts · 3 on-screen labels · size budget 40 MB
- Recordings used (3): `ge6a_skill_upload`, `ge6b_skill_use`, `ge6c_tips_tour`
- Opens with: Uploading the report-style skill ZIP
- Ends with: Meeting notes reformatted by /cymbal-report-style

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:07 | Upload the company report-style skill ZIP under *Skills* |
| 2 | 0:30 | Press `/` in the chat to invoke the skill and tidy meeting notes |
| 3 | 1:04 | Tour the library · projects · unified search · agents |

### `ge7` — GE Lab 7 · Chat agent — internal help desk

- Lab page: `production/content/v2/ge_labs/lab7.py` · script: `production/render/scripts/v2/ge7.json`
- 16 segments (1 title, 13 screen, 1 card, 1 outro) · 93 narration sentences · 0 callouts · 10 on-screen labels · size budget 40 MB
- Recordings used (13): `ge7a_build`, `ge7b_test`, `ge7c_create`, `ge7d_use`, `ge7e_open_edit`, `ge7f2_model_menu`, `ge7f_node_instructions`, `ge7g2_starter_prompt`, `ge7g_node_knowledge`, `ge7h2_subagent2`, `ge7h3_schedule`, `ge7h_subagent`, `ge7i_preview_update`
- Opens with: Building the chat agent from a policy PDF
- Ends with: Compound question delegated to two parallel sub-agents, then Update

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:08 | *+ New agent* → *Chat agent*; describe it together with the policy PDF |
| 2 | 0:46 | Test policy questions in *Preview*, then open the *Flow* |
| 3 | 1:06 | Check the agent node details (instructions · model · knowledge), then *Create* |
| 4 | 1:21 | Call it from *Chat with agent* and from the normal chat with `@mention` |
| 5 | 2:20 | Reopen the agent, add rules to *Instructions* and choose a *Model* |
| 6 | 2:52 | Remove the web-search *connector* · upload a *knowledge* PDF · edit *starter prompts* |
| 7 | 3:19 | Add the first sub-agent ("settlement-deadline calculator") with the canvas ⊕ button |
| 8 | 3:54 | Add the second, parallel sub-agent ("leave, work-policy & security advisor") · *Add connector* dialog · attach its own knowledge PDF |
| 9 | 4:31 | Explore scheduled automation for chat agents in the *Schedule* tab |
| 10 | 4:51 | Verify a compound question delegated to both sub-agents in *Preview*, then publish with *Update* |

### `ge8` — GE Lab 8 · Workflow — inquiry triage & reply drafts

- Lab page: `production/content/v2/ge_labs/lab8.py` · script: `production/render/scripts/v2/ge8.json`
- 16 segments (1 title, 13 screen, 1 card, 1 outro) · 95 narration sentences · 0 callouts · 12 on-screen labels · size budget 40 MB
- Recordings used (12): `ge8a_build`, `ge8b_edit`, `ge8c_test`, `ge8d_trigger`, `ge8e2_step_file_schema`, `ge8e_step`, `ge8f0_flow_menu`, `ge8f_approval`, `ge8g2_reject_branch`, `ge8g_branch`, `ge8h_test_approval`, `ge8i_update`
- Opens with: Describing the 3-step workflow in natural language
- Ends with: Full test run including human approval, then Update

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:08 | *+ New agent* → *Workflow*; describe the step-by-step flow in natural language |
| 2 | 0:41 | Ask for an extra step by chatting; check the trigger and node details |
| 3 | 1:36 | Run the basic workflow in the *Test* tab and verify the briefing |
| 4 | 1:55 | Check *Enable* and the permission notice |
| 5 | 2:23 | Reopen the workflow, check the *trigger* type and change the start time to 08:30 |
| 6 | 2:47 | Edit the step-1 classification agent node: instructions · connected apps · model |
| 7 | 3:11 | Attach the product-brief file to the step-1 node and explore the visual JSON-schema editor |
| 8 | 3:33 | Add a flow-control *Condition* node and look at the If / Else expression |
| 9 | 3:52 | Add a human-in-the-loop *Approval* node and insert the previous step's briefing as a variable |
| 10 | 4:08 | Add a "CS-team announcement summary agent" on the *approved* branch · insert variables · rename |
| 11 | 4:36 | Connect an existing ADK agent ("Cymbal event guide") and set up a human-in-the-loop *Request info* node on the *rejected* branch |
| 12 | 5:16 | Verify the full run including approval in the *Test* tab, then *Update* |

### `ge9` — GE Lab 9 · Sharing, gallery & managing agents

- Lab page: `production/content/v2/ge_labs/lab9.py` · script: `production/render/scripts/v2/ge9.json`
- 7 segments (1 title, 5 screen, 1 outro) · 58 narration sentences · 0 callouts · 5 on-screen labels · size budget 40 MB
- Recordings used (3): `ge9a_gallery`, `ge9b_manage`, `ge9c_combo`
- Opens with: The agent gallery
- Ends with: One-page report combining an ADK agent answer with a skill

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:07 | Browse company agents in the sidebar *Agents* gallery |
| 2 | 0:17 | Edit · delete · manage status from the agent card menu (⋮) |
| 3 | 0:27 | Call any agent instantly with `@AgentName` from any chat |
| 4 | 0:44 | `@mention` the company ADK agent running on Vertex AI Agent Engine |
| 5 | 1:14 | Combine the agent's answer with the `/cymbal-report-style` skill to finish a one-page report |

### `ag_opening` — AG opening · Building software with agents

- Script: `production/render/scripts/v2/ag_opening.json` · 35 segments (1 title, 32 screen, 1 card, 1 outro) · 108 narration sentences · 49 callouts · 13 on-screen labels · size budget 90 MB
- Slide recordings (10): `ag_s_adk`, `ag_s_custom`, `ag_s_family`, `ag_s_labs`, `ag_s_loop`, `ag_s_mcp`, `ag_s_safety`, `ag_s_shift`, `ag_s_signin`, `ag_s_story` — HTML slides built by `production/render/out/openings/make_slides.py`
- Real-UI clips (13): `ag2a_signin`, `ag3v_open`, `ag3v_plan`, `ag4v_browse`, `ag4v_build`, `ag4v_dash`, `ag5v_use`, `ag6v_install`, `ag6v_query`, `ag7v_deck`, `ag8v_run`, `ag9v_ge_use`, `ag9v_publish`
- *Note:* the last published render of this opening (9:37) predates the current script (which adds the cymbal-voc story and result previews). Render the script to regenerate it.

### `ag1` — AG Lab 1 · Getting started A — GE license

- Lab page: `production/content/v2/ag_labs/lab1.py` · script: `production/render/scripts/v2/ag1.json`
- 10 segments (1 title, 7 screen, 1 card, 1 outro) · 84 narration sentences · 23 callouts · 7 on-screen labels · size budget 40 MB
- Recordings used (2): `ag1r_console`, `ag2a_signin`
- Opens with: Sign-in choice, then the Google Cloud console admin settings
- Ends with: Use Business Account sign-in and the Developer tools metrics page

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:06 | Check first — which sign-in method do you use? |
| 2 | 0:23 | Admin prep ① — supported editions and billing account |
| 3 | 0:31 | Admin prep ② — APIs and IAM roles |
| 4 | 0:41 | Admin setting ③ — turn on *AI developer tools* |
| 5 | 1:09 | Admin setting ④ — security policies and logs |
| 6 | 1:45 | Admin setting ⑤ — features: `/boost` · `/teamwork-preview` |
| 7 | 2:06 | Admin setting ⑥ — allowed models |
| 8 | 2:40 | User — sign in with *Use Business Account* |
| 9 | 2:56 | Admin — usage (*Developer tools metrics*) |

### `ag2` — AG Lab 2 · Getting started B — personal Google account

- Lab page: `production/content/v2/ag_labs/lab2.py` · script: `production/render/scripts/v2/ag2.json`
- 7 segments (1 title, 4 card, 1 screen, 1 outro) · 61 narration sentences · 2 callouts · 2 on-screen labels · size budget 40 MB
- Recordings used (1): `ag2a_signin`
- Opens with: Card: the two sign-in options
- Ends with: Plan / quota / credit comparison cards

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:17 | Install the app, then *Continue with Google* |
| 2 | 0:28 | Sign in in the browser and return to the app |
| 3 | 0:43 | Plan differences — quotas and models |
| 4 | 1:06 | When the quota runs out — AI credits |
| 5 | 1:19 | How is this different from a company account (Lab 1)? |

### `ag3` — AG Lab 3 · Taking on the project

- Lab page: `production/content/v2/ag_labs/lab3.py` · script: `production/render/scripts/v2/ag3.json`
- 14 segments (1 title, 1 card, 11 screen, 1 outro) · 46 narration sentences · 30 callouts · 5 on-screen labels · size budget 45 MB
- Recordings used (6): `ag3v_ask`, `ag3v_open`, `ag3v_plan`, `ag3v_plandoc`, `ag3v_setup`, `ag3v_verify`
- Opens with: Agenda card, then opening cymbal-voc and the request memo
- Ends with: The Implementation Plan produced by /plan, revised after feedback

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:26 | Open the practice folder and read the request |
| 2 | 1:04 | Prepare permissions · panels · model |
| 3 | 1:47 | Understand the request and data with `@mentions` |
| 4 | 2:35 | Verify numbers with tools — approve command execution |
| 5 | 3:26 | Plan the dashboard with `/plan` and give feedback |

### `ag4` — AG Lab 4 · Build the VOC dashboard

- Lab page: `production/content/v2/ag_labs/lab4.py` · script: `production/render/scripts/v2/ag4.json`
- 28 segments (1 title, 25 screen, 1 card, 1 outro) · 77 narration sentences · 44 callouts · 7 on-screen labels · size budget 60 MB
- Recordings used (6): `ag4v_browse`, `ag4v_build`, `ag4v_dash`, `ag4v_iterate`, `ag4v_settings`, `ag4v_verify`
- Opens with: Result preview: the finished VOC dashboard
- Ends with: Step 6: using the dashboard (filters, urgent-only) at 2x

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:37 | Build per plan — *Proceed* and review changes |
| 2 | 2:00 | Change settings — *Always Proceed* only in the practice folder |
| 3 | 2:26 | Check the page with `/browser` — verification report and screenshots |
| 4 | 3:24 | Add features — product filter and "urgent only" |
| 5 | 4:20 | Verify again — confirm the filters with `/browser` |
| 6 | 5:29 | Use the finished dashboard yourself |

### `ag5` — AG Lab 5 · Team rules & weekly-report skill

- Lab page: `production/content/v2/ag_labs/lab5.py` · script: `production/render/scripts/v2/ag5.json`
- 25 segments (1 title, 1 card, 22 screen, 1 outro) · 52 narration sentences · 41 callouts · 5 on-screen labels · size budget 45 MB
- Recordings used (8): `ag5v_check`, `ag5v_custom`, `ag5v_rules`, `ag5v_rules_file`, `ag5v_skill`, `ag5v_skill_file`, `ag5v_slash`, `ag5v_use`
- Opens with: Agenda card: rules always, skills when needed
- Ends with: Weekly VOC report generated by the auto-selected skill; /slash invocation

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:06 | Create the team-rules file `AGENTS.md` |
| 2 | 1:34 | Check and fix according to the rules |
| 3 | 2:34 | Build the weekly-report skill — `SKILL.md` + script |
| 4 | 3:54 | Confirm the skill is used automatically — auto-selection |
| 5 | 4:53 | Call it directly with slash (`/`) and *Customizations* |

### `ag6` — AG Lab 6 · Connect company data with MCP — BigQuery

- Lab page: `production/content/v2/ag_labs/lab6.py` · script: `production/render/scripts/v2/ag6.json`
- 29 segments (1 title, 1 card, 26 screen, 1 outro) · 68 narration sentences · 48 callouts · 5 on-screen labels · size budget 45 MB
- Recordings used (6): `ag6v_env`, `ag6v_insight`, `ag6v_install`, `ag6v_query`, `ag6v_run`, `ag6v_skill`
- Opens with: Agenda card: the CSV is a copy, the source is BigQuery
- Ends with: Week-over-week table from BigQuery via MCP; upgraded skill run

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:30 | Fill the lab variables and load the data into BigQuery |
| 2 | 1:29 | Install the BigQuery MCP server from the MCP Store |
| 3 | 2:41 | Query real data with MCP tools |
| 4 | 3:53 | Find the cause in the data |
| 5 | 4:56 | Upgrade the skill to MCP and run it again |

### `ag7` — AG Lab 7 · Executive report slides

- Lab page: `production/content/v2/ag_labs/lab7.py` · script: `production/render/scripts/v2/ag7.json`
- 29 segments (1 title, 26 screen, 1 card, 1 outro) · 60 narration sentences · 54 callouts · 9 on-screen labels · size budget 45 MB
- Recordings used (6): `ag7v_before`, `ag7v_deck`, `ag7v_edit`, `ag7v_pdf`, `ag7v_slides`, `ag7v_template`
- Opens with: Result preview: the 6-slide deck built from the company template
- Ends with: Step 4: the finished deck paged through in presentation mode

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:34 | Build slides from the company template + skill + BigQuery MCP |
| 2 | 2:50 | Check with `/browser` and export to PDF |
| 3 | 4:09 | Apply feedback — key three lines into one · numbers on the safety issue → PDF again |
| 4 | 5:27 | The finished six slides — page through in presentation mode and review the numbers |

### `ag8` — AG Lab 8 · VOC analysis agent — ADK

- Lab page: `production/content/v2/ag_labs/lab8.py` · script: `production/render/scripts/v2/ag8.json`
- 22 segments (1 title, 19 screen, 1 card, 1 outro) · 52 narration sentences · 29 callouts · 6 on-screen labels · size budget 45 MB
- Recordings used (5): `ag8v_create`, `ag8v_eval`, `ag8v_run`, `ag8v_score`, `ag8v_tools`
- Opens with: Result preview: the agent's answer (6 tickets) and 5/5 eval scores
- Ends with: Evaluation report with per-case scores

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:42 | Create an ADK agent project with agents-cli |
| 2 | 1:38 | Add two BigQuery tools — weekly summary · urgent tickets |
| 3 | 2:49 | Run with `agents-cli run` — check the tool calls |
| 4 | 4:08 | Evaluate with `agents-cli eval` — three cases |
| 5 | 5:08 | Open the evaluation report and check the scores |

### `ag9` — AG Lab 9 · Deploy + publish to Gemini Enterprise

- Lab page: `production/content/v2/ag_labs/lab9.py` · script: `production/render/scripts/v2/ag9.json`
- 21 segments (1 title, 16 screen, 3 card, 1 outro) · 59 narration sentences · 29 callouts · 4 on-screen labels · size budget 45 MB
- Recordings used (4): `ag9v_deploy`, `ag9v_ge_use`, `ag9v_iam`, `ag9v_publish`
- Opens with: Result preview: a CX team member asking the published agent in GE
- Ends with: GE answer table with masked names and phone numbers

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:52 | Deploy to Agent Runtime — `agents-cli deploy` |
| 2 | 2:08 | Give the deployed agent BigQuery permissions — IAM |
| 3 | 3:10 | Publish to Gemini Enterprise — `agents-cli publish gemini-enterprise` |
| 4 | 4:09 | Use it in Gemini Enterprise — a CX team member's question |
| 5 | 5:27 | Do it yourself with commands · clean up (cost) |

### `ag10` — AG Lab 10 · Operations automation

- Lab page: `production/content/v2/ag_labs/lab10.py` · script: `production/render/scripts/v2/ag10.json`
- 25 segments (1 title, 20 screen, 3 card, 1 outro) · 59 narration sentences · 30 callouts · 9 on-screen labels · size budget 45 MB
- Recordings used (5): `ag10v_schedule`, `ag10v_sub`, `ag4v_dash`, `ag7v_deck`, `ag9v_ge_use`
- Opens with: Result preview: schedule status answer and 6 passing tests
- Ends with: Recap montage of dashboard, deck and GE assistant; request checklist

| Chapter = step | Starts at | Title |
|---|---|---|
| 1 | 0:52 | Schedule the Monday 08:30 report with `/schedule` |
| 2 | 1:54 | Check the schedule · ask for status · stop it |
| 3 | 3:14 | Two sub-agents for tests and the ops guide at the same time |
| 4 | 5:08 | Wrap-up — the three request items and what to watch in operations |
