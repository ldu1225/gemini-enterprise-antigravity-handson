#!/usr/bin/env python3
"""Find exact CSS-px boxes of on-screen text in a screenshot (Apple Vision OCR) — use these to author callouts.

    python3 production/qa/find_text.py ge_5_01_dr_home "Deep Research" "새 에이전트"
    python3 production/qa/find_text.py ge_8_21_trigger_edited --all
Prints every OCR line that contains one of the needles (normalized, fuzzy) with its box in CSS px [x, y, w, h].
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from callout_audit import find_src, match_score, ocr  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    stem, needles = argv[0], argv[1:]
    src = find_src(stem) if not Path(stem).is_file() else Path(stem)
    if not src:
        print("not found:", stem)
        return 1
    with Image.open(src) as im:
        W, H = im.size
    dpr = 2 if W >= 2400 else 1
    show_all = "--all" in needles
    needles = [n for n in needles if n != "--all"]
    print(f"{src.name}  {W}x{H}  → CSS {round(W / dpr)}x{round(H / dpr)} (dpr {dpr})")
    for r in ocr(src):
        x, y, w, h = (v / dpr for v in r["box"])
        if show_all or any(match_score(n, r["text"]) >= 0.8 for n in needles):
            print(f"  [{x:6.1f}, {y:6.1f}, {w:6.1f}, {h:5.1f}]  conf={r['conf']:.2f}  {r['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
