"""Loads a ge.py screen recording (VFR CDP screencast frames + interaction events).

Recording time ("rec time") is seconds since the FIRST captured frame:
  * frame times  = frames.json ts - ts0
  * event times  = event.wall - ts0          (new recordings, same epoch clock as frames)
                 = event.t                   (older recordings without 'wall')
"""
from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .common import CAPTURE_CSS_W, RECS_DIR, log

STATIC_GAP = 0.20      # a gap between repaints longer than this is a "static" (unchanging) interval


def _jpeg_size(p: Path) -> tuple[int, int] | None:
    """(w, h) from the JPEG SOF marker without decoding the image."""
    try:
        with open(p, "rb") as f:
            d = f.read(65536)
    except OSError:
        return None
    i = 2
    while i + 9 < len(d):
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", d[i + 5:i + 9])
            return int(w), int(h)
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    return None


def _glitch_frames(path: Path, frames: list[dict], ts0: float, shots: list[float],
                   win: float = 1.0, max_run: int = 4, thr: float = 6.0) -> set[int]:
    """Indices of frames that form a short 'spike' near a shot: a run of <= max_run frames whose 96x54 grey
    thumbnail differs (> thr) from the frame before the run, while the frame after the run matches the one before."""
    t = np.array([f["ts"] - ts0 for f in frames])
    cache: dict[int, np.ndarray] = {}

    def th(k: int) -> np.ndarray | None:
        if k not in cache:
            im = cv2.imread(str(path / "frames" / frames[k]["file"]), cv2.IMREAD_GRAYSCALE)
            cache[k] = None if im is None else cv2.resize(im, (96, 54), interpolation=cv2.INTER_AREA).astype(np.float32)
        return cache[k]

    def diff(a: int, b: int) -> float:
        x, y = th(a), th(b)
        return 0.0 if x is None or y is None else float(np.abs(x - y).mean())

    bad: set[int] = set()
    for s in shots:
        idx = [k for k in np.nonzero((t >= s - win) & (t <= s + win))[0]]
        if len(idx) < 3:
            continue
        lo, hi = max(int(idx[0]) - 1, 0), min(int(idx[-1]) + 1, len(frames) - 1)
        k = lo + 1
        while k < hi:
            if k in bad or diff(k - 1, k) <= thr:
                k += 1
                continue
            for run in range(1, max_run + 1):          # frames k .. k+run-1 differ; k+run returns to k-1
                j = k + run
                if j > hi:
                    break
                if diff(k - 1, j) < thr / 3:
                    bad.update(range(k, j))
                    break
            k += 1
    return bad


@dataclass
class Recording:
    rid: str
    path: Path
    files: list[Path]
    times: np.ndarray            # rec time of each frame (s)
    events: list[dict]
    size: tuple[int, int]        # source frame (w, h)
    css_scale: float             # CSS px -> frame px
    duration: float
    _static: list = field(default_factory=list)

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, rid: str, base: Path = RECS_DIR) -> "Recording":
        path = Path(rid) if Path(rid).is_absolute() else base / rid
        fj = path / "frames.json"
        if not fj.exists():
            raise FileNotFoundError(f"recording '{rid}': {fj} not found")
        frames = json.loads(fj.read_text())
        if not frames:
            raise ValueError(f"recording '{rid}' has no frames")
        frames = sorted(frames, key=lambda f: f["ts"])
        ts_all0 = frames[0]["ts"]
        ts0 = ts_all0
        events = []
        ej = path / "events.json"
        if ej.exists():
            for i, e in enumerate(json.loads(ej.read_text())):
                e = dict(e)
                if e.get("wall") is not None:
                    e["rt"] = float(e["wall"]) - ts0
                elif e.get("t") is not None:
                    e["rt"] = float(e["t"])
                else:
                    continue
                e["idx"] = i
                events.append(e)
        # ge.py's hi-DPR screenshots make the screencast emit a few frames at another resolution (some with a
        # glitched layout) -> keep only frames with the recording's majority size.
        sizes = [_jpeg_size(path / "frames" / f["file"]) for f in frames]
        valid = [s for s in sizes if s]
        if valid:
            base = max(set(valid), key=valid.count)
            kept = [f for f, s in zip(frames, sizes) if s == base or s is None]
            if len(kept) < len(frames):
                log(f"{rid}: dropped {len(frames) - len(kept)} off-size frames (base {base[0]}x{base[1]})")
            frames = kept or frames
        # ...and same-size glitch frames around shots (a short run that differs from the frames on both sides)
        shots = [e["rt"] for e in events if e.get("kind") == "shot"]
        if shots:
            bad = _glitch_frames(path, frames, ts0, shots)
            if bad:
                log(f"{rid}: dropped {len(bad)} glitch frames near shots")
                frames = [f for k, f in enumerate(frames) if k not in bad]
        ts = np.array([f["ts"] for f in frames], np.float64)
        files = [path / "frames" / f["file"] for f in frames]
        img = cv2.imread(str(files[0]), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"cannot read {files[0]}")
        h, w = img.shape[:2]
        meta = {}
        mj = path / "meta.json"
        if mj.exists():
            meta = json.loads(mj.read_text())
        css_w = meta.get("css_width", CAPTURE_CSS_W)
        times = ts - ts0
        stop = [e["rt"] for e in events if e.get("kind") == "rec_stop"]
        duration = max(float(times[-1]), stop[-1] if stop else 0.0)
        rec = cls(rid=str(rid), path=path, files=files, times=times, events=events,
                  size=(w, h), css_scale=w / css_w, duration=duration)
        return rec

    # --------------------------------------------------------------- queries
    def frame_index(self, rt: np.ndarray | float):
        idx = np.searchsorted(self.times, np.asarray(rt) + 1e-6, side="right") - 1
        return np.clip(idx, 0, len(self.times) - 1)

    def static_intervals(self, r0: float, r1: float, gap: float = STATIC_GAP) -> list[tuple[float, float]]:
        """Intervals inside [r0, r1] during which the displayed frame does not change."""
        out = []
        t = self.times
        # (frame i displayed from t[i] until t[i+1]); keep 1 frame (33ms) of the change visible
        for i in range(len(t)):
            a = t[i] + 0.034
            b = t[i + 1] if i + 1 < len(t) else max(r1, t[i]) + 1e9
            if b - t[i] >= gap:
                lo, hi = max(a, r0), min(b, r1)
                if hi - lo > 0.02:
                    out.append((lo, hi))
        if r0 < t[0]:
            out.insert(0, (r0, min(t[0], r1)))
        return out

    def is_static(self, rt: float) -> bool:
        i = int(self.frame_index(rt))
        nxt = self.times[i + 1] if i + 1 < len(self.times) else 1e18
        return (nxt - self.times[i]) >= STATIC_GAP and rt >= self.times[i] + 0.034

    def box_frame(self, ev: dict) -> list[float] | None:
        b = ev.get("box")
        if not b:
            return None
        s = self.css_scale
        return [b["x"] * s, b["y"] * s, b["width"] * s, b["height"] * s]

    def cursor_at(self, rt: float, max_age: float = 20.0):
        """Demo-cursor tip (frame px) at rec time rt ≈ centre of the newest click/hover box at or before rt
        (capture scripts move the mouse to the element centre before hovering/clicking). None if unknown."""
        best = None
        for e in self.events:
            if e.get("kind") in ("click", "hover") and e.get("box") and e["rt"] <= rt + 0.05:
                if best is None or e["rt"] >= best["rt"]:
                    best = e
        if best is None or rt - best["rt"] > max_age:
            return None
        b = self.box_frame(best)
        return (b[0] + b[2] / 2, b[1] + b[3] / 2)

    # ------------------------------------------------------------ references
    _REF = re.compile(r"^\s*(?P<kind>[a-z_]+)(?::(?P<label>.*?))?(?:#(?P<n>\d+))?\s*(?P<off>[+-]\s*\d+(?:\.\d+)?)?\s*$")

    def resolve_event(self, ref, near: float | None = None, window: tuple[float, float] | None = None) -> dict | None:
        """Resolve an event reference.

        ref: "click" | "click:시작하기" | "click#2" | "type_start:prompt" | "event:3" (index in events.json)
             optional trailing offset "click:시작하기 -1.2" (seconds, rec time).  Also dict form
             {"event": "click", "label": "시작하기", "n": 1, "offset": -1.2}.
        Returns a copy of the event with 'rt' already offset.
        """
        if isinstance(ref, dict):
            kind, label, n, off = ref.get("event", "click"), ref.get("label"), ref.get("n"), float(ref.get("offset", 0))
        else:
            m = self._REF.match(str(ref))
            if not m:
                return None
            kind, label, n = m["kind"], m["label"], m["n"]
            off = float(m["off"].replace(" ", "")) if m["off"] else 0.0
        if kind == "event":
            i = int(label or n or 0)
            cands = [e for e in self.events if e["idx"] == i]
        else:
            cands = [e for e in self.events if e.get("kind") == kind]
            if label:
                exact = [e for e in cands if str(e.get("label", "")) == label]
                cands = exact or [e for e in cands if label in str(e.get("label", ""))]
        if not cands:
            return None
        if n:
            k = int(n) - 1
            ev = cands[k] if 0 <= k < len(cands) else None
        else:
            ev = None
            if window:
                inside = [e for e in cands if window[0] - 0.5 <= e["rt"] <= window[1] + 0.5]
                if inside:
                    ev = inside[0]
            if ev is None and near is not None:
                ev = min(cands, key=lambda e: abs(e["rt"] - near))
            if ev is None:
                ev = cands[0]
        if ev is None:
            return None
        ev = dict(ev)
        ev["rt"] = ev["rt"] + off
        return ev

    def resolve_time(self, v, near=None, window=None) -> float | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        ev = self.resolve_event(v, near=near, window=window)
        if ev is None:
            log(f"WARN: {self.rid}: cannot resolve time reference {v!r}")
            return None
        return ev["rt"]

    def resolve_box(self, v, near=None, window=None) -> list[float] | None:
        """[x,y,w,h] in frame px | 'auto:click' | 'click:<label>' | event ref with a box."""
        if v is None:
            return None
        if isinstance(v, (list, tuple)) and len(v) == 4:
            return [float(a) for a in v]
        s = str(v) if not isinstance(v, dict) else v
        if isinstance(s, str) and s.startswith("auto:"):
            s = s[5:]
        ev = self.resolve_event(s, near=near, window=window)
        if ev is None or not ev.get("box"):
            log(f"WARN: {self.rid}: cannot resolve box reference {v!r}")
            return None
        return self.box_frame(ev)

    def describe(self) -> str:
        lines = [f"recording {self.rid}: {len(self.files)} frames, {self.size[0]}x{self.size[1]}, "
                 f"duration {self.duration:.2f}s, css_scale {self.css_scale:.4f}"]
        for e in self.events:
            extra = {k: v for k, v in e.items() if k not in ("t", "wall", "rt", "kind", "idx")}
            if "box" in extra and extra["box"]:
                extra["box_frame"] = [round(a, 1) for a in self.box_frame(e)]
                extra.pop("box")
            lines.append(f"  [{e['idx']:>2}] {e['rt']:7.2f}s  {e['kind']:<10} {json.dumps(extra, ensure_ascii=False)}")
        st = self.static_intervals(0, self.duration)
        lines.append("  static (unchanging) intervals: " + ", ".join(f"{a:.2f}-{b:.2f}" for a, b in st))
        return "\n".join(lines)
