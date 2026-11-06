#!/usr/bin/env python3
"""Per-STEP chapters for a lab video, derived from its edit script (no re-render needed).

    python3 -u production/render/tools/chapters.py production/render/scripts/lab1.json [--out site/assets/video]

The edit script carries a "chapters" list mapping portal steps (content.py LABS[id]['steps'], 1-based) to
anchors in the timeline:  {"step": 2, "seg": 4, "say": 0}  -> start of sentence 0 of segment 4 (minus a 0.4 s
lead, never before the segment's visible start);  {"step": 1, "seg": 2} -> start of segment 2.
Writes <id>.chapters.json  {"video", "duration", "chapters": [{"step", "title", "start", "end"}]}  (step order)
and <id>.chapters.vtt (kind=chapters cues 'STEP n · title', time order).  end = next chapter start in time
order; the last chapter ends where the outro starts.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.common import ROOT, SITE_VIDEO_DIR, fmt_ts, log  # noqa: E402
from engine.timeline import build_plan  # noqa: E402


def content_steps(lab_id: str, track: str | None = None) -> list[str]:
    cdir = ROOT / "production" / "content"
    paths = [cdir / "v2" / f"{track}.py"] if track else [cdir / "content.py"]
    for path in paths:
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location(f"lab_content_{path.stem}", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for lab in getattr(m, "LABS", []):
            if lab["id"] == lab_id:
                return [s["title"] for s in lab["steps"]]
    raise SystemExit(f"{lab_id}: not found in content modules")


def compute(script: dict, plan: dict) -> dict:
    fps = plan["fps"]
    segs = plan["segments"]
    total = plan["total_f"] / fps
    titles = content_steps(script.get("lab", script["id"]), script.get("track"))
    specs = script.get("chapters") or []
    got = sorted(int(c["step"]) for c in specs)
    if got != list(range(1, len(titles) + 1)):
        raise SystemExit(f"{script['id']}: chapters must list every step 1..{len(titles)} exactly once (got {got})")
    starts = {}
    for c in specs:
        ps = segs[int(c["seg"])]
        seg0 = ps["start_f"] / fps
        visible = seg0 + 0.5 * ps.get("xf_in", 0) / fps
        t = visible
        if c.get("say") is not None:
            sents = ps["sentences"]
            k = int(c["say"])
            if not (0 <= k < len(sents)):
                raise SystemExit(f"{script['id']}: step {c['step']}: segment {c['seg']} has no sentence {k}")
            t = max(visible, seg0 + sents[k][0] - float(c.get("lead", 0.4)))
        t += float(c.get("offset", 0.0))
        starts[int(c["step"])] = round(t, 1)
    outro = next((p["start_f"] / fps + 0.5 * p.get("xf_in", 0) / fps for p in segs if p["type"] == "outro"), total)
    order = sorted(starts, key=lambda s: starts[s])
    ends = {}
    for i, s in enumerate(order):
        ends[s] = round(starts[order[i + 1]], 1) if i + 1 < len(order) else round(outro, 1)
    chapters = [{"step": s, "title": titles[s - 1], "start": starts[s], "end": ends[s]} for s in sorted(starts)]
    return {"video": f"{script['id']}.mp4", "duration": round(total, 2), "chapters": chapters}


def write(data: dict, out_dir: Path) -> tuple[Path, Path]:
    vid = data["video"][:-4]
    j = out_dir / f"{vid}.chapters.json"
    j.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["WEBVTT", "", f"NOTE chapters for {data['video']}", ""]
    for i, c in enumerate(sorted(data["chapters"], key=lambda c: c["start"]), 1):
        lines += [str(i), f"{fmt_ts(c['start'])} --> {fmt_ts(c['end'])}", f"STEP {c['step']} · {c['title']}", ""]
    v = out_dir / f"{vid}.chapters.vtt"
    v.write_text("\n".join(lines), encoding="utf-8")
    return j, v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", nargs="+")
    ap.add_argument("--out", default=str(SITE_VIDEO_DIR))
    a = ap.parse_args()
    for sp in a.scripts:
        script = json.loads(Path(sp).read_text(encoding="utf-8"))
        plan = build_plan(script)
        data = compute(script, plan)
        for p in write(data, Path(a.out)):
            log(f"wrote {p}")
        for c in data["chapters"]:
            print(f"  STEP {c['step']}: {c['start']:6.1f} -> {c['end']:6.1f}  {c['title']}")


if __name__ == "__main__":
    main()
