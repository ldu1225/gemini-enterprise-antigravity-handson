#!/usr/bin/env python3
"""Authoring helper: inspect a ge.py recording before writing an edit script.

    python3 production/render/inspect_rec.py s1a_welcome [--every 0.5]

Prints frame size, events (rec time + boxes in frame px and CSS px) and static (unchanging)
intervals, and writes a contact sheet to production/render/out/inspect_<id>.jpg with a
timestamp on every tile and click boxes outlined - use it to pick zoom/callout times and boxes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from engine.common import OUT_DIR  # noqa: E402
from engine.recording import Recording  # noqa: E402
from engine.typo import font  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rec")
    ap.add_argument("--every", type=float, default=0.5, help="seconds between contact-sheet tiles")
    ap.add_argument("--cols", type=int, default=5)
    a = ap.parse_args()
    rec = Recording.load(a.rec)
    print(rec.describe())
    times = list(np.arange(0, rec.duration + 1e-6, a.every))
    times += [e["rt"] for e in rec.events if e.get("kind") in ("click", "paste", "type_start", "type_end")]
    times = sorted(set(round(t, 2) for t in times))
    tw = 384
    th = int(tw * rec.size[1] / rec.size[0])
    tiles = []
    for t in times:
        img = cv2.imread(str(rec.files[int(rec.frame_index(t))]))
        sx = tw / rec.size[0]
        for e in rec.events:
            if e.get("box") and abs(e["rt"] - t) < 1.0:
                x, y, w, h = rec.box_frame(e)
                cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (80, 200, 255), 3)
        img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        ev = [e for e in rec.events if abs(e["rt"] - t) < 0.02 and e.get("kind") not in ("rec_start",)]
        label = f"{t:6.2f}s" + (f"  {ev[0]['kind']}:{ev[0].get('label', '')}" if ev else "")
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(pil)
        d.rectangle([0, 0, tw, 24], fill=(0, 0, 0))
        d.text((6, 3), label, font=font("semibold", 15), fill=(255, 255, 255))
        img = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
        tiles.append(img)
    while len(tiles) % a.cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + a.cols]) for i in range(0, len(tiles), a.cols)]
    sheet = np.vstack(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / f"inspect_{Path(a.rec).name}.jpg"
    cv2.imwrite(str(p), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"contact sheet: {p}")


if __name__ == "__main__":
    main()
