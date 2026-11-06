#!/usr/bin/env python3
"""Text-only recording summary (no images): events in rec time, frame density, long gaps / static spans.

    python3 -u production/render/tools/rec_summary.py s1a_welcome [s1b_settings ...] [--gap 1.0]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from engine.recording import Recording  # noqa: E402


def summarize(rid: str, gap: float):
    rec = Recording.load(rid)
    t = rec.times
    print(f"=== {rid}: {len(t)} frames {rec.size[0]}x{rec.size[1]} css_scale={rec.css_scale:.3f} "
          f"dur={rec.duration:.2f}s")
    for e in rec.events:
        k = e.get("kind")
        extra = {kk: v for kk, v in e.items() if kk not in ("t", "wall", "rt", "kind", "idx", "box")}
        b = e.get("box")
        bs = f" box_css=[{b['x']:.0f},{b['y']:.0f},{b['width']:.0f},{b['height']:.0f}]" if isinstance(b, dict) else ""
        txt = json.dumps(extra, ensure_ascii=False)
        if len(txt) > 160:
            txt = txt[:160] + "…"
        print(f"  [{e['idx']:>2}] {e['rt']:8.2f}s {k:<11}{bs} {txt if extra else ''}")
    d = np.diff(t)
    big = np.nonzero(d >= gap)[0]
    if len(big):
        print(f"  repaint gaps >= {gap}s: " + ", ".join(f"{t[i]:.1f}-{t[i + 1]:.1f}({d[i]:.1f})" for i in big))
    # frame density per 10 s
    hist = np.histogram(t, bins=np.arange(0, rec.duration + 10, 10))[0]
    print("  frames/10s: " + " ".join(f"{int(h)}" for h in hist))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recs", nargs="+")
    ap.add_argument("--gap", type=float, default=1.0)
    a = ap.parse_args()
    for r in a.recs:
        summarize(r, a.gap)


if __name__ == "__main__":
    main()
