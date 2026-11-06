#!/usr/bin/env python3
"""Render an edit script into a polished tutorial video.

    python3 production/render/render.py production/render/scripts/<id>.json
        -> site/assets/video/<id>.mp4  +  <id>.ko.vtt  +  <id>.jpg

Options:
    --dry-run            build the plan (TTS is synthesized/cached) and print the timeline only
    --stills 1.5,4,7.2   render only these timestamps (s) as PNGs into production/render/out/<id>/
    --stills-every 0.5   ...or a still every N seconds
    --fast               quick preview encode (x264 veryfast, crf 23)
    --no-bgm             disable background music
    --workers N          parallel frame renderers (default: cores-4, max 8)
    --out DIR            output directory (default site/assets/video)
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
import tempfile
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import compositor  # noqa: E402
from engine.common import H, OUT_DIR, ROOT, SITE_VIDEO_DIR, W, fmt_ts, log, write_wav  # noqa: E402
from engine.music import DEFAULT_NEGATIVE, DEFAULT_PROMPT, MIX_SR, build_mix, get_music, loudnorm  # noqa: E402
from engine.timeline import build_plan, describe  # noqa: E402


def write_vtt(plan: dict, path: Path):
    out = ["WEBVTT", "", f"NOTE {plan['title']}", ""]
    for i, c in enumerate(plan["cues"], 1):
        out += [str(i), f"{fmt_ts(c['t0'])} --> {fmt_ts(c['t1'])}", *c["lines"], ""]
    path.write_text("\n".join(out), encoding="utf-8")


def make_audio(plan: dict, tmp: Path, no_bgm: bool) -> Path:
    total = plan["total_f"] / plan["fps"]
    bgm = plan.get("bgm", True)
    music = None
    if bgm and not no_bgm:
        cfg = bgm if isinstance(bgm, dict) else {}
        music = get_music(cfg.get("prompt", DEFAULT_PROMPT), cfg.get("negative_prompt", DEFAULT_NEGATIVE),
                          cfg.get("seed"))
    cfg = bgm if isinstance(bgm, dict) else {}
    mix = build_mix(total, [(s, w) for s, w, _, _ in plan["narration"]], music, cfg)
    raw = tmp / "mix_raw.wav"
    write_wav(raw, mix, MIX_SR)
    final = tmp / "mix.wav"
    if plan["narration"] or music is not None:
        loudnorm(raw, final)
    else:
        final = raw
    return final


def encode(plan: dict, audio: Path, dst: Path, workers: int, fast: bool, tmp: Path, crf: float | None = None) -> float:
    fps, total_f = plan["fps"], plan["total_f"]
    plan_path = tmp / "plan.pkl"
    with open(plan_path, "wb") as f:
        pickle.dump(plan, f, protocol=pickle.HIGHEST_PROTOCOL)
    enc = plan.get("encode", {})
    preset = "veryfast" if fast else str(enc.get("preset", "slow"))
    crf = str(crf if crf is not None else (23 if fast else enc.get("crf", 24)))
    akbps = int(enc.get("audio_kbps", 160))
    part = dst.with_name(dst.stem + ".part.mp4")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
           "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd+full_chroma_int,format=yuv420p,"
                  "setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv",
           "-c:v", "libx264", "-preset", preset, "-crf", crf, "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-g", str(fps * 2), "-x264-params", "aq-mode=3",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
           "-c:a", "aac", "-b:a", f"{akbps}k", "-ar", "48000", "-ac", "2",
           "-t", f"{total_f / fps:.3f}", "-movflags", "+faststart", str(part)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    chunk = 8
    ranges = [(a, min(a + chunk, total_f)) for a in range(0, total_f, chunk)]
    t0 = time.time()
    done = 0
    try:
        with ProcessPoolExecutor(max_workers=workers, initializer=compositor.init_worker,
                                 initargs=(str(plan_path),)) as ex:
            it = iter(ranges)
            pending: deque = deque()
            for _ in range(workers * 2):
                r = next(it, None)
                if r is None:
                    break
                pending.append(ex.submit(compositor.render_chunk, r))
            last_report = time.time()
            while pending:
                data = pending.popleft().result()
                proc.stdin.write(data)
                done += len(data) // (W * H * 3)
                r = next(it, None)
                if r is not None:
                    pending.append(ex.submit(compositor.render_chunk, r))
                if time.time() - last_report > 5:
                    el = time.time() - t0
                    log(f"  {done}/{total_f} frames  {done / el:.1f} fps")
                    last_report = time.time()
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
    except BaseException:
        proc.kill()
        part.unlink(missing_ok=True)
        raise
    part.replace(dst)
    return time.time() - t0


def render_stills(plan: dict, times: list[float], outdir: Path) -> list[Path]:
    import cv2
    compositor.init_worker(plan)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for t in times:
        f = min(plan["total_f"] - 1, max(0, int(round(t * plan["fps"]))))
        img = compositor.render_frame(f)
        p = outdir / f"still_{t:07.3f}s_f{f:05d}.png"
        cv2.imwrite(str(p), img)
        paths.append(p)
    return paths


def callout_qa(plan: dict, outdir: Path) -> tuple[Path, list[dict]]:
    """Render 3 frames (in / middle / out) of every callout with the real compositor, write a contact sheet
    and a JSON report with the tracker's metrics. Returns (sheet path, report rows)."""
    import cv2
    import numpy as np
    from engine import callout_track
    compositor.init_worker(plan)
    outdir.mkdir(parents=True, exist_ok=True)
    fps = plan["fps"]
    rows, tiles = [], []
    for seg in plan["segments"]:
        if seg.get("type") != "screen":
            continue
        for ci, c in enumerate(seg.get("callouts", [])):
            s = callout_track.summarize(c, seg["src_size"])
            g0 = seg["start_f"] / fps
            times = [c["t0"] + 0.55, (c["t0"] + c["t1"]) / 2, max(c["t0"] + 0.6, c["t1"] - 0.4)]
            row = {"segment": seg["index"], "callout": ci, "text": c.get("text", ""),
                   "t_global": round(g0 + c["t0"], 2), **s}
            rows.append(row)
            strip = []
            clipped = False
            for tl in times:
                f = min(plan["total_f"] - 1, int(round((g0 + tl) * fps)))
                lf = min(seg["n_f"] - 1, max(0, f - seg["start_f"]))
                S, tx, ty = (float(v) for v in seg["cam"][lf])
                dx, dy, av = compositor.callout_offset(c, lf)
                bx, by, bw, bh = c["box"]
                X0, Y0 = S * (bx + dx) + tx, S * (by + dy) + ty
                X1, Y1 = X0 + S * bw, Y0 + S * bh
                if av > 0.5 and (X0 < 0 or Y0 < 0 or X1 > compositor.W or Y1 > compositor.H):
                    cut = (max(0, -X0) + max(0, X1 - compositor.W)) / max(1, X1 - X0) + \
                          (max(0, -Y0) + max(0, Y1 - compositor.H)) / max(1, Y1 - Y0)
                    clipped = clipped or cut > 0.06
                img = compositor.render_frame(f)
                strip.append(cv2.resize(img, (480, 270), interpolation=cv2.INTER_AREA))
            if clipped:
                s["problems"] = s.get("problems", []) + ["ring cut off by the frame edge at this zoom"]
                s["ok"] = False
                row.update(s)
            tile = np.concatenate(strip, axis=1)
            bar = np.full((34, tile.shape[1], 3), 255, np.uint8)
            color = (40, 150, 40) if s.get("ok", True) else (30, 30, 210)
            label = (f"seg{seg['index']} #{ci} @{row['t_global']:.1f}s  {s.get('mode')}  vis={s.get('vis_frac')} "
                     f"med={s.get('score_med')} drift={s.get('drift_px')}px  {'OK' if s.get('ok', True) else 'FAIL: ' + '; '.join(s['problems'])}")
            cv2.putText(bar, label[:150], (8, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
            tiles.append(np.concatenate([bar, tile], axis=0))
    sheet = outdir / f"{plan['id']}_callouts.jpg"
    if tiles:
        cv2.imwrite(str(sheet), np.concatenate(tiles, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 82])
    (outdir / f"{plan['id']}_callouts.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return sheet, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stills")
    ap.add_argument("--stills-every", type=float)
    ap.add_argument("--callout-qa", action="store_true", help="contact sheet + report of every highlight box")
    ap.add_argument("--strict-callouts", action="store_true", help="abort if any highlight box fails QA")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--workers", type=int, default=max(2, min(8, (os.cpu_count() or 6) - 4)))
    ap.add_argument("--out", default=str(SITE_VIDEO_DIR))
    a = ap.parse_args(argv)

    script_path = Path(a.script)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    if "id" not in script or not script.get("segments"):
        sys.exit("edit script needs 'id' and a non-empty 'segments' list")
    t_start = time.time()
    plan = build_plan(script)
    total = plan["total_f"] / plan["fps"]
    print(describe(plan), file=sys.stderr)
    log(f"plan ready in {time.time() - t_start:.1f}s")
    if a.dry_run:
        return
    if a.callout_qa or a.strict_callouts:
        sheet, rows = callout_qa(plan, OUT_DIR / plan["id"])
        bad = [r for r in rows if not r.get("ok", True)]
        log(f"callout QA: {len(rows)} callouts, {len(bad)} failing -> {sheet}")
        for r in bad:
            log(f"  FAIL seg{r['segment']} #{r['callout']} @{r['t_global']}s {r['text']!r}: {'; '.join(r['problems'])}")
        if a.callout_qa:
            print(sheet)
            return
        if bad:
            sys.exit("callout QA failed — fix the highlight anchors/boxes before rendering")
    if a.stills or a.stills_every:
        times = [float(x) for x in a.stills.split(",")] if a.stills else \
            [i * a.stills_every for i in range(int(total / a.stills_every) + 1)]
        outdir = OUT_DIR / plan["id"]
        for p in render_stills(plan, times, outdir):
            print(p)
        return

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4, vtt, jpg = out_dir / f"{plan['id']}.mp4", out_dir / f"{plan['id']}.ko.vtt", out_dir / f"{plan['id']}.jpg"
    with tempfile.TemporaryDirectory(prefix="render_", dir=str(OUT_DIR.parent / "cache")) as td:
        tmp = Path(td)
        t_a = time.time()
        audio = make_audio(plan, tmp, a.no_bgm)
        log(f"audio ready in {time.time() - t_a:.1f}s")
        enc = plan.get("encode", {})
        crf = float(enc.get("crf", 24))
        max_mb = float(enc.get("max_mb", 30))
        for attempt in range(3):
            log(f"rendering {plan['total_f']} frames with {a.workers} workers "
                f"({'fast' if a.fast else 'x264 ' + str(enc.get('preset', 'slow')) + f' crf{crf:g}'})")
            el = encode(plan, audio, mp4, a.workers, a.fast, tmp, None if a.fast else crf)
            mb = mp4.stat().st_size / 1e6
            log(f"mp4: {mb:.1f} MB ({mb * 8 / total:.2f} Mbit/s)")
            if a.fast or mb <= max_mb:
                break
            crf += 2
            log(f"over {max_mb:g} MB -> re-encoding with crf {crf:g}")
    write_vtt(plan, vtt)
    import cv2
    compositor.init_worker(plan)
    pf = min(plan["total_f"] - 1, int(round(plan["poster"] * plan["fps"])))
    cv2.imwrite(str(jpg), compositor.render_frame(pf), [cv2.IMWRITE_JPEG_QUALITY, 92])
    wall = time.time() - t_start
    log(f"video encode: {el:.1f}s for {total:.1f}s of video = {el / total:.2f}x realtime "
        f"({plan['total_f'] / el:.1f} fps); total wall {wall:.1f}s")
    for p in (mp4, vtt, jpg):
        print(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)
    if script.get("chapters"):
        sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
        import chapters as chap  # noqa: E402
        for p in chap.write(chap.compute(script, plan), out_dir):
            print(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)


if __name__ == "__main__":
    main()
