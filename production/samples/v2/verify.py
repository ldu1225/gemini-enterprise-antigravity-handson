"""Verify every generated v2 sample file. Exit code 1 on any failure (adapted from v1 verify.py).

Checks: xlsx structure/values (stdlib zipfile + ElementTree on our own output; no external entities),
PDF page counts / disclaimer on every page / embedded fonts (Type0 + NanumGothic only, i.e. no fallback
glyphs) / clean Korean text layer / key facts, real rendering of every PDF page (macOS sips → PNG, non-blank
+ contact sheets for visual review), skill frontmatter + zip, bundle zip, previews, manifest, answer keys,
calendar arithmetic, and banned real-company names.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageStat
from pypdf import PdfReader

import build_skill
import calendar_kr as C
import data_inquiries as Q
import data_sales as S
from common import FILES, KEYS, OUT, SHORT_DISC, DISCLAIMER, HERE, WORK, preview_path

sys.path.insert(0, str(HERE / "tools"))
from pdf_pages import rasterize  # noqa: E402

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
FAIL: list[str] = []
BANNED = ["삼성", "Samsung", "SK", "현대", "Google", "구글", "Gemini", "쿠팡", "네이버", "카카오", "Apple", "애플",
          "Dyson", "다이슨", "Xiaomi", "샤오미", "Amazon", "아마존", "코웨이", "위니아"]


def check(cond: bool, msg: str) -> None:
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def banned_hits(text: str) -> list[str]:
    hits = []
    for b in BANNED:
        if b.isascii():
            if re.search(rf"(?<![A-Za-z]){re.escape(b)}(?![A-Za-z])", text):
                hits.append(b)
        elif b in text:
            hits.append(b)
    return hits


# ---------------------------------------------------------------- xlsx
def read_xlsx(path):
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    sheets = {}
    for s in wb.find("m:sheets", NS):
        target = rmap[s.get(f"{{{NS['r']}}}id")]
        raw = z.read("xl/" + target.lstrip("/").replace("xl/", ""))
        cells = {}
        for c in ET.fromstring(raw).iter(f"{{{NS['m']}}}c"):
            v = c.find("m:v", NS)
            if v is None:
                continue
            cells[c.get("r")] = ss[int(v.text)] if c.get("t") == "s" else float(v.text)
        sheets[s.get("name")] = {"cells": cells, "xml": raw.decode("utf-8")}
    props = z.read("docProps/core.xml").decode("utf-8") if "docProps/core.xml" in z.namelist() else ""
    return sheets, props, ss


def col(n: int) -> str:
    return chr(ord("A") + n)


def common_sheet_checks(sheets, props):
    for name, sh in sheets.items():
        check(SHORT_DISC in str(sh["cells"].get("A1", "")), f"{name}: A1 title shows '{SHORT_DISC}'")
        check('state="frozen"' in sh["xml"], f"{name}: freeze panes")
        check("<autoFilter" in sh["xml"], f"{name}: autofilter")
        check("<f>" not in sh["xml"], f"{name}: static values (no formulas)")
    check(SHORT_DISC in props, "document properties contain disclaimer")


def verify_sales():
    print("[1] " + FILES["sales"])
    sheets, props, ss = read_xlsx(OUT / FILES["sales"])
    check(list(sheets) == ["매출데이터", "목표"], f"2 sheets {list(sheets)}")
    common_sheet_checks(sheets, props)
    c = sheets["매출데이터"]["cells"]
    hdr = [c.get(f"{col(i)}2") for i in range(len(S.SALES_COLS))]
    check(hdr == S.SALES_COLS, f"header {hdr}")
    rows = S.rows()
    n = sum(1 for k in c if re.fullmatch(r"A\d+", k)) - 2
    check(n == 225 == len(rows), f"data rows = {n}")
    ok = all(c[f"A{i + 3}"] == r["월"] and c[f"C{i + 3}"] == r["제품"] and c[f"D{i + 3}"] == r["지역"]
             and c[f"E{i + 3}"] == r["판매수량(대)"] and abs(c[f"G{i + 3}"] - r["매출액(백만원)"]) < 1e-9
             and abs(c[f"H{i + 3}"] - r["매출총이익(백만원)"]) < 1e-9 for i, r in enumerate(rows))
    check(ok, "매출데이터 cell values == dataset (225 rows)")
    rev_ok = all(abs(r["매출액(백만원)"] - round(r["판매수량(대)"] * r["평균판매가(원)"] / 1e6, 1)) <= 0.11 for r in rows)
    check(rev_ok, "매출액 ≈ 판매수량 × 평균판매가 (±0.1)")
    gp_ok = all(abs(r["매출총이익(백만원)"] - r["매출액(백만원)"] * r["매출총이익률(%)"] / 100) <= 0.06 for r in rows)
    check(gp_ok, "매출총이익 ≈ 매출액 × 매출총이익률")
    t = sheets["목표"]["cells"]
    check(sum(1 for k in t if re.fullmatch(r"A\d+", k)) - 2 == 45, "목표 rows = 45")
    F = S.facts()
    total = round(sum(c[f"G{i}"] for i in range(3, 228)), 1)
    check(abs(total - F["total_rev"]) < 0.05, f"sheet total revenue {total:,.1f} == facts {F['total_rev']:,.1f}")
    check(F["sep_rank"][0] == "로봇청소기", "story: 로봇청소기 = 9월 매출 1위")
    check(F["robot_growth_x"] >= 2.3 and F["achv_q"]["로봇청소기"]["3분기"] > 120, "story: 로봇청소기 급성장·목표 초과")
    check(F["camera_q3_vs_q2_pct"] < -25 and F["achv_q"]["홈카메라"]["3분기"] < 70, "story: 홈카메라 3분기 부진")
    check(F["online_share"]["2026-01"] < 23 and F["online_share"]["2026-09"] > 37, "story: 온라인 비중 22% → 38%+")
    check(max(F["gm_pct_ytd"], key=F["gm_pct_ytd"].get) == "스마트 조명", "story: 스마트 조명 마진 최고")
    check(not banned_hits(" ".join(ss)), f"no real company names in shared strings {banned_hits(' '.join(ss))}")


def verify_cs():
    print("[2] " + FILES["cs"])
    sheets, props, ss = read_xlsx(OUT / FILES["cs"])
    check(list(sheets) == ["문의로그"], f"sheets {list(sheets)}")
    common_sheet_checks(sheets, props)
    c = sheets["문의로그"]["cells"]
    hdr = [c.get(f"{col(i)}2") for i in range(len(Q.COLUMNS))]
    check(hdr == Q.COLUMNS, f"header {hdr}")
    check(c.get(f"{col(len(Q.COLUMNS))}2") is None, "no extra columns (no category/urgency answers)")
    check(not any(k in " ".join(map(str, hdr)) for k in ("분류", "카테고리", "긴급", "category", "urgent")),
          "header has no answer columns")
    n = sum(1 for k in c if re.fullmatch(r"A\d+", k)) - 2
    check(n == 60, f"rows = {n}")
    ids = [c[f"A{i}"] for i in range(3, 63)]
    key = json.loads((KEYS / "inquiries_answer_key.json").read_text(encoding="utf-8"))
    check(ids == [k["문의번호"] for k in key["items"]], "answer key IDs match xlsx order")
    check(len(set(ids)) == 60, "unique 문의번호")
    texts = [c[f"G{i}"] for i in range(3, 63)]
    check(len(set(texts)) == 60 and all(10 <= len(t) <= 120 for t in texts), "60 unique inquiry texts (10~120 chars)")
    check(key["counts"] == {"배송지연": 11, "불량/고장": 12, "환불/교환": 11, "사용법": 11, "안전 이슈": 7, "개인정보/계정": 8},
          f"category counts {key['counts']}")
    check(len(key["urgent_ids"]) == 7 and all(k["urgent"] == (k["category"] == "안전 이슈") for k in key["items"]),
          "urgent == 안전 이슈 (7)")
    blank_order = {c[f"A{i}"] for i in range(3, 63) if not c.get(f"F{i}")}
    check(set(key["needs_info_ids"]) <= blank_order and len(key["needs_info_ids"]) == 5, "needs_info rows have blank 주문번호 (5)")
    safety_words = ("연기", "불꽃", "타는 냄새", "녹는 냄새", "부풀", "뜨겁")
    safety_rows = [k for k in key["items"] if k["urgent"]]
    full = {c[f"A{i}"]: c[f"G{i}"] for i in range(3, 63)}
    check(all(any(w in full[k["문의번호"]] for w in safety_words) for k in safety_rows), "every urgent row has a safety cue")
    check(not any(any(w in full[k["문의번호"]] for w in ("연기", "불꽃", "타는 냄새", "부풀")) for k in key["items"] if not k["urgent"]),
          "no non-urgent row contains a fire/smoke cue")
    check(not banned_hits(" ".join(ss)), f"no real company names {banned_hits(' '.join(ss))}")


# ---------------------------------------------------------------- pdf
def verify_pdf(key, lo, hi, facts):
    print(f"[pdf] {FILES[key]}")
    r = PdfReader(OUT / FILES[key])
    n = len(r.pages)
    check(lo <= n <= hi, f"page count {n} in [{lo},{hi}]")
    texts = [nfc(p.extract_text() or "") for p in r.pages]
    check(all(SHORT_DISC in t for t in texts), "'실습용 가상 데이터' on every page")
    check(DISCLAIMER in texts[0] or DISCLAIMER in texts[-1], "full disclaimer sentence present")
    kinds, bases = set(), set()
    for p in r.pages:
        for _k, v in (p["/Resources"].get("/Font") or {}).items():
            o = v.get_object()
            kinds.add(str(o.get("/Subtype")))
            bases.add(str(o.get("/BaseFont")).split("+")[-1])
            if str(o.get("/Subtype")) == "/Type0":
                desc = o["/DescendantFonts"][0].get_object()["/FontDescriptor"].get_object()
                if not any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                    kinds.add("NOT-EMBEDDED")
    check(kinds == {"/Type0"}, f"all fonts embedded TrueType CID (Type0): {kinds}")
    check(all(b.startswith("NanumGothic") for b in bases), f"only NanumGothic (no fallback glyphs): {sorted(bases)}")
    box = r.pages[0].mediabox
    check(abs(float(box.width) - 595) < 2 and abs(float(box.height) - 842) < 2, "A4 page size")
    full = "\n".join(texts)
    spaced = len(re.findall(r"(?:[가-힣] ){4,}", full))
    check(spaced == 0, f"clean Korean text layer (no syllable-spaced runs: {spaced})")
    check("\ufffd" not in full and "\u25a1" not in full, "no replacement/tofu characters in text layer")
    for f in facts:
        check(nfc(f) in full, f"text contains: {f}")
    check(not banned_hits(full), f"no real company names {banned_hits(full)}")
    return n


def verify_rendering():
    print("[render] rasterize every PDF page with macOS sips (real PDF renderer)")
    pages_dir = WORK / "pages"
    for old in pages_dir.glob("*.png") if pages_dir.exists() else []:
        old.unlink()
    for key in ("travel", "leave", "it", "brief", "brand"):
        pngs = rasterize(OUT / FILES[key], pages_dir, 900)
        renamed = []
        for p in pngs:
            dst = p.with_name(f"{key}-{p.stem.rsplit('-', 1)[1]}.png")
            p.rename(dst)
            renamed.append(dst)
        stats = []
        for p in renamed:
            im = Image.open(p).convert("L")
            st = ImageStat.Stat(im)
            stats.append(st.stddev[0])
        check(all(s > 8 for s in stats), f"{key}: {len(renamed)} pages rendered, none blank (min stddev {min(stats):.1f})")
        thumbs = [Image.open(p).convert("RGB").resize((300, 424)) for p in renamed]
        sheet = Image.new("RGB", (310 * len(thumbs) + 10, 434), "#D0D4DA")
        for i, t in enumerate(thumbs):
            sheet.paste(t, (10 + 310 * i, 5))
        sheet.save(WORK / f"contact_{key}.png")
    print(f"       contact sheets: {WORK}/contact_*.png")


# ---------------------------------------------------------------- skill / bundle / previews / keys
def verify_skill():
    print("[skill] " + FILES["skill_zip"])
    raw = (OUT / FILES["skill_md"]).read_bytes()
    check(not raw.startswith(b"\xef\xbb\xbf") and raw.startswith(b"---\n"), "SKILL.md starts with '---' (no BOM)")
    check(b"\r\n" not in raw, "LF line endings")
    info = build_skill.validate(raw.decode("utf-8"))
    check(True, f"frontmatter valid: {info}")
    text = raw.decode("utf-8")
    with zipfile.ZipFile(OUT / FILES["skill_zip"]) as z:
        names = z.namelist()
        check(names == ["cymbal-report-style/SKILL.md"], f"zip entries {names}")
        check(z.read(names[0]) == raw, "zip SKILL.md identical to raw file")
    for kw in ("결론", "3줄 요약", "표", "다음 단계", "금지 표현"):
        check(kw in text, f"body enforces '{kw}'")
    fm = text.split("---\n")[1]
    for kw in ("보고서", "3줄 요약", "executive summary"):
        check(kw in fm, f"description trigger '{kw}'")
    F = S.facts()
    check(f"{F['prod_q']['로봇청소기']['3분기']:,.1f}" in text and str(F["achv_q"]["홈카메라"]["3분기"]) in text,
          "skill example numbers == sales data")
    check(not banned_hits(text), f"no real company names {banned_hits(text)}")


def verify_bundle():
    print("[bundle] " + FILES["bundle"])
    root = "Cymbal_실습파일"
    with zipfile.ZipFile(OUT / FILES["bundle"]) as z:
        check(z.testzip() is None, "zip CRC ok")
        names = [nfc(n) for n in z.namelist()]
        expect = {FILES[k] for k in ("sales", "cs", "travel", "leave", "it", "brief", "brand", "skill_zip", "skill_md")}
        got = {n.split("/", 1)[1] for n in names if "/" in n}
        check(expect <= got, "bundle contains all 9 learner files")
        check(not any("answer" in n or "정답" in n for n in names), "answer keys NOT bundled")
        check(all(n.startswith(root + "/") for n in names), "single top-level folder")
        check(all(i.flag_bits & 0x800 for i in z.infolist() if not i.filename.isascii()), "UTF-8 filename flag set")
        for k in ("sales", "travel", "skill_zip"):
            check(z.read(f"{root}/{FILES[k]}") == (OUT / FILES[k]).read_bytes(), f"bundle copy identical: {k}")
        readme = z.read(f"{root}/README_읽어주세요.txt").decode("utf-8-sig")
        check(DISCLAIMER in readme, "README contains disclaimer")


def verify_previews_manifest():
    print("[previews + manifest]")
    for f in (FILES["sales"], FILES["cs"], FILES["travel"], FILES["leave"], FILES["it"], FILES["brief"], FILES["brand"],
              "SKILL.md", FILES["bundle"]):
        p = preview_path(f)
        ok = p.is_file()
        w = Image.open(p).size[0] if ok else 0
        check(ok and 1150 <= w <= 1250, f"preview {p.name} width={w}")
    items = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    check(len(items) == 10, f"manifest has {len(items)} entries")
    for it in items:
        p = OUT / it["file"]
        check(p.is_file() and p.stat().st_size == it["sizeBytes"], f"size matches {it['file']}")
        check((OUT / it["preview"]).is_file(), f"preview exists {it['preview']}")


def verify_keys_calendar():
    print("[answer keys + calendar]")
    for d, wd in [(C.D(2026, 10, 23), "금"), (C.D(2026, 11, 3), "화"), (C.D(2026, 10, 5), "월"), (C.D(2026, 9, 25), "금"),
                  (C.D(2026, 10, 6), "화"), (C.D(2026, 11, 16), "월"), (C.D(2026, 12, 1), "화")]:
        check(C.wd(d) == wd, f"{d} is {wd}요일")
    check(C.EX_DEADLINE_A == C.D(2026, 11, 3), "10/23(금) 귀국 → 정산 마감 11/3(화)")
    check(C.EX_DEADLINE_B == C.D(2026, 10, 6), "9/22(화) 귀국 → 정산 마감 10/6(화)")
    check(C.EX_CARD_STOP_A == C.D(2026, 11, 16), "10/23 귀국 → 법인카드 정지 11/16(월)부터")
    check(not any(d.month == 11 for d in C.HOLIDAYS_2026), "no holidays in 2026-11")
    md = (KEYS / "policies_qa.md").read_text(encoding="utf-8")
    rows = [ln for ln in md.split("\n") if re.match(r"^\| \d+ \|", ln)]
    check(len(rows) == 12, f"policies_qa.md has {len(rows)} questions")
    for s in ("2026년 11월 3일(화)", "2026년 10월 6일(화)", "2026년 11월 16일(월)", "USD 475", "USD 240", "범위 밖", "제목", "시도한 조치"):
        check(s in md, f"policies_qa.md contains '{s}'")
    travel_txt = nfc("\n".join(p.extract_text() or "" for p in PdfReader(OUT / FILES["travel"]).pages))
    check("11월 3일" not in travel_txt and "10월 6일" not in travel_txt,
          "test-question deadlines are NOT printed in the PDF (agent must calculate)")


def main():
    verify_sales()
    verify_cs()
    verify_pdf("travel", 6, 10, ["CYM-FIN-POL-012", "2026-07-01", "USD 280", "USD 95", "USD 60", "USD 220", "7영업일 이내",
                                 "15영업일 초과", "30영업일 초과", "미주·유럽 기준", "100,000원", "500,000원 초과",
                                 "간이영수증 불인정", "2026-10-05", "대체공휴일(개천절)", "11월에는 공휴일이 없다", "제23조"])
    verify_pdf("leave", 6, 10, ["CYM-HR-POL-003", "2026-07-01", "최대 5일", "다음 해 6월 30일", "0.25일", "20일 (최대 3회 분할)",
                                "120일 이내", "주 2일 이내", "전주 금요일 15:00", "10:00~16:00", "제9조"])
    verify_pdf("it", 6, 10, ["CYM-IT-GDE-005", "2026-07-01", "12자 이상", "5회 연속", "30분간", "계정 셀프서비스 포털",
                             "5영업일 이내", "30분 이내", "02-0000-7119", "시도한 조치", "발생 시각", "긴급도", "제20조"])
    verify_pdf("brief", 2, 3, ["Cymbal AirPole Pro", "에어폴 프로", "2026년 12월 1일(화)", "699,000원", "629,100원",
                               "공기는 맑게, 공간은 넓게", "톤앤매너", "경쟁사 A"])
    verify_pdf("brand", 2, 2, ["#4285F4", "#0E1116", "톤 오브 보이스", "금지 표현", "결론 먼저", "3줄 요약", "다음 단계"])
    verify_rendering()
    verify_skill()
    verify_bundle()
    verify_previews_manifest()
    verify_keys_calendar()
    print("\nRESULT:", "ALL CHECKS PASSED" if not FAIL else f"{len(FAIL)} FAILED")
    for f in FAIL:
        print("  -", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
