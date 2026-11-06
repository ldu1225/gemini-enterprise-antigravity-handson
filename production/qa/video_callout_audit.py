#!/usr/bin/env python3
"""Semantic audit of every highlight ring (callout) in the tutorial videos.

render.py --strict-callouts proves a ring stays on the SAME pixels while it is shown (tracking), but not that
those pixels are the thing the chip names. This tool renders, for every callout, the real compositor frame the
viewer sees in the middle of the callout, crops around the ring at full resolution, OCRs the source frame inside
the box (Apple Vision, Korean + English) and compares it with the chip text. Every ring must be looked at on the
sheets before a video ships.

    python3 production/qa/video_callout_audit.py production/render/scripts/v2/ge4.json [more.json ...]
    → production/qa/out/video/<id>/report.json, sheet_*.jpg
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "production" / "render"))
sys.path.insert(0, str(HERE))

from callout_audit import font, match_score, ocr, prefetch  # noqa: E402
from engine import compositor  # noqa: E402
from engine.timeline import build_plan  # noqa: E402

OUT = ROOT / "production" / "qa" / "out" / "video"


def audit_script(path: Path, out_root: Path) -> list[dict]:
    script = json.loads(path.read_text(encoding="utf-8"))
    plan = build_plan(script)
    compositor.init_worker(plan)
    fps = plan["fps"]
    out = out_root / plan["id"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        old.unlink()
    rows, jobs = [], []
    for seg in plan["segments"]:
        if seg.get("type") != "screen":
            continue
        sw, sh = seg["src_size"]
        for ci, c in enumerate(seg.get("callouts", [])):
            tl = (c["t0"] + c["t1"]) / 2
            f = min(plan["total_f"] - 1, int(round(seg["start_f"] + tl * fps)))
            lf = min(seg["n_f"] - 1, max(0, f - seg["start_f"]))
            S, tx, ty = (float(v) for v in seg["cam"][lf])
            dx, dy, av = compositor.callout_offset(c, lf)
            bx, by, bw, bh = c["box"]
            ring = [S * (bx + dx) + tx, S * (by + dy) + ty, S * bw, S * bh]
            frame = compositor.render_frame(f)
            src = Path(seg["files"][int(seg["fidx"][lf])])
            box_src = [bx + dx, by + dy, bw, bh]
            jobs.append((src, box_src))
            rows.append({"seg": seg["index"], "n": ci, "text": c.get("text", ""), "t_global": round(f / fps, 2),
                         "ring": [round(v, 1) for v in ring], "visible": round(float(av), 2), "src": str(src),
                         "box_src": [round(v, 1) for v in box_src], "src_size": [sw, sh], "_frame": frame})
    prefetch(jobs)
    tiles = []
    f_hdr, f_lab = font(17), font(16)
    for r in rows:
        txt = " ".join(o["text"] for o in ocr(Path(r["src"]), r["box_src"]))
        r["ocr_in_box"] = txt[:160]
        r["score"] = match_score(r["text"], txt) if r["text"] else 1.0
        frame = r.pop("_frame")
        X, Y, Wr, Hr = r["ring"]
        # crop around the ring incl. its chip (chips sit ~60 px above/below the ring)
        cw = max(Wr * 1.8, 560.0)
        ch = cw * 330 / 620
        if Hr + 150 > ch:
            ch = Hr + 150
            cw = ch * 620 / 330
        cw, ch = min(cw, frame.shape[1]), min(ch, frame.shape[0])
        x0 = int(min(max(0, X + Wr / 2 - cw / 2), frame.shape[1] - cw))
        y0 = int(min(max(0, Y + Hr / 2 - ch / 2), frame.shape[0] - ch))
        crop = frame[y0:y0 + int(ch), x0:x0 + int(cw)]
        crop = cv2.cvtColor(cv2.resize(crop, (620, 330), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        tile = Image.new("RGB", (620, 330 + 52), (255, 255, 255))
        tile.paste(Image.fromarray(crop), (0, 52))
        d = ImageDraw.Draw(tile)
        ok = r["score"] >= 0.6 and r["visible"] > 0.5
        d.text((8, 4), f"{plan['id']} seg{r['seg']} #{r['n']} @{r['t_global']}s vis={r['visible']}", fill=(60, 60, 60), font=f_hdr)
        d.text((8, 27), f"«{r['text']}»  ocr={r['score']:.2f}"[:64], fill=(20, 130, 40) if ok else (200, 30, 30), font=f_lab)
        tiles.append(tile)
    for i in range(0, len(tiles), 6):
        chunk = tiles[i:i + 6]
        rows_n = (len(chunk) + 1) // 2
        sheet = Image.new("RGB", (2 * 620 + 12, rows_n * (382 + 8) + 4), (225, 228, 233))
        for n, t in enumerate(chunk):
            sheet.paste(t, (4 + (n % 2) * 624, 4 + (n // 2) * 390))
        sheet.save(out / f"sheet_{i // 6 + 1:02d}.jpg", quality=72)
    (out / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    for p in a.scripts:
        rows = audit_script(p, a.out)
        low = [r for r in rows if r["score"] < 0.6 or r["visible"] <= 0.5]
        print(f"{p.name}: {len(rows)} callouts, {len(low)} need a look → {a.out / p.stem}")
        for r in low:
            print(f"   seg{r['seg']} #{r['n']} @{r['t_global']}s «{r['text']}» score={r['score']} vis={r['visible']} in-box={r['ocr_in_box'][:60]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
