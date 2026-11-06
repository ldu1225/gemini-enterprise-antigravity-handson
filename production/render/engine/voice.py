"""Gemini 3.8 Flash TTS narrator voice shared by the lab videos and the opening deck.

Follows the official Gemini TTS prompting guide (gemini-enterprise-agent-platform/models/text-to-speech):
* ``parts[].text`` is a verbatim transcript; sustained delivery goes in ``parts[].speechMetadata.style``
  (one short constant string for every line → one consistent instructor voice).
* Comma pauses: the style asks for a brief natural pause at every comma and the model pauses on the comma
  itself (PAUSE_MODE="comma"; inline ``<short pause>`` tags were tested and dropped because they induced
  hesitation fillers). The silence at each comma is then measured and shaped to ~[COMMA_MIN, COMMA_MAX] s.
* Each take is transcribed back with Gemini (ASR) and rejected if words are added/dropped/changed, a filler
  ("어", "아" …) or a tag is heard, a version number / month is misread, a comma pause is missing or the
  pacing is off; up to ``max_takes`` takes, the best one wins.
"""
from __future__ import annotations
import os

import base64
import io
import json
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
import wave

import numpy as np

PROJECT = os.environ.get("TTS_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
TTS_MODEL = "gemini-3.8-flash-tts"
ASR_MODELS = ("gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash")
VOICE = "Kore"
STYLE = ("Clear, warm and engaging instructor narration at a steady, moderate pace, "
         "with a brief natural pause at every comma")
PAUSE_TAG = "<short pause>"
COMMA_MIN, COMMA_MAX = 0.30, 0.40        # silence kept at each comma (s); soft knee above COMMA_MAX
INNER_MAX = 0.62                         # cap for any other silence inside one sentence (s)
PAD_START, PAD_END = 0.045, 0.085        # natural onset / breath release kept around the trimmed clip
VERSION = "v5-style-comma-asr"           # cache-key salt for every consumer of this module
CER_OK = 0.08                            # max character error rate vs. the script (after normalisation)
RUN_OK = 2                               # max consecutive changed characters (≥3 ⇒ a word was added/dropped/changed)
# "comma": the model pauses on the comma itself (no inline tag) — <short pause> tags were found to induce
# hesitation fillers ("어", "아", "저") on some takes; "tag": insert <short pause> after every comma.
PAUSE_MODE = "comma"
FILLERS = {"어", "아", "음", "엄", "으", "저", "자", "그", "에", "흠", "허", "응"}

_COMMA = re.compile(r",(?!\d)|(?<!\d),")  # commas, except thousands separators like 1,000
_LEAK = re.compile(r"쇼트|숏\s*포즈|포즈|short|pause", re.I)
_CRITICAL = re.compile(r"[영일이삼사오육칠팔구]점[영일이삼사오육칠팔구]+|(?:십일|십이|[일이삼사오유칠팔구시])월")
_tok_lock = threading.Lock()
_tok = {"value": None, "at": 0.0}
_tts_gate = threading.BoundedSemaphore(4)
_asr_gate = threading.BoundedSemaphore(6)
_schema = {"tts": None, "asr_model": None, "asr_thinking": True}
_schema_lock = threading.Lock()


def log(*a):
    import sys
    print("[voice]", *a, file=sys.stderr, flush=True)


# ------------------------------------------------------------------ auth + HTTP
def token(force: bool = False) -> str:
    with _tok_lock:
        if force or not _tok["value"] or time.time() - _tok["at"] > 40 * 60:
            out = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True,
                                 timeout=60, stdin=subprocess.DEVNULL)
            if out.returncode != 0 or not out.stdout.strip():
                raise RuntimeError("gcloud auth print-access-token failed (run `gcloud auth login`): "
                                   + out.stderr.strip()[:300])
            _tok.update(value=out.stdout.strip(), at=time.time())
        return _tok["value"]


class HTTPFail(RuntimeError):
    def __init__(self, code: int, msg: str):
        super().__init__(f"HTTP {code}: {msg}")
        self.code, self.msg = code, msg


def post(url: str, body: dict, timeout: float = 150, retries: int = 6) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last: Exception | None = None
    for attempt in range(retries):
        force = isinstance(last, HTTPFail) and last.code == 401
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Authorization": f"Bearer {token(force=force)}",
            "X-Goog-User-Project": PROJECT,
            "Content-Type": "application/json; charset=utf-8",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:600]
            last = HTTPFail(e.code, msg)
            if e.code in (400, 403, 404):
                raise last from e
            log(f"HTTP {e.code} (attempt {attempt + 1}/{retries}): {msg[:160]}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            log(f"network error (attempt {attempt + 1}/{retries}): {e}")
        time.sleep(min(30.0, 2.0 * (attempt + 1)))
    raise RuntimeError(f"request failed after {retries} attempts: {last}")


def _url(model: str, api: str = "v1") -> str:
    return (f"https://aiplatform.googleapis.com/{api}/projects/{PROJECT}/locations/global"
            f"/publishers/google/models/{model}:generateContent")


# ------------------------------------------------------------------ text
def transcript(spoken: str, mode: str | None = None) -> str:
    """Verbatim transcript; in "tag" mode a <short pause> tag follows every comma."""
    t = re.sub(r"\s+", " ", spoken.strip())
    if (mode or PAUSE_MODE) == "tag":
        t = _COMMA.sub(f", {PAUSE_TAG} ", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def cache_tag(spoken: str) -> str:
    """Extra cache-key component: only lines with commas depend on the pause mode."""
    return f"pause-{PAUSE_MODE}-v2" if _COMMA.search(spoken) else ""


def comma_weights(spoken: str) -> tuple[list[float], float]:
    """Relative spoken length of each comma-separated clause (Hangul syllable ≈ 1, Latin letter ≈ 0.45)."""
    def w(s: str) -> float:
        return (len(re.findall(r"[가-힣]", s)) + 0.45 * len(re.findall(r"[A-Za-z]", s))
                + 0.9 * len(re.findall(r"\d", s)) + 0.1)
    clauses = _COMMA.split(spoken)
    ws = [w(c) for c in clauses]
    return ws, sum(ws)


_DIG = "영일이삼사오육칠팔구"
_EN_DIG = {"제로": "영", "원": "일", "투": "이", "쓰리": "삼", "포": "사", "파이브": "오", "식스": "육",
           "세븐": "칠", "에잇": "팔", "나인": "구"}


def _sino(n: int) -> str:
    if n == 0:
        return "영"
    out = ""
    for unit_val, unit in ((10 ** 8, "억"), (10 ** 4, "만")):
        if n >= unit_val:
            out += _sino_small(n // unit_val) + unit
            n %= unit_val
    return out + (_sino_small(n) if n else "")


def _sino_small(n: int) -> str:
    s = ""
    for val, name in ((1000, "천"), (100, "백"), (10, "십")):
        d = n // val
        if d:
            s += ("" if d == 1 else _DIG[d]) + name
        n %= val
    return s + (_DIG[n] if n else "")


_LEXICON: list[tuple[re.Pattern, str]] | None = None


def _lexicon() -> list[tuple[re.Pattern, str]]:
    """Display → pronunciation rules from the render + slides lexicons (applied to the ASR transcript too)."""
    global _LEXICON
    if _LEXICON is None:
        from pathlib import Path
        base = Path(__file__).resolve().parents[2]
        pairs: dict[str, str] = {}
        for p in (base / "slides" / "lexicon.json", base / "render" / "lexicon.json"):
            if p.exists():
                for k, v in json.loads(p.read_text(encoding="utf-8")).items():
                    if not k.startswith("_") and not k.startswith("re:"):
                        pairs[k] = v
        pairs.update({"AI": "에이아이", "GE": "지이", "%": "퍼센트", "워크플로우": "워크플로"})
        rules = []
        for k, v in sorted(pairs.items(), key=lambda kv: -len(kv[0])):
            pat = re.escape(k)
            if re.fullmatch(r"[A-Za-z0-9 .\-]+", k):
                pat = r"(?<![A-Za-z])" + pat + r"(?![A-Za-z])"
            rules.append((re.compile(pat, re.I if k.isascii() else 0), v))
        _LEXICON = rules
    return _LEXICON


def normalize_ko(text: str) -> str:
    t = re.sub(r"<[^>]+>", " ", text)
    for pat, rep in _lexicon():
        t = pat.sub(rep, t)
    t = t.replace("의", "에").replace("쩜", "점")
    t = re.sub(r"(원|투|쓰리|포|파이브|식스|세븐|에잇|나인|제로)\s*포인트\s*(원|투|쓰리|포|파이브|식스|세븐|에잇|나인|제로)",
               lambda m: _EN_DIG[m.group(1)] + "점" + _EN_DIG[m.group(2)], t)
    t = re.sub(r"(?<!\d)10\s*월", "시월", t)
    t = re.sub(r"(?<!\d)6\s*월", "유월", t)
    t = re.sub(r"(\d+)\.(\d+)", lambda m: _sino(int(m.group(1))) + "점" + "".join(_DIG[int(c)] for c in m.group(2)), t)
    t = re.sub(r"\d[\d,]*", lambda m: _sino(int(m.group(0).replace(",", "") or 0)), t)
    return "".join(re.findall(r"[가-힣]", t))


def align(ref: str, hyp: str) -> tuple[float, int]:
    """(character error rate, longest run of consecutive edits) between normalised ref and hyp."""
    a, b = normalize_ko(ref), normalize_ko(hyp)
    if not a:
        return (0.0, 0) if not b else (1.0, len(b))
    n, m = len(a), len(b)
    d = np.zeros((n + 1, m + 1), dtype=np.int32)
    d[:, 0] = np.arange(n + 1)
    d[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (a[i - 1] != b[j - 1]))
    i, j, run, best = n, m, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i, j] == d[i - 1, j - 1] + (a[i - 1] != b[j - 1]):
            edit = a[i - 1] != b[j - 1]
            i, j = i - 1, j - 1
        elif i > 0 and d[i, j] == d[i - 1, j] + 1:
            edit, i = True, i - 1
        else:
            edit, j = True, j - 1
        run = run + 1 if edit else 0
        best = max(best, run)
    return float(d[n, m]) / n, best


def cer(ref: str, hyp: str) -> float:
    return align(ref, hyp)[0]


# ------------------------------------------------------------------ audio helpers
def decode_audio(raw: bytes, mime: str = "") -> tuple[np.ndarray, int]:
    """WAV (RIFF) or raw 16-bit PCM → (mono float32, sr)."""
    if raw[:4] == b"RIFF":
        with wave.open(io.BytesIO(raw)) as w:
            sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
            frames = w.readframes(w.getnframes())
        if sw != 2:
            raise RuntimeError(f"unexpected sample width {sw}")
        x = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
        if ch > 1:
            x = x.reshape(-1, ch).mean(axis=1)
        return x, sr
    m = re.search(r"rate=(\d+)", mime or "")
    sr = int(m.group(1)) if m else 24000
    return np.frombuffer(raw[: len(raw) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0, sr


def encode_wav(x: np.ndarray, sr: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def frame_db(x: np.ndarray, sr: int) -> np.ndarray:
    win = max(1, int(0.01 * sr))
    n = len(x) // win
    if n == 0:
        return np.zeros(0)
    fr = x[: n * win].reshape(n, win)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)


def trim(x: np.ndarray, sr: int, thresh_db: float = -45.0) -> np.ndarray:
    env = np.convolve(np.abs(x), np.ones(max(1, int(0.01 * sr))) / max(1, int(0.01 * sr)), mode="same")
    idx = np.nonzero(env > 10 ** (thresh_db / 20))[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(PAD_START * sr))
    b = min(len(x), idx[-1] + int(PAD_END * sr))
    out = x[a:b].astype(np.float32).copy()
    f = min(int(0.008 * sr), len(out) // 4)
    if f > 0:
        r = np.linspace(0.0, 1.0, f, dtype=np.float32)
        out[:f] *= r
        out[-f:] *= r[::-1]
    return out


def silent_runs(x: np.ndarray, sr: int, thr: float = -40.0, min_len: float = 0.09):
    """Silences strictly inside the voiced span → list of (start_s, end_s), plus (v0_s, v1_s)."""
    db = frame_db(x, sr)
    if len(db) < 10:
        return [], (0.0, len(x) / sr)
    sdb = np.convolve(db, np.ones(3) / 3, mode="same")
    voiced = np.where(sdb > thr)[0]
    if len(voiced) == 0:
        return [], (0.0, len(x) / sr)
    v0, v1 = int(voiced[0]), int(voiced[-1])
    runs, i = [], v0
    while i <= v1:
        if sdb[i] <= thr:
            j = i
            while j <= v1 and sdb[j] <= thr:
                j += 1
            if (j - i) * 0.01 >= min_len:
                runs.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return runs, (v0 * 0.01, (v1 + 1) * 0.01)


def match_commas(x: np.ndarray, sr: int, spoken: str):
    """Assign each comma to the silence nearest its expected position (in order).

    Returns (assigned runs or None per comma, all runs, voiced span)."""
    runs, (v0, v1) = silent_runs(x, sr)
    ws, tot = comma_weights(spoken)
    n = len(ws) - 1
    if n <= 0:
        return [], runs, (v0, v1)
    speech = max(0.3, (v1 - v0) - sum(b - a for a, b in runs))
    assigned, cum, k0 = [], 0.0, 0
    for c in range(n):
        cum += ws[c]
        # expected time: map clause weights onto speech time, then add the silences already passed
        est_speech = cum / tot * speech
        best, best_s = None, -1e9
        for k in range(k0, len(runs)):
            a, b = runs[k]
            before = sum(bb - aa for aa, bb in runs[:k])
            t_speech = (a - v0) - before
            d = abs(t_speech - est_speech)
            if d > max(0.9, 0.22 * speech):
                continue
            s = (b - a) * 1.6 - d
            if s > best_s:
                best, best_s = k, s
        if best is None:
            assigned.append(None)
        else:
            assigned.append(best)
            k0 = best + 1
    return assigned, runs, (v0, v1)


def shape_pauses(x: np.ndarray, sr: int, spoken: str, fill_missing: bool = True) -> tuple[np.ndarray, dict]:
    """Clamp comma silences to [COMMA_MIN, COMMA_MAX], cap other inner silences at INNER_MAX."""
    assigned, runs, (v0, v1) = match_commas(x, sr, spoken)
    edits = []  # (sample_index, delta_samples)  delta>0 insert zeros, delta<0 remove
    comma_runs = {k for k in assigned if k is not None}
    for k, (a, b) in enumerate(runs):
        L = b - a
        mid = int(round((a + b) / 2 * sr))
        if k in comma_runs:
            if L < COMMA_MIN:
                edits.append((mid, int(round((COMMA_MIN - L) * sr))))
            elif L > COMMA_MAX:
                # soft knee: keep a little of the model's own variation (0.50 s → ~0.44 s, cap +0.04 s)
                target = min(COMMA_MAX + 0.04, COMMA_MAX + 0.2 * (L - COMMA_MAX))
                edits.append((mid, -int(round((L - target) * sr))))
        elif L > INNER_MAX:
            edits.append((mid, -int(round((L - INNER_MAX) * sr))))
    missing = [i for i, k in enumerate(assigned) if k is None]
    if missing and fill_missing:
        # last resort: lowest-energy point near the expected position gets a COMMA_MIN breath
        db = np.convolve(frame_db(x, sr), np.ones(4) / 4, mode="same")
        ws, tot = comma_weights(spoken)
        cum = np.cumsum(ws)[:-1] / tot
        for i in missing:
            est = v0 + cum[i] * (v1 - v0)
            lo, hi = int((est - 0.35) * 100), int((est + 0.35) * 100)
            lo, hi = max(lo, int(v0 * 100) + 5), min(hi, int(v1 * 100) - 5)
            if hi > lo:
                f = lo + int(np.argmin(db[lo:hi]))
                edits.append((f * int(0.01 * sr), int(round(COMMA_MIN * sr))))
    if not edits:
        return x, {"commas": len(assigned), "missing": len(missing), "edits": 0}
    edits.sort()
    out, prev = [], 0
    fade = int(0.006 * sr)
    for idx, delta in edits:
        if delta > 0:
            seg = x[prev:idx].copy()
            if len(seg) > fade:
                seg[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
            out += [seg, np.zeros(delta, dtype=np.float32)]
            prev = idx
            if idx + fade <= len(x):
                x = x.copy()
                x[idx: idx + fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        else:
            cut = -delta
            a, b = idx - cut // 2, idx + (cut - cut // 2)
            a, b = max(prev, a), min(len(x), b)
            seg = x[prev:a].copy()
            if len(seg) > fade:
                seg[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
            out.append(seg)
            prev = b
            if b + fade <= len(x):
                x = x.copy()
                x[b: b + fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    out.append(x[prev:])
    return np.concatenate(out).astype(np.float32), {"commas": len(assigned), "missing": len(missing),
                                                     "edits": len(edits)}


def comma_pauses(x: np.ndarray, sr: int, spoken: str) -> list[float]:
    assigned, runs, _ = match_commas(x, sr, spoken)
    return [round(runs[k][1] - runs[k][0], 3) if k is not None else 0.0 for k in assigned]


# ------------------------------------------------------------------ model calls
def _tts_body(text: str, voice: str, temperature: float, schema: str, style: str | None = None
              ) -> tuple[str, dict]:
    part = {"text": text}
    if schema != "nostyle":
        part["speechMetadata"] = {"style": style or STYLE}
    if schema in ("v1", "nostyle"):
        url, vc = _url(TTS_MODEL, "v1"), {"voice": voice}
    else:
        url, vc = _url(TTS_MODEL, "v1beta1"), {"prebuiltVoiceConfig": {"voiceName": voice}}
    return url, {
        "contents": [{"role": "user", "parts": [part]}],
        "generationConfig": {"temperature": temperature, "responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": vc}},
    }


def synth_raw(text: str, voice: str = VOICE, temperature: float = 0.35, style: str | None = None
              ) -> tuple[np.ndarray, int]:
    schemas = [_schema["tts"]] if _schema["tts"] else ["v1", "v1beta1", "nostyle"]
    last = None
    for schema in schemas:
        url, body = _tts_body(text, voice, temperature, schema, style)
        for empty_try in range(4):
            try:
                with _tts_gate:
                    resp = post(url, body)
            except HTTPFail as e:
                last = e
                if e.code == 400 and not _schema["tts"]:
                    log(f"schema {schema} rejected ({e.msg[:140]}); trying next")
                    break
                raise
            cand = (resp.get("candidates") or [{}])[0]
            parts = (cand.get("content") or {}).get("parts") or []
            blob = next((p["inlineData"] for p in parts if "inlineData" in p), None)
            if blob and blob.get("data"):
                with _schema_lock:
                    if not _schema["tts"]:
                        _schema["tts"] = schema
                        log(f"TTS schema: {schema}")
                return decode_audio(base64.b64decode(blob["data"]), blob.get("mimeType", ""))
            log(f"empty TTS candidate (finishReason={cand.get('finishReason')}); retry {empty_try + 1}")
            time.sleep(1.5 * (empty_try + 1))
        else:
            raise RuntimeError(f"TTS returned no audio for: {text[:60]}")
    raise RuntimeError(f"no TTS request schema accepted: {last}")


ASR_PROMPT = ("이 한국어 음성을 들리는 그대로 받아 적으세요. 설명이나 따옴표 없이 받아쓴 문장만 출력하세요. "
              "영어 단어와 약어도 들리는 발음 그대로 한글로 적고, 숫자도 읽힌 그대로 한글로 적으세요. "
              "말하지 않은 내용은 추가하지 마세요.")


def asr(x: np.ndarray, sr: int) -> str:
    b64 = base64.b64encode(encode_wav(x, sr)).decode()
    models = [_schema["asr_model"]] if _schema["asr_model"] else list(ASR_MODELS)
    last = None
    for model in models:
        body = {
            "contents": [{"role": "user", "parts": [{"inlineData": {"mimeType": "audio/wav", "data": b64}},
                                                    {"text": ASR_PROMPT}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048},
        }
        if _schema["asr_thinking"]:
            body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "low"}
        try:
            with _asr_gate:
                resp = post(_url(model, "v1"), body, timeout=120)
        except HTTPFail as e:
            last = e
            if e.code == 400 and _schema["asr_thinking"] and "think" in e.msg.lower():
                _schema["asr_thinking"] = False
                return asr(x, sr)
            if e.code in (400, 404) and not _schema["asr_model"]:
                log(f"ASR model {model} unavailable ({e.code}); trying next")
                continue
            raise
        cand = (resp.get("candidates") or [{}])[0]
        text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts") or []
                       if not p.get("thought"))
        with _schema_lock:
            if not _schema["asr_model"]:
                _schema["asr_model"] = model
                log(f"ASR model: {model}")
        return text.strip()
    raise RuntimeError(f"no ASR model available: {last}")


# ------------------------------------------------------------------ best take
def fillers(spoken: str, heard: str) -> list[str]:
    """Hesitation sounds in the take that the script doesn't have (e.g. a stray "어" at a pause)."""
    want = set(re.findall(r"[가-힣]+", spoken))
    return [t for t in re.findall(r"[가-힣]+", heard) if t in FILLERS and t not in want]


def missing_critical(spoken: str, heard: str) -> list[str]:
    """Version numbers / months that must be heard exactly (삼점팔, 유월, 시월 …)."""
    have = normalize_ko(heard)
    return [m for m in _CRITICAL.findall(normalize_ko(spoken)) if m not in have]


def evaluate(x: np.ndarray, sr: int, spoken: str, check_asr: bool = True) -> dict:
    pauses = comma_pauses(x, sr, spoken)
    runs, (v0, v1) = silent_runs(x, sr)
    speech = max(0.05, (v1 - v0) - sum(b - a for a, b in runs))
    syl = sum(comma_weights(spoken)[0])
    rate = syl / speech
    rep = {"pauses": pauses, "missing": sum(1 for p in pauses if p < 0.12), "rate": round(rate, 2),
           "dur": round(len(x) / sr, 3)}
    if check_asr:
        try:
            heard = asr(x, sr)
            c, run = align(spoken, heard)
            if c > 0.3:                       # ASR hiccup (empty / truncated)? ask once more, keep the better
                heard2 = asr(x, sr)
                c2, run2 = align(spoken, heard2)
                if c2 < c:
                    heard, c, run = heard2, c2, run2
            rep["asr"] = heard
            rep["cer"], rep["run"] = round(c, 3), run
            rep["leak"] = bool(_LEAK.search(heard)) and not _LEAK.search(spoken)
            rep["fillers"] = fillers(spoken, heard)
            rep["crit"] = missing_critical(spoken, heard)
        except Exception as e:  # ASR is a quality gate, never a hard failure
            log(f"ASR skipped: {e}")
            rep["cer"], rep["run"], rep["leak"] = None, 0, False
    rep["rate_ok"] = 3.6 <= rate <= 8.2 if syl >= 8 else True
    return judge(rep)


def judge(rep: dict) -> dict:
    """ok/score from a report (also used to re-judge cached reports offline)."""
    c, run = rep.get("cer"), rep.get("run", 0) or 0
    nf, nc = len(rep.get("fillers") or []), len(rep.get("crit") or [])
    rep["ok"] = (rep["missing"] == 0 and not rep.get("leak") and rep["rate_ok"] and nf == 0 and nc == 0
                 and (c is None or (c <= CER_OK and run <= RUN_OK)))
    rep["score"] = ((c or 0.0) + 0.04 * max(0, run - RUN_OK) + 0.15 * rep["missing"] + 0.12 * nf + 0.2 * nc
                    + (2.0 if rep.get("leak") else 0.0) + (0.3 if not rep["rate_ok"] else 0.0))
    return rep


def best_take(spoken: str, voice: str = VOICE, max_takes: int = 4, check_asr: bool = True,
              style: str | None = None) -> tuple[np.ndarray, int, dict]:
    """Synthesize `spoken` (already lexicon-normalised) → (trimmed mono float32, sr, report)."""
    text = transcript(spoken)
    best = None
    for k in range(max_takes):
        x, sr = synth_raw(text, voice, temperature=round(0.35 + 0.1 * k, 2), style=style)
        x = trim(x, sr)
        rep = evaluate(x, sr, spoken, check_asr)
        rep["take"] = k + 1
        if best is None or rep["score"] < best[2]["score"]:
            best = (x, sr, rep)
        if rep["ok"]:
            break
        log(f"take {k + 1} rejected (cer={rep.get('cer')}, run={rep.get('run')}, missing={rep['missing']}, "
            f"fillers={rep.get('fillers')}, crit={rep.get('crit')}, leak={rep.get('leak')}, rate={rep['rate']}): "
            f"{spoken[:40]}")
    x, sr, rep = best
    x, info = shape_pauses(x, sr, spoken)
    rep.update(info)
    rep["final_pauses"] = comma_pauses(x, sr, spoken)
    rep["final_dur"] = round(len(x) / sr, 3)
    rep["takes"] = k + 1
    return x, sr, rep
