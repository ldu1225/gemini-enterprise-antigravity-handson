#!/usr/bin/env python3
"""Semantic audit of every portal screenshot callout (highlight box) — is the box really on the thing its label names?

The build/QA gates (site_build_v2/build.py + qa.py --callouts-only) prove that a box is DRAWN where the content
coordinates say. This tool checks the coordinates THEMSELVES against the real screenshot:

  1. OCR (Apple Vision, Korean + English) inside the box (+ small margin) → does the text match the label?
  2. OCR of the whole screenshot → if the label's text is visible somewhere else, the box is probably misplaced
     (reported with the location where the text actually is).
  3. Contact sheets (≤ 1280 px wide) with every box drawn on a zoomed crop, for a human/agent visual pass.
     A callout is only "verified" after it was looked at on these sheets.

    python3 production/qa/callout_audit.py                 # all tracks
    python3 production/qa/callout_audit.py --track ge --labs lab4 lab8
    → production/qa/out/stills/report.json, sheet_*.jpg
"""
from __future__ import annotations

import argparse
import atexit
import difflib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "production" / "assets" / "shots"
CONTENT = ROOT / "production" / "content" / "v2"
OCR_JS = ROOT / "production" / "qa" / "vision_ocr.js"
FONT = ROOT / "production" / "render" / "fonts"
OUT = ROOT / "production" / "qa" / "out" / "stills"
# per-process: concurrent audits used to overwrite each other's crop files (c00000.png …) and swap OCR results
TMP = ROOT / "production" / "qa" / "out" / "_ocr_tmp" / f"p{os.getpid()}"
atexit.register(shutil.rmtree, TMP, True)

_OCR_CACHE: dict[tuple, list] = {}


def font(size: int):
    for name in ("Pretendard-SemiBold.otf", "Pretendard-Bold.otf", "Pretendard-Regular.otf"):
        p = FONT / name
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    for p in FONT.glob("*.otf"):
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def _key(path: Path, crop) -> tuple:
    return (str(path), tuple(round(v) for v in crop) if crop else None)


def prefetch(jobs: list[tuple[Path, list | None]]) -> None:
    """OCR many (image, crop) jobs with one osascript call per 40 images (Apple Vision, ko-KR + en-US)."""
    TMP.mkdir(parents=True, exist_ok=True)
    todo, files = [], []
    for path, crop in jobs:
        k = _key(path, crop)
        if k in _OCR_CACHE or k in todo:
            continue
        if crop:
            x, y, w, h = (round(v) for v in crop)
            with Image.open(path) as im:
                x0, y0 = max(0, x), max(0, y)
                x1, y1 = min(im.width, x + w), min(im.height, y + h)
                f = TMP / f"c{len(files):05d}.png"
                im.convert("RGB").crop((x0, y0, x1, y1)).save(f)
            off = (x0, y0)
        else:
            f, off = path, (0, 0)
        todo.append(k)
        files.append((f, off))
    for i in range(0, len(files), 40):
        chunk = files[i:i + 40]
        res = subprocess.run(["osascript", "-l", "JavaScript", str(OCR_JS)] + [str(f) for f, _ in chunk],
                             capture_output=True, text=True, timeout=600)
        by_file: dict[str, list] = {str(f): [] for f, _ in chunk}
        for line in res.stdout.splitlines():
            if line.strip().startswith("{"):
                r = json.loads(line)
                if "text" in r:
                    by_file.setdefault(r["file"], []).append(r)
        for (f, off), k in zip(chunk, todo[i:i + 40]):
            rows = []
            for r in by_file.get(str(f), []):
                bx, by, bw, bh = r["box"]
                rows.append({"text": r["text"], "conf": r["conf"], "box": [bx + off[0], by + off[1], bw, bh]})
            _OCR_CACHE[k] = rows


def ocr(path: Path, crop=None) -> list[dict]:
    k = _key(path, crop)
    if k not in _OCR_CACHE:
        prefetch([(path, crop)])
    return _OCR_CACHE[k]


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[\s·•…—–\-_/|,.:;!?'\"“”‘’()\[\]{}<>@#*+=~`]", "", s)
    return s


def tokens(label: str) -> list[str]:
    parts = re.split(r"[\s·•—–,/+→()]+", label)
    return [p for p in (norm(x) for x in parts) if len(p) >= 2]


def match_score(label: str, text: str) -> float:
    """Share of label tokens present in text (exact substring, else fuzzy ≥ 0.8 against a sliding window)."""
    toks = tokens(label)
    if not toks:
        return 1.0
    t = norm(text)
    hit = 0.0
    for tok in toks:
        if tok in t:
            hit += 1
            continue
        best = 0.0
        L = len(tok)
        for i in range(0, max(1, len(t) - L + 1)):
            r = difflib.SequenceMatcher(None, tok, t[i:i + L]).ratio()
            if r > best:
                best = r
        if best >= 0.8:
            hit += best
    return round(hit / len(toks), 2)


def load_labs(track: str) -> list[dict]:
    spec = importlib.util.spec_from_file_location(f"v2_{track}", CONTENT / f"{track}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(CONTENT))
    spec.loader.exec_module(mod)
    return mod.LABS


def iter_shots(step: dict):
    if step.get("shot"):
        s = step["shot"]
        yield s if isinstance(s, dict) else {"stem": s, "caption": step.get("caption", ""), "callouts": step.get("callouts") or []}
    if step.get("shot2"):
        yield {"stem": step["shot2"], "caption": step.get("caption2", ""), "callouts": step.get("callouts2") or []}
    for s in step.get("shots") or []:
        yield s if isinstance(s, dict) else {"stem": s, "caption": "", "callouts": []}


def find_src(stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = SHOTS / f"{stem}{ext}"
        if p.is_file():
            return p
    return None


def audit(tracks: list[str], labs_filter: list[str] | None) -> list[dict]:
    rows = []
    for tr in tracks:
        for lab in load_labs(tr):
            if labs_filter and lab["id"] not in labs_filter:
                continue
            for si, st in enumerate(lab.get("steps") or []):
                for k, s in enumerate(iter_shots(st)):
                    cos = s.get("callouts") or []
                    if not cos:
                        continue
                    src = find_src(s["stem"])
                    if not src:
                        rows.append({"track": tr, "lab": lab["id"], "step": si + 1, "stem": s["stem"], "problem": "screenshot missing"})
                        continue
                    with Image.open(src) as im:
                        W, H = im.size
                    if s.get("viewport"):
                        cw, ch = s["viewport"]
                    else:
                        dpr = 2 if W >= 2400 else 1
                        cw, ch = round(W / dpr), round(H / dpr)
                    sx, sy = W / cw, H / ch
                    full = ocr(src)
                    for j, c in enumerate(cos):
                        x, y, w, h = (float(v) for v in c["box"])
                        label = str(c.get("label") or "")
                        m = 6
                        crop = [(x - m) * sx, (y - m) * sy, (w + 2 * m) * sx, (h + 2 * m) * sy]
                        inside = ocr(src, crop)
                        text_in = " ".join(r["text"] for r in inside)
                        score = match_score(label, text_in) if label else 1.0
                        # where else does the label text appear on the screenshot?
                        elsewhere = []
                        if label and score < 0.6:
                            for r in full:
                                if match_score(label, r["text"]) >= 0.8:
                                    bx, by, bw, bh = (v / sx for v in r["box"])
                                    cx, cy = bx + bw / 2, by + bh / 2
                                    if not (x - 4 <= cx <= x + w + 4 and y - 4 <= cy <= y + h + 4):
                                        elsewhere.append({"text": r["text"], "box_css": [round(bx), round(by), round(bw), round(bh)]})
                        rows.append({"track": tr, "lab": lab["id"], "step": si + 1, "shot": k + 1, "n": j + 1, "stem": s["stem"],
                                     "label": label, "box": [x, y, w, h], "cap": [cw, ch], "ocr_in_box": text_in[:160],
                                     "score": score, "label_elsewhere": elsewhere[:3], "src": str(src), "scale": [sx, sy]})
    return rows


def sheets(rows: list[dict], out: Path, per_sheet: int = 6, tile_w: int = 620, crop_h: int = 300) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("sheet_*.jpg"):
        old.unlink()
    f_hdr, f_lab = font(17), font(16)
    tiles = []
    for r in rows:
        if "box" not in r:
            continue
        x, y, w, h = r["box"]
        sx, sy = r["scale"]
        cw, ch = r["cap"]
        # crop: box + context, aspect tile_w:crop_h, at least 1.0 CSS px per tile px (zoom in on small targets)
        ctx_w = max(w * 2.2, 360.0)
        ctx_h = ctx_w * crop_h / tile_w
        if h * 1.6 > ctx_h:
            ctx_h = h * 1.6
            ctx_w = ctx_h * tile_w / crop_h
        ctx_w, ctx_h = min(ctx_w, cw), min(ctx_h, ch)
        # Clamping one side breaks the tile aspect: the crop would be squashed and the box drawn with the wrong
        # vertical scale (wide boxes looked shifted down). Restore the aspect by trimming the longer side (never
        # below the box itself) and draw with separate x/y scales so the box is exact even if a distortion remains.
        if ctx_w / ctx_h > tile_w / crop_h:
            ctx_w = max(ctx_h * tile_w / crop_h, min(w + 8.0, cw))
        else:
            ctx_h = max(ctx_w * crop_h / tile_w, min(h + 8.0, ch))
        cx, cy = x + w / 2, y + h / 2
        X0 = min(max(0.0, cx - ctx_w / 2), cw - ctx_w)
        Y0 = min(max(0.0, cy - ctx_h / 2), ch - ctx_h)
        with Image.open(r["src"]) as im:
            im = im.convert("RGB")
            region = im.crop((round(X0 * sx), round(Y0 * sy), round((X0 + ctx_w) * sx), round((Y0 + ctx_h) * sy)))
        region = region.resize((tile_w, crop_h), Image.LANCZOS)
        d = ImageDraw.Draw(region)
        kx, ky = tile_w / ctx_w, crop_h / ctx_h
        bx0, by0 = (x - X0) * kx, (y - Y0) * ky
        d.rectangle([bx0, by0, bx0 + w * kx, by0 + h * ky], outline=(255, 0, 170), width=3)
        tile = Image.new("RGB", (tile_w, crop_h + 52), (255, 255, 255))
        tile.paste(region, (0, 52))
        d = ImageDraw.Draw(tile)
        ok = r["score"] >= 0.6
        color = (20, 130, 40) if ok else (200, 30, 30)
        d.text((8, 4), f"{r['track']}/{r['lab']} s{r['step']} #{r['n']}  {r['stem']}"[:70], fill=(60, 60, 60), font=f_hdr)
        d.text((8, 27), f"«{r['label']}»  ocr={r['score']:.2f}"[:64], fill=color, font=f_lab)
        tiles.append(tile)
    paths = []
    for i in range(0, len(tiles), per_sheet):
        chunk = tiles[i:i + per_sheet]
        cols = 2
        rows_n = (len(chunk) + 1) // 2
        th = chunk[0].height
        sheet = Image.new("RGB", (cols * tile_w + 12, rows_n * (th + 8) + 4), (225, 228, 233))
        for n, t in enumerate(chunk):
            sheet.paste(t, (4 + (n % 2) * (tile_w + 4), 4 + (n // 2) * (th + 8)))
        p = out / f"sheet_{i // per_sheet + 1:02d}.jpg"
        sheet.save(p, quality=72)
        paths.append(p)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", action="append", choices=["ge", "ag"])
    ap.add_argument("--labs", nargs="*")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    rows = audit(a.track or ["ge", "ag"], a.labs)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    paths = sheets(rows, a.out)
    low = [r for r in rows if r.get("score", 1) < 0.6 or r.get("problem")]
    print(f"{len(rows)} callouts, {len(low)} need attention (OCR text inside the box does not match the label)")
    for r in low:
        print(f"  {r['track']}/{r['lab']} s{r['step']} #{r.get('n')} {r['stem']} «{r.get('label')}» score={r.get('score')} "
              f"in-box={r.get('ocr_in_box', '')[:50]!r} elsewhere={r.get('label_elsewhere')}")
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
