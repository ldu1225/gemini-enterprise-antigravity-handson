"""Edit script -> frame-accurate render plan.

The plan is a plain picklable dict consumed by the compositor workers.  All timing decisions are
made here: narration scheduling, recording time-remapping (time-lapse / holds), camera moves,
callouts, step labels, fast-forward badges and caption cues.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import callout_track
from .common import DEFAULT_VOICE, H, W, ease_in_out_cubic, log
from .recording import Recording
from .tts import TTS, split_sentences
from .typo import SpriteStore, font, wrap_keep_all

DEFAULTS = {
    "fps": 30,
    "transition": 0.5,      # crossfade between segments (s)
    "gap": 0.42,            # pause between narration sentences (s)
    "lead": 0.30,           # narration starts this long after a segment starts (+ half the incoming transition)
    "tail": 0.30,           # ...and the segment lasts this long after the narration ends (+ half the outgoing one)
    "max_speed": 8.0,       # time-lapse cap for dynamic content
    "min_speed": 0.8,       # slow-motion floor when there is no static frame to hold
    "type_speed": 1.6,      # typing may be sped up to this
    "idle_speed": 2.0,      # other motion when the recording marks AI waits (wait_start/wait_end)
    "frame_scale": 0.84,    # zoomed-out "device frame" width as a fraction of the output width
    "frame_top": 40,        # top margin of the zoomed-out device frame (px)
    "caption_band": 150,    # bottom band kept clear of zoom targets while captions are on
    "max_zoom": 1.6,        # max magnification relative to "recording fills the 1920px frame"
    "caption_max_w": 1500,
}


# =============================================================== camera maths
def overview_state(sw: int, sh: int, cfg: dict) -> tuple[float, float, float]:
    S = W * cfg["frame_scale"] / sw
    tx, ty = (W - S * sw) / 2, cfg["frame_top"]
    return to_view(S, tx, ty)


def to_view(S, tx, ty):
    return ((W / 2 - tx) / S, (H / 2 - ty) / S, W / S)


def from_view(v):
    cx, cy, vw = v
    S = W / vw
    return S, W / 2 - cx * S, H / 2 - cy * S


def interp_view(A, B, u: float):
    """Zoom about the fixed point of the two views (pure 'push in' feel); log-scale zoom speed."""
    ax, ay, aw = A
    bx, by, bw = B
    if abs(math.log(bw / aw)) < 1e-3:
        return (ax + (bx - ax) * u, ay + (by - ay) * u, aw + (bw - aw) * u)
    wu = aw * (bw / aw) ** u
    k = wu / aw
    fx = (ax * bw - bx * aw) / (bw - aw)
    fy = (ay * bw - by * aw) / (bw - aw)
    return (fx + (ax - fx) * k, fy + (ay - fy) * k, wu)


def zoom_state(box, sw, sh, cfg, zc: dict, cap_band: float):
    bx, by, bw, bh = box
    S0 = W * cfg["frame_scale"] / sw
    fit = W / sw                                   # recording exactly fills the output width
    safe_w, safe_h = W - 2 * 80, H - cap_band - 2 * 48
    S = min(safe_w / max(bw, 1), safe_h / max(bh, 1))
    S = min(S, float(zc.get("max", cfg["max_zoom"])) * fit)
    if zc.get("scale"):
        S = float(zc["scale"]) * fit
    S = max(S, S0)
    vw, vh = W / S, H / S
    cx = bx + bw / 2
    cy = by + bh / 2 + (H / 2 - (H - cap_band) / 2) / S
    if vw <= sw:
        cx = min(max(cx, vw / 2), sw - vw / 2)
    else:
        cx = sw / 2
    if vh <= sh:
        hi = sh - vh / 2
        if zc.get("overscan"):                 # may reveal the device-frame bottom edge (captions over background)
            hi += float(zc.get("overscan_px", cap_band + 40)) / S
        cy = min(max(cy, vh / 2), hi)
    else:
        ty = max(0.0, min(cfg["frame_top"], (H - S * sh) / 2))
        cy = (H / 2 - ty) / S
    return (cx, cy, vw)


def camera_track(moves, n_f: int, fps: int, start_state):
    """moves: [(t0, dur, target_state)] sorted; sequential (a move never interrupts the previous one)."""
    resolved, last_end = [], -1e9
    for t0, d, B in sorted(moves, key=lambda m: m[0]):
        t0 = max(t0, last_end)
        resolved.append([t0, max(d, 1e-3), None, B])
        last_end = t0 + d

    def state_at(t, upto):
        s = start_state
        for t0, d, A, B in resolved[:upto]:
            if t < t0:
                break
            p = (t - t0) / d
            s = interp_view(A, B, ease_in_out_cubic(p)) if p < 1 else B
        return s

    for i, m in enumerate(resolved):
        m[2] = state_at(m[0], i)
    cam = np.zeros((n_f, 3), np.float64)
    for f in range(n_f):
        cam[f] = from_view(state_at(f / fps, len(resolved)))
    return cam


# ========================================================== time remapping
@dataclass
class Piece:
    ra: float
    rb: float
    dur: float          # output seconds


def _dyn_caps(rec: Recording, a: float, b: float, cfg: dict, keep: list) -> list[tuple[float, float, float]]:
    """Split a dynamic interval into (a, b, cap) by proximity to interaction events.

    Protected (1x): around click / hover / submit / paste and author 'keep' ranges.  Typing: type_speed.
    AI waits (wait_start..wait_end): max_speed.  Other motion: max_speed, or idle_speed when the
    recording marks its waits explicitly (then only the waits are time-lapsed hard).
    """
    wins = []
    evs = rec.events
    has_waits = any(e.get("kind") == "wait_start" for e in evs)
    for e in evs:
        k, t = e.get("kind"), e["rt"]
        if k == "click":
            wins.append((t - 1.0, t + 0.7, 1.0))
        elif k == "hover":
            wins.append((t - 0.6, t + 0.5, 1.0))
        elif k in ("submit", "paste"):
            wins.append((t - 0.4, t + 0.9, 1.0))
        elif k == "type_start":
            end = next((x["rt"] for x in evs if x.get("kind") == "type_end" and x["rt"] >= t), t + 3)
            wins.append((t - 0.3, end + 0.3, cfg["type_speed"]))
        elif k == "wait_start":
            end = next((x["rt"] for x in evs if x.get("kind") == "wait_end" and x["rt"] >= t), b)
            wins.append((t + 0.4, end - 0.2, cfg["max_speed"]))
    wins += [(float(k0), float(k1), 1.0) for k0, k1 in keep]
    default = cfg["idle_speed"] if has_waits else cfg["max_speed"]
    cuts = sorted({a, b, *[w[0] for w in wins if a < w[0] < b], *[w[1] for w in wins if a < w[1] < b]})
    out = []
    for x0, x1 in zip(cuts[:-1], cuts[1:]):
        mid = (x0 + x1) / 2
        inside = [w[2] for w in wins if w[0] <= mid <= w[1]]
        protected = [c for c in inside if c < cfg["max_speed"]]
        cap = min(protected) if protected else (cfg["max_speed"] if inside else default)
        out.append((x0, x1, cap))
    return out


def solve_span(rec: Recording, ra: float, rb: float, T: float, cfg: dict, speed, keep) -> tuple[list[Piece], float]:
    """Map recording span [ra, rb] onto ~T output seconds. Returns (pieces, actual_duration >= T)."""
    L = rb - ra
    if L <= 1e-6:
        return ([Piece(rb, rb, T)] if T > 0 else []), max(T, 0.0)
    if isinstance(speed, (int, float)):                          # uniform speed, then hold
        d = L / float(speed)
        ps = [Piece(ra, rb, d)]
        if T > d:
            ps.append(Piece(rb, rb, T - d))
        return ps, max(T, d)
    if isinstance(speed, list):                                  # explicit ranges
        cuts = sorted({ra, rb, *[float(r["from"]) for r in speed if ra < float(r["from"]) < rb],
                       *[float(r["to"]) for r in speed if ra < float(r["to"]) < rb]})
        ps = []
        for x0, x1 in zip(cuts[:-1], cuts[1:]):
            mid = (x0 + x1) / 2
            x = next((float(r["x"]) for r in speed if float(r["from"]) <= mid <= float(r["to"])), 1.0)
            ps.append(Piece(x0, x1, (x1 - x0) / x))
        d = sum(p.dur for p in ps)
        if T > d:
            ps.append(Piece(rb, rb, T - d))
        return ps, max(T, d)

    # ---- auto: stretch/compress static (unchanging) intervals first, then time-lapse dynamic ones
    statics = rec.static_intervals(ra, rb)
    items = []          # (a, b, kind, cap)
    cur = ra
    for a, b in statics:
        if a > cur + 1e-6:
            items += [(x0, x1, "dyn", c) for x0, x1, c in _dyn_caps(rec, cur, a, cfg, keep)]
        items.append((a, b, "static", 1e9))
        cur = b
    if rb > cur + 1e-6:
        items += [(x0, x1, "dyn", c) for x0, x1, c in _dyn_caps(rec, cur, rb, cfg, keep)]
    Ls = sum(b - a for a, b, k, _ in items if k == "static")
    Ld = L - Ls
    durs = [b - a for a, b, _, _ in items]
    if T >= L:                                                   # stretch: hold unchanging frames longer
        extra = T - L
        if Ls > 0.05:
            durs = [d + (extra * d / Ls if k == "static" else 0) for d, (_, _, k, _) in zip(durs, items)]
            return [Piece(a, b, d) for (a, b, _, _), d in zip(items, durs)], T
        s = max(L / T, cfg["min_speed"])
        ps = [Piece(ra, rb, L / s)]
        if T > L / s:
            ps.append(Piece(rb, rb, T - L / s))
        return ps, T
    # compress
    smin = float(cfg.get("static_min", 0.2))
    mins = [min(d, smin) if k == "static" else d for d, (_, _, k, _) in zip(durs, items)]
    min_static = sum(m for m, (_, _, k, _) in zip(mins, items) if k == "static")
    if Ld + min_static <= T:
        beta = (T - Ld - min_static) / max(Ls - min_static, 1e-9)
        durs = [(m + (d - m) * beta) if k == "static" else d for d, m, (_, _, k, _) in zip(durs, mins, items)]
        return [Piece(a, b, d) for (a, b, _, _), d in zip(items, durs)], T
    Td = T - min_static
    dyn = [(b - a, c) for a, b, k, c in items if k == "dyn"]
    f = lambda lam: sum(l / min(c, lam) for l, c in dyn)  # noqa: E731
    cmax = max(c for _, c in dyn)
    if f(cmax) >= Td:
        lam = cmax
    else:
        lo, hi = 1.0, cmax
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) > Td else (lo, mid)
        lam = hi
    out = []
    for (a, b, k, c), m in zip(items, mins):
        out.append(Piece(a, b, m if k == "static" else (b - a) / min(c, lam)))
    return out, max(T, sum(p.dur for p in out))


def pieces_to_frames(pieces: list[Piece], n_f: int, fps: int, smooth_s: float = 0.10) -> np.ndarray:
    ko, kr = [0.0], [pieces[0].ra if pieces else 0.0]
    for p in pieces:
        if p.dur <= 0:
            continue
        ko.append(ko[-1] + p.dur)
        kr.append(p.rb)
    t = np.arange(n_f) / fps
    rec_t = np.interp(t, ko, kr)
    s = smooth_s * fps
    if s > 0.5 and n_f > 8:
        r = int(3 * s)
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
        k /= k.sum()
        padded = np.concatenate([np.full(r, rec_t[0]), rec_t, np.full(r, rec_t[-1])])
        rec_t = np.convolve(padded, k, mode="valid")
    return rec_t


def fmt_speed(x: float) -> str:
    if x >= 2.75:
        return f"×{int(round(x))}"
    return f"×{round(x * 2) / 2:g}"


# ================================================================ builders
class Ctx:
    def __init__(self, script: dict, cfg: dict):
        self.script, self.cfg = script, cfg
        self.fps = int(cfg["fps"])
        self.store = SpriteStore()
        self._recs: dict[str, Recording] = {}

    def rec(self, rid: str) -> Recording:
        if rid not in self._recs:
            self._recs[rid] = Recording.load(rid)
        return self._recs[rid]


def normalize_narration(n) -> list[dict]:
    if not n:
        return []
    if isinstance(n, (str, dict)):
        n = [n]
    out = []
    for it in n:
        if isinstance(it, str):
            out += [{"text": s} for s in split_sentences(it)]
        elif isinstance(it, dict) and it.get("text"):
            out.append(dict(it))
    return out


def schedule(items: list[dict], lead: float, gap: float) -> list[float]:
    t, out = lead, []
    for it in items:
        out.append(t)
        t += it["dur"] + float(it.get("pause", gap))
    return out


def text_block(store: SpriteStore, **kw) -> dict:
    return store.get("text", **kw)


def stack_layout(blocks: list[tuple[dict, float, int]], center_y: float) -> list[float]:
    """blocks: (sprite_meta, gap_before, font_size). Returns sprite top y for each so the stack is centred."""
    hs = []
    for m, gap, size in blocks:
        n = len(m["lines"])
        lhp = (m["block_h"] - size) / max(n - 1, 1) if n > 1 else 0
        hs.append((n - 1) * lhp + 0.88 * size)
    total = sum(hs) + sum(g for _, g, _ in blocks[1:])
    y = center_y - total / 2
    tops = []
    for i, ((m, gap, size), h) in enumerate(zip(blocks, hs)):
        if i:
            y += gap
        tops.append(y - (m["first_base"] - 0.80 * size))
        y += h
    return tops


def brand_el(seg, ctx: Ctx) -> dict | None:
    """Text-only brand line (top-left) shared by title/card/outro segments."""
    b = seg.get("brand", ctx.script.get("brand"))
    if not b:
        return None
    m = ctx.store.get("brand", text=str(b))
    return {"sprite": m, "role": "brand", "x": 66.0, "y": 50.0, "delay": 0.1}


def _vis(m: dict, size: int | None = None) -> tuple[float, float]:
    """(visual top offset inside the sprite, visual height) for text blocks / bodies."""
    if size is not None and "first_base" in m:
        n = len(m["lines"])
        lhp = (m["block_h"] - size) / max(n - 1, 1) if n > 1 else 0
        return m["first_base"] - 0.80 * size, (n - 1) * lhp + 0.88 * size
    b = m.get("body", [0, 0, m["w"], m["h"]])
    return float(b[1]), float(b[3])


def build_checklist(seg, ctx: Ctx, items, lead, tail):
    """Outro with a check icon, kicker, title, checklist rows (synced to narration) and a subtitle."""
    cfg, st = ctx.cfg, ctx.store
    checks = [str(c) for c in seg["checklist"]]
    gap = float(seg.get("gap", cfg["gap"]))
    narr = sum(it["dur"] for it in items) + gap * max(len(items) - 1, 0)
    D = max(float(seg.get("duration", 3.8 + 0.9 * len(checks))), (lead + narr + tail) if items else 0)
    sched = schedule(items, lead, gap)
    nat = [st.get("checkitem", text=c)["natural_w"] for c in checks]
    roww = int(math.ceil(max(nat))) if nat else 0
    parts = []          # (role, sprite, gap_before, size or None)
    parts.append(("icon", st.get("check", d=92), 0, None))
    if seg.get("kicker"):
        parts.append(("kicker", text_block(st, text=seg["kicker"], weight="semibold", size=28, tracking_em=0.2,
                                           gradient=True, max_w=1400), 20, 28))
    if seg.get("title"):
        parts.append(("title", text_block(st, text=seg["title"], weight="bold", size=60, max_w=1500, lh=1.2), 18, 60))
    for i, c in enumerate(checks):
        parts.append(("check", st.get("checkitem", text=c, width=roww), 46 if i == 0 else 14, None))
    if seg.get("subtitle"):
        parts.append(("subtitle", text_block(st, text=seg["subtitle"], weight="medium", size=32, color="#AEB6C2",
                                             max_w=1400, lh=1.4, tracking_em=-0.01), 44, 32))
    vis = [_vis(m, size) for _, m, _, size in parts]
    total = sum(h for _, h in vis) + sum(g for _, _, g, _ in parts[1:])
    y = float(seg.get("center_y", (H - 120) / 2)) - total / 2
    els = []
    # when rows are revealed: explicit sentence indices, or one sentence per row (optionally after an intro)
    at = seg.get("check_at")
    if at is None and items:
        if len(items) == len(checks) + 1:
            at = list(range(1, len(checks) + 1))
        elif len(items) == len(checks):
            at = list(range(len(checks)))
    ci = 0
    last_row = 0.0
    for i, ((role, m, g, size), (vt, vh)) in enumerate(zip(parts, vis)):
        if i:
            y += g
        e = {"sprite": m, "role": role, "x": (W - m["w"]) / 2, "y": y - vt}
        if role == "check":
            if at is not None and ci < len(at) and 0 <= int(at[ci]) < len(sched):
                e["delay"], e["abs"] = max(0.35, sched[int(at[ci])] - 0.12), True
            else:
                e["delay"] = 0.85 + 0.42 * ci
            last_row = max(last_row, e["delay"])
            ci += 1
        else:
            e["delay"] = {"icon": 0.0, "kicker": 0.08, "title": 0.2}.get(role, 0.0)
        els.append(e)
        y += vh
    for e in els:
        if e["role"] == "subtitle":
            e["delay"], e["abs"] = last_row + 0.5, True
    b = brand_el(seg, ctx)
    if b:
        els.append(b)
    return {"type": "outro", "dur": D, "els": els, "accent": False,
            "sentences": [(s, it) for s, it in zip(sched, items)]}


def build_title(seg, ctx: Ctx, items, lead, tail, kind="title"):
    cfg, fps, st = ctx.cfg, ctx.fps, ctx.store
    if kind == "outro" and seg.get("checklist"):
        return build_checklist(seg, ctx, items, lead, tail)
    narr = sum(it["dur"] for it in items) + float(seg.get("gap", cfg["gap"])) * max(len(items) - 1, 0)
    D = max(float(seg.get("duration", 3.5 if kind == "title" else 4.0)), (lead + narr + tail) if items else 0)
    els = []
    blocks = []
    if kind == "outro":
        chk = st.get("check")
        els.append({"sprite": chk, "role": "icon"})
    if seg.get("kicker"):
        m = text_block(st, text=seg["kicker"], weight="semibold", size=30, tracking_em=0.24, gradient=True, max_w=1400)
        blocks.append((m, 0, 30))
        els.append({"sprite": m, "role": "kicker"})
    if seg.get("title"):
        size = 92 if kind == "title" else 80
        m = text_block(st, text=seg["title"], weight="bold", size=size, max_w=1560, lh=1.18)
        blocks.append((m, 40 if blocks else 0, size))
        els.append({"sprite": m, "role": "title"})
    if seg.get("subtitle"):
        m = text_block(st, text=seg["subtitle"], weight="medium", size=40, color="#AEB6C2", max_w=1400, lh=1.45,
                       tracking_em=-0.01)
        blocks.append((m, 34 if blocks else 0, 40))
        els.append({"sprite": m, "role": "subtitle"})
    cy = H / 2 - 16 + (50 if kind == "outro" else 0)
    tops = stack_layout(blocks, cy) if blocks else []
    j = 0
    for e in els:
        if e["role"] == "icon":
            continue
        m = e["sprite"]
        e["x"], e["y"] = (W - m["w"]) / 2, tops[j]
        j += 1
    if kind == "outro":
        icon = els[0]
        top_text = min(e["y"] for e in els[1:]) if len(els) > 1 else H / 2
        icon["x"], icon["y"] = (W - icon["sprite"]["w"]) / 2, top_text - icon["sprite"]["h"] + 6
    delays = {"icon": 0.0, "kicker": 0.08, "title": 0.2, "subtitle": 0.36}
    for e in els:
        e["delay"] = delays[e["role"]]
    b = brand_el(seg, ctx)
    if b:
        els.append(b)
    sched = schedule(items, lead, float(seg.get("gap", cfg["gap"])))
    return {"type": kind, "dur": D, "els": els, "accent": bool(seg.get("kicker")) and kind == "title",
            "sentences": [(s, it) for s, it in zip(sched, items)]}


def build_card(seg, ctx: Ctx, items, lead, tail):
    cfg, st = ctx.cfg, ctx.store
    bullets = seg.get("bullets", [])
    gap = float(seg.get("gap", cfg["gap"]))
    narr = sum(it["dur"] for it in items) + gap * max(len(items) - 1, 0)
    D = max(float(seg.get("duration", 2.5 + 1.0 * len(bullets))), (lead + narr + tail) if items else 0)
    sched = schedule(items, lead, gap)
    els = []
    parts = []
    if seg.get("kicker"):
        m = text_block(st, text=seg["kicker"], weight="semibold", size=26, tracking_em=0.2, gradient=True,
                       align="left", max_w=1320)
        parts.append(("kicker", m, 0))
    if seg.get("title"):
        m = text_block(st, text=seg["title"], weight="bold", size=64, max_w=1320, lh=1.22, align="left")
        parts.append(("title", m, 22 if parts else 0))
    for i, b in enumerate(bullets):
        m = st.get("bullet", n=i + 1, text=b)
        parts.append(("bullet", m, 56 if i == 0 else 26))
    content_w = max((m["w"] - 2 * m.get("pad", 12) for _, m, _ in parts), default=0)
    x0 = max(220.0, (W - content_w) / 2)                  # centred column, left-aligned text
    heights = [p[1]["h"] for p in parts]
    total = sum(heights) + sum(p[2] for p in parts)
    y = H / 2 - total / 2 - 20
    bi = 0
    synced = bool(items) and len(items) == len(bullets)
    for role, m, g in parts:
        y += g
        pad = m.get("pad", 12)
        e = {"sprite": m, "role": role, "x": x0 - pad, "y": y}
        if role == "bullet":
            if synced:                                    # bullet i appears as sentence i starts
                e["delay"], e["abs"] = max(0.3, sched[bi] - 0.12), True
            else:
                e["delay"] = 0.75 + 0.35 * bi
            bi += 1
        else:
            e["delay"] = 0.1 if role == "kicker" else 0.22
        els.append(e)
        y += m["h"]
    b = brand_el(seg, ctx)
    if b:
        els.append(b)
    return {"type": "card", "dur": D, "els": els, "sentences": [(s, it) for s, it in zip(sched, items)]}


def build_screen(seg, ctx: Ctx, items, lead, tail, prev_type):
    cfg, fps, st = ctx.cfg, ctx.fps, ctx.store
    rec = ctx.rec(seg["rec"])
    sw, sh = rec.size
    r0 = rec.resolve_time(seg.get("from", 0.0)) or 0.0
    r1 = rec.resolve_time(seg.get("to")) if seg.get("to") is not None else rec.duration
    r1 = max(r1 if r1 is not None else rec.duration, r0 + 0.1)
    gap = float(seg.get("gap", cfg["gap"]))
    speed = seg.get("speed", "auto")
    seg_cfg = dict(cfg)
    for k in ("max_speed", "min_speed", "type_speed", "idle_speed", "max_zoom"):
        if k in seg:
            seg_cfg[k] = float(seg[k])
    keep = seg.get("keep", [])
    sched = schedule(items, lead, gap)
    # --- sync points (anchored sentences)
    syncs = []
    for k, it in enumerate(items):
        if it.get("at") is None:
            continue
        rt = rec.resolve_time(it["at"], near=r0, window=(r0, r1))
        if rt is None or not (r0 < rt < r1):
            log(f"WARN: narration anchor {it['at']!r} outside clip [{r0:.2f},{r1:.2f}] - ignored")
            continue
        if syncs and rt <= syncs[-1][0]:
            log(f"WARN: narration anchor {it['at']!r} is not after the previous anchor - ignored")
            continue
        syncs.append((rt, k))
    delays = [0.0] * len(items)
    pieces: list[Piece] = []
    prev_r, prev_t = r0, 0.0
    for rt, k in syncs:
        it = items[k]
        t_evt = sched[k] + delays[k] + float(it.get("align", 0.0)) * it["dur"] + float(it.get("offset", 0.0))
        T = t_evt - prev_t
        ps, Tout = solve_span(rec, prev_r, rt, max(T, 0.0), seg_cfg, speed, keep)
        if Tout > T + 1e-3:                        # visuals cannot fit: delay this and later sentences
            for j in range(k, len(items)):
                delays[j] += Tout - T
        pieces += ps
        prev_r, prev_t = rt, prev_t + Tout
    narr_end = (sched[-1] + delays[-1] + items[-1]["dur"]) if items else 0.0
    if items or seg.get("duration"):
        T_total = max(narr_end + tail if items else 0.0, float(seg.get("duration", 0.0)))
        T_last = T_total - prev_t
    elif isinstance(speed, (int, float)):
        T_last = (r1 - prev_r) / float(speed)
    else:                       # silent + auto: max(lead+tail, shortest acceptable clip)
        T_last = lead + tail
        seg_cfg["static_min"] = max(seg_cfg.get("static_min", 0.2), 0.5)
    ps, Tout = solve_span(rec, prev_r, r1, max(T_last, 0.05), seg_cfg, speed, keep)
    pieces += ps
    D = prev_t + Tout
    n_f = max(2, int(round(D * fps)))
    rec_t = pieces_to_frames(pieces, n_f, fps, smooth_s=float(seg.get("speed_smooth", 0.10)))
    rec_t = np.clip(rec_t, r0, r1)
    fidx_global = rec.frame_index(rec_t)
    uniq = sorted(set(int(i) for i in fidx_global))
    remap = {g: i for i, g in enumerate(uniq)}
    fidx = np.array([remap[int(i)] for i in fidx_global], np.int32)
    files = [str(rec.files[g]) for g in uniq]

    def out_time(rt: float) -> float:
        return float(np.searchsorted(rec_t, rt - 1e-6)) / fps

    # --- speed badge: smoothed playback speed >= 1.9x while the picture visibly changes
    win = max(2, int(1.0 * fps))
    idx = np.arange(n_f)
    lo, hi = np.clip(idx - win // 2, 0, n_f - 1), np.clip(idx + win // 2, 0, n_f - 1)
    inst = np.gradient(rec_t) * fps if n_f > 2 else np.ones(n_f)
    sg = 0.15 * fps
    kr = np.exp(-0.5 * (np.arange(-int(3 * sg), int(3 * sg) + 1) / sg) ** 2)
    rate = np.convolve(np.pad(inst, len(kr) // 2, mode="edge"), kr / kr.sum(), mode="valid")[:n_f]
    chg = np.cumsum(np.concatenate([[0], (np.diff(fidx_global) != 0).astype(np.int32)]))
    fast = (rate >= 1.9) & ((chg[hi] - chg[lo]) >= 3)
    badges = []
    if seg.get("badge", True):
        f = 0
        while f < n_f:
            if not fast[f]:
                f += 1
                continue
            g = f
            last = f
            while g < n_f and (fast[g] or (g - last) < int(1.2 * fps)):
                if fast[g]:
                    last = g
                g += 1
            if last - f + 1 >= int(0.8 * fps):
                x = float(np.percentile(rate[f:last + 1][fast[f:last + 1]], 90))
                badges.append({"t0": f / fps, "t1": (last + 1) / fps, "x": x,
                               "sprite": st.get("badge", text=f"빨리 감기 {fmt_speed(x)}")})
            f = g
    # --- camera
    cap_band = cfg["caption_band"] if ctx.script.get("captions", True) else 0
    O = overview_state(sw, sh, cfg)
    moves = []
    zooms = []
    def spec_box(spec: dict, default, near, window):
        if spec.get("box_css") is not None:
            return [float(v) * rec.css_scale for v in spec["box_css"]]
        return rec.resolve_box(spec.get("box", default), near=near, window=window)

    for z in seg.get("zoom", []) or []:
        zf = rec.resolve_time(z.get("from", r0), near=r0, window=(r0, r1))
        zt = rec.resolve_time(z.get("to"), near=zf, window=(r0, r1)) if z.get("to") is not None else None
        if zf is None:
            continue
        box = spec_box(z, "auto:click", zf, (zf, zt if zt is not None else r1))
        if box is None:
            continue
        if z.get("box_css") is None and (isinstance(z.get("box"), str) or z.get("box") is None):
            bx, by, bw, bh = box                                       # event target: add context
            m = 60 * rec.css_scale
            cw = max(bw + 2 * max(0.4 * bw, m), float(z.get("min_w", 0.27 * sw)))
            ch = max(bh + 2 * max(0.4 * bh, m), float(z.get("min_h", 0.28 * sh)))
            box = [bx + bw / 2 - cw / 2, by + bh / 2 - ch / 2, cw, ch]
        state = zoom_state(box, sw, sh, seg_cfg, z, cap_band)
        t_in = out_time(zf) + float(z.get("lead", 0.0))
        t_out = out_time(zt) + float(z.get("lead_out", 0.0)) if zt is not None else None
        if z.get("from_say") is not None and 0 <= int(z["from_say"]) < len(items):
            k = int(z["from_say"])
            t_in = sched[k] + delays[k] + float(z.get("lead", 0.0))
        if z.get("to_say") is not None and 0 <= int(z["to_say"]) < len(items):
            k = int(z["to_say"])
            t_out = sched[k] + delays[k] + float(z.get("lead_out", 0.0))
        zooms.append((t_in, t_out, state, z))
    zooms.sort(key=lambda a: a[0])
    start_state = O
    intro = seg.get("intro", "settle" if prev_type != "screen" else "none")
    if intro == "settle" and (not zooms or zooms[0][0] > 0.9):
        S0, tx0, ty0 = from_view(O)
        k = 0.94
        S1 = S0 * k
        start_state = to_view(S1, W / 2 - (W / 2 - tx0) * k, (H / 2) - (H / 2 - ty0) * k)
        moves.append((0.0, 1.2, O))
    S_O = W / O[2]
    last_S = S_O
    for i, (t_in, t_out, state, z) in enumerate(zooms):
        tgt_S = W / state[2]
        d = float(z.get("dur", min(1.4, max(0.75, 0.6 + 0.45 * abs(math.log(tgt_S / last_S))))))
        moves.append((t_in, d, state))
        last_S = tgt_S
        nxt = zooms[i + 1] if i + 1 < len(zooms) else None
        if t_out is not None and not (nxt and nxt[0] - t_out < 0.3):
            d_out = float(z.get("dur_out", min(1.3, max(0.75, 0.6 + 0.4 * abs(math.log(tgt_S / S_O))))))
            moves.append((t_out, d_out, O))
            last_S = S_O
    cam = camera_track(moves, n_f, fps, start_state)
    # --- callouts
    callouts = []
    for c in seg.get("callouts", []) or []:
        at = rec.resolve_time(c.get("at", r0), near=r0, window=(r0, r1))
        if at is None:
            continue
        default_box = "click"
        if isinstance(c.get("at"), (str, dict)):
            ev = rec.resolve_event(c["at"], near=r0, window=(r0, r1))
            if ev is not None and ev.get("box"):
                default_box = c["at"]                     # highlight the referenced element itself
        box = spec_box(c, default_box, at, (at - 0.5, r1))
        if box is None:
            continue
        raw_box = list(box)
        pad = float(c.get("pad", 6 * rec.css_scale))
        box = [box[0] - pad, box[1] - pad, box[2] + 2 * pad, box[3] + 2 * pad]
        t0 = out_time(at) + float(c.get("lead", 0.0))
        if c.get("say") is not None and 0 <= int(c["say"]) < len(items):
            k = int(c["say"])
            t0 = sched[k] + delays[k] + float(c.get("lead", 0.0))
        spot = c.get("spotlight", True)
        spot = 0.28 if spot is True else 0.0 if spot is False or spot is None else float(spot)
        t0 = max(0.0, t0)
        t1 = t0 + float(c.get("dur", 2.4))
        co = {"t0": t0, "t1": t1, "box": box,
              "chip": st.get("chip", text=c["text"]) if c.get("text") else None,
              "spotlight": spot,
              "position": c.get("position", "auto"), "radius": float(c.get("radius", 14)),
              "text": c.get("text", ""), "at_rec": float(at)}
        if c.get("track", True):
            f0 = max(0, int(math.floor(t0 * fps)))
            f1 = min(n_f - 1, int(math.ceil(t1 * fps)))
            # reference picture of the target: the event frame when the callout is tied to an event ("at"),
            # otherwise the frame the viewer actually sees when the ring appears (say-anchored / manual boxes)
            ref_rt = float(at) if c.get("at") is not None else float(rec_t[min(n_f - 1, int((t0 + 0.5) * fps))])
            co["at_rec"] = ref_rt
            ref_file = str(rec.files[int(rec.frame_index(ref_rt))])
            co["track"] = callout_track.track(raw_box, ref_file, files, fidx, f0, f1, (sw, sh),
                                              cursor=rec.cursor_at(ref_rt), cursor_scale=rec.css_scale)
            co["track"]["f0"] = f0
        callouts.append(co)
    # --- step labels: "label" (one, output seconds) or "labels" (list; "at" output s or "at_rec" rec time/event)
    labels = []
    labs = seg.get("labels")
    if labs is None:
        labs = [seg["label"]] if seg.get("label") else []
    for lab in labs:
        if isinstance(lab, str):
            lab = {"text": lab}
        t0 = float(lab.get("at", 0.55))
        if lab.get("at_rec") is not None:
            rt = rec.resolve_time(lab["at_rec"], near=r0, window=(r0, r1))
            if rt is not None:
                t0 = out_time(rt) + float(lab.get("lead", 0.0))
        if lab.get("say") is not None and 0 <= int(lab["say"]) < len(items):
            k = int(lab["say"])
            t0 = sched[k] + delays[k] + float(lab.get("lead", 0.0))
        labels.append({"sprite": st.get("label", kicker=lab.get("kicker", ""), text=lab["text"]),
                       "t0": max(0.0, t0), "t1": max(0.0, t0) + float(lab.get("dur", 3.6))})
    labels.sort(key=lambda lb: lb["t0"])
    for a, b in zip(labels[:-1], labels[1:]):
        a["t1"] = min(a["t1"], b["t0"] - 0.25)
    debug = {"rec": rec.rid, "from": r0, "to": r1, "dur": D,
             "pieces": [(round(float(p.ra), 2), round(float(p.rb), 2), round(float(p.dur), 2)) for p in pieces],
             "syncs": [(round(float(rt), 2), k) for rt, k in syncs]}
    sents = [(s + dl, it) for s, dl, it in zip(sched, delays, items)]
    return {"type": "screen", "dur": D, "n_f": n_f, "files": files, "fidx": fidx, "rec_t": rec_t,
            "cam": cam, "src_size": (sw, sh), "callouts": callouts, "labels": labels, "badges": badges,
            "sentences": sents, "debug": debug, "corner": float(seg.get("corner", 18)),
            "frame_scale": cfg["frame_scale"]}


# ==================================================================== plan
def chunk_caption(text: str, f, max_w: float) -> list[list[str]]:
    chunks = []
    for s in split_sentences(text) or [text]:
        lines = wrap_keep_all(s, f, max_w)
        if len(lines) <= 2:
            chunks.append(lines)
            continue
        words, cur = s.split(), []
        for w in words:
            trial = cur + [w]
            if len(wrap_keep_all(" ".join(trial), f, max_w)) <= 2:
                cur = trial
                continue
            cut = len(cur)
            for j in range(len(cur) - 1, max(len(cur) // 2, 1) - 1, -1):
                if cur[j - 1][-1] in ",.;:!?·":
                    cut = j
                    break
            chunks.append(wrap_keep_all(" ".join(cur[:cut]), f, max_w))
            cur = cur[cut:] + [w]
        if cur:
            chunks.append(wrap_keep_all(" ".join(cur), f, max_w))
    return chunks


def build_plan(script: dict, overrides: dict | None = None) -> dict:
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in script.items() if k in DEFAULTS})
    cfg.update(overrides or {})
    ctx = Ctx(script, cfg)
    fps = ctx.fps
    X = float(cfg["transition"])
    segs = script["segments"]

    def x_into(i: int) -> float:              # crossfade INTO segment i ("transition" on the segment overrides)
        return float(segs[i].get("transition", X)) if 0 < i < len(segs) else 0.0

    tts = TTS(voice=script.get("voice", DEFAULT_VOICE), rate=float(script.get("speaking_rate", 1.0)),
              lexicon=script.get("lexicon", True))
    seg_items = [normalize_narration(s.get("narration")) for s in segs]
    jobs = [(it["text"], s.get("voice"), s.get("speaking_rate"), it.get("say"))
            for s, items in zip(segs, seg_items) for it in items]
    infos = tts.synth_many(jobs) if jobs else []
    k = 0
    for items in seg_items:
        for it in items:
            it["dur"], it["wav"] = infos[k]["dur"], infos[k]["wav"]
            k += 1
    out = []
    for i, (seg, items) in enumerate(zip(segs, seg_items)):
        x_in = x_into(i)
        x_out = x_into(i + 1)
        lead = float(seg.get("lead", cfg["lead"])) + 0.5 * x_in
        tail = float(seg.get("tail", cfg["tail"])) + 0.5 * x_out
        t = seg.get("type")
        if t == "screen":
            ps = build_screen(seg, ctx, items, lead, tail, segs[i - 1].get("type") if i else None)
        elif t in ("title", "outro"):
            ps = build_title(seg, ctx, items, lead, tail, kind=t)
        elif t == "card":
            ps = build_card(seg, ctx, items, lead, tail)
        else:
            raise ValueError(f"segment {i}: unknown type {t!r}")
        ps.setdefault("n_f", max(2, int(round(ps["dur"] * fps))))
        ps["index"] = i
        out.append(ps)
    # brand line stays put across consecutive title/card/outro segments (no fade out/in between them)
    cardish = ("title", "card", "outro")
    for i, ps in enumerate(out):
        for e in ps.get("els", []):
            if e.get("role") == "brand":
                e["keep_in"] = i > 0 and out[i - 1]["type"] in cardish
                e["keep_out"] = i < len(out) - 1 and out[i + 1]["type"] in cardish
    start = 0
    for i, ps in enumerate(out):
        ps["start_f"] = start
        ps["xf_in"] = out[i - 1]["xf_out"] if i else 0
        if i < len(out) - 1:
            ps["xf_out"] = min(int(round(x_into(i + 1) * fps)), ps["n_f"] // 2, out[i + 1]["n_f"] // 2)
            start += ps["n_f"] - ps["xf_out"]
        else:
            ps["xf_out"] = 0
    total_f = out[-1]["start_f"] + out[-1]["n_f"]
    total = total_f / fps
    # narration + captions
    narration, cues = [], []
    fcap = font("semibold", 40)
    for ps in out:
        base = ps["start_f"] / fps
        for ls, it in ps["sentences"]:
            g0 = base + ls
            narration.append((g0, it["wav"], it["dur"], it["text"]))
            if not script.get("captions", True):
                continue
            chunks = chunk_caption(it.get("caption", it["text"]), fcap, cfg["caption_max_w"])
            weights = [max(1, len("".join(c).replace(" ", ""))) for c in chunks]
            t = g0
            for lines, wgt in zip(chunks, weights):
                d = it["dur"] * wgt / sum(weights)
                cues.append({"t0": t, "t1": t + d, "lines": lines})
                t += d
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["t0"] if i + 1 < len(cues) else total
        c["t1"] = nxt if nxt - c["t1"] < 0.6 else min(nxt - 0.05, c["t1"] + 0.35)
        c["t1"] = min(c["t1"], total - 0.3)
        c["sprite"] = ctx.store.get("caption", lines=c["lines"])
    for i, c in enumerate(cues):
        if i + 1 < len(cues) and 0 < cues[i + 1]["t0"] - c["t1"] < 0.4:
            c["t1"] = cues[i + 1]["t0"]
    for i, c in enumerate(cues):
        c["fin"] = not (i > 0 and c["t0"] - cues[i - 1]["t1"] < 0.05)
        c["fout"] = not (i + 1 < len(cues) and cues[i + 1]["t0"] - c["t1"] < 0.05)
    poster = script.get("poster")
    if poster is None:
        first = out[0]
        poster = (first["start_f"] / fps + min(2.6, first["dur"] - 0.6)) if first["type"] == "title" else \
            next((p["start_f"] / fps + p["dur"] / 2 for p in out if p["type"] == "screen"), total / 2)
    return {"id": script["id"], "title": script.get("title", script["id"]), "W": W, "H": H, "fps": fps,
            "total_f": total_f, "segments": out, "cues": cues, "narration": narration, "cfg": cfg,
            "poster": float(poster), "fade_in": float(script.get("fade_in", 0.4)),
            "fade_out": float(script.get("fade_out", 0.8)), "bgm": script.get("bgm", True),
            "encode": dict(script.get("encode", {}))}


def describe(plan: dict) -> str:
    fps = plan["fps"]
    lines = [f"{plan['id']}: {plan['total_f']} frames = {plan['total_f'] / fps:.2f}s @ {fps}fps"]
    for ps in plan["segments"]:
        s = ps["start_f"] / fps
        lines.append(f"  [{ps['index']}] {ps['type']:<6} {s:7.2f}s -> {s + ps['n_f'] / fps:7.2f}s ({ps['n_f'] / fps:.2f}s)")
        if ps["type"] == "screen":
            d = ps["debug"]
            lines.append(f"        rec {d['rec']} {d['from']:.2f}-{d['to']:.2f}  syncs {d['syncs']}")
            lines.append(f"        pieces (rec_a, rec_b, out_s): {d['pieces']}")
            for b in ps["badges"]:
                lines.append(f"        badge {b['t0']:.2f}-{b['t1']:.2f}  x{b.get('x', 0):.1f}")
            for c in ps["callouts"]:
                lines.append(f"        callout {c['t0']:.2f}-{c['t1']:.2f} box={[round(v) for v in c['box']]}")
        for ls, it in ps["sentences"]:
            lines.append(f"        say {s + ls:7.2f}s +{it['dur']:.2f}s  {it['text']}")
    return "\n".join(lines)
