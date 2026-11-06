"""Rebuild every v2 sample file, then verify. Usage: cd production/samples/v2 && python3 build_all.py"""
from __future__ import annotations

import json
import subprocess
import sys

from common import KEYS, OUT, PREV, WORK

STEPS = [
    "build_xlsx.py",
    "build_travel_pdf.py",
    "build_leave_pdf.py",
    "build_it_pdf.py",
    "build_marketing_pdfs.py",
    "build_skill.py",
    "build_previews.py",
    "build_voc_starter.py",
    "build_voc_previews.py",
    "build_bundle.py",
    "write_answer_keys.py",
    "verify.py",
]

if __name__ == "__main__":
    for d in (OUT, PREV, WORK, KEYS):
        d.mkdir(parents=True, exist_ok=True)
    for s in STEPS:
        print(f"\n=== {s} ===", flush=True)
        r = subprocess.run([sys.executable, s], capture_output=True, text=True)
        out = r.stdout.strip()
        if s.startswith("build_") and s.endswith("_pdf.py") and out.startswith("{"):
            rep = json.loads(out)
            print("pages:", rep["paginate"]["pages"], "| log:", rep["paginate"]["log"],
                  "| fill%:", [o["fill"] for o in rep["overflow"]])
        else:
            print(out[-6000:])
        if r.returncode != 0:
            print(r.stderr[-4000:])
            sys.exit(f"step failed: {s}")
