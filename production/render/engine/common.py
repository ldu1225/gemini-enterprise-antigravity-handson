"""Shared paths, constants, easing curves, colour helpers and robust WAV I/O."""
from __future__ import annotations
import os

import hashlib
import io
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

RENDER_DIR = Path(__file__).resolve().parents[1]          # production/render
ROOT = RENDER_DIR.parents[1]                              # repo root
RECS_DIR = ROOT / "production" / "assets" / "recordings"
FONTS_DIR = RENDER_DIR / "fonts"
CACHE_DIR = RENDER_DIR / "cache"
OUT_DIR = RENDER_DIR / "out"
SITE_VIDEO_DIR = ROOT / "site" / "assets" / "video"

W, H = 1920, 1080
CAPTURE_CSS_W = 1440          # ge.py viewport width in CSS px (frames are 1920 px wide -> x4/3)
DEFAULT_VOICE = "Kore"
GCP_PROJECT = os.environ.get("TTS_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")  # TTS / Lyria quota project

# Design tokens (DESIGN.md)
INK_DARK = "#0B0F17"
GEMINI = ["#4285F4", "#9B72CB", "#D96570"]
ACCENT_RED = "#A50034"


def log(*a):
    print("[render]", *a, file=sys.stderr, flush=True)


def sha(obj) -> str:
    return hashlib.sha1(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


# ----------------------------------------------------------------- easing
def clamp01(x: float) -> float:
    return 0.0 if x <= 0 else 1.0 if x >= 1 else float(x)


def ease_in_out_cubic(p: float) -> float:
    p = clamp01(p)
    return 4 * p * p * p if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out_cubic(p: float) -> float:
    p = clamp01(p)
    return 1 - (1 - p) ** 3


def ease_in_cubic(p: float) -> float:
    p = clamp01(p)
    return p ** 3


def ease_out_quint(p: float) -> float:
    p = clamp01(p)
    return 1 - (1 - p) ** 5


def ease_out_back(p: float, s: float = 1.2) -> float:
    p = clamp01(p)
    c3 = s + 1
    return 1 + c3 * (p - 1) ** 3 + s * (p - 1) ** 2


def smoothstep(e0: float, e1: float, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------- colour
def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_bgr(h: str) -> tuple[int, int, int]:
    r, g, b = hex_rgb(h)
    return b, g, r


def gemini_gradient(n: int, stops=None) -> np.ndarray:
    """(n,3) float32 RGB 0..255 sampled along the Gemini gradient (#4285F4 -> #9B72CB @55% -> #D96570)."""
    stops = stops or [(0.0, GEMINI[0]), (0.55, GEMINI[1]), (1.0, GEMINI[2])]
    xs = np.linspace(0, 1, max(n, 2), dtype=np.float32)
    out = np.zeros((len(xs), 3), np.float32)
    pos = [s[0] for s in stops]
    cols = np.array([hex_rgb(s[1]) for s in stops], np.float32)
    for c in range(3):
        out[:, c] = np.interp(xs, pos, cols[:, c])
    return out[:n]


# ----------------------------------------------------------------- WAV I/O
def read_wav(src) -> tuple[np.ndarray, int]:
    """Robust PCM WAV reader -> (float32 array shaped (n, ch), sample_rate).

    Tolerates bogus RIFF/data sizes (Lyria returns a data chunk size larger than the payload).
    """
    b = Path(src).read_bytes() if not isinstance(src, (bytes, bytearray)) else bytes(src)
    if b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    i, fmt, data = 12, None, None
    while i + 8 <= len(b):
        cid, size = b[i:i + 4], struct.unpack("<I", b[i + 4:i + 8])[0]
        body = b[i + 8:i + 8 + size]
        if cid == b"fmt ":
            fmt = struct.unpack("<HHIIHH", body[:16])
        elif cid == b"data":
            data = body  # slicing clamps automatically if size is bogus
            break
        i += 8 + size + (size & 1)
    if fmt is None or data is None:
        raise ValueError("missing fmt/data chunk")
    tag, ch, sr, _, _, bits = fmt
    if bits == 16:
        x = np.frombuffer(data[: len(data) // (2 * ch) * 2 * ch], np.int16).astype(np.float32) / 32768.0
    elif bits == 32 and tag == 3:
        x = np.frombuffer(data[: len(data) // (4 * ch) * 4 * ch], np.float32).copy()
    elif bits == 32:
        x = np.frombuffer(data[: len(data) // (4 * ch) * 4 * ch], np.int32).astype(np.float32) / 2147483648.0
    elif bits == 24:
        n = len(data) // (3 * ch) * 3 * ch
        a = np.frombuffer(data[:n], np.uint8).reshape(-1, 3)
        v = (a[:, 0].astype(np.int32) | (a[:, 1].astype(np.int32) << 8) | (a[:, 2].astype(np.int32) << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        x = v.astype(np.float32) / float(1 << 23)
    else:
        raise ValueError(f"unsupported WAV format bits={bits} tag={tag}")
    return x.reshape(-1, ch), sr


def write_wav(path, x: np.ndarray, sr: int):
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        x = x[:, None]
    pcm = (np.clip(x, -1, 1) * 32767.0).round().astype("<i2")
    ch = pcm.shape[1]
    payload = pcm.tobytes()
    hdr = b"RIFF" + struct.pack("<I", 36 + len(payload)) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, ch, sr, sr * ch * 2, ch * 2, 16)
    hdr += b"data" + struct.pack("<I", len(payload))
    Path(path).write_bytes(hdr + payload)


def fmt_ts(t: float, vtt=True) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}" if vtt else f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
