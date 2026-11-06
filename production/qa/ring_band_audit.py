#!/usr/bin/env python3
"""Ring-band audit — does any video highlight ring cut through text it should not touch?

video_callout_audit.py proves the text INSIDE a ring matches its chip. It does not catch a ring whose stroke runs
through the neighbouring line/row (the engine pads every callout box by 6 CSS px, then draws a 4 px stroke outside
it — in dense UI that lands on the next line), a box edge that cuts the target text, a ring clamped at the frame edge,
or a ring hidden under a caption. This tool checks exactly that, from the render plan (same maths as the compositor):

  for every callout, at 3 moments while it is fully shown:
    ring band  = padded box ±(−0.5 … +4.5) output px, clamped like the compositor
    text ink   = Apple-Vision OCR lines of the source frame actually shown, refined to glyph-ink blobs
                 (high-contrast pixels, split into words/rows, demo cursor masked out)
    FAIL  if the band crosses a glyph blob (> 0.75 px), the ring is clamped at the frame edge, or overlaps a caption
    WARN  if the only crossings are next to the demo cursor, or the tracker hides the ring

    python3 production/qa/ring_band_audit.py production/render/scripts/v2/ag5.json [more.json ...]
    → production/qa/out/ring/<id>/report.json, fail_*.jpg (contact sheet of FAIL/WARN rings, crossings boxed red)
    exit code 1 if any FAIL.  Uses cached narration (TTS_REUSE=1 is set by default; no new TTS is synthesised).

Fixing a FAIL: re-measure the box from the shown frame (glyph rows, not OCR boxes), set "pad": 0 (or small) on the
callout, keep 1–2 CSS px between box and glyphs, move the camera ("zoom") if the ring touches the frame edge or the
caption band; re-render with TTS_REUSE=1 --strict-callouts and run this tool + video_callout_audit.py again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("TTS_REUSE", "1")

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "production" / "render"))
sys.path.insert(0, str(HERE))

from callout_audit import font  # noqa: E402
from engine import compositor  # noqa: E402
from engine.recording import Recording  # noqa: E402
from engine.timeline import build_plan  # noqa: E402

OUT = ROOT / "production" / "qa" / "out" / "ring"
OCR_JS = ROOT / "production" / "qa" / "vision_ocr.js"
CACHE = OUT / "_ocr"
TMP = OUT / "_tmp" / f"p{os.getpid()}"
STROKE_OUT, STROKE_IN = 4.5, 0.5          # compositor.draw_callout: stroke centred 2 px outside the box, 4 px wide
LUM_T = 48                                # glyph ink = |lum - lum(bg)| > LUM_T (rejects faint bands/borders)


# ------------------------------------------------------------------ OCR (crops, disk cache, parallel batches)
def _ckey(path: str, crop) -> Path:
    return CACHE / (hashlib.sha1(f"{path}|{crop}".encode()).hexdigest() + ".json")


def _ocr_batch(items):
    files = [str(t) for _, _, t, _ in items]
    res = subprocess.run(["osascript", "-l", "JavaScript", str(OCR_JS)] + files, capture_output=True, text=True,
                         timeout=1800)
    by = {f: [] for f in files}
    for line in res.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            r = json.loads(line)
            if "text" in r:
                by.setdefault(r["file"], []).append(r)
    for path, crop, tmp, off in items:
        rows = [{"text": r["text"], "box": [r["box"][0] + off[0], r["box"][1] + off[1], r["box"][2], r["box"][3]]}
                for r in by.get(str(tmp), [])]
        _ckey(path, crop).write_text(json.dumps(rows, ensure_ascii=False))


def ocr_crops(jobs, workers: int) -> dict:
    """jobs: [(frame_path, (x0,y0,x1,y1) src px)] → {(path, crop): [{'text', 'box' (src px)}]}"""
    CACHE.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    todo = []
    for path, crop in dict.fromkeys(jobs):
        if _ckey(path, crop).exists():
            continue
        t = TMP / f"c{len(todo):05d}.png"
        with Image.open(path) as im:
            im.convert("RGB").crop(crop).save(t)
        todo.append((path, crop, t, (crop[0], crop[1])))
    if todo:
        print(f"[ring] OCR {len(todo)} crops ({workers} workers)", flush=True)
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(_ocr_batch, [todo[i:i + 16] for i in range(0, len(todo), 16)]))
    shutil.rmtree(TMP, ignore_errors=True)
    return {(p, c): json.loads(_ckey(p, c).read_text()) for p, c in dict.fromkeys(jobs)}


# ------------------------------------------------------------------ glyph-ink blobs inside an OCR line box
_IMG: dict[str, np.ndarray] = {}


def _lum(path: str) -> np.ndarray:
    if path not in _IMG:
        if len(_IMG) > 48:
            _IMG.clear()
        a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
        _IMG[path] = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    return _IMG[path]


def _runs(v: np.ndarray, min_gap: int):
    idx = np.where(v)[0]
    if not len(idx):
        return []
    out, s, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > min_gap:
            out.append((s, prev + 1))
            s = i
        prev = i
    out.append((s, prev + 1))
    return out


def ink_blobs(path: str, box, cursor_rects=None, css: float = 1.0):
    """Word/row blobs (src px x0,y0,x1,y1) of high-contrast glyph ink inside an OCR box (cursor rects masked)."""
    L = _lum(path)
    x, y, w, h = box
    X0, Y0 = max(0, int(x) - 1), max(0, int(y) - 1)
    X1, Y1 = min(L.shape[1], int(np.ceil(x + w)) + 1), min(L.shape[0], int(np.ceil(y + h)) + 1)
    reg = L[Y0:Y1, X0:X1]
    if reg.size == 0:
        return []
    hist = np.bincount(np.clip(reg, 0, 255).astype(np.int32).ravel() // 4, minlength=64)
    bg = hist.argmax() * 4 + 2
    m = np.abs(reg - bg) > LUM_T
    if cursor_rects and not isinstance(cursor_rects[0], (list, tuple)):
        cursor_rects = [cursor_rects]
    for cr in cursor_rects or []:
        cx0, cy0, cx1, cy1 = (int(round(v)) for v in cr)
        m[max(0, cy0 - Y0):max(0, cy1 - Y0), max(0, cx0 - X0):max(0, cx1 - X0)] = False
    blobs = []
    for r0, r1 in _runs(m.any(axis=1), max(1, int(round(1.5 * css)))):
        for c0, c1 in _runs(m[r0:r1].any(axis=0), max(3, int(round(6 * css)))):
            sub = m[r0:r1, c0:c1]
            rr = np.where(sub.any(axis=1))[0]
            blobs.append((X0 + c0, Y0 + r0 + rr[0], X0 + c1, Y0 + r0 + rr[-1] + 1))
    return blobs


def _inter(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def band_depth(B, outer, inner) -> float:
    """How far (output px) the ring band (outer minus inner rect) reaches into blob B."""
    if not _inter(B, outer):
        return 0.0
    if B[0] >= inner[0] and B[1] >= inner[1] and B[2] <= inner[2] and B[3] <= inner[3]:
        return 0.0
    d = 0.0
    if B[0] < outer[2] and B[2] > outer[0]:
        for lo, hi in ((outer[1], inner[1]), (inner[3], outer[3])):
            a, b = max(B[1], lo), min(B[3], hi)
            if b > a:
                d = max(d, b - a)
    if B[1] < outer[3] and B[3] > outer[1]:
        for lo, hi in ((outer[0], inner[0]), (inner[2], outer[2])):
            a, b = max(B[0], lo), min(B[2], hi)
            if b > a:
                d = max(d, b - a)
    return d


# ------------------------------------------------------------------ audit
def audit_script(path: Path, out_root: Path, workers: int, min_depth: float = 0.75) -> list[dict]:
    script = json.loads(path.read_text(encoding="utf-8"))
    plan = build_plan(script)
    compositor.init_worker(plan)
    W, H, fps = compositor.W, compositor.H, plan["fps"]
    recs: dict[str, Recording] = {}
    samples = []
    for seg in plan["segments"]:
        if seg.get("type") != "screen":
            continue
        rid = seg.get("debug", {}).get("rec")
        if rid and rid not in recs:
            recs[rid] = Recording.load(rid)
        for ci, c in enumerate(seg.get("callouts", [])):
            a, b = c["t0"] + 0.45, c["t1"] - 0.35
            if b <= a:
                a = b = (c["t0"] + c["t1"]) / 2
            for q in (0.0, 0.5, 1.0):
                lf = min(seg["n_f"] - 1, max(0, int(round((a + (b - a) * q) * fps))))
                S, tx, ty = (float(v) for v in seg["cam"][lf])
                dx, dy, vis = compositor.callout_offset(c, lf)
                bx, by, bw, bh = c["box"]
                R = [S * (bx + dx) + tx, S * (by + dy) + ty, S * (bx + dx + bw) + tx, S * (by + dy + bh) + ty]
                src = str(seg["files"][int(seg["fidx"][lf])])
                sw, sh = seg["src_size"]
                m = 60.0
                crop = (int(max(0, (R[0] - STROKE_OUT - tx) / S - m)), int(max(0, (R[1] - STROKE_OUT - ty) / S - m)),
                        int(min(sw, (R[2] + STROKE_OUT - tx) / S + m)), int(min(sh, (R[3] + STROKE_OUT - ty) / S + m)))
                samples.append({"seg": seg, "ci": ci, "c": c, "q": q, "lf": lf, "S": S, "tx": tx, "ty": ty,
                                "vis": float(vis), "R": R, "src": src, "crop": crop, "rid": rid})
    O = ocr_crops([(s["src"], s["crop"]) for s in samples], workers)
    rows: dict[tuple, dict] = {}
    for s in samples:
        seg, c, S, tx, ty = s["seg"], s["c"], s["S"], s["tx"], s["ty"]
        X0, Y0, X1, Y1 = s["R"]
        clamped = [n for n, v in (("left", X0 < 4), ("top", Y0 < 4), ("right", X1 > W - 4), ("bottom", Y1 > H - 4)) if v]
        X0, Y0, X1, Y1 = max(X0, 4.0), max(Y0, 4.0), min(X1, W - 4.0), min(Y1, H - 4.0)
        outer = (X0 - STROKE_OUT, Y0 - STROKE_OUT, X1 + STROKE_OUT, Y1 + STROKE_OUT)
        inner = (X0 + STROKE_IN, Y0 + STROKE_IN, X1 - STROKE_IN, Y1 - STROKE_IN)
        css = seg["src_size"][0] / 1440.0
        rec = recs.get(s["rid"])
        curs = []
        if rec is not None:
            rt = float(seg["rec_t"][s["lf"]])
            tips = [rec.cursor_at(rt)]
            nxt = None                    # the demo cursor already travels to / rests on the next click/hover target
            for e in rec.events:
                if e.get("kind") in ("click", "hover") and e.get("box") and rt < e["rt"] <= rt + 1.5:
                    if nxt is None or e["rt"] < nxt["rt"]:
                        nxt = e
            if nxt is not None:
                b = rec.box_frame(nxt)
                tips.append((b[0] + b[2] / 2, b[1] + b[3] / 2))
            curs = [(t[0] - 7 * css, t[1] - 5 * css, t[0] + 27 * css, t[1] + 31 * css) for t in tips if t is not None]
        crossings, near_cursor = [], []
        for o in O[(s["src"], s["crop"])]:
            bx, by, bw, bh = o["box"]
            Lo = (S * bx + tx, S * by + ty, S * (bx + bw) + tx, S * (by + bh) + ty)
            if not _inter(Lo, outer):
                continue
            for Bs in ink_blobs(s["src"], o["box"], curs, css):
                B = (S * Bs[0] + tx, S * Bs[1] + ty, S * Bs[2] + tx, S * Bs[3] + ty)
                d = band_depth(B, outer, inner)
                if d <= min_depth:
                    continue
                ins = _inter(B, inner)
                frac = 0.0 if not ins else (ins[2] - ins[0]) * (ins[3] - ins[1]) / max(1.0, (B[2] - B[0]) * (B[3] - B[1]))
                rec_x = {"text": o["text"][:60], "depth_px": round(d, 1), "inside": round(frac, 2),
                         "blob_out": [round(v) for v in B], "kind": "cuts target text" if frac >= 0.5 else "crosses neighbour text"}
                near = any(_inter((c0 - 6 * css, c1 - 6 * css, c2 + 6 * css, c3 + 6 * css), Bs) for c0, c1, c2, c3 in curs)
                (near_cursor if near else crossings).append(rec_x)
        cap = []
        T = (seg["start_f"] + s["lf"]) / fps
        for cu in plan.get("cues", []):
            if cu["t0"] <= T < cu["t1"]:
                spr = cu["sprite"]
                px, py = (W - spr["w"]) / 2, H - 40 - spr["h"]
                bxm, bym, bwc, bhc = spr.get("body", (0, 0, spr["w"], spr["h"]))
                ov = _inter((px + bxm, py + bym, px + bxm + bwc, py + bym + bhc), outer)
                if ov:
                    cap.append([round(v) for v in ov])
        key = (seg["index"], s["ci"])
        r = rows.setdefault(key, {"seg": seg["index"], "n": s["ci"], "text": c.get("text", ""), "samples": []})
        r["samples"].append({"q": s["q"], "t": round(T, 2), "f": seg["start_f"] + s["lf"], "ring": [round(v) for v in (X0, Y0, X1, Y1)],
                             "vis": round(s["vis"], 2), "clamped": clamped, "caption": cap, "crossings": crossings,
                             "near_cursor": near_cursor, "src": s["src"]})
    out = out_root / plan["id"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        if old.is_file():
            old.unlink()
    result = []
    for key in sorted(rows):
        r = rows[key]
        reasons, warns = [], []
        for sm in r["samples"]:
            if sm["clamped"]:
                reasons.append(f"t={sm['t']} ring clamped at frame edge {sm['clamped']}")
            if sm["caption"]:
                reasons.append(f"t={sm['t']} ring under caption {sm['caption'][0]}")
            for x in sm["crossings"]:
                reasons.append(f"t={sm['t']} {x['kind']} «{x['text'][:28]}» {x['depth_px']}px")
            for x in sm["near_cursor"]:
                warns.append(f"t={sm['t']} next to demo cursor «{x['text'][:28]}» {x['depth_px']}px")
            if sm["vis"] < 0.3:
                warns.append(f"t={sm['t']} ring hidden by tracker (vis {sm['vis']})")
        r["verdict"] = "FAIL" if reasons else "WARN" if warns else "PASS"
        r["reasons"] = list(dict.fromkeys(reasons))[:6]
        r["warnings"] = list(dict.fromkeys(warns))[:4]
        result.append(r)
    (out / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    _sheets([r for r in result if r["verdict"] != "PASS"], out)
    return result


def _sheets(bad: list[dict], out: Path, tile_w: int = 620, crop_h: int = 330, per: int = 6):
    tiles = []
    f_hdr, f_lab = font(17), font(15)
    for r in bad:
        sm = max(r["samples"], key=lambda s: (len(s["crossings"]) + 3 * bool(s["clamped"]) + 2 * bool(s["caption"]),
                                              -abs(s["q"] - 0.5)))
        frame = compositor.render_frame(int(sm["f"]))
        X0, Y0, X1, Y1 = sm["ring"]
        cw = max((X1 - X0) * 1.6, 560.0)
        ch = cw * crop_h / tile_w
        if (Y1 - Y0) + 150 > ch:
            ch = (Y1 - Y0) + 150
            cw = ch * tile_w / crop_h
        cw, ch = min(cw, frame.shape[1]), min(ch, frame.shape[0])
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
        x0 = int(min(max(0, cx - cw / 2), frame.shape[1] - cw))
        y0 = int(min(max(0, cy - ch / 2), frame.shape[0] - ch))
        img = Image.fromarray(frame[y0:y0 + int(ch), x0:x0 + int(cw), ::-1].copy())
        d = ImageDraw.Draw(img)
        for x in sm["crossings"] + sm["near_cursor"]:
            bx0, by0, bx1, by1 = x["blob_out"]
            d.rectangle([bx0 - x0 - 2, by0 - y0 - 2, bx1 - x0 + 2, by1 - y0 + 2], outline=(255, 40, 40), width=2)
        img = img.resize((tile_w, crop_h), Image.LANCZOS)
        tile = Image.new("RGB", (tile_w, crop_h + 52), (255, 255, 255))
        tile.paste(img, (0, 52))
        d = ImageDraw.Draw(tile)
        col = (200, 30, 30) if r["verdict"] == "FAIL" else (190, 120, 0)
        d.text((8, 4), f"seg{r['seg']} #{r['n']} t={sm['t']}s {r['verdict']}  «{r['text']}»"[:66], fill=(50, 50, 50), font=f_hdr)
        d.text((8, 27), ((r["reasons"] or r["warnings"]) or [""])[0][:72], fill=col, font=f_lab)
        tiles.append(tile)
    for i in range(0, len(tiles), per):
        chunk = tiles[i:i + per]
        rows_n = (len(chunk) + 1) // 2
        th = chunk[0].height
        sheet = Image.new("RGB", (2 * tile_w + 12, rows_n * (th + 8) + 4), (225, 228, 233))
        for n, t in enumerate(chunk):
            sheet.paste(t, (4 + (n % 2) * (tile_w + 4), 4 + (n // 2) * (th + 8)))
        sheet.save(out / f"fail_{i // per + 1:02d}.jpg", quality=80)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("scripts", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--min-depth", type=float, default=0.75, help="output px of glyph crossed before it counts")
    a = ap.parse_args()
    any_fail = False
    for p in a.scripts:
        res = audit_script(p, a.out, a.workers, a.min_depth)
        n_f = sum(r["verdict"] == "FAIL" for r in res)
        n_w = sum(r["verdict"] == "WARN" for r in res)
        any_fail |= n_f > 0
        sid = json.loads(p.read_text(encoding="utf-8"))["id"]
        print(f"{p.name}: {len(res)} callouts — {n_f} FAIL, {n_w} WARN → {a.out / sid}")
        for r in res:
            if r["verdict"] != "PASS":
                print(f"   {r['verdict']} seg{r['seg']} #{r['n']} «{r['text'][:48]}»: " + "; ".join((r["reasons"] or r["warnings"])[:3]))
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
