#!/usr/bin/env python3
"""Text-only change detector: mean abs diff of CSS-px regions vs a reference time.

    python3 -u production/render/tools/regiondiff.py s6a_skill_upload --ref 11.0 \
        --t 11.2:16.9:0.5 --box toast=8,754,345,48 --box dialog=440,190,590,430
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.recording import Recording  # noqa: E402


def crop(img, box, s):
    x, y, w, h = [int(v * s) for v in box]
    return img[y:y + h, x:x + w].astype(np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rec")
    ap.add_argument("--ref", type=float, required=True)
    ap.add_argument("--t", required=True, help="a:b:step")
    ap.add_argument("--box", action="append", required=True, help="name=x,y,w,h (CSS px)")
    a = ap.parse_args()
    rec = Recording.load(a.rec)
    css_w = rec.size[0] / rec.css_scale
    boxes = []
    for b in a.box:
        n, v = b.split("=")
        boxes.append((n, [float(x) for x in v.split(",")]))

    def frame(t):
        img = cv2.imread(str(rec.files[int(rec.frame_index(t))]))
        return img, img.shape[1] / css_w

    ref, rs = frame(a.ref)
    t0, t1, st = [float(x) for x in a.t.split(":")]
    print("t      " + "  ".join(f"{n:>10}" for n, _ in boxes))
    t = t0
    while t <= t1 + 1e-6:
        img, s = frame(t)
        vals = []
        for _, bx in boxes:
            r = crop(ref, bx, rs)
            c = crop(img, bx, s)
            if r.shape != c.shape:
                c = cv2.resize(c.astype(np.uint8), (r.shape[1], r.shape[0])).astype(np.int16)
            vals.append(float(np.abs(r - c).mean()))
        print(f"{t:6.2f} " + "  ".join(f"{v:10.1f}" for v in vals))
        t += st


if __name__ == "__main__":
    main()
