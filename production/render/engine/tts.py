"""Vertex AI gemini-3.8-flash-tts (REST + gcloud user token) with per-sentence caching and comma breath pauses."""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import voice as voice_mod
from .common import CACHE_DIR, DEFAULT_VOICE, GCP_PROJECT, log, read_wav, sha, write_wav

TTS_MODEL = "gemini-3.8-flash-tts"
TTS_URL = (
    f"https://aiplatform.googleapis.com/v1beta1/projects/{GCP_PROJECT}"
    f"/locations/global/publishers/google/models/{TTS_MODEL}:generateContent"
)
SR = 24000
_token_lock = threading.Lock()
_token: dict = {"value": None, "at": 0.0}


def normalize_voice(voice: str | None) -> str:
    """Map legacy Chirp3 voice names to focused Korean instructor voice on gemini-3.8-flash-tts."""
    if not voice or "Chirp3" in voice or voice in ("Despina", "Charon", "default"):
        return "Kore"
    return voice.split("-")[-1]


def gcloud_token(force: bool = False) -> str:
    with _token_lock:
        if force or not _token["value"] or time.time() - _token["at"] > 45 * 60:
            out = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, timeout=60)
            if out.returncode != 0 or not out.stdout.strip():
                raise RuntimeError("gcloud auth print-access-token failed: " + out.stderr.strip()[:300])
            _token.update(value=out.stdout.strip(), at=time.time())
        return _token["value"]


def post_json(url: str, body: dict, timeout: float = 120, retries: int = 5) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Authorization": f"Bearer {gcloud_token(force=attempt > 0 and isinstance(last, urllib.error.HTTPError) and last.code == 401)}",
            "X-Goog-User-Project": GCP_PROJECT,
            "Content-Type": "application/json; charset=utf-8",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            msg = e.read().decode("utf-8", "replace")[:500]
            if e.code in (400, 403, 404):
                raise RuntimeError(f"HTTP {e.code} from {url}: {msg}") from e
            log(f"HTTP {e.code} (attempt {attempt + 1}/{retries}): {msg[:200]}")
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            log(f"network error (attempt {attempt + 1}/{retries}): {e}")
        time.sleep(1.8 * (attempt + 1))
    raise RuntimeError(f"request to {url} failed: {last}")


# ------------------------------------------------------------------ sentences
_SENT = re.compile(r"(?<=[.!?。…])\s+")


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    return [s.strip() for s in _SENT.split(text) if s.strip()]


# ------------------------------------------------------------------ pronunciation lexicon
DEFAULT_LEXICON = Path(__file__).resolve().parents[1] / "lexicon.json"


def load_lexicon(spec=True) -> list[tuple[re.Pattern, str]]:
    """spec: True/None -> production/render/lexicon.json, False -> none, str path, or a dict."""
    if spec is False:
        return []
    if spec is None or spec is True:
        spec = DEFAULT_LEXICON
    if isinstance(spec, (str, Path)):
        p = Path(spec)
        if not p.is_absolute():
            p = Path(__file__).resolve().parents[3] / p
        spec = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    rules: list[tuple[re.Pattern, str]] = []
    lits = []
    for k, v in spec.items():
        if k.startswith("_"):
            continue
        if k.startswith("re:"):
            rules.append((re.compile(k[3:]), v))
        else:
            lits.append((k, v))
    for k, v in sorted(lits, key=lambda kv: -len(kv[0])):
        pat = re.escape(k)
        if re.fullmatch(r"[A-Za-z0-9 .\-]+", k):
            pat = r"(?<![A-Za-z])" + pat + r"(?![A-Za-z])"
        rules.append((re.compile(pat), v.replace("\\", "\\\\")))
    return rules


def apply_lexicon(text: str, rules) -> str:
    for pat, rep in rules or []:
        text = pat.sub(rep, text)
    return re.sub(r"\s{2,}", " ", text).strip()


def enforce_comma_pauses(pcm: np.ndarray, sr: int, text: str, min_pause: float = 0.25) -> np.ndarray:
    """Ensure every comma (,) in `text` has at least `min_pause` seconds of natural breathing pause."""
    parts = [p.strip() for p in re.split(r",\s*", text) if p.strip()]
    if len(parts) <= 1:
        return pcm
    mono = pcm.mean(axis=1) if pcm.ndim == 2 else pcm
    win = max(1, int(0.01 * sr))
    n = len(mono) // win
    if n < 24:
        return pcm
    frames = mono[:n * win].reshape(n, win)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    voiced = np.where(db > -42.0)[0]
    if len(voiced) < 12:
        return pcm
    v0, v1 = int(voiced[0]), int(voiced[-1])
    span = v1 - v0
    if span < 20:
        return pcm
    lens = [max(1, len(re.sub(r"\s+", "", p))) for p in parts]
    tot = sum(lens)
    kern = np.ones(4) / 4
    sdb = np.convolve(db, kern, mode="same")
    cum = 0
    inserts = []
    last_f = v0 + 6
    for l in lens[:-1]:
        cum += l
        est = v0 + int(round((cum / tot) * span))
        lo = max(last_f + 12, est - max(18, int(0.18 * span)))
        hi = min(v1 - 8, est + max(18, int(0.18 * span)))
        if hi <= lo:
            continue
        best_f = lo + int(np.argmin(sdb[lo:hi]))
        last_f = best_f
        s_lo, s_hi = best_f, best_f
        while s_lo > lo and db[s_lo - 1] < -37.0:
            s_lo -= 1
        while s_hi < hi and db[s_hi] < -37.0:
            s_hi += 1
        cur_pause = (s_hi - s_lo) * 0.01
        if cur_pause < min_pause:
            extra_s = min_pause - cur_pause
            inserts.append((best_f * win, int(round(extra_s * sr))))
    if not inserts:
        return pcm
    out = []
    prev = 0
    fade = min(int(0.012 * sr), 240)
    for idx, extra in inserts:
        seg = pcm[prev:idx].copy()
        if len(seg) > fade > 0:
            ramp = np.linspace(1.0, 0.0, fade, dtype=seg.dtype)
            seg[-fade:] *= ramp[:, None] if seg.ndim == 2 else ramp
        out.append(seg)
        zeros = np.zeros((extra, pcm.shape[1]), dtype=pcm.dtype) if pcm.ndim == 2 else np.zeros(extra, dtype=pcm.dtype)
        out.append(zeros)
        prev = idx
    tail = pcm[prev:].copy()
    if len(tail) > fade > 0:
        ramp = np.linspace(0.0, 1.0, fade, dtype=tail.dtype)
        tail[:fade] *= ramp[:, None] if tail.ndim == 2 else ramp
    out.append(tail)
    return np.concatenate(out, axis=0)


def _trim(x: np.ndarray, sr: int, thresh_db: float = -45.0, pad_start: float = 0.045, pad_end: float = 0.085) -> np.ndarray:
    """Trim leading/trailing silence gently while preserving natural breath release at sentence end."""
    mono = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    win = max(1, int(sr * 0.01))
    env = np.convolve(mono, np.ones(win) / win, mode="same")
    thr = 10 ** (thresh_db / 20)
    idx = np.nonzero(env > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad_start * sr))
    b = min(len(x), idx[-1] + int(pad_end * sr))
    out = x[a:b].copy()
    fade = min(int(0.008 * sr), len(out) // 4)
    if fade > 0:
        ramp = np.linspace(0.0, 1.0, fade, dtype=out.dtype)
        out[:fade] *= ramp[:, None] if out.ndim == 2 else ramp
        out[-fade:] *= ramp[::-1, None] if out.ndim == 2 else ramp[::-1]
    return out


class TTS:
    def __init__(self, voice: str = DEFAULT_VOICE, rate: float = 1.0, cache: Path = CACHE_DIR / "tts",
                 lexicon=True):
        self.voice = normalize_voice(voice)
        self.rate, self.cache = rate, cache
        self.cache.mkdir(parents=True, exist_ok=True)
        self.rules = load_lexicon(lexicon)

    def key(self, text: str, voice: str | None = None, rate: float | None = None) -> str:
        v = normalize_voice(voice) if voice else self.voice
        parts = [voice_mod.VERSION, TTS_MODEL, voice_mod.STYLE, voice_mod.COMMA_MIN, voice_mod.COMMA_MAX,
                 v, rate or self.rate, text, SR]
        tag = voice_mod.cache_tag(text)          # pause mode only matters for lines with commas
        return sha(parts + [tag] if tag else parts)

    def spoken(self, text: str, say: str | None = None) -> str:
        return say if say else apply_lexicon(text, self.rules)

    _index: list | None = None

    def closest_take(self, text: str, voice: str, min_ratio: float = 0.85) -> dict | None:
        """Most similar cached take (same voice) — used only with TTS_REUSE=1 to keep existing narration."""
        import difflib
        if TTS._index is None:
            idx = []
            for m in self.cache.glob("*.json"):
                try:
                    info = json.loads(m.read_text())
                except (OSError, ValueError):
                    continue
                if info.get("text") and Path(info.get("wav", "")).exists():
                    idx.append(info)
            TTS._index = idx
        norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
        t = norm(text)
        best, best_r = None, 0.0
        for info in TTS._index:
            if info.get("voice") != voice:
                continue
            r = difflib.SequenceMatcher(None, t, norm(info["text"])).ratio()
            if r > best_r:
                best, best_r = info, r
        if best is None or best_r < min_ratio:
            return None
        return {**best, "_ratio": best_r}

    def synth(self, text: str, voice: str | None = None, rate: float | None = None, say: str | None = None) -> dict:
        """Gemini 3.8 Flash TTS via engine.voice: instructor style, <short pause> at commas, ASR-verified take."""
        v = normalize_voice(voice) if voice else self.voice
        rate = rate or self.rate
        display = text
        text = self.spoken(text, say)
        k = self.key(text, v, rate)
        wav, meta = self.cache / f"{k}.wav", self.cache / f"{k}.json"
        if wav.exists() and meta.exists():
            return json.loads(meta.read_text())
        if os.environ.get("TTS_REUSE") == "1":
            hit = self.closest_take(text, v, float(os.environ.get("TTS_REUSE_MIN", "0.85")))
            if hit:
                log(f"TTS reuse ({hit['_ratio']:.2f}): {text[:50]}")
                return hit
            if os.environ.get("TTS_REUSE_STRICT", "1") == "1":
                raise RuntimeError(f"TTS_REUSE: no cached take close to: {text[:80]}")
        if text != display:
            log(f"TTS say: {text}")
        x, sr, rep = voice_mod.best_take(text, voice=v)
        write_wav(wav, x, sr)
        info = {"text": text, "model": TTS_MODEL, "voice": v, "style": voice_mod.STYLE, "rate": rate,
                "wav": str(wav), "sr": sr, "dur": len(x) / sr, "qa": rep}
        meta.write_text(json.dumps(info, ensure_ascii=False))
        log(f"TTS [{TTS_MODEL}/{v}] {info['dur']:.2f}s take{rep.get('take')} cer={rep.get('cer')} "
            f"pauses={rep.get('final_pauses')}  {text[:40]}")
        return info

    def synth_many(self, texts: list[tuple[str, str | None, float | None, str | None]], workers: int = 3) -> list[dict]:
        with ThreadPoolExecutor(workers) as ex:
            return list(ex.map(lambda a: self.synth(*a), texts))
