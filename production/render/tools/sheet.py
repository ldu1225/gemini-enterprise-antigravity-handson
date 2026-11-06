#!/usr/bin/env python3
"""Small, budget-friendly contact sheets (<= 1280 px wide, JPEG q<=70).

    python3 -u production/render/tools/sheet.py --out production/render/out/plan_lab1.jpg \
        --tile 320 --cols 4 s1a_welcome@1.9,9.0 s1b_settings@3.4,6.1
    # crop a CSS-px region of the 1440x810 viewport:  s2a_prompt_search@55.9[400,80,900,600]
    # rendered video frames:  --video site/assets/video/lab1.mp4@3,10,20

Each tile gets a "rid t" label; click/hover boxes within +-0.8 s are outlined (yellow).
A faint grid every 180 CSS px (x) / 135 CSS px (y) helps estimating coordinates (--grid to enable).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from engine.recording import Recording  # noqa: E402
from engine.typo import font  # noqa: E402

SPEC = re.compile(r"^(?P<rid>[^@]+)@(?P<times>[0-9.,]+)(?:\[(?P<crop>[0-9.,]+)\])?$")


def label(img: np.ndarray, text: str) -> np.ndarray:
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = font("semibold", 13)
    w = d.textlength(text, font=f)
    d.rectangle([0, 0, w + 10, 18], fill=(0, 0, 0))
    d.text((5, 2), text, font=f, fill=(255, 255, 0))
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)


def rec_tiles(spec: str, tile: int, grid: bool) -> list[np.ndarray]:
    m = SPEC.match(spec)
    if not m:
        raise SystemExit(f"bad spec {spec!r}")
    rec = Recording.load(m["rid"])
    crop = [float(v) for v in m["crop"].split(",")] if m["crop"] else None
    out = []
    for ts in m["times"].split(","):
        t = float(ts)
        img = cv2.imread(str(rec.files[int(rec.frame_index(t))]))
        s = img.shape[1] / (rec.size[0] / rec.css_scale)  # frames may switch resolution mid-recording
        for e in rec.events:
            if e.get("box") and e.get("kind") in ("click", "hover") and abs(e["rt"] - t) < 0.8:
                x, y, w, h = [v * s / rec.css_scale for v in rec.box_frame(e)]
                cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (0, 230, 255), 2)
        if grid:
            for gx in range(180, 1440, 180):
                cv2.line(img, (int(gx * s), 0), (int(gx * s), img.shape[0]), (255, 0, 255), 1)
            for gy in range(135, 810, 135):
                cv2.line(img, (0, int(gy * s)), (img.shape[1], int(gy * s)), (255, 0, 255), 1)
        if crop:
            x, y, w, h = [int(v * s) for v in crop]
            img = img[y:y + h, x:x + w]
        th = int(round(tile * img.shape[0] / img.shape[1]))
        img = cv2.resize(img, (tile, th), interpolation=cv2.INTER_AREA)
        out.append(label(img, f"{m['rid']} {t:.2f}" + (f" crop{crop}" if crop else "")))
    return out


def video_tiles(spec: str, tile: int) -> list[np.ndarray]:
    path, times = spec.rsplit("@", 1)
    out = []
    for ts in times.split(","):
        t = float(ts)
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                            "-vf", f"scale={tile}:-2:flags=area", "-f", "image2pipe", "-vcodec", "png", "-"],
                           capture_output=True)
        img = cv2.imdecode(np.frombuffer(p.stdout, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        out.append(label(img, f"{Path(path).stem} {t:.1f}s"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="*")
    ap.add_argument("--video", action="append", default=[])
    ap.add_argument("--images", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--tile", type=int, default=320)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--q", type=int, default=65)
    ap.add_argument("--grid", action="store_true")
    a = ap.parse_args()
    if a.tile * a.cols > 1280:
        raise SystemExit("sheet would exceed 1280 px")
    tiles = []
    for s in a.specs:
        tiles += rec_tiles(s, a.tile, a.grid)
    for v in a.video:
        tiles += video_tiles(v, a.tile)
    for p in a.images:
        img = cv2.imread(p)
        if img is None:
            continue
        img = cv2.resize(img, (a.tile, int(round(a.tile * img.shape[0] / img.shape[1]))), interpolation=cv2.INTER_AREA)
        tiles.append(label(img, Path(p).stem.replace("still_", "")))
    if not tiles:
        raise SystemExit("no tiles")
    th = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, th - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=0) for t in tiles]
    while len(tiles) % a.cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + a.cols]) for i in range(0, len(tiles), a.cols)]
    sheet = np.vstack(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(a.out, sheet, [cv2.IMWRITE_JPEG_QUALITY, min(a.q, 70)])
    print(f"{a.out}: {sheet.shape[1]}x{sheet.shape[0]} {Path(a.out).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
