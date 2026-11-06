#!/usr/bin/env python3
"""Zoomed proof image of one or more callout boxes on a screenshot (for verifying a fix by eye).

    python3 production/qa/proof.py ge_4_13_image_full 470,330,720,70 --box 480,344,700,46 --box 477,347,704,38 --out /tmp/p.jpg
Region and boxes are CSS px. Output ≤ 1280 px wide.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from callout_audit import find_src, font  # noqa: E402

COLORS = [(255, 0, 170), (0, 170, 255), (20, 170, 60), (255, 140, 0)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stem")
    ap.add_argument("region", help="x,y,w,h CSS px")
    ap.add_argument("--box", action="append", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = find_src(a.stem)
    im = Image.open(src).convert("RGB")
    dpr = 2 if im.width >= 2400 else 1
    x, y, w, h = (float(v) for v in a.region.split(","))
    crop = im.crop((round(x * dpr), round(y * dpr), round((x + w) * dpr), round((y + h) * dpr)))
    k = min(1280 / crop.width, 900 / crop.height, 2.0)
    crop = crop.resize((round(crop.width * k), round(crop.height * k)), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    s = k * dpr
    for i, b in enumerate(a.box):
        bx, by, bw, bh = (float(v) for v in b.split(","))
        c = COLORS[i % len(COLORS)]
        d.rectangle([(bx - x) * s, (by - y) * s, (bx - x + bw) * s, (by - y + bh) * s], outline=c, width=3)
        d.text(((bx - x) * s + 4, (by - y) * s + 2), str(i + 1), fill=c, font=font(18))
    crop.save(a.out, quality=80)
    print(a.out, crop.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
