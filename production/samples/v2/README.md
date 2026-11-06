# production/samples/v2 — synthetic Cymbal practice files

> All data here is **fictional**. Cymbal (Korean: 심벌) is a fictional company; names, phone numbers, orders and
> figures are generated from fixed random seeds and have no relation to real companies or people.
> The original Korean README is kept as [README.ko.md](README.ko.md).

These scripts generate every file learners download from the portal: Excel workbooks, policy PDFs, a GE skill
ZIP, the Antigravity starter project, preview thumbnails and an all-in-one bundle. The generated files are
committed under `build/` so the portal can be built without running the generators.

## Rebuild everything

```bash
cd production/samples/v2
python3 build_all.py      # generate → previews → bundle + manifest → answer keys + DATA_NOTES → verify.py
python3 verify.py         # verification only (exit 1 on failure)
```

`build_all.py` runs, in order: `build_xlsx.py`, `build_travel_pdf.py`, `build_leave_pdf.py`, `build_it_pdf.py`,
`build_marketing_pdfs.py`, `build_skill.py`, `build_previews.py`, `build_voc_starter.py`,
`build_voc_previews.py`, `build_bundle.py`, `write_answer_keys.py`, then `verify.py`.

Requirements: `xlsxwriter`, `playwright` (Chromium), `pypdf`, `Pillow`, `PyYAML`; the **NanumGothic** font
installed on the system (PDF body font, see below); macOS `sips` for the page-render check in `verify.py`.

## Outputs (`build/`)

| File (Korean name) | What it is | Generator | Used in |
|---|---|---|---|
| `Cymbal_제품별_지역별_월별매출_2026_가상.xlsx` | Monthly sales by product × region, Jan–Sep 2026 (225 rows) + monthly targets (45 rows) | `build_xlsx.py` + `data_sales.py` | GE Lab 3 |
| `Cymbal_고객문의_로그_2026-10_가상.xlsx` | 60 customer inquiries (channel, product, message) — **no category/urgency columns** (the workflow must infer them) | `build_xlsx.py` + `data_inquiries.py` | GE Lab 8 |
| `Cymbal_출장비_및_경비처리_규정_가상.pdf` (7 pages) | Travel & expense policy (CYM-FIN-POL-012) incl. a 2026 holiday table | `build_travel_pdf.py` + `calendar_kr.py` | GE Lab 7 |
| `Cymbal_휴가_및_근무제도_규정_가상.pdf` (6 pages) | Leave & work policy (CYM-HR-POL-003) | `build_leave_pdf.py` | GE Lab 7 |
| `Cymbal_IT보안_및_계정관리_가이드_가상.pdf` (6 pages) | IT security & account guide (CYM-IT-GDE-005) | `build_it_pdf.py` | GE Lab 7 |
| `Cymbal_신제품_브리프_에어폴_프로_가상.pdf` (3 pages) | Launch brief for the fictional "AirPole Pro" air purifier | `build_marketing_pdfs.py` | GE Labs 4, 5, 8 |
| `Cymbal_브랜드_가이드_가상.pdf` (2 pages) | Brand colours, tone of voice, banned phrases, customer-care rules | `build_marketing_pdfs.py` | GE Labs 4, 6; AG Labs 4, 7 |
| `Cymbal_보고서스타일_스킬.zip`, `skills/cymbal-report-style/SKILL.md` | GE skill "cymbal-report-style" (conclusion first, 3-line summary, evidence table, next steps) | `build_skill.py` | GE Labs 6, 9 |
| `Cymbal_VOC_스타터.zip`, `cymbal-voc/` | Antigravity starter project: CX team request memo (`요청서_CX팀.md`), `data/voc_tickets.csv` (300 tickets over 4 weeks), `lab.env`, `setup/load_to_bigquery.sh`, `templates/exec_deck_template.html`, `README.md` | `build_voc_starter.py` | AG Labs 3–10 |
| `previews/*.png` (1200 px wide) | Cover thumbnails shown on the portal | PDFs: each `build_*_pdf.py`; others: `build_previews.py`, `build_voc_previews.py` | portal |
| `Cymbal_실습파일_전체.zip`, `manifest.json` | GE learner bundle (2 workbooks, 5 PDFs, the skill as ZIP and `SKILL.md`, plus a read-me; no answer keys) and a manifest of all files | `build_bundle.py` | portal |

Instructor-only material (not part of any learner bundle): `answer_keys/inquiries_answer_key.json` (category,
urgency, needs-info per inquiry), `answer_keys/policies_qa.md` (12 test questions with answers),
`answer_keys/voc_facts.json` (facts of the VOC story used in narration and checks). [DATA_NOTES.md](DATA_NOTES.md)
is generated from the same constants — do not edit it by hand.

## The stories built into the data

- **Sales (GE Lab 3):** robot vacuums grow fast (September = 2.55 × January; Q3 attainment 137.6 %), home
  cameras drop in Q3 (−33.4 % QoQ, 58.6 % attainment), online share rises from 22.0 % to 38.8 %, air purifiers
  peak in March–April, smart-speaker margin falls after a May price cut, smart lighting has the best margin
  (45.1 %).
- **Inquiries (GE Lab 8):** six categories (shipping delay 11, defect 12, refund/exchange 11, how-to 11,
  safety 7, privacy/account 8). Only the 7 safety issues are urgent. Five shipping/refund inquiries lack an
  order number (for the "request info" branch); one says "urgent!!" but is not a safety issue (a trap).
- **Policies (GE Lab 7):** deadline questions require working-day arithmetic with 2026 Korean public holidays
  (asserted in `calendar_kr.py`); the PDFs deliberately use different example dates.
- **VOC story (AG track):** 300 tickets over four weeks starting Monday 2026-09-28 (weekly totals 62 / 68 / 79 /
  91); robot-vacuum *app connection* complaints jump after an update on 2026-10-14 (3 → 1 → 13 → 20 per week);
  safety issues rise from 2 to 6 in the last week, and six urgent tickets are still open — see
  `answer_keys/voc_facts.json`.
- **Product brief:** Cymbal AirPole Pro (CY-AP700), launch 2026-12-01, price 699,000 KRW (pre-order 629,100 KRW).

## Implementation notes

- **Excel:** `xlsxwriter`; row 1 = title + "synthetic data" disclaimer, row 2 = header in Cymbal Blue
  (#4285F4), tidy static values (no formulas), frozen panes, auto-filter, thousands separators.
- **PDF:** HTML/CSS rendered by a separate headless Chromium (`common.py`, own paginator, A4). Network requests
  other than `file:`/`data:` are blocked; no CDN or remote fonts. Body font is **NanumGothic** because Chromium
  exports the variable Pretendard subsets as Type3 glyphs, which breaks the PDF text layer (bad for RAG);
  `verify.py` checks that every embedded font is Type0 NanumGothic (no fallback glyphs). Preview PNGs use
  Pretendard (`production/site_build_v2/vendor/fonts`).
- **Skill ZIP:** front matter `---` without BOM, `name` = folder name `cymbal-report-style`, `description`
  under 1,024 bytes, exactly one `SKILL.md` in the ZIP.
- **Determinism:** fixed seeds (sales 2026, inquiries 1026, VOC tickets 20261027). Answer keys, DATA_NOTES and
  skill examples are derived from the same constants, so they never disagree.
- **Safety:** generated HTML escapes all data text; contacts use `example.com` and `0000` placeholders; real
  company names are rejected by the `BANNED` list in `verify.py` (competitors appear only as "competitor A/B").

## Localizing

For an English edition: translate the strings in `data_*.py`, the policy/brief generators, `build_voc_starter.py`
(README, request memo, `lab.env` comments, ticket messages) and `build_skill.py`; replace the Korean holiday
calendar (`calendar_kr.py`) if you change the locale; pick a static (non-variable) Latin font for PDF bodies and
update `doccss.py` / `verify.py` accordingly; then re-run `build_all.py` and update the file names referenced in
`production/content/v2/site.py`. See [docs/LOCALIZATION.md](../../../docs/LOCALIZATION.md).
