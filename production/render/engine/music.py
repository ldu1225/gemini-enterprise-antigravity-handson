"""Background music (Vertex AI Lyria, REST + gcloud token) and the final narration/music mix."""
from __future__ import annotations

import base64
import json
import re
import subprocess
from math import gcd
from pathlib import Path

import numpy as np

from .common import CACHE_DIR, GCP_PROJECT, log, read_wav, sha, write_wav
from .tts import post_json

LYRIA_URL = (f"https://us-central1-aiplatform.googleapis.com/v1/projects/{GCP_PROJECT}/locations/us-central1/"
             "publishers/google/models/lyria-002:predict")
DEFAULT_PROMPT = ("Calm, modern corporate ambient background music for a software tutorial. Soft warm analog synth "
                  "pads, gentle felt piano motifs, subtle airy textures, light soft pulse, optimistic and focused, "
                  "minimal, clean mix, 92 BPM, instrumental.")
DEFAULT_NEGATIVE = "vocals, singing, speech, harsh, distortion, loud drums, aggressive, dissonant"
MIX_SR = 48000


def get_music(prompt: str = DEFAULT_PROMPT, negative: str = DEFAULT_NEGATIVE, seed: int | None = None) -> Path | None:
    """Return a cached Lyria track (generated on first use). None if Lyria is unavailable."""
    d = CACHE_DIR / "music"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{sha(['lyria-002', prompt, negative, seed])}.wav"
    if path.exists():
        return path
    inst = {"prompt": prompt, "negative_prompt": negative}
    params = {}
    if seed is not None:
        inst["seed"] = int(seed)
    else:
        params["sample_count"] = 1
    try:
        log("generating background music with Lyria (lyria-002)...")
        resp = post_json(LYRIA_URL, {"instances": [inst], "parameters": params}, timeout=300, retries=2)
        pred = resp["predictions"][0]
        b64 = pred.get("bytesBase64Encoded") or pred.get("audioContent")
        x, sr = read_wav(base64.b64decode(b64))
        x = x[int(0.08 * sr):]                     # Lyria clips start with a click
        n = int(0.05 * sr)
        x[:n] *= np.linspace(0, 1, n, dtype=np.float32)[:, None]
        write_wav(path, x, sr)
        (path.with_suffix(".json")).write_text(json.dumps({"prompt": prompt, "negative": negative, "seed": seed,
                                                           "sr": sr, "dur": len(x) / sr}, ensure_ascii=False))
        log(f"music cached: {path.name} ({len(x) / sr:.1f}s)")
        return path
    except Exception as e:  # noqa: BLE001 - music is optional
        log(f"WARN: Lyria unavailable, rendering without music: {e}")
        return None


def _resample(x: np.ndarray, sr: int, to: int = MIX_SR) -> np.ndarray:
    if sr == to:
        return x
    from scipy.signal import resample_poly
    g = gcd(sr, to)
    return resample_poly(x, to // g, sr // g, axis=0).astype(np.float32)


def _rms_db(x: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(np.square(x, dtype=np.float64))) + 1e-9)


def _loop_to(m: np.ndarray, n: int, sr: int, xf: float = 3.0) -> np.ndarray:
    """Loop a music clip to n samples with equal-power crossfades."""
    tail_trim = int(0.6 * sr)          # skip the clip's very last decay
    body = m[: max(len(m) - tail_trim, int(sr * 4))]
    k = min(int(xf * sr), len(body) // 3)
    out = body.copy()
    th = np.linspace(0, np.pi / 2, k, dtype=np.float32)[:, None]
    fo, fi = np.cos(th), np.sin(th)
    while len(out) < n:
        seg = body.copy()
        out[-k:] = out[-k:] * fo + seg[:k] * fi
        out = np.concatenate([out, seg[k:]])
    return out[:n]


def _smooth(x: np.ndarray, win: int) -> np.ndarray:
    if win <= 1:
        return x
    c = np.cumsum(np.concatenate([[x[0]] * (win // 2), x, [x[-1]] * (win - win // 2)]), dtype=np.float64)
    return ((c[win:] - c[:-win]) / win)[: len(x)].astype(np.float32)


def build_mix(total: float, narration: list[tuple[float, str]], music: Path | None, bgm: dict) -> np.ndarray:
    """Mix narration clips (start_s, wav) + optional music bed with ducking. Returns (n, 2) float32 @48k."""
    sr = MIX_SR
    n = int(round(total * sr))
    voice = np.zeros(n, np.float32)
    spans = []
    for start, wav in narration:
        x, s = read_wav(wav)
        x = _resample(x.mean(axis=1), s, sr)
        a = int(round(start * sr))
        b = min(n, a + len(x))
        if a < n:
            voice[a:b] += x[: b - a]
            spans.append((start, start + len(x) / sr))
    mix = np.repeat(voice[:, None], 2, axis=1)
    if music is not None:
        m, msr = read_wav(music)
        if m.shape[1] == 1:
            m = np.repeat(m, 2, axis=1)
        m = _resample(m, msr, sr)
        m = _loop_to(m, n, sr)
        m_db = _rms_db(m)
        # voice level measured over active speech
        active_v = voice[np.abs(voice) > 1e-3]
        v_db = _rms_db(active_v) if len(active_v) > sr // 2 else -20.0
        duck_rel, bed_rel = float(bgm.get("duck_db", -22.0)), float(bgm.get("bed_db", -10.0))
        if not spans:
            v_db = -20.0
        g_duck = 10 ** ((v_db + duck_rel - m_db) / 20)
        g_bed = 10 ** ((v_db + bed_rel - m_db) / 20)
        # narration activity (merge short gaps so the bed does not pump between sentences)
        merged = []
        for a, b in sorted(spans):
            a, b = a - 0.18, b + 0.45
            if merged and a - merged[-1][1] < 1.4:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        target = np.full(n, g_bed, np.float32)
        for a, b in merged:
            target[max(0, int(a * sr)): min(n, int(b * sr))] = g_duck
        env = _smooth(_smooth(target, int(0.25 * sr)), int(0.25 * sr))
        fi, fo = int(float(bgm.get("fade_in", 1.5)) * sr), int(float(bgm.get("fade_out", 2.5)) * sr)
        env[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi, dtype=np.float32)) ** 2
        env[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo, dtype=np.float32)) ** 2
        mix += m * env[:, None]
        log(f"music bed: voice {v_db:.1f} dBFS, music {m_db:.1f} dBFS -> bed {bed_rel:+.0f} dB, duck {duck_rel:+.0f} dB")
    # final fade-out to match the picture
    k = int(0.8 * sr)
    if n > k:
        mix[-k:] *= np.linspace(1, 0, k, dtype=np.float32)[:, None]
    return mix


def loudnorm(src: Path, dst: Path, target_i: float = -16.0, tp: float = -1.5, lra: float = 11.0):
    """Two-pass EBU R128 loudness normalisation with ffmpeg (audio only, fast)."""
    flt = f"loudnorm=I={target_i}:TP={tp}:LRA={lra}"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", flt + ":print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if not m:
        log("WARN: loudnorm measurement failed; copying mix as-is")
        dst.write_bytes(src.read_bytes())
        return
    j = json.loads(m.group(0))
    flt2 = (f"{flt}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
            f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af", flt2,
                    "-ar", str(MIX_SR), "-ac", "2", "-c:a", "pcm_s16le", str(dst)], check=True)
    log(f"loudness: {float(j['input_i']):.1f} LUFS -> {target_i} LUFS")
