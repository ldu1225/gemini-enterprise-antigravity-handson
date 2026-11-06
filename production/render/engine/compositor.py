"""Per-frame compositor.  Runs inside worker processes (one plan per process, loaded once).

Screen frames:  dark gradient background -> soft two-layer drop shadow -> recording warped with a
float affine (sub-pixel camera, bicubic) inside an anti-aliased rounded "device" mask -> inner
highlight -> callouts (spotlight + animated gradient ring + label chip) -> fast-forward badge ->
step label.  Then segment crossfades, burned-in captions and global fades are applied.
"""
from __future__ import annotations

import math
import pickle
from collections import OrderedDict

import cv2
import numpy as np

from .common import (GEMINI, H, W, clamp01, ease_in_cubic, ease_in_out_cubic, ease_out_back, ease_out_cubic,
                     gemini_gradient, hex_bgr)

_P: dict | None = None
_C: dict = {}
SQRT2 = math.sqrt(2.0)


def init_worker(plan_or_path):
    global _P
    cv2.setNumThreads(1)
    if isinstance(plan_or_path, dict):
        _P = plan_or_path
    else:
        with open(plan_or_path, "rb") as f:
            _P = pickle.load(f)
    _C.clear()
    _C["frames"] = OrderedDict()
    _C["sprites"] = {}


# =================================================================== assets
def _erfc(x):
    from scipy.special import erfc
    return erfc(x)


def sdf_full(w, h, x0, y0, x1, y1, r, scale=1.0):
    """Rounded-rect signed distance on a w x h grid whose pixel (i,j) covers [j*scale, (j+1)*scale)."""
    xs = (np.arange(w, dtype=np.float32) + 0.5) * scale
    ys = (np.arange(h, dtype=np.float32) + 0.5) * scale
    cx, cy, bx, by = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    r = float(max(0.0, min(r, bx, by)))
    qx = (np.abs(xs - cx) - bx + r)[None, :]
    qy = (np.abs(ys - cy) - by + r)[:, None]
    ox, oy = np.maximum(qx, 0), np.maximum(qy, 0)
    return np.sqrt(ox * ox + oy * oy) + np.minimum(np.maximum(qx, qy), 0) - r


def _noise():
    if "noise" not in _C:
        rng = np.random.default_rng(7)
        _C["noise"] = (rng.random((H, W, 1), np.float32) + rng.random((H, W, 1), np.float32) - 1.0)
    return _C["noise"]


def _glow(acc, cx, cy, r, color, s, xs, ys):
    d2 = ((xs - cx) ** 2)[None, :] + ((ys - cy) ** 2)[:, None]
    g = np.exp(-d2 / (2 * r * r)) * s
    acc += g[..., None] * np.asarray(color, np.float32)[None, None, :]


def screen_bg() -> np.ndarray:
    if "bg" in _C:
        return _C["bg"]
    lw, lh = W // 4, H // 4
    xs, ys = np.arange(lw, dtype=np.float32), np.arange(lh, dtype=np.float32)
    top, bot = np.array(hex_bgr("#111827"), np.float32), np.array(hex_bgr("#07090F"), np.float32)
    v = (ys / (lh - 1))[:, None, None]
    acc = top * (1 - v) + bot * v
    acc = np.broadcast_to(acc, (lh, lw, 3)).copy()
    _glow(acc, 0.08 * lw, 0.95 * lh, 0.42 * lw, hex_bgr(GEMINI[0]), 0.26, xs, ys)
    _glow(acc, 0.94 * lw, 0.04 * lh, 0.36 * lw, hex_bgr(GEMINI[1]), 0.20, xs, ys)
    _glow(acc, 0.78 * lw, 1.05 * lh, 0.26 * lw, hex_bgr(GEMINI[2]), 0.12, xs, ys)
    yy = ((ys - lh / 2) / (lh / 2))[:, None]
    xx = ((xs - lw / 2) / (lw / 2))[None, :]
    acc *= (1 - 0.22 * np.clip(xx * xx * 0.6 + yy * yy * 0.8, 0, 1))[..., None]
    up = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    _C["bg"] = np.clip(up + _noise() * 0.9, 0, 255).astype(np.uint8)
    return _C["bg"]


def title_bg(t: float, kind: str) -> np.ndarray:
    """Dark #0B0F17 with slowly drifting Gemini-gradient glows (rendered at 1/4 res, dithered)."""
    lw, lh = W // 4, H // 4
    xs, ys = np.arange(lw, dtype=np.float32), np.arange(lh, dtype=np.float32)
    base = np.array(hex_bgr("#0B0F17"), np.float32)
    acc = np.broadcast_to(base, (lh, lw, 3)).copy()
    k = {"title": 1.0, "outro": 0.9, "card": 0.55}.get(kind, 0.8)
    blobs = [(GEMINI[0], 0.30, 0.70, 0.30, 0.42), (GEMINI[1], 0.68, 0.36, 0.28, 0.34),
             (GEMINI[2], 0.62, 0.86, 0.22, 0.26), (GEMINI[0], 0.86, 0.10, 0.18, 0.14)]
    if kind == "card":
        blobs = [(GEMINI[0], 0.06, 0.92, 0.34, 0.40), (GEMINI[1], 0.96, 0.06, 0.28, 0.30),
                 (GEMINI[2], 0.90, 0.98, 0.18, 0.18)]
    for i, (col, bx, by, r, s) in enumerate(blobs):
        cx = (bx + 0.045 * math.sin(0.33 * t + i * 2.1)) * lw
        cy = (by + 0.035 * math.cos(0.27 * t + i * 1.3)) * lh
        _glow(acc, cx, cy, r * lw, hex_bgr(col), s * k, xs, ys)
    yy = ((ys - lh / 2) / (lh / 2))[:, None]
    xx = ((xs - lw / 2) / (lw / 2))[None, :]
    acc *= (1 - 0.30 * np.clip(xx * xx * 0.5 + yy * yy * 0.7, 0, 1))[..., None]
    up = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    return np.clip(up + _noise() * 0.9, 0, 255).astype(np.uint8)


def frame_img(path: str, size) -> np.ndarray:
    cache = _C["frames"]
    if path in cache:
        cache.move_to_end(path)
        return cache[path]
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"cannot read frame {path}")
    if (img.shape[1], img.shape[0]) != tuple(size):
        img = cv2.resize(img, tuple(size), interpolation=cv2.INTER_AREA)
    cache[path] = img
    if len(cache) > 10:
        cache.popitem(last=False)
    return img


def sprite(meta: dict) -> dict:
    sc = _C["sprites"]
    key = meta["path"]
    if key in sc:
        return sc[key]
    img = cv2.imread(key, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise IOError(f"cannot read sprite {key}")
    a = img[..., 3].astype(np.float32) / 255.0
    pa = np.dstack([img[..., :3].astype(np.float32) * a[..., None], a * 255.0]).astype(np.float32)
    gm = None
    if meta.get("glass"):
        x, y, w, h, r = meta["glass"]
        gm = np.clip(0.5 - sdf_full(pa.shape[1], pa.shape[0], x, y, x + w, y + h, r), 0, 1).astype(np.float32)
    s = {"pa": pa, "gm": gm, "meta": meta, "w": pa.shape[1], "h": pa.shape[0]}
    sc[key] = s
    return s


# =================================================================== blending
def blit(dst: np.ndarray, meta: dict, x: float, y: float, opacity: float = 1.0, scale: float = 1.0,
         blur: float = 14.0):
    """Composite a premultiplied sprite at float top-left (x, y) with optional scale; glass blur if the sprite has one."""
    if opacity <= 0.003:
        return
    s = sprite(meta)
    pa, gm = s["pa"], s["gm"]
    h, w = pa.shape[:2]
    integer = abs(scale - 1) < 1e-6 and abs(x - round(x)) < 1e-3 and abs(y - round(y)) < 1e-3
    if integer:
        xi, yi = int(round(x)), int(round(y))
        cx0, cy0, cx1, cy1 = max(xi, 0), max(yi, 0), min(xi + w, W), min(yi + h, H)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        src = pa[cy0 - yi:cy1 - yi, cx0 - xi:cx1 - xi]
        g = gm[cy0 - yi:cy1 - yi, cx0 - xi:cx1 - xi] if gm is not None else None
    else:
        X0, Y0 = math.floor(x), math.floor(y)
        X1, Y1 = math.ceil(x + w * scale), math.ceil(y + h * scale)
        cx0, cy0, cx1, cy1 = max(X0, 0), max(Y0, 0), min(X1, W), min(Y1, H)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        rw, rh = cx1 - cx0, cy1 - cy0
        M = np.float32([[scale, 0, x - cx0], [0, scale, y - cy0]])
        src = cv2.warpAffine(pa, M, (rw, rh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        np.clip(src[..., 3], 0, 255, out=src[..., 3])
        np.clip(src[..., :3], 0, src[..., 3:4], out=src[..., :3])
        g = cv2.warpAffine(gm, M, (rw, rh), flags=cv2.INTER_LINEAR) if gm is not None else None
    region = dst[cy0:cy1, cx0:cx1].astype(np.float32)
    if g is not None and blur > 0:
        bl = cv2.GaussianBlur(region, (0, 0), blur)
        region += (bl - region) * (g * opacity)[..., None]
    region = src[..., :3] * opacity + region * (1.0 - src[..., 3:4] * (opacity / 255.0))
    dst[cy0:cy1, cx0:cx1] = np.clip(region + 0.5, 0, 255).astype(np.uint8)


# =============================================================== screen frames
def window_layers(seg, S, tx, ty):
    key = ("wl", seg["index"], round(S, 6), round(tx, 4), round(ty, 4))
    if _C.get("wl_key") == key:
        return _C["wl"]
    sw, sh = seg["src_size"]
    S0 = W * seg["frame_scale"] / sw
    k = S / S0
    x0, y0, x1, y1 = tx, ty, tx + S * sw, ty + S * sh
    r = seg["corner"] * k
    sd = sdf_full(W, H, x0, y0, x1, y1, r)
    mask = np.clip(0.5 - sd, 0, 1).astype(np.float32)
    # soft shadows at half resolution (they are blurry anyway)
    q = 2
    sdk = sdf_full(W // q, H // q, x0, y0 + 26 * k, x1, y1 + 26 * k, r, scale=q)
    sda = sdf_full(W // q, H // q, x0, y0 + 4 * k, x1, y1 + 4 * k, r, scale=q)
    a_key = 0.5 * _erfc(sdk / (44 * k * SQRT2)) * 0.62
    a_amb = 0.5 * _erfc(sda / (10 * k * SQRT2)) * 0.40
    a_sh = (1 - (1 - a_key) * (1 - a_amb)).astype(np.float32)
    a_sh = cv2.resize(a_sh, (W, H), interpolation=cv2.INTER_LINEAR)
    bgs = (screen_bg().astype(np.float32) * (1 - a_sh)[..., None])
    bgs = np.clip(bgs + 0.5, 0, 255).astype(np.uint8)
    ring = (np.clip(1.0 - np.abs(sd + 0.9), 0, 1) * 0.16).astype(np.float32)
    lay = {"bgs": bgs, "mask": mask, "inv": (1.0 - mask).astype(np.float32), "ring": ring,
           "rect": (x0, y0, x1, y1)}
    _C["wl_key"], _C["wl"] = key, lay
    return lay


def _apply_ring(out, ring, rect):
    """Lighten the 1px inner edge of the device frame. `ring` is consumed (zeroed band by band) so the
    overlapping corner areas of the four edge bands are only applied once."""
    x0, y0, x1, y1 = rect
    bands = [(math.floor(y0) - 2, math.ceil(y0) + 3, 0, W), (math.floor(y1) - 3, math.ceil(y1) + 2, 0, W),
             (0, H, math.floor(x0) - 2, math.ceil(x0) + 3), (0, H, math.floor(x1) - 3, math.ceil(x1) + 2)]
    for ya, yb, xa, xb in bands:
        ya, yb, xa, xb = max(ya, 0), min(yb, H), max(xa, 0), min(xb, W)
        if yb <= ya or xb <= xa:
            continue
        rg = ring[ya:yb, xa:xb]
        if rg.max() <= 0:
            continue
        reg = out[ya:yb, xa:xb].astype(np.float32)
        reg += (255.0 - reg) * rg[..., None]
        out[ya:yb, xa:xb] = np.clip(reg + 0.5, 0, 255).astype(np.uint8)
        rg[:] = 0


def _sharpened(src: np.ndarray, path: str, S: float) -> np.ndarray:
    """Unsharp mask proportional to the magnification (only when upscaling noticeably)."""
    amt = clamp01((S - 1.4) / 0.8) * 0.55
    if amt < 0.03:
        return src
    if _C.get("blur_key") != path:
        _C["blur_key"], _C["blur"] = path, cv2.GaussianBlur(src, (0, 0), 1.1)
    return cv2.addWeighted(src, 1.0 + amt, _C["blur"], -amt, 0)


def composite_window(seg, src, S, tx, ty, path=""):
    sw, sh = seg["src_size"]
    M = np.float32([[S, 0, tx], [0, S, ty]])
    x0, y0, x1, y1 = tx, ty, tx + S * sw, ty + S * sh
    src = _sharpened(src, path, S)
    content = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if x0 <= 0.01 and y0 <= 0.01 and x1 >= W - 0.01 and y1 >= H - 0.01:
        return content                                    # zoomed in: recording fills the frame
    lay = window_layers(seg, S, tx, ty)
    out = cv2.blendLinear(content, lay["bgs"], lay["mask"], lay["inv"])
    _apply_ring(out, lay["ring"].copy(), lay["rect"])
    return out


def callout_offset(c, lf):
    """(dx, dy, visibility 0..1) of a tracked callout at segment frame lf."""
    tr = c.get("track")
    if not tr or lf is None:
        return 0.0, 0.0, 1.0
    k = lf - tr["f0"]
    n = len(tr["vis"])
    if n == 0:
        return 0.0, 0.0, 1.0
    k = min(max(k, 0), n - 1)
    lo, hi = max(0, k - 5), min(n, k + 6)
    v = float(np.mean(tr["vis"][lo:hi]))          # soft fade in/out around hidden stretches
    return float(tr["dx"][k]), float(tr["dy"][k]), ease_in_out_cubic(v)


def draw_callout(out, c, t, S, tx, ty, S0, lf=None):
    t0, t1 = c["t0"], c["t1"]
    if not (t0 <= t <= t1):
        return
    a_in = ease_out_cubic((t - t0) / 0.45)
    a_out = ease_in_out_cubic(clamp01((t1 - t) / 0.35))
    dx, dy, a_vis = callout_offset(c, lf)
    alpha = min(a_in, a_out) * a_vis
    if alpha <= 0.003:
        return
    bx, by, bw, bh = c["box"]
    bx, by = bx + dx, by + dy
    X0, Y0 = S * bx + tx, S * by + ty
    X1, Y1 = X0 + S * bw, Y0 + S * bh
    X0, Y0, X1, Y1 = max(X0, 4.0), max(Y0, 4.0), min(X1, W - 4.0), min(Y1, H - 4.0)   # keep the ring visible
    if X1 - X0 < 4 or Y1 - Y0 < 4:
        return
    hw, hh = (X1 - X0) / 2, (Y1 - Y0) / 2
    r = min(c["radius"] * max(1.0, S / S0 * 0.75), hw, hh)
    # spotlight: dim everything outside the target
    if c["spotlight"] > 0:
        q = 4
        sd = sdf_full(W // q, H // q, X0 - 4, Y0 - 4, X1 + 4, Y1 + 4, r + 4, scale=q)
        outside = np.clip(sd / 26.0, 0, 1).astype(np.float32)
        outside = cv2.resize(outside, (W, H), interpolation=cv2.INTER_LINEAR)
        fac = 1.0 - (c["spotlight"] * alpha) * outside
        out[:] = np.clip(out.astype(np.float32) * fac[..., None] + 0.5, 0, 255).astype(np.uint8)
    # gradient ring + soft glow
    m = 34
    rx0, ry0 = max(0, math.floor(X0 - m)), max(0, math.floor(Y0 - m))
    rx1, ry1 = min(W, math.ceil(X1 + m)), min(H, math.ceil(Y1 + m))
    if rx1 > rx0 and ry1 > ry0:
        sd = sdf_full(rx1 - rx0, ry1 - ry0, X0 - rx0, Y0 - ry0, X1 - rx0, Y1 - ry0, r)
        stroke = 4.0
        ring = np.clip(stroke / 2 + 0.5 - np.abs(sd - stroke / 2), 0, 1)
        pulse = 0.8 + 0.2 * math.sin(2 * math.pi * (t - t0) / 1.5)
        glow = np.exp(-np.maximum(sd - stroke, 0) ** 2 / (2 * 11.0 ** 2)) * (sd > 0) * 0.55 * pulse
        g = gemini_gradient(rx1 - rx0)[:, ::-1]              # RGB -> BGR
        xs = np.clip((np.arange(rx0, rx1) - X0) / max(1.0, X1 - X0), 0, 1)
        idx = (xs * (len(g) - 1)).astype(np.int32)
        grad = np.broadcast_to(g[idx][None, :, :], (ry1 - ry0, rx1 - rx0, 3))
        reg = out[ry0:ry1, rx0:rx1].astype(np.float32)
        ga = (glow * alpha)[..., None]
        reg = reg * (1 - ga) + np.array(hex_bgr("#8AB4F8"), np.float32) * ga
        ra = (ring * alpha)[..., None]
        reg = reg * (1 - ra) + grad * ra
        out[ry0:ry1, rx0:rx1] = np.clip(reg + 0.5, 0, 255).astype(np.uint8)
    # label chip
    chip = c.get("chip")
    if chip:
        ac = min(ease_out_cubic((t - t0 - 0.12) / 0.4), a_out) * a_vis
        if ac > 0.003:
            bxm, bym, bwc, bhc = chip["body"]
            cxp = min(max((X0 + X1) / 2, bwc / 2 + 24), W - bwc / 2 - 24)
            above = Y0 - 16 - bhc
            below = Y1 + 16
            pos = c.get("position", "auto")
            fits_above = above > 24
            fits_below = below + bhc <= H - 190                       # keep clear of the caption band
            if pos == "top":
                use = "above" if fits_above else "inside"
            elif pos == "bottom":
                use = "below" if fits_below else "inside"
            else:
                use = "above" if fits_above else "below" if fits_below else "inside"
            if use == "above":
                body_y, dy = above, 10 * (1 - ac)
            elif use == "below":
                body_y, dy = below, -10 * (1 - ac)
            else:                                                      # tall target: chip inside the top edge
                body_y, dy = max(24.0, Y0 + 12), -6 * (1 - ac)
            blit(out, chip, cxp - bwc / 2 - bxm, body_y - bym + dy, opacity=ac, blur=0)


def render_screen(seg, lf: int, t: float) -> np.ndarray:
    S, tx, ty = (float(v) for v in seg["cam"][lf])
    fi = int(seg["fidx"][lf])
    key = (seg["index"], fi, round(S, 6), round(tx, 4), round(ty, 4))
    if _C.get("base_key") == key:
        out = _C["base"].copy()
    else:
        src = frame_img(seg["files"][fi], seg["src_size"])
        base = composite_window(seg, src, S, tx, ty, seg["files"][fi])
        _C["base_key"], _C["base"] = key, base
        out = base.copy()
    S0 = W * seg["frame_scale"] / seg["src_size"][0]
    for c in seg["callouts"]:
        draw_callout(out, c, t, S, tx, ty, S0, lf)
    for b in seg["badges"]:
        if b["t0"] - 0.3 <= t <= b["t1"] + 0.3:
            a = min(clamp01((t - b["t0"] + 0.3) / 0.3), clamp01((b["t1"] + 0.3 - t) / 0.3))
            spr = b["sprite"]
            bxm, bym, bwc, bhc = spr["body"]
            blit(out, spr, W - 44 - bwc - bxm, 40 - bym, opacity=ease_in_out_cubic(a))
    labs = seg.get("labels")
    if labs is None:
        labs = [seg["label"]] if seg.get("label") else []
    for lab in labs:
        if not (lab["t0"] <= t <= lab["t1"]):
            continue
        a_in = ease_out_cubic((t - lab["t0"]) / 0.6)
        a_out = ease_in_out_cubic(clamp01((lab["t1"] - t) / 0.45))
        spr = lab["sprite"]
        bxm, bym, bwc, bhc = spr["body"]
        blit(out, spr, 56 - bxm - 30 * (1 - a_in), H - 178 - bhc - bym, opacity=min(a_in, a_out))
    return out


# ============================================================== cards/titles
def render_card(seg, lf: int, t: float) -> np.ndarray:
    kind = seg["type"]
    out = title_bg(t, kind)
    D = seg["dur"]
    fps = _P["fps"]
    x_in = seg.get("xf_in", 0) / fps
    x_out = seg.get("xf_out", 0) / fps
    # exit: text leaves before the outgoing dissolve starts (no double exposure over the next scene)
    a_exit, dy_exit = 1.0, 0.0
    if x_out > 0:
        pe = (t - (D - x_out - 0.12)) / 0.40
        a_exit = 1.0 - ease_in_out_cubic(pe)
        dy_exit = -16 * ease_in_cubic(clamp01(pe))
    gs = 1.0 + (0.022 * t / max(D, 1.0) if kind in ("title", "outro") else 0.0)
    for e in seg["els"]:
        if e["role"] == "brand":                       # brand line: fixed position, persists across cards
            a = 1.0 if e.get("keep_in") else ease_out_cubic((t - e["delay"] - 0.75 * x_in) / 0.85)
            if not e.get("keep_out"):
                a *= a_exit
            if a > 0.003:
                blit(out, e["sprite"], e["x"], e["y"], opacity=a, blur=0)
            continue
        if a_exit <= 0.003:
            continue
        p = (t - e["delay"] - (0.0 if e.get("abs") else 0.75 * x_in)) / 0.85
        if p <= 0:
            continue
        a = ease_out_cubic(p) * a_exit
        x, y, sc = e["x"], e["y"] + dy_exit, 1.0
        if e["role"] in ("bullet", "check"):
            x -= 26 * (1 - ease_out_cubic(p))
        elif e["role"] == "icon":
            sc = 0.82 + 0.18 * ease_out_back(clamp01(p * 1.1))
            spr = e["sprite"]
            x += spr["w"] * (1 - sc) / 2
            y += spr["h"] * (1 - sc) / 2
        else:
            y += 26 * (1 - ease_out_cubic(p))
        if gs != 1.0:
            x, y, sc = W / 2 + (x - W / 2) * gs, H / 2 + (y - H / 2) * gs, sc * gs
        blit(out, e["sprite"], x, y, opacity=a, scale=sc, blur=0)
        if seg.get("accent") and e["role"] == "kicker":
            # animated gradient rule under the kicker
            m = e["sprite"]
            p2 = ease_in_out_cubic((t - e["delay"] - 0.25) / 0.9)
            if p2 > 0:
                base_y = y + (m["first_base"] + 0.08 * 30 + 20) * gs
                half = 70 * p2 * gs
                X0, X1, Y0, Y1 = W / 2 - half, W / 2 + half, base_y, base_y + 4 * gs
                rx0, ry0, rx1, ry1 = math.floor(X0) - 2, math.floor(Y0) - 2, math.ceil(X1) + 2, math.ceil(Y1) + 2
                sd = sdf_full(rx1 - rx0, ry1 - ry0, X0 - rx0, Y0 - ry0, X1 - rx0, Y1 - ry0, 2 * gs)
                al = (np.clip(0.5 - sd, 0, 1) * a)[..., None]
                g = gemini_gradient(rx1 - rx0)[:, ::-1]
                reg = out[ry0:ry1, rx0:rx1].astype(np.float32)
                reg = reg * (1 - al) + g[None, :, :] * al
                out[ry0:ry1, rx0:rx1] = np.clip(reg + 0.5, 0, 255).astype(np.uint8)
    return out


# =================================================================== frames
def render_seg(seg, lf: int) -> np.ndarray:
    t = lf / _P["fps"]
    if seg["type"] == "screen":
        return render_screen(seg, lf, t)
    return render_card(seg, lf, t)


def draw_captions(img, T: float):
    for c in _P["cues"]:
        fi = 0.16 if c.get("fin", True) else 0.0           # soft fade only at isolated edges;
        fo = 0.16 if c.get("fout", True) else 0.0          # back-to-back cues cut cleanly (no double pill)
        if not (c["t0"] - fi <= T < c["t1"] + fo):
            continue
        a_in = clamp01((T - c["t0"] + fi) / fi) if fi > 0 else 1.0
        a_out = clamp01((c["t1"] + fo - T) / fo) if fo > 0 else 1.0
        a = min(a_in, a_out)
        if a <= 0:
            continue
        spr = c["sprite"]
        rise = 6 * (1 - ease_out_cubic(clamp01((T - c["t0"] + 0.16) / 0.3))) if fi > 0 else 0.0
        blit(img, spr, (W - spr["w"]) / 2, H - 40 - spr["h"] + rise, opacity=ease_in_out_cubic(a), blur=12)


def render_frame(f: int) -> np.ndarray:
    P = _P
    fps = P["fps"]
    act = [s for s in P["segments"] if s["start_f"] <= f < s["start_f"] + s["n_f"]]
    if not act:
        act = [P["segments"][-1]]
    if len(act) == 1:
        img = render_seg(act[0], min(f - act[0]["start_f"], act[0]["n_f"] - 1))
    else:
        A, B = act[0], act[1]
        a = render_seg(A, f - A["start_f"])
        b = render_seg(B, f - B["start_f"])
        p = (f - B["start_f"] + 1) / (A["xf_out"] + 1)
        w = ease_in_out_cubic(p)
        img = cv2.addWeighted(a, 1 - w, b, w, 0)
    T = f / fps
    draw_captions(img, T)
    total = P["total_f"] / fps
    k = min(clamp01(T / P["fade_in"]) if P["fade_in"] > 0 else 1.0,
            clamp01((total - T - 1 / fps) / P["fade_out"]) if P["fade_out"] > 0 else 1.0)
    if k < 1.0:
        img = cv2.convertScaleAbs(img, alpha=ease_in_out_cubic(k) if k > 0 else 0.0)
    return img


def render_chunk(rng: tuple[int, int]) -> bytes:
    f0, f1 = rng
    buf = np.empty((f1 - f0, H, W, 3), np.uint8)
    for i, f in enumerate(range(f0, f1)):
        buf[i] = render_frame(f)
    return buf.tobytes()
