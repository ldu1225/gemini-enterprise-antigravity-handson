"""Typography + static overlay sprites (captions, chips, badges, step labels, card text).

Text is rendered with FreeType (PIL) using Pretendard; shapes are drawn with signed-distance
fields in numpy so every edge is analytically anti-aliased.  Sprites are cached as straight-alpha
RGBA PNGs (+ JSON meta) under cache/sprites/ and animated/composited per frame by the compositor.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .common import CACHE_DIR, FONTS_DIR, GEMINI, gemini_gradient, hex_rgb, log, sha

SPRITE_VERSION = 8
WEIGHTS = {
    "regular": "Pretendard-Regular.otf",
    "medium": "Pretendard-Medium.otf",
    "semibold": "Pretendard-SemiBold.otf",
    "bold": "Pretendard-Bold.otf",
    "extrabold": "Pretendard-ExtraBold.otf",
}
_FALLBACK = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
_FALLBACK_STYLE = {"regular": "Regular", "medium": "Medium", "semibold": "SemiBold", "bold": "Bold", "extrabold": "ExtraBold"}


@lru_cache(maxsize=64)
def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    p = FONTS_DIR / WEIGHTS.get(weight, WEIGHTS["regular"])
    if p.exists():
        return ImageFont.truetype(str(p), size)
    want = _FALLBACK_STYLE.get(weight, "Regular")
    for i in range(16):
        try:
            f = ImageFont.truetype(_FALLBACK, size, index=i)
        except OSError:
            break
        if f.getname()[1].replace(" ", "").lower() == want.lower():
            return f
    return ImageFont.truetype(_FALLBACK, size, index=0)


def text_w(s: str, f, tracking: float = 0.0) -> float:
    if not s:
        return 0.0
    if not tracking:
        return f.getlength(s)
    return sum(f.getlength(c) for c in s) + tracking * (len(s) - 1)


def wrap_keep_all(text: str, f, max_w: float, tracking: float = 0.0, balance: bool = True) -> list[str]:
    """Line-break only at spaces (CSS word-break: keep-all) and balance 2-line paragraphs."""
    out: list[str] = []
    for para in str(text).split("\n"):
        words = para.split()
        if not words:
            out.append("")
            continue
        lines, cur = [], words[0]
        for w in words[1:]:
            if text_w(cur + " " + w, f, tracking) <= max_w:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if balance and len(lines) == 2:
            best = None
            for k in range(1, len(words)):
                a, b = " ".join(words[:k]), " ".join(words[k:])
                wa, wb = text_w(a, f, tracking), text_w(b, f, tracking)
                if max(wa, wb) > max_w:
                    continue
                score = max(wa, wb) + 0.25 * max(0.0, wb - wa)   # prefer a slightly longer first line
                if a[-1] in ".,!?…:;·":
                    score -= 0.12 * max(wa, wb)                    # ...and breaks right after punctuation
                if best is None or score < best[0]:
                    best = (score, [a, b])
            if best:
                lines = best[1]
        out += lines
    return out


def draw_line(d: ImageDraw.ImageDraw, x: float, baseline: float, s: str, f, tracking: float = 0.0, fill=255):
    if not tracking:
        d.text((x, baseline), s, font=f, fill=fill, anchor="ls")
        return
    for c in s:
        d.text((x, baseline), c, font=f, fill=fill, anchor="ls")
        x += f.getlength(c) + tracking


# ------------------------------------------------------------------ SDF shapes
def sdf_rrect(w: int, h: int, x0, y0, x1, y1, r) -> np.ndarray:
    ys = np.arange(h, dtype=np.float32)[:, None] + 0.5
    xs = np.arange(w, dtype=np.float32)[None, :] + 0.5
    cx, cy, bx, by = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    r = float(min(r, bx, by))
    qx = np.abs(xs - cx) - bx + r
    qy = np.abs(ys - cy) - by + r
    ox, oy = np.maximum(qx, 0), np.maximum(qy, 0)
    return np.sqrt(ox * ox + oy * oy) + np.minimum(np.maximum(qx, qy), 0) - r


def fill_a(sd: np.ndarray) -> np.ndarray:
    return np.clip(0.5 - sd, 0.0, 1.0)


def blur_shadow(sd: np.ndarray, sigma: float) -> np.ndarray:
    from scipy.special import erfc
    return (0.5 * erfc(sd / (sigma * math.sqrt(2)))).astype(np.float32)


class Canvas:
    """Premultiplied RGB(0..255) + alpha(0..1) float canvas."""

    def __init__(self, w: int, h: int):
        self.w, self.h = int(w), int(h)
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.zeros((self.h, self.w), np.float32)

    def over(self, color, alpha: np.ndarray):
        alpha = np.clip(alpha, 0, 1).astype(np.float32)
        col = np.asarray(color, np.float32)
        if col.ndim == 1:
            col = col[None, None, :]
        self.rgb = col * alpha[..., None] + self.rgb * (1 - alpha[..., None])
        self.a = alpha + self.a * (1 - alpha)

    def to_image(self) -> Image.Image:
        a = np.clip(self.a, 0, 1)
        rgb = np.where(a[..., None] > 1e-4, self.rgb / np.maximum(a[..., None], 1e-4), 0)
        arr = np.dstack([np.clip(rgb, 0, 255), a * 255]).round().astype(np.uint8)
        return Image.fromarray(arr, "RGBA")


def text_alpha(w: int, h: int, items: list[tuple[float, float, str, object, float]]) -> np.ndarray:
    """items: (x, baseline, text, font, tracking) -> float alpha mask (h, w)."""
    m = Image.new("L", (int(w), int(h)), 0)
    d = ImageDraw.Draw(m)
    for x, y, s, f, tr in items:
        draw_line(d, x, y, s, f, tr)
    return np.asarray(m, np.float32) / 255.0


def hgrad(w: int, h: int, x0: float = 0, x1: float | None = None) -> np.ndarray:
    x1 = w if x1 is None else x1
    g = gemini_gradient(256)
    xs = np.clip((np.arange(w) + 0.5 - x0) / max(1.0, x1 - x0), 0, 1)
    row = np.stack([np.interp(xs, np.linspace(0, 1, 256), g[:, c]) for c in range(3)], axis=-1)
    return np.broadcast_to(row[None, :, :], (h, w, 3)).astype(np.float32)


def vgrad(w: int, h: int, y0: float, y1: float) -> np.ndarray:
    g = gemini_gradient(256)
    ys = np.clip((np.arange(h) + 0.5 - y0) / max(1.0, y1 - y0), 0, 1)
    col = np.stack([np.interp(ys, np.linspace(0, 1, 256), g[:, c]) for c in range(3)], axis=-1)
    return np.broadcast_to(col[:, None, :], (h, w, 3)).astype(np.float32)


VC = 0.36   # visual centre of Hangul/caps above the baseline, in em


# ------------------------------------------------------------------ sprite store
class SpriteStore:
    def __init__(self, root: Path = CACHE_DIR / "sprites"):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def get(self, kind: str, **params) -> dict:
        key = sha([SPRITE_VERSION, kind, params])
        png, meta = self.root / f"{kind}_{key}.png", self.root / f"{kind}_{key}.json"
        if png.exists() and meta.exists():
            m = json.loads(meta.read_text())
            m["path"] = str(png)
            return m
        img, m = getattr(self, "_" + kind)(**params)
        img.save(png)
        m.update(w=img.width, h=img.height, kind=kind)
        meta.write_text(json.dumps(m, ensure_ascii=False))
        m["path"] = str(png)
        return m

    # ---- burned-in caption: white Pretendard SemiBold 40px on an rgba(0,0,0,.62) pill
    def _caption(self, lines: list[str], size: int = 40, lh: float = 1.42, padx: int = 34, pady: int = 13):
        f = font("semibold", size)
        lhp = round(size * lh)
        widths = [text_w(s, f) for s in lines]
        w = int(math.ceil(max(widths))) + 2 * padx
        h = len(lines) * lhp + 2 * pady
        r = h / 2 if len(lines) == 1 else 28
        c = Canvas(w, h)
        c.over((0, 0, 0), fill_a(sdf_rrect(w, h, 0, 0, w, h, r)) * 0.62)
        items = []
        for i, s in enumerate(lines):
            base = h / 2 - (len(lines) - 1) * lhp / 2 + i * lhp + VC * size
            items.append(((w - widths[i]) / 2, base, s, f, 0.0))
        c.over((255, 255, 255), text_alpha(w, h, items))
        return c.to_image(), {"glass": [0, 0, w, h, r]}

    # ---- callout label chip (Gemini gradient pill + soft shadow)
    def _chip(self, text: str, size: int = 30, padx: int = 24, height: int = 58):
        f = font("semibold", size)
        tw_ = text_w(text, f)
        bw, bh = int(math.ceil(tw_)) + 2 * padx, height
        m = 26
        w, h = bw + 2 * m, bh + 2 * m
        c = Canvas(w, h)
        sd_sh = sdf_rrect(w, h, m, m + 6, m + bw, m + bh + 6, bh / 2)
        c.over((0, 0, 0), blur_shadow(sd_sh, 9) * 0.42)
        body = fill_a(sdf_rrect(w, h, m, m, m + bw, m + bh, bh / 2))
        c.over(hgrad(w, h, m, m + bw), body)
        # thin inner highlight
        ring = np.clip(1.0 - np.abs(sdf_rrect(w, h, m, m, m + bw, m + bh, bh / 2) + 0.9), 0, 1)
        c.over((255, 255, 255), ring * 0.22)
        c.over((255, 255, 255), text_alpha(w, h, [(m + padx, m + bh / 2 + VC * size, text, f, 0.0)]))
        return c.to_image(), {"body": [m, m, bw, bh]}

    # ---- fast-forward badge (glass pill, vector >> icon)
    def _badge(self, text: str, size: int = 28, height: int = 58):
        f = font("semibold", size)
        tw_ = text_w(text, f)
        icon_w, gap, padx = 34, 12, 22
        bw, bh = int(math.ceil(padx + icon_w + gap + tw_ + padx)), height
        m = 24
        w, h = bw + 2 * m, bh + 2 * m
        c = Canvas(w, h)
        c.over((0, 0, 0), blur_shadow(sdf_rrect(w, h, m, m + 6, m + bw, m + bh + 6, bh / 2), 10) * 0.35)
        sd = sdf_rrect(w, h, m, m, m + bw, m + bh, bh / 2)
        c.over((14, 18, 26), fill_a(sd) * 0.70)
        c.over((255, 255, 255), np.clip(1.0 - np.abs(sd + 0.9), 0, 1) * 0.20)
        # icon: two rounded triangles drawn at 4x then downsampled
        S = 4
        ic = Image.new("L", (icon_w * S, 24 * S), 0)
        d = ImageDraw.Draw(ic)
        for k in range(2):
            x0 = k * 15 * S
            d.polygon([(x0 + 1 * S, 2 * S), (x0 + 17 * S, 12 * S), (x0 + 1 * S, 22 * S)], fill=255)
        ic = ic.resize((icon_w, 24), Image.LANCZOS)
        ia = np.zeros((h, w), np.float32)
        ix, iy = m + padx, int(round(m + bh / 2 - 12))
        ia[iy:iy + 24, ix:ix + icon_w] = np.asarray(ic, np.float32) / 255
        c.over(hgrad(w, h, ix, ix + icon_w), ia)
        c.over((255, 255, 255), text_alpha(w, h, [(ix + icon_w + gap, m + bh / 2 + VC * size, text, f, 0.0)]))
        return c.to_image(), {"body": [m, m, bw, bh], "glass": [m, m, bw, bh, bh / 2]}

    # ---- step label (lower third): glass panel + gradient accent bar + kicker + title
    def _label(self, kicker: str, text: str):
        fk, ft = font("semibold", 22), font("bold", 38)
        trk = 2.6
        kw, tw_ = text_w(kicker, fk, trk), text_w(text, ft, -0.4)
        padl, padr, padt = 30, 34, 20
        bw = int(math.ceil(padl + 6 + 18 + max(kw, tw_) + padr))
        bh = 112 if kicker else 84
        m = 34
        w, h = bw + 2 * m, bh + 2 * m
        c = Canvas(w, h)
        c.over((0, 0, 0), blur_shadow(sdf_rrect(w, h, m, m + 10, m + bw, m + bh + 10, 22), 18) * 0.45)
        sd = sdf_rrect(w, h, m, m, m + bw, m + bh, 22)
        c.over((12, 16, 24), fill_a(sd) * 0.74)
        c.over((255, 255, 255), np.clip(1.0 - np.abs(sd + 0.9), 0, 1) * 0.16)
        bx = m + padl
        bar = fill_a(sdf_rrect(w, h, bx, m + 20, bx + 6, m + bh - 20, 3))
        c.over(vgrad(w, h, m + 20, m + bh - 20), bar)
        tx = bx + 6 + 18
        items_k, items_t = [], []
        if kicker:
            items_k.append((tx, m + padt + 24, kicker, fk, trk))
            items_t.append((tx, m + padt + 24 + 50, text, ft, -0.4))
        else:
            items_t.append((tx, m + bh / 2 + VC * 38, text, ft, -0.4))
        if items_k:
            c.over(hgrad(w, h, tx, tx + kw), text_alpha(w, h, items_k))
        c.over((255, 255, 255), text_alpha(w, h, items_t))
        return c.to_image(), {"body": [m, m, bw, bh], "glass": [m, m, bw, bh, 22]}

    # ---- generic text block (title cards, cards, outro)
    def _text(self, text: str, weight: str = "bold", size: int = 88, color: str = "#FFFFFF", max_w: int = 1560,
              lh: float = 1.2, tracking_em: float = -0.02, align: str = "center", gradient: bool = False,
              balance: bool = True):
        f = font(weight, size)
        if any("\uac00" <= ch <= "\ud7a3" for ch in text):
            tracking_em = min(tracking_em, 0.03)          # wide tracking breaks Hangul words apart
        tr = tracking_em * size
        lines = wrap_keep_all(text, f, max_w, tr, balance=balance)
        lhp = round(size * lh)
        widths = [text_w(s, f, tr) for s in lines]
        asc, desc = f.getmetrics()
        pad = int(size * 0.25) + 4
        w = int(math.ceil(max(widths))) + 2 * pad
        h = int(math.ceil((len(lines) - 1) * lhp + asc + desc)) + 2 * pad
        items = []
        for i, s in enumerate(lines):
            x = pad + ((w - 2 * pad - widths[i]) / 2 if align == "center" else 0)
            items.append((x, pad + asc + i * lhp, s, f, tr))
        c = Canvas(w, h)
        a = text_alpha(w, h, items)
        c.over(hgrad(w, h, pad, w - pad) if gradient else hex_rgb(color), a)
        # visual centre of the block (from top), used for layout
        vc = pad + asc + (len(lines) - 1) * lhp / 2 - VC * size
        return c.to_image(), {"lines": lines, "vcenter": vc, "pad": pad, "first_base": pad + asc,
                              "block_h": (len(lines) - 1) * lhp + size}

    # ---- numbered bullet for cards
    def _bullet(self, n: int, text: str, size: int = 40, max_w: int = 1240):
        f = font("medium", size)
        fn = font("bold", 24)
        lines = wrap_keep_all(text, f, max_w, 0, balance=False)
        lhp = round(size * 1.45)
        dot = 46
        gap = 26
        widths = [text_w(s, f) for s in lines]
        pad = 12
        w = int(math.ceil(dot + gap + max(widths))) + 2 * pad
        h = int((len(lines) - 1) * lhp + max(dot, size * 1.3)) + 2 * pad
        c = Canvas(w, h)
        cy = pad + dot / 2
        c.over(hgrad(w, h, pad, pad + dot), fill_a(sdf_rrect(w, h, pad, cy - dot / 2, pad + dot, cy + dot / 2, dot / 2)))
        num = str(n)
        c.over((255, 255, 255), text_alpha(w, h, [(pad + (dot - text_w(num, fn)) / 2, cy + VC * 24, num, fn, 0.0)]))
        items = [(pad + dot + gap, cy + VC * size + i * lhp, s, f, 0.0) for i, s in enumerate(lines)]
        c.over(hex_rgb("#E6E9EF"), text_alpha(w, h, items))
        return c.to_image(), {"lines": lines}

    # ---- outro check icon (gradient ring + check)
    def _check(self, d: int = 128):
        S = 4
        m = 30
        w = h = d + 2 * m
        c = Canvas(w, h)
        sd = sdf_rrect(w, h, m, m, m + d, m + d, d / 2)
        c.over(hgrad(w, h, m, m + d), np.clip(3.0 - np.abs(sd + 3.0), 0, 1))          # 6px ring
        glow = np.exp(-np.maximum(sd, 0) ** 2 / (2 * 14 ** 2)) * (sd > -1)
        c.over(hex_rgb(GEMINI[0]), glow * 0.25)
        ck = Image.new("L", (w * S, h * S), 0)
        dr = ImageDraw.Draw(ck)
        pts = [(m + d * 0.29, m + d * 0.52), (m + d * 0.44, m + d * 0.66), (m + d * 0.72, m + d * 0.37)]
        dr.line([(x * S, y * S) for x, y in pts], fill=255, width=int(9 * S), joint="curve")
        for x, y in (pts[0], pts[-1]):
            r = 4.5 * S
            dr.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=255)
        ck = ck.resize((w, h), Image.LANCZOS)
        c.over((255, 255, 255), np.asarray(ck, np.float32) / 255)
        return c.to_image(), {"body": [m, m, d, d]}

    # ---- text-only brand line for title/card/outro (no logo imitation -> red accent bar + text)
    def _brand(self, text: str, size: int = 24, accent: str = "#D6336C", color: str = "#D5DBE3"):
        f = font("semibold", size)
        tw_ = text_w(text, f, 0.2)
        bar_w, gap, pad = 5, 14, 8
        w = int(math.ceil(pad + bar_w + gap + tw_ + pad))
        h = int(size * 1.6) + 2 * pad
        c = Canvas(w, h)
        c.over(hex_rgb(accent), fill_a(sdf_rrect(w, h, pad, h / 2 - size * 0.55, pad + bar_w, h / 2 + size * 0.55, 2.5)))
        c.over(hex_rgb(color), text_alpha(w, h, [(pad + bar_w + gap, h / 2 + VC * size, text, f, 0.2)]))
        return c.to_image(), {"body": [0, 0, w, h]}

    # ---- outro checklist row: subtle glass row + gradient check disc + text
    def _checkitem(self, text: str, width: int = 0, size: int = 38):
        f = font("medium", size)
        tw_ = text_w(text, f)
        disc, gap, padl, padr, rh = 44, 24, 26, 34, 84
        bw = max(int(math.ceil(padl + disc + gap + tw_ + padr)), int(width))
        m = 22
        w, h = bw + 2 * m, rh + 2 * m
        c = Canvas(w, h)
        c.over((0, 0, 0), blur_shadow(sdf_rrect(w, h, m, m + 6, m + bw, m + rh + 6, 22), 12) * 0.28)
        sd = sdf_rrect(w, h, m, m, m + bw, m + rh, 22)
        c.over((255, 255, 255), fill_a(sd) * 0.065)
        c.over((255, 255, 255), np.clip(1.0 - np.abs(sd + 0.9), 0, 1) * 0.14)
        cx, cy = m + padl + disc / 2, m + rh / 2
        c.over(hgrad(w, h, cx - disc / 2, cx + disc / 2),
               fill_a(sdf_rrect(w, h, cx - disc / 2, cy - disc / 2, cx + disc / 2, cy + disc / 2, disc / 2)))
        S = 4
        ck = Image.new("L", (w * S, h * S), 0)
        dr = ImageDraw.Draw(ck)
        pts = [(cx - disc * 0.21, cy + disc * 0.01), (cx - disc * 0.05, cy + disc * 0.16), (cx + disc * 0.22, cy - disc * 0.15)]
        dr.line([(x * S, y * S) for x, y in pts], fill=255, width=int(4.2 * S), joint="curve")
        for x, y in (pts[0], pts[-1]):
            r = 2.1 * S
            dr.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=255)
        ck = ck.resize((w, h), Image.LANCZOS)
        c.over((255, 255, 255), np.asarray(ck, np.float32) / 255)
        c.over(hex_rgb("#E9ECF1"), text_alpha(w, h, [(cx + disc / 2 + gap, cy + VC * size, text, f, 0.0)]))
        return c.to_image(), {"body": [m, m, bw, rh], "natural_w": padl + disc + gap + tw_ + padr}

