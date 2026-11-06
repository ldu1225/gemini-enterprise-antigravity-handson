#!/usr/bin/env python3
"""English/number OCR of recording frames (tesseract, eng only) -> words with CSS-px boxes. Text only.

    python3 -u production/render/tools/ocr.py s1c_tour@27.8 [--crop x,y,w,h] [--min-conf 55] [--lines]
"""
from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from engine.recording import Recording  # noqa: E402


def ocr(rid: str, t: float, crop=None, min_conf=55.0, lines=False):
    rec = Recording.load(rid)
    img = cv2.imread(str(rec.files[int(rec.frame_index(t))]))
    s = img.shape[1] / (rec.size[0] / rec.css_scale)      # frames may switch resolution mid-recording
    ox = oy = 0
    if crop:
        x, y, w, h = [int(v * s) for v in crop]
        img = img[y:y + h, x:x + w]
        ox, oy = x, y
    k = 2.0
    big = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    ok, png = cv2.imencode(".png", big)
    p = subprocess.run(["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "11", "tsv"],
                       input=png.tobytes(), capture_output=True)
    rows = list(csv.DictReader(io.StringIO(p.stdout.decode("utf-8", "replace")), delimiter="\t"))
    words = []
    for r in rows:
        try:
            conf = float(r["conf"])
        except (TypeError, ValueError):
            continue
        txt = (r.get("text") or "").strip()
        if conf < min_conf or not txt:
            continue
        x = (int(r["left"]) / k + ox) / s
        y = (int(r["top"]) / k + oy) / s
        w = int(r["width"]) / k / s
        h = int(r["height"]) / k / s
        words.append((y, x, w, h, txt, conf, (r["block_num"], r["par_num"], r["line_num"])))
    words.sort()
    print(f"--- {rid} @ {t:.2f}s ({len(words)} words, conf>={min_conf})")
    if lines:
        groups = {}
        for y, x, w, h, txt, conf, key in words:
            groups.setdefault(key, []).append((x, y, w, h, txt))
        for key, ws in sorted(groups.items(), key=lambda kv: (min(v[1] for v in kv[1]), min(v[0] for v in kv[1]))):
            ws.sort()
            x0 = min(v[0] for v in ws)
            y0 = min(v[1] for v in ws)
            x1 = max(v[0] + v[2] for v in ws)
            y1 = max(v[1] + v[3] for v in ws)
            print(f"  [{x0:5.0f},{y0:4.0f},{x1 - x0:4.0f},{y1 - y0:3.0f}] {' '.join(v[4] for v in ws)}")
    else:
        for y, x, w, h, txt, conf, _ in words:
            print(f"  [{x:5.0f},{y:4.0f},{w:4.0f},{h:3.0f}] {conf:3.0f} {txt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--crop")
    ap.add_argument("--min-conf", type=float, default=55.0)
    ap.add_argument("--lines", action="store_true")
    a = ap.parse_args()
    crop = [float(v) for v in a.crop.split(",")] if a.crop else None
    for s in a.specs:
        rid, ts = s.split("@")
        for t in ts.split(","):
            ocr(rid, float(t), crop, a.min_conf, a.lines)


if __name__ == "__main__":
    main()
