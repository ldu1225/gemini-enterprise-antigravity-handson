#!/usr/bin/env python3
"""Build the v2 Hands-on Lab portal (static, multi-page, CSP-strict).

    python3 production/site_build_v2/build.py              # content: production/content/v2  → site_v2/
    python3 production/site_build_v2/build.py --fixture    # content: production/content/v2/_fixture → site_v2_fixture/
    python3 production/site_build_v2/build.py --out DIR    # custom output directory (inside the repo)

Schema: production/content/v2/schema.md

Page structure (2026-10 redesign):
- home  : hero · track cards (each with its lab list) · how it works · opening talks · demo videos (tabs) ·
          prep & practice files (tabs) · FAQ · next steps & references
- track : hero band (stats · progress · resume · opening video) · lab cards · prep & files · FAQ
- lab   : sticky top bar (reading progress) · sidebar = lab tree with the current lab's steps (drawer below
          1024px, plus a sticky "current step" bar) · goal · demo video + chapter list · timeline steps ·
          '더 해 보기' · checklist · prev/next

Security model (static site served by nginx with a strict CSP, see deploy/nginx — not touched here):
- every text value is html.escape()d at build time; md subset = **bold**, *emphasis*, `code`, [text](https://…),
  "- " bullet lists and "1. " numbered lists (schema.md §1)
- no inline <script>, no inline event handlers, no style="" (CSP style-src 'self'): per-image callout geometry,
  aspect ratios and per-track accent colours are emitted as generated CSS rules
- client JS (assets/js/portal.js) builds DOM with createElement/textContent only; localStorage holds UI state only
- content paths (shots, files, video ids) are validated against allow-list patterns and resolved inside their roots
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import math
import os
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATIC = HERE / "static"
CONTENT_DIR = ROOT / "production" / "content" / "v2"
FIXTURE_DIR = CONTENT_DIR / "_fixture"
SHOTS_SRC = ROOT / "production" / "assets" / "shots"
# Pretendard (OFL) dynamic subsets, vendored in vendor/fonts (pretendard.css + pretendard/*.woff2); read-only here.
FONT_SRCS = [HERE / "vendor" / "fonts", ROOT / "site" / "assets" / "fonts"]

SHOT_WIDTHS = (800, 1600, 2400)
WEBP_Q = 82
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; "
       "font-src 'self'; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'")
LEVELS = {"입문": "lv1", "기본": "lv2", "중급": "lv2", "심화": "lv3"}
DEFAULT_ACCENT = {"ge": "#4285F4", "ag": "#9B72CB"}
BRAND_ACCENT = "#4285F4"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
SAFE_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,120}$")
SAFE_VIDEO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
SHELL_LANGS = {"bash", "sh", "shell", "zsh", "console", "terminal"}

WARNINGS: list[str] = []
GEN_CSS: list[str] = []
OUT: Path = ROOT / "site_v2"
ASSETS: Path = OUT / "assets"
VIDEO_DIR: Path = ASSETS / "video"


class BuildError(Exception):
    pass


# --------------------------------------------------------------------------- helpers
def e(value) -> str:
    return html.escape(str(value), quote=True)


_QUIET = False


def warn(msg: str) -> None:
    if _QUIET or msg in WARNINGS:
        return
    WARNINGS.append(msg)
    print("  ! " + msg)


def digest(data: bytes, n: int = 10) -> str:
    return hashlib.sha256(data).hexdigest()[:n]


def icon(name: str, cls: str = "ic") -> str:
    return f'<svg class="{e(cls)}" aria-hidden="true" focusable="false"><use href="#i-{e(name)}"></use></svg>'


def rel(p: Path) -> str:
    return p.relative_to(OUT).as_posix()


def url(path: str) -> str:
    """Percent-encode a site-relative path (Korean filenames) for href/src attributes."""
    return e(urllib.parse.quote(path, safe="/._-~#?=&"))


_FP: dict[Path, str] = {}


def media_url(p: Path, base: str) -> str:
    """URL + content fingerprint (?v=) so a re-rendered video/caption/poster is never replayed from cache.

    Used for EVERY emitted asset that can change under the same filename: videos, posters, captions,
    screenshot WebP variants (src/srcset/lightbox href), file previews and practice-file downloads.
    A re-captured screenshot keeps its stem; without ?v= browsers (heuristic cache) and nginx
    (max-age=86400) kept showing the OLD image under the NEW callout box.
    """
    fp = _FP.get(p)
    if fp is None:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        fp = _FP[p] = h.hexdigest()[:10]
    return f"{base}{url(rel(p))}?v={fp}"


def attr_if(cond: bool, name: str, value: str = "true") -> str:
    return f' {name}="{e(value)}"' if cond else ""


# --------------------------------------------------------------------------- markdown (schema.md §1)
# Inline: `code` → literal, [label](https://…) → external link, **bold**, *emphasis* (bold/emphasis may wrap code).
# Blocks: one list item / paragraph per string (or per line of a multi-line string); "- " → <ul>, "1. " → <ol>.
_PH = "\ue000{}\ue001"
_PH_RE = re.compile("\ue000(\\d+)\ue001")
_CODE_RE = re.compile(r"`([^`\n]+)`")
_LINK = re.compile(r"\[([^\]\n]+)\]\((https://[^\s)\"'<>]+)\)")
_BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_EM_RE = re.compile(r"(?<!\*)\*(?![\s*])(.+?)(?<![\s*])\*(?!\*)")
_UL_RE = re.compile(r"^[-*•]\s+(.+)$", re.S)
_OL_RE = re.compile(r"^(\d{1,3})[.)]\s+(.+)$", re.S)
CODE_NOWRAP_MAX = 22  # short inline code never breaks mid-token; longer code may wrap anywhere


def md_inline(text) -> str:
    """Escape, then render the inline md subset. Unmatched ** markers are dropped instead of shown."""
    tokens: list[str] = []

    def stash(markup: str) -> str:
        tokens.append(markup)
        return _PH.format(len(tokens) - 1)

    src = str(text or "")
    parts, last = [], 0
    for m in _CODE_RE.finditer(src):
        inner = m.group(1)
        cls = ' class="c-long"' if len(inner) > CODE_NOWRAP_MAX else ""
        parts.append(e(src[last:m.start()]))
        parts.append(stash(f"<code{cls}>{e(inner)}</code>"))
        last = m.end()
    parts.append(e(src[last:]))
    s = "".join(parts)
    s = _LINK.sub(lambda m: stash(
        f'<a href="{m.group(2)}" target="_blank" rel="noopener noreferrer">{m.group(1)}'
        f'{icon("external", "ic ic-xs")}<span class="sr-only"> (새 탭)</span></a>'), s)
    s = _BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", s)
    s = _EM_RE.sub(lambda m: f"<em>{m.group(1)}</em>", s)
    s = s.replace("**", "")
    for _ in range(3):  # link labels may themselves hold code placeholders
        if "\ue000" not in s:
            break
        s = _PH_RE.sub(lambda m: tokens[int(m.group(1))], s)
    return s


def md_blocks(items) -> str:
    """md strings → <p> / <ul class="md-ul"> / <ol class="md-ol"> (numbers rendered in the DOM, list semantics kept)."""
    if isinstance(items, str):
        items = [items]
    lines = [ln.strip() for it in (items or []) for ln in str(it).split("\n") if ln.strip()]
    out: list[str] = []
    state = {"kind": None, "buf": [], "start": 1}

    def flush() -> None:
        kind, buf = state["kind"], state["buf"]
        if kind == "ul":
            out.append('<ul class="md-ul">' + "".join(f"<li>{md_inline(t)}</li>" for t in buf) + "</ul>")
        elif kind == "ol":
            start = f' start="{state["start"]}"' if state["start"] != 1 else ""
            out.append(f'<ol class="md-ol"{start}>' + "".join(
                f'<li><span class="md-n" aria-hidden="true">{n}</span><span class="md-li">{md_inline(t)}</span></li>'
                for n, t in buf) + "</ol>")
        state["kind"], state["buf"] = None, []

    for s in lines:
        m_ul, m_ol = _UL_RE.match(s), _OL_RE.match(s)
        if m_ul:
            if state["kind"] != "ul":
                flush()
                state["kind"] = "ul"
            state["buf"].append(m_ul.group(1))
        elif m_ol:
            n = int(m_ol.group(1))
            if state["kind"] != "ol":
                flush()
                state["kind"], state["start"] = "ol", n
            state["buf"].append((n, m_ol.group(2)))
        else:
            flush()
            out.append(f"<p>{md_inline(s)}</p>")
    flush()
    return "".join(out)


def plain(text) -> str:
    s = _LINK.sub(r"\1", str(text or ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = _EM_RE.sub(r"\1", s)
    return s.replace("**", "").replace("`", "").strip()


def fmt_t(sec: float) -> str:
    s = max(0, int(round(sec)))
    return f"{s // 60}:{s % 60:02d}"


def fmt_minutes(m: int) -> str:
    if m < 60:
        return f"{m}분"
    h, r = divmod(m, 60)
    return f"{h}시간 {r}분" if r else f"{h}시간"


def lab_no(lab: dict) -> str:
    try:
        return f"{int(lab.get('no')):02d}"
    except (TypeError, ValueError):
        return str(lab.get("no", ""))


def check_key(track: str, lab: str, text: str) -> str:
    return f"{track}/{lab}:{hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]}"


def link_file(src: Path, dst: Path) -> None:
    """Hard-link (fallback copy) when the destination is missing or stale."""
    if dst.exists():
        s, d = src.stat(), dst.stat()
        if s.st_size == d.st_size and d.st_mtime >= s.st_mtime:
            return
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- colour (per-track accent tokens)
def _rgb(hex_: str) -> tuple[float, ...]:
    h = hex_.lstrip("#")
    return tuple(float(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def _hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in rgb)


def _lum(rgb) -> float:
    def ch(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _mix(a, b, t: float):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _until(fg, bg, target: float, toward):
    """Move fg toward `toward` (black/white) in 1% steps until it reaches the WCAG contrast target on bg."""
    for i in range(101):
        c = _mix(fg, toward, i / 100)
        if contrast(c, bg) >= target:
            return c
    return toward


_WHITE, _BLACK = (255.0, 255.0, 255.0), (0.0, 0.0, 0.0)
_LIGHT_SURFACE, _DARK_SURFACE = _rgb("#FFFFFF"), _rgb("#141821")


def accent_tokens(acc: str) -> tuple[str, str]:
    """Light + dark custom-property sets for one accent: text-safe ink (≥4.8:1 on the soft tint), soft tint,
    hairline, and a solid fill that carries white text at ≥4.7:1. Plain hex so QA can measure contrast."""
    a = _rgb(acc)
    soft_l, line_l = _mix(_LIGHT_SURFACE, a, 0.09), _mix(_LIGHT_SURFACE, a, 0.30)
    ink_l = _until(a, soft_l, 4.8, _BLACK)
    solid = _until(a, _WHITE, 4.7, _BLACK)
    soft_d, line_d = _mix(_DARK_SURFACE, a, 0.17), _mix(_DARK_SURFACE, a, 0.42)
    ink_d = _until(a, soft_d, 4.8, _WHITE)
    light = (f"--accent:{acc};--accent-ink:{_hex(ink_l)};--accent-soft:{_hex(soft_l)};--accent-line:{_hex(line_l)};"
             f"--accent-solid:{_hex(solid)};--accent-solid-hover:{_hex(_mix(solid, _BLACK, 0.14))}")
    dark = f"--accent-ink:{_hex(ink_d)};--accent-soft:{_hex(soft_d)};--accent-line:{_hex(line_d)}"
    return light, dark


def accent_css(tracks: list) -> None:
    def emit(sel: str, sel_dark_sys: str, sel_dark_pin: str, acc: str) -> None:
        light, dark = accent_tokens(acc)
        GEN_CSS.append(f"{sel}{{{light}}}")
        GEN_CSS.append(f"@media (prefers-color-scheme: dark){{{sel_dark_sys}{{{dark}}}}}")
        GEN_CSS.append(f"{sel_dark_pin}{{{dark}}}")

    # One look on every page: the whole site (home, track, lab) runs on the brand accent. A track's own colour only
    # tints explicit identity markers (.t-<id>: dots, kickers, home track cards) — never a whole page.
    emit(":root", ':root:not([data-theme="light"])', ':root[data-theme="dark"]', BRAND_ACCENT)
    for t in tracks:
        tid = t["id"]
        emit(f'.t-{tid}', f':root:not([data-theme="light"]) .t-{tid}', f':root[data-theme="dark"] .t-{tid}', t["accent"])


# --------------------------------------------------------------------------- content
def load_module(path: Path, name: str):
    if not path.is_file():
        raise BuildError(f"content module not found: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def norm_shots(st: dict) -> list[dict]:
    shots = []
    raw = st.get("shots")
    if isinstance(raw, (list, tuple)):
        for s in raw:
            shots.append({"stem": s} if isinstance(s, str) else dict(s))
    if st.get("shot"):
        s = st["shot"]
        shots.insert(0, {"stem": s, "caption": st.get("caption", ""), "callouts": st.get("callouts") or []}
                     if isinstance(s, str) else dict(s))
    if st.get("shot2"):  # v1 compatibility
        shots.append({"stem": st["shot2"], "caption": st.get("caption2", ""), "callouts": st.get("callouts2") or []})
    return [s for s in shots if s.get("stem")]


def norm_code(st: dict) -> list[dict]:
    raw = st.get("code")
    if not raw:
        return []
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    out = []
    for c in items:
        if isinstance(c, str):
            c = {"lang": "text", "text": c}
        if c.get("text"):
            out.append({"lang": str(c.get("lang") or "text").lower(), "text": str(c["text"]).rstrip("\n"),
                        "file": c.get("file") or "", "label": c.get("label") or ""})
    return out


def load_content(content_dir: Path):
    site_mod = load_module(content_dir / "site.py", "v2_site")
    site, tracks = dict(site_mod.SITE), [dict(t) for t in site_mod.TRACKS]
    for key in ("title", "hero_title", "hero_sub"):
        if not site.get(key):
            raise BuildError(f"SITE['{key}'] is required")
    seen = set()
    for t in tracks:
        tid = t.get("id", "")
        if not SAFE_ID.match(tid) or tid in seen:
            raise BuildError(f"invalid/duplicate track id: {tid!r}")
        seen.add(tid)
        acc = t.get("accent") or DEFAULT_ACCENT.get(tid, BRAND_ACCENT)
        t["accent"] = acc if HEX.match(acc) else DEFAULT_ACCENT.get(tid, BRAND_ACCENT)
        labs = [dict(lab) for lab in load_module(content_dir / f"{tid}.py", f"v2_{tid}").LABS]
        ids = set()
        for lab in labs:
            lid = lab.get("id", "")
            if not SAFE_ID.match(lid) or lid in ids or lid == "index":
                raise BuildError(f"{tid}: invalid/duplicate lab id {lid!r}")
            ids.add(lid)
            if lab.get("level") and lab["level"] not in LEVELS:
                warn(f"{tid}/{lid}: unknown level {lab['level']!r} (입문|기본|심화)")
            lab["minutes"] = int(lab.get("minutes") or 0)
            steps = []
            for st in lab.get("steps") or []:
                st = dict(st)
                st["title"] = plain(st.get("title", ""))
                st["_shots"] = norm_shots(st)
                for s_item in st["_shots"]:
                    if s_item.get("caption"):
                        s_item["caption"] = plain(s_item["caption"])
                st["_code"] = norm_code(st)
                steps.append(st)
            lab["steps"] = steps
            lab["check"] = [plain(c) for c in (lab.get("check") or [])]
            lab["more"] = [plain(m) for m in (lab.get("more") or [])]
            lab["_keys"] = [check_key(tid, lid, c) for c in lab.get("check") or []]
            if lab.get("video") and not SAFE_VIDEO.match(str(lab["video"])):
                raise BuildError(f"{tid}/{lid}: invalid video id {lab['video']!r}")
        t["labs"] = labs
        op = t.get("opening")
        if isinstance(op, str):
            t["opening"] = {"video": op}
        if t.get("opening") and not SAFE_VIDEO.match(str(t["opening"].get("video", ""))):
            raise BuildError(f"{tid}: invalid opening video id")
    return site, tracks


def ready(lab: dict) -> bool:
    return bool(lab.get("steps"))


# --------------------------------------------------------------------------- images
def to_webp(src: Path, out: Path, width: int) -> tuple[int, int]:
    with Image.open(src) as im:
        w = min(width, im.width)
        h = round(im.height * w / im.width)
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            im = im.convert("RGB")
            if (w, h) != im.size:
                im = im.resize((w, h), Image.LANCZOS)
            out.parent.mkdir(parents=True, exist_ok=True)
            im.save(out, "WEBP", quality=WEBP_Q, method=6)
        return w, h


_SHOTS: dict[str, dict | None] = {}
_AR: set[tuple[int, int]] = set()


def aspect_class(cw: int, ch: int) -> str:
    if (cw, ch) not in _AR:
        _AR.add((cw, ch))
        r = cw / ch
        GEN_CSS.append(f".ar-{cw}x{ch}{{aspect-ratio:{cw}/{ch}}}")
        GEN_CSS.append(f'.lightbox[data-ar="ar-{cw}x{ch}"]{{width:min(96vw,calc((100dvh - 172px) * {r:.4f}),1800px)}}')
    return f"ar-{cw}x{ch}"


def shot(stem: str, viewport=None) -> dict | None:
    """Real capture → WebP variants. CSS capture size = viewport, or image size / DPR (2 when ≥2400px wide)."""
    if not stem or not SAFE_STEM.match(stem):
        warn(f"invalid screenshot stem: {stem!r}")
        return None
    key = f"{stem}|{viewport}"
    if key in _SHOTS:
        return _SHOTS[key]
    src = next((SHOTS_SRC / f"{stem}{ext}" for ext in (".png", ".jpg", ".jpeg", ".webp")
                if (SHOTS_SRC / f"{stem}{ext}").is_file()), None)
    if src is None or not inside(src, SHOTS_SRC):
        warn(f"screenshot not found: {stem}")
        _SHOTS[key] = None
        return None
    with Image.open(src) as im:
        W, H = im.size
    if viewport and len(viewport) == 2:
        cw, ch = int(viewport[0]), int(viewport[1])
    else:
        dpr = 2 if W >= 2400 else 1
        cw, ch = round(W / dpr), round(H / dpr)
    out_dir = ASSETS / "img" / "shots"
    variants = []
    for w in sorted({min(x, W) for x in SHOT_WIDTHS}):
        p = out_dir / f"{stem}-{w}.webp"
        vw, vh = to_webp(src, p, w)
        variants.append((rel(p), vw, vh))
    info = {"variants": variants, "cw": cw, "ch": ch, "ar": aspect_class(cw, ch)}
    _SHOTS[key] = info
    return info


def img_tag(info: dict, alt: str, base: str, *, sizes: str, cls: str = "", eager: bool = False) -> str:
    vs = info["variants"]
    main = next((v for v in vs if v[1] >= 1600), vs[-1])
    srcset = ", ".join(f"{media_url(OUT / p, base)} {w}w" for p, w, _ in vs)
    attrs = (f'src="{media_url(OUT / main[0], base)}" srcset="{srcset}" sizes="{e(sizes)}" width="{main[1]}" height="{main[2]}" '
             f'alt="{e(alt)}" decoding="async"')
    attrs += ' fetchpriority="high"' if eager else ' loading="lazy"'
    if cls:
        attrs += f' class="{e(cls)}"'
    return f"<img {attrs}>"


_CO_RULES: dict[str, str] = {}


def callout_css(box, cw: int, ch: int, pos: str | None, where: str = "") -> str:
    """Callout geometry → generated CSS class.

    The class name is derived from the geometry itself (content-addressed). It must NEVER be derived from
    lab/step ids: both tracks have lab1…lab9, and id-based names (`co-lab4-0-00`) made the GE and AG rules
    collide in the shared stylesheet — the later track's boxes were drawn on the other track's screenshots.
    """
    x, y, w, h = (float(v) for v in box)
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > cw + 0.5 or y + h > ch + 0.5:
        raise BuildError(f"{where}: callout box {list(box)} is outside the {cw}x{ch} capture")
    if pos not in (None, "", "above", "below", "inside"):
        raise BuildError(f"{where}: unknown callout pos {pos!r} (above | below | inside)")
    mods = []
    if pos not in ("above", "below", "inside"):
        if y < 40:
            pos = "inside" if h >= 120 else "below"
        else:
            pos = "below" if h >= ch * 0.3 and y + h + 40 <= ch else "above"
    if pos == "inside":
        mods.append("co--in")
    elif pos == "below":
        mods.append("co--below")
    if x + w / 2 > cw * 0.7:
        mods.append("co--end")
    rule = (f"left:{x / cw * 100:.3f}%;top:{y / ch * 100:.3f}%;"
            f"width:{w / cw * 100:.3f}%;height:{h / ch * 100:.3f}%")
    cls = "co-" + hashlib.sha1(rule.encode("ascii")).hexdigest()[:12]
    prev = _CO_RULES.setdefault(cls, rule)
    if prev != rule:
        raise BuildError(f"{where}: callout class collision {cls}")
    GEN_CSS.append(f".{cls}{{{rule}}}")
    return " ".join([cls] + mods)


# --------------------------------------------------------------------------- video
def sync_videos(site: dict, tracks: list) -> None:
    """Optional: copy referenced media from SITE['video_src'] into assets/video (fixture / staging)."""
    src_rel = site.get("video_src")
    if not src_rel:
        return
    src = (ROOT / src_rel).resolve()
    if not inside(src, ROOT) or not src.is_dir():
        warn(f"video_src not found or outside repo: {src_rel}")
        return
    ids = set()
    for t in tracks:
        if t.get("opening"):
            ids.add(t["opening"]["video"])
        ids.update(str(lab["video"]) for lab in t["labs"] if lab.get("video"))
    for vid in sorted(ids):
        for suffix in (".mp4", ".ko.vtt", ".jpg", ".chapters.json", ".chapters.vtt"):
            f = src / f"{vid}{suffix}"
            if f.is_file():
                link_file(f, VIDEO_DIR / f.name)


def vtt_duration(path: Path) -> int:
    last = 0
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.search(r"-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,]\d+)?", line)
            if m:
                last = max(last, int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3)))
    except (OSError, UnicodeDecodeError):
        return 0
    return last


def load_chapters(name: str) -> dict | None:
    path = VIDEO_DIR / f"{name}.chapters.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        warn(f"{path.name} unreadable: {exc}")
        return None
    raw = data.get("chapters") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        warn(f"{path.name}: missing 'chapters' list")
        return None
    dur = data.get("duration")
    dur = float(dur) if isinstance(dur, (int, float)) and not isinstance(dur, bool) and math.isfinite(dur) and dur > 0 else None
    chapters = []
    for c in raw:
        if not isinstance(c, dict):
            continue
        try:
            step, start, end = int(c.get("step")), float(c.get("start")), float(c.get("end"))
        except (TypeError, ValueError):
            continue
        if step < 1 or not (math.isfinite(start) and math.isfinite(end)) or start < 0 or end <= start:
            continue
        if dur is not None:
            if start >= dur:
                continue
            end = min(end, dur)
        chapters.append({"step": step, "title": plain(c.get("title") or ""), "start": start, "end": end})
    if not chapters:
        warn(f"{path.name}: no valid chapters")
        return None
    chapters.sort(key=lambda c: c["start"])
    by_step: dict[int, dict] = {}
    for c in chapters:
        by_step.setdefault(c["step"], c)
    vtt = VIDEO_DIR / f"{name}.chapters.vtt"
    return {"list": chapters, "by_step": by_step, "duration": dur, "vtt": vtt if vtt.is_file() else None}


_VIDEOS: dict[str, dict | None] = {}


def video_info(name: str | None) -> dict | None:
    if not name:
        return None
    if name not in _VIDEOS:
        _VIDEOS[name] = _video_info(name)
    return _VIDEOS[name]


def _video_info(name: str) -> dict | None:
    mp4 = VIDEO_DIR / f"{name}.mp4"
    if not mp4.is_file():
        return None
    vtt, poster = VIDEO_DIR / f"{name}.ko.vtt", VIDEO_DIR / f"{name}.jpg"
    chapters = load_chapters(name)
    secs = int(chapters["duration"]) if chapters and chapters.get("duration") else (vtt_duration(vtt) if vtt.is_file() else 0)
    return {"name": name, "mp4": mp4, "vtt": vtt if vtt.is_file() else None, "poster": poster if poster.is_file() else None,
            "chapters": chapters, "secs": secs}


def video_tag(v: dict, base: str, *, vid_id: str, label: str, lab: str | None = None, preload: str = "metadata") -> str:
    p_attr = f' poster="{media_url(v["poster"], base)}"' if v["poster"] else ""
    tracks = (f'<track kind="captions" srclang="ko" label="한국어" src="{media_url(v["vtt"], base)}" default>'
              if v["vtt"] else "")
    ch = v.get("chapters")
    if lab and ch and ch.get("vtt"):
        tracks += f'<track kind="chapters" srclang="ko" label="단계" src="{media_url(ch["vtt"], base)}" default>'
    lab_attr = f' data-lab="{e(lab)}"' if lab else ""
    return (f'<video id="{e(vid_id)}"{lab_attr} controls preload="{preload}" playsinline{p_attr} aria-label="{e(label)}">'
            f'<source src="{media_url(v["mp4"], base)}" type="video/mp4">{tracks}</video>')


# --------------------------------------------------------------------------- files
def collect_files(site: dict, tracks: list) -> None:
    src_rel = site.get("files_src")
    src_root = (ROOT / src_rel).resolve() if src_rel else None
    for t in tracks:
        out = []
        for it in t.get("files") or []:
            f = str(it.get("file") or "")
            if not f or f.startswith(("/", "\\")) or ".." in Path(f).parts or "\\" in f:
                raise BuildError(f"{t['id']}: unsafe file path {f!r}")
            if src_root is None or not src_root.is_dir():
                warn(f"files_src missing — skipped {f}")
                continue
            src = src_root / f
            if not inside(src, src_root) or not src.is_file():
                warn(f"practice file not found: {f}")
                continue
            dst = ASSETS / "files" / f
            link_file(src, dst)
            item = dict(it)
            item["_href"] = rel(dst)
            item["_size"] = src.stat().st_size
            item["_kind"] = f.rsplit(".", 1)[-1].upper() if "." in f else "FILE"
            pv = it.get("preview")
            if pv:
                pv_src = src_root / str(pv)
                if ".." not in Path(str(pv)).parts and inside(pv_src, src_root) and pv_src.is_file():
                    o = ASSETS / "img" / "files" / f"{digest(str(pv).encode())}.webp"
                    w, h = to_webp(pv_src, o, 720)
                    item["_pv"] = (rel(o), w, h)
                else:
                    warn(f"file preview missing: {pv}")
            out.append(item)
        t["_files"] = out


def human_size(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{max(1, round(n / 1024))} KB"


# --------------------------------------------------------------------------- static assets
def ensure_fonts() -> str:
    out_dir = ASSETS / "fonts"
    css = ""
    for src in FONT_SRCS:
        if (src / "pretendard.css").is_file() and (src / "pretendard").is_dir():
            (out_dir / "pretendard").mkdir(parents=True, exist_ok=True)
            for f in (src / "pretendard").iterdir():
                if f.suffix in (".woff2", ".txt"):
                    link_file(f, out_dir / "pretendard" / f.name)
            css = (src / "pretendard.css").read_text(encoding="utf-8").replace("url('pretendard/", "url('../fonts/pretendard/")
            break
    if not css:
        warn("Pretendard not found — falling back to system fonts")
    for f in (STATIC / "fonts").iterdir():
        if f.suffix in (".woff2", ".txt"):
            link_file(f, out_dir / f.name)
    return css


def dark_wrap(css: str) -> str:
    """static/css/tokens-dark.css holds the dark declarations once; emit them for the system preference
    (unless pinned light), the pinned dark theme, and always-dark scopes."""
    dark = (STATIC / "css" / "tokens-dark.css").read_text(encoding="utf-8")
    return css.replace("/*@DARK_TOKENS@*/",
                       f"@media (prefers-color-scheme: dark){{:root:not([data-theme=\"light\"]){{{dark}}}}}\n"
                       f":root[data-theme=\"dark\"],.scope-dark{{{dark}}}")


def write_static(font_css: str, search_index: list) -> dict[str, str]:
    css = dark_wrap((STATIC / "css" / "portal.css").read_text(encoding="utf-8"))
    css = (font_css + "\n" + css + "\n/* ---- generated: accents · aspect ratios · callout geometry (capture CSS px → %) ---- */\n"
           + "\n".join(GEN_CSS) + "\n")
    out = {}
    files = [("portal.css", css, "css"), ("theme.js", (STATIC / "js" / "theme.js").read_text(encoding="utf-8"), "js"),
             ("portal.js", (STATIC / "js" / "portal.js").read_text(encoding="utf-8"), "js"),
             ("search.json", json.dumps(search_index, ensure_ascii=False, separators=(",", ":")), "js")]
    for name, text, sub in files:
        p = ASSETS / sub / name
        p.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        p.write_bytes(data)
        out[name] = f"assets/{sub}/{name}?v={digest(data)}"
    return out


BRAND_FILES = ("google-cloud.svg", "google-cloud-dark.svg", "favicon.ico", "cloud-192.png")


def copy_brand() -> None:
    """Official Google Cloud marks (static/brand/SOURCE.md) → assets/img/brand/. Runs before rendering."""
    dst = ASSETS / "img" / "brand"
    dst.mkdir(parents=True, exist_ok=True)
    for name in BRAND_FILES:
        src = STATIC / "brand" / name
        if not src.is_file():
            raise BuildError(f"brand asset missing: {src}")
        shutil.copy2(src, dst / name)


def brand_url(name: str, base: str) -> str:
    return media_url(ASSETS / "img" / "brand" / name, base)


# --------------------------------------------------------------------------- shared chrome
_SPRITE: str | None = None


def sprite() -> str:
    global _SPRITE
    if _SPRITE is None:
        _SPRITE = (STATIC / "icons.svg").read_text(encoding="utf-8")
    return _SPRITE


def head(title: str, desc: str, assets: dict, base: str, track: dict | None, page: str) -> str:
    tr = f' data-track="{e(track["id"])}"' if track else ""
    return f"""<!doctype html>
<html lang="ko" class="no-js pg-{e(page)}" data-base="{e(base)}" data-search="{base}{e(assets['search.json'])}"{tr}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{e(CSP)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="robots" content="noindex, nofollow">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0B0D12" media="(prefers-color-scheme: dark)">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<link rel="icon" href="{brand_url('favicon.ico', base)}" sizes="16x16 32x32">
<link rel="icon" href="{brand_url('cloud-192.png', base)}" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="{brand_url('cloud-192.png', base)}">
<link rel="stylesheet" href="{base}{e(assets['portal.css'])}">
<script src="{base}{e(assets['theme.js'])}"></script>
<script src="{base}{e(assets['portal.js'])}" defer></script>
</head>
<body>
{sprite()}
<a class="skip-link" href="#main">본문으로 건너뛰기</a>"""


def brand(site: dict, base: str, cls: str = "brand") -> str:
    """Official Google Cloud logo (reversed wordmark in dark mode) │ portal title."""
    return (f'<a class="{cls}" href="{base}index.html" aria-label="Google Cloud {e(site["title"])} 홈">'
            f'<img class="brand-logo logo-l" src="{brand_url("google-cloud.svg", base)}" alt="" width="123" height="20">'
            f'<img class="brand-logo logo-d" src="{brand_url("google-cloud-dark.svg", base)}" alt="" width="123" height="20">'
            f'<span class="brand-sep" aria-hidden="true"></span><span class="brand-name">{e(site["title"])}</span></a>')


def search_btn() -> str:
    return ('<button type="button" class="search-btn" data-cmdk aria-haspopup="dialog" aria-keyshortcuts="Meta+K Control+K" '
            'aria-label="검색 — Lab · 단계 · 프롬프트">'
            f'{icon("search")}<span class="search-btn-t" aria-hidden="true">Lab · 단계 · 프롬프트 검색</span>'
            '<kbd class="kbd" data-kbd aria-hidden="true">⌘K</kbd></button>')


def theme_btn() -> str:
    return (f'<button type="button" class="icon-btn" data-theme-toggle aria-label="테마 전환">'
            f'{icon("sun", "ic ic-sun")}{icon("moon", "ic ic-moon")}</button>')


def topbar(site: dict, tracks: list, base: str, track: dict | None = None, page: str = "home") -> str:
    links = "".join(
        f'<a class="topnav-link t-{e(t["id"])}" href="{base}{e(t["id"])}/index.html"{attr_if(t is track, "aria-current")}>'
        f'<span class="dot" aria-hidden="true"></span><span>{e(t["title"])}</span></a>' for t in tracks)
    # Same bar on every page (user: "메인에 맞춰서 모든 탭 똑같이"): tracks │ 결과물 · 진행 방식 · 준비물 · FAQ │ search · theme · CTA.
    # 준비물/FAQ point at the current track's own sections on track and lab pages, at the home sections elsewhere.
    home = "" if page == "home" else f"{base}index.html"
    own = {"track": "", "lab": "index.html"}.get(page) if track else None
    secs = [(f"{home}#showcase", "결과물"), (f"{home}#how", "진행 방식"),
            (f"{own}#files" if own is not None else f"{home}#files", "준비물"),
            (f"{own}#faq" if own is not None else f"{home}#faq", "FAQ")]
    links += '<span class="topnav-sep" aria-hidden="true"></span>' + "".join(
        f'<a class="topnav-link topnav-sec" href="{e(h)}">{e(t)}</a>' for h, t in secs)
    progress = '<div class="read-progress" aria-hidden="true"><span></span></div>' if page == "lab" else ""
    files_btn = ""
    cta = f'<a class="btn btn-primary btn-sm topbar-cta" href="{home}#tracks"><span>실습 시작</span>{icon("arrow", "ic ic-sm ic-arrow-move")}</a>'
    return f"""
<header class="topbar">
  <div class="topbar-in">
    <button type="button" class="icon-btn topbar-menu" data-open="drawer" aria-haspopup="dialog" aria-label="메뉴 열기">{icon('menu')}</button>
    {brand(site, base)}
    <nav class="topnav" aria-label="주요 메뉴">{links}</nav>
    <div class="topbar-end">
      {search_btn()}
      {files_btn}
      {theme_btn()}
      {cta}
    </div>
    {progress}
  </div>
</header>"""


def drawer(site: dict, base: str, inner: str) -> str:
    return f"""
<dialog class="drawer" id="drawer" closedby="any" aria-label="실습 목록">
  <div class="drawer-head">{brand(site, base)}
    <button type="button" class="icon-btn" data-close aria-label="목록 닫기">{icon('close')}</button></div>
  <div class="drawer-body">{inner}</div>
</dialog>"""


def overlays() -> str:
    return f"""
<dialog class="cmdk" id="cmdk" closedby="any" aria-label="검색">
  <div class="cmdk-in">
    {icon('search', 'ic cmdk-ic-search')}
    <input id="cmdk-q" type="text" role="combobox" aria-expanded="true" aria-controls="cmdk-list" aria-autocomplete="list"
      placeholder="Lab, 단계, 프롬프트를 검색하세요" autocomplete="off" spellcheck="false" enterkeyhint="go">
    <button type="button" class="cmdk-esc" data-close aria-label="검색 닫기"><kbd>esc</kbd></button>
  </div>
  <div class="cmdk-list" id="cmdk-list" role="listbox" aria-label="검색 결과"></div>
  <div class="cmdk-foot" aria-hidden="true"><span><kbd>↑</kbd><kbd>↓</kbd> 이동</span><span><kbd>↵</kbd> 열기</span><span><kbd>esc</kbd> 닫기</span></div>
</dialog>
<dialog class="lightbox" id="lightbox" closedby="any" aria-labelledby="lb-cap">
  <div class="lb-top">
    <p class="lb-ctx"><span class="lb-ctx-t" data-lb-ctx></span><span class="lb-count" data-lb-count></span></p>
    <button class="lb-btn" type="button" data-close aria-label="닫기">{icon('close')}</button>
  </div>
  <div class="lb-stage"><img class="lb-img" alt="" decoding="async"></div>
  <div class="lb-foot">
    <button class="lb-btn lb-prev" type="button" data-lb-prev aria-label="이전 스크린샷">{icon('chev-left')}</button>
    <p class="lb-cap" id="lb-cap">스크린샷</p>
    <button class="lb-btn lb-next" type="button" data-lb-next aria-label="다음 스크린샷">{icon('chev-right')}</button>
  </div>
</dialog>
<p class="sr-only" id="live" aria-live="polite"></p>"""


def footer(site: dict, base: str) -> str:
    refs = "".join(f'<li><a href="{e(r["url"])}" target="_blank" rel="noopener noreferrer">{e(r["title"])}'
                   f'{icon("external", "ic ic-xs")}<span class="sr-only"> (새 탭)</span></a></li>'
                   for r in site.get("references") or [] if str(r.get("url", "")).startswith("https://"))
    note = f'<p class="footer-note md">{md_inline(site["footer_note"])}</p>' if site.get("footer_note") else ""
    links = (f'<nav class="footer-links" aria-label="공식 문서"><p class="footer-h">공식 문서</p><ul>{refs}</ul></nav>'
             if refs else "")
    return f"""
<footer class="footer scope-dark">
  <div class="container footer-in">
    <div class="footer-brand">{brand(site, base)}{note}</div>
    {links}
  </div>
  <div class="container footer-legal"><p>Google, Google Cloud, Gemini, Antigravity는 Google LLC의 상표입니다. 이 포털은 교육용으로 제작되었습니다.</p>
    <span class="gdots" aria-hidden="true"><i></i><i></i><i></i><i></i></span></div>
</footer>"""


def page_end() -> str:
    return overlays() + "\n</body>\n</html>\n"


def state_mark() -> str:
    """Progress ring that turns into a check badge (driven by the closest [data-checks] → --p / .is-complete)."""
    return f'<span class="state" aria-hidden="true"><span class="ring"></span>{icon("check", "ic state-done")}</span>'


def level_chip(level: str | None) -> str:
    if not level:
        return ""
    return f'<span class="chip chip-level {LEVELS.get(level, "lv2")}"><span class="lv-dot" aria-hidden="true"></span>{e(level)}</span>'


def resume_attr(track: dict, prefix: str) -> str:
    """'labid href k1 k2|…' for every ready lab — portal.js picks '시작하기 / 이어서 하기' and the target."""
    parts = []
    for lab in track["labs"]:
        if ready(lab):
            parts.append(" ".join([lab["id"], f"{prefix}{lab['id']}.html"] + lab["_keys"]))
    return e("|".join(parts))


def track_keys(track: dict) -> str:
    return " ".join(k for lab in track["labs"] for k in lab["_keys"])


def track_counts(track: dict) -> dict:
    labs = track["labs"]
    return {"labs": len(labs), "minutes": sum(l["minutes"] for l in labs),
            "videos": sum(1 for l in labs if ready(l) and video_info(l.get("video"))),
            "checks": sum(len(l["_keys"]) for l in labs)}


def first_href(track: dict, prefix: str) -> str:
    rl = [l for l in track["labs"] if ready(l)]
    return f"{prefix}{rl[0]['id']}.html" if rl else f"{prefix}index.html"


def crumbs(items: list[tuple[str, str | None]]) -> str:
    lis = "".join(f'<li><a href="{e(h)}">{e(t)}</a></li>' if h else f'<li aria-current="page">{e(t)}</li>' for t, h in items)
    return f'<nav class="crumbs" aria-label="현재 위치"><ol>{lis}</ol></nav>'


def section_head(eyebrow: str, title: str, hid: str, lead: str = "", extra: str = "", center: bool = False) -> str:
    lead_html = f'<p class="section-lead">{e(lead)}</p>' if lead else ""
    cls = "section-head is-center" if center else "section-head"
    return (f'<div class="{cls}"><div class="section-head-t"><p class="eyebrow">{e(eyebrow)}</p>'
            f'<h2 class="section-title" id="{e(hid)}">{e(title)}</h2>{lead_html}</div>{extra}</div>')


# --------------------------------------------------------------------------- navigation tree (sidebar + drawer)
def nav_labs(track: dict, base: str, current: str | None = None) -> str:
    tid = track["id"]
    items = []
    for lab in track["labs"]:
        lid = lab["id"]
        is_cur = lid == current
        soon = "" if ready(lab) else " is-soon"
        meta = f'{lab["minutes"]}분' if ready(lab) else "준비 중"
        steps_html = ""
        if is_cur and lab["steps"]:
            steps = "".join(
                f'<li><a class="nav-step" href="#s{i + 1}"><span class="nav-step-n">{i + 1}</span>'
                f'<span class="nav-step-t">{e(s.get("title", ""))}</span></a></li>' for i, s in enumerate(lab["steps"]))
            if lab.get("more"):
                steps += (f'<li><a class="nav-step nav-step-x" href="#more"><span class="nav-step-n">{icon("bolt", "ic ic-xs")}</span>'
                          f'<span class="nav-step-t">더 해 보기</span></a></li>')
            if lab.get("check"):
                steps += (f'<li><a class="nav-step nav-step-x" href="#checklist"><span class="nav-step-n">{icon("check", "ic ic-xs")}</span>'
                          f'<span class="nav-step-t">체크리스트</span></a></li>')
            steps_html = f'<ol class="nav-steps" aria-label="이 Lab의 단계">{steps}</ol>'
        items.append(
            f'<li class="nav-item{" is-open" if is_cur else ""}">'
            f'<a class="nav-lab{soon}" href="{base}{e(tid)}/{e(lid)}.html"{attr_if(is_cur, "aria-current", "page")} '
            f'data-checks="{e(" ".join(lab["_keys"]))}">{state_mark()}'
            f'<span class="nav-lab-t"><span class="nav-lab-no">LAB {e(lab_no(lab))}</span>'
            f'<span class="nav-lab-title">{e(lab["title"])}</span></span><span class="nav-lab-m">{e(meta)}</span></a>'
            f'{steps_html}</li>')
    return f'<ol class="nav-labs">{"".join(items)}</ol>'


def nav_tree(site: dict, tracks: list, base: str, track: dict | None = None, current: str | None = None,
             overview: bool = False, home_current: bool = True) -> str:
    if track is None:  # home: every track
        groups = "".join(
            f'<div class="nav-group t-{e(t["id"])}"><a class="nav-track" href="{base}{e(t["id"])}/index.html">'
            f'<span class="dot" aria-hidden="true"></span><span>{e(t["title"])}</span>{icon("arrow", "ic ic-xs")}</a>'
            f'{nav_labs(t, base)}</div>' for t in tracks)
        return (f'<nav class="nav-tree" aria-label="전체 실습"><a class="nav-overview" href="{base}index.html"{attr_if(home_current, "aria-current", "page")}>'
                f'{icon("home", "ic ic-sm")}<span>홈</span></a>{groups}</nav>')
    switch = "".join(
        f'<a class="seg-a t-{e(t["id"])}" href="{base}{e(t["id"])}/index.html"{attr_if(t is track, "aria-current")}>'
        f'<span class="dot" aria-hidden="true"></span><span>{e(t.get("short") or t["title"])}</span></a>' for t in tracks)
    c = track_counts(track)
    return f"""<nav class="nav-tree" aria-label="{e(track['title'])} 실습 목록">
      <div class="seg" role="group" aria-label="트랙 전환">{switch}</div>
      <a class="nav-overview" href="{base}{e(track['id'])}/index.html"{attr_if(overview, "aria-current", "page")}>{icon('grid', 'ic ic-sm')}<span>{e(track['title'])} 트랙 개요</span></a>
      <p class="nav-label">실습 <span>{c['labs']}</span></p>
      {nav_labs(track, base, current)}
      <div class="nav-progress" data-checks="{e(track_keys(track))}">
        <div class="nav-progress-row"><span>트랙 진행률</span><span><span class="js-count">0 / {c['checks']}</span> 완료</span></div>
        <span class="bar"><span class="bar-fill"></span></span>
      </div>
    </nav>"""


# --------------------------------------------------------------------------- lab page parts
def seek_attrs(lid: str, c: dict, title: str) -> str:
    return (f'data-lab="{e(lid)}" data-step="{int(c["step"])}" data-seek="{c["start"]:.2f}" '
            f'data-end="{c["end"]:.2f}" data-title="{e(title)}"')


def chapter_title(c: dict, steps: list) -> str:
    if c["title"]:
        return c["title"]
    i = c["step"] - 1
    return str(steps[i].get("title", "")) if 0 <= i < len(steps) else f"STEP {c['step']}"


def copy_btn(target: str, cls: str = "") -> str:
    extra = f" {cls}" if cls else ""
    return (f'<button class="copy-btn{extra}" type="button" data-copy="{e(target)}">'
            f'{icon("copy", "ic ic-sm ic-copy")}{icon("check", "ic ic-sm ic-done")}<span class="copy-label">복사</span></button>')


def demo_section(lab: dict, v: dict | None, base: str) -> str:
    lid = lab["id"]
    if not v:
        return f"""
      <section class="demo demo--soon" id="demo" aria-label="데모 영상">
        <div class="video-frame video-soon"><div class="soon-in">{icon('play', 'ic ic-lg')}<strong>데모 영상 준비 중</strong>
          <span>영상이 올라오기 전까지는 아래 단계별 가이드를 따라 진행해 주세요.</span></div></div>
      </section>"""
    steps = lab["steps"]
    ch = v.get("chapters")
    meta = " · ".join(x for x in (fmt_t(v["secs"]) if v["secs"] else "", "한국어 내레이션", "자막" if v["vtt"] else "") if x)
    chip, chap = "", ""
    if ch:
        chip = ('<span class="vchip" data-vchip hidden><span class="vchip-n"></span>'
                '<span class="sr-only"> · </span><span class="vchip-t"></span></span>')
        ordered = sorted(ch["list"], key=lambda c: (c["step"], c["start"]))
        btns = "".join(
            f'<li><button type="button" class="chapter" {seek_attrs(lid, c, chapter_title(c, steps))} '
            f'aria-label="{c["step"]}단계 · {e(chapter_title(c, steps))} · {fmt_t(c["start"])}부터 재생">'
            f'<span class="chapter-n">{c["step"]}</span><span class="chapter-t">{e(chapter_title(c, steps))}</span>'
            f'<span class="chapter-time">{fmt_t(c["start"])}</span></button></li>' for c in ordered)
        chap = f"""
        <div class="chapters" role="group" aria-labelledby="chapters-h">
          <div class="chapters-head">
            <p class="chapters-title" id="chapters-h">{icon('list', 'ic ic-sm')}<span>단계별로 골라 보기</span><span class="chapters-meta">{len(ordered)}개 구간</span></p>
            <label class="switch"><input type="checkbox" class="switch-in" role="switch" data-step-only><span class="switch-ui" aria-hidden="true"></span><span class="switch-t">이 단계만 재생</span></label>
          </div>
          <ol class="chapter-list">{btns}</ol>
        </div>"""
    return f"""
      <section class="demo" id="demo" aria-labelledby="demo-h">
        <div class="demo-head">
          <h2 class="demo-title" id="demo-h">{icon('play', 'ic ic-fill')}<span>데모 영상</span></h2>
          <span class="demo-meta">{e(meta)}</span>
        </div>
        <div class="video-frame">{video_tag(v, base, vid_id=f"v-{lid}", label=f"Lab {lab_no(lab)} 데모 영상", lab=lid)}{chip}</div>{chap}
      </section>"""


def figure(lid: str, si: int, k: int, s: dict, info: dict, base: str, idx: int, count: int) -> str:
    cap = str(s.get("caption") or "")
    co_html, labels = [], []
    where = f"{lid} step {si + 1} shot {k + 1} ({s.get('stem')})"
    for j, c in enumerate(s.get("callouts") or []):
        box = c.get("box")
        if not box or len(box) != 4:
            raise BuildError(f"{where}: callout #{j + 1} needs box [x, y, w, h]")
        cls = callout_css(box, info["cw"], info["ch"], c.get("pos"), f"{where} callout #{j + 1}")
        label = str(c.get("label") or "")
        labels.append(label)
        tag = f'<span class="co-tag">{e(label)}</span>' if label else ""
        geo = ",".join(f"{float(v):g}" for v in box)
        co_html.append(f'<span class="co {cls}" data-box="{geo}" data-cap="{info["cw"]}x{info["ch"]}" aria-hidden="true">{tag}</span>')
    alt = cap + (f" (강조 표시: {', '.join(x for x in labels if x)})" if any(labels) else "")
    big = info["variants"][-1][0]
    n_html = f'<span class="fig-n">{idx}<span aria-hidden="true">/</span><span class="sr-only"> / </span>{count}</span>' if count > 1 else ""
    cap_html = f'<figcaption class="fig-cap">{n_html}<span>{e(cap)}</span></figcaption>' if (cap or n_html) else ""
    return f"""
          <figure class="fig">
            <a class="fig-link" href="{media_url(OUT / big, base)}" data-zoom data-ar="{info['ar']}" data-caption="{e(cap)}" data-alt="{e(alt)}" aria-label="스크린샷 크게 보기: {e(cap or '화면')}">
              <span class="fig-frame"><span class="fig-stage {info['ar']}">{img_tag(info, alt, base, sizes="(min-width: 1280px) 800px, (min-width: 768px) 80vw, 94vw")}{''.join(co_html)}</span></span>
              <span class="fig-zoom" aria-hidden="true">{icon('zoom', 'ic ic-sm')}<span>크게 보기</span></span>
            </a>
            {cap_html}
          </figure>"""


def prompt_block(pid: str, text: str, label: str = "프롬프트") -> str:
    return f"""
          <div class="prompt">
            <div class="prompt-head"><span class="prompt-label">{icon('sparkle', 'ic ic-sm')}<span>{e(label)}</span><span class="prompt-hint">복사해서 그대로 붙여 넣으세요</span></span>
              {copy_btn(pid)}</div>
            <pre class="prompt-text" id="{e(pid)}">{e(text)}</pre>
          </div>"""


def code_block(cid: str, c: dict) -> str:
    lang = c["lang"]
    shell_ = lang in SHELL_LANGS
    lines, cont = [], False
    for ln in c["text"].split("\n"):
        cls = "ln"
        if shell_:
            if ln.strip().startswith("#"):
                cls += " ln-c"
            elif ln.strip() and not cont:
                cls += " ln-p"
            cont = ln.rstrip().endswith("\\")
        elif lang in ("yaml", "yml", "python", "py", "toml", "text") and ln.strip().startswith("#"):
            cls += " ln-c"
        lines.append(f'<span class="{cls}">{e(ln)}</span>')
    label = c["file"] or c["label"] or ("Terminal" if shell_ else lang.upper())
    ic = "terminal" if shell_ and not c["file"] else "file"
    numbered = "" if shell_ else " code-num"
    return f"""
          <div class="code{numbered}">
            <div class="code-head"><span class="code-file">{icon(ic, 'ic ic-sm')}<span>{e(label)}</span></span>
              <span class="code-lang">{e(lang)}</span>{copy_btn(cid, 'copy-btn-dark')}</div>
            <pre class="code-pre" id="{e(cid)}" tabindex="0" aria-label="{e(label)} 코드"><code>{''.join(lines)}</code></pre>
          </div>"""


def callout(kind: str, text: str) -> str:
    ic, label = ("bulb", "TIP") if kind == "tip" else ("info", "참고")
    return (f'<div class="callout callout-{kind}" role="note">{icon(ic, "ic callout-ic")}'
            f'<div class="callout-b md"><strong class="callout-k">{label}</strong><p>{md_inline(text)}</p></div></div>')


def step_html(lab: dict, si: int, st: dict, v: dict | None, base: str) -> str:
    lid = lab["id"]
    n = si + 1
    total = len(lab["steps"])
    title = st.get("title", "")
    play = ""
    ch = v["chapters"]["by_step"].get(n) if v and v.get("chapters") else None
    if ch:
        t = chapter_title(ch, lab["steps"])
        play = (f'<button type="button" class="step-play" {seek_attrs(lid, ch, t)} data-reveal>'
                f'{icon("play", "ic ic-sm ic-fill")}<span>이 단계 영상</span>'
                f'<span class="step-play-t">{fmt_t(ch["start"])}–{fmt_t(ch["end"])}</span>'
                f'<span class="sr-only"> ({n}단계 데모 영상 구간 재생)</span></button>')
    parts = []
    if st.get("body"):
        parts.append(f'<div class="prose">{md_blocks(st["body"])}</div>')
    if st.get("prompt"):
        parts.append(prompt_block(f"p-{lid}-{n}", st["prompt"]))
    for k, c in enumerate(st["_code"]):
        parts.append(code_block(f"c-{lid}-{n}-{k}", c))
    infos = [(k, s, shot(s["stem"], s.get("viewport"))) for k, s in enumerate(st["_shots"])]
    infos = [x for x in infos if x[2]]
    if infos:
        figs = "".join(figure(lid, si, k, s, info, base, i + 1, len(infos)) for i, (k, s, info) in enumerate(infos))
        parts.append(f'<div class="figs" data-gallery="STEP {n} · {e(title)}">{figs}</div>')
    if st.get("tip"):
        parts.append(callout("tip", st["tip"]))
    if st.get("note"):
        parts.append(callout("note", st["note"]))
    return f"""
        <li class="step" id="s{n}" data-step="{n}" data-title="{e(title)}">
          <div class="step-head">
            <span class="step-num" aria-hidden="true">{n}</span>
            <div class="step-head-t">
              <p class="step-kicker" aria-hidden="true">STEP {n} <span>/ {total}</span></p>
              <h3 class="step-title"><span class="sr-only">{n}단계. </span>{e(title)}</h3>
            </div>
            {play}
          </div>
          <div class="step-body">{''.join(parts)}</div>
        </li>"""


def more_section(lab: dict) -> str:
    more = lab.get("more") or []
    if not more:
        return ""
    lid = lab["id"]
    cards = "".join(f"""
          <li class="more-item"><span class="more-n" aria-hidden="true">{i + 1:02d}</span>
            <pre class="more-text" id="m-{e(lid)}-{i}">{e(t)}</pre>{copy_btn(f"m-{lid}-{i}", "copy-btn-ghost")}</li>"""
                    for i, t in enumerate(more))
    return f"""
      <section class="more" id="more" aria-labelledby="more-h">
        <div class="sub-head"><h2 class="sub-title" id="more-h">{icon('bolt')}<span>더 해 보기</span></h2>
          <p class="sub-lead">시간이 남으면 아래 프롬프트도 시도해 보세요.</p></div>
        <ul class="more-list">{cards}</ul>
      </section>"""


def checklist_html(track: dict, lab: dict, nxt: dict | None) -> str:
    checks = lab.get("check") or []
    if not checks:
        return ""
    data_lab = f"{track['id']}/{lab['id']}"
    keys = e(" ".join(lab["_keys"]))
    n = len(checks)
    items = "".join(
        f'<li><label class="check"><input class="check-in" type="checkbox" data-check="{e(k)}" data-lab="{e(data_lab)}">'
        f'<span class="check-t">{e(c)}</span></label></li>' for c, k in zip(checks, lab["_keys"]))
    if nxt:
        nxt_btn = (f'<a class="btn btn-primary" href="{e(nxt["id"])}.html"><span>다음 · Lab {e(lab_no(nxt))} {e(nxt["title"])}</span>'
                   f'{icon("arrow", "ic ic-sm")}</a>')
        done_sub = "다음 실습으로 넘어가 볼까요?"
    else:
        nxt_btn = f'<a class="btn btn-primary" href="index.html"><span>{e(track["title"])} 트랙 개요</span>{icon("arrow", "ic ic-sm")}</a>'
        done_sub = "이 트랙의 마지막 실습입니다. 수고하셨습니다!"
    return f"""
      <section class="checklist" id="checklist" aria-labelledby="checklist-h" data-checks="{keys}">
        <header class="checklist-head">
          <span class="ring-wrap" aria-hidden="true"><span class="ring ring-lg"></span><span class="ring-label js-pct">0%</span></span>
          <div class="checklist-head-t">
            <p class="checklist-kicker">LAB {e(lab_no(lab))} · 체크리스트</p>
            <h2 class="checklist-title" id="checklist-h">이번 실습으로 할 수 있게 된 것</h2>
            <p class="checklist-sub">해낸 항목을 눌러 체크하세요 · <strong><span class="js-count">0 / {n}</span> 완료</strong></p>
          </div>
        </header>
        <ol class="check-list">{items}</ol>
        <p class="checklist-note">{icon('info', 'ic ic-xs')}<span>진행 상황은 이 브라우저에만 저장되며, 왼쪽 목록과 홈 화면 진행률에 반영됩니다.</span></p>
        <div class="checklist-done">
          <span class="checklist-done-ic">{icon('sparkle', 'ic ic-lg')}</span>
          <div class="checklist-done-t"><strong>모든 항목을 완료했어요!</strong><span>{done_sub}</span></div>
          {nxt_btn}
        </div>
      </section>"""


def pager(track: dict, idx: int, base: str) -> str:
    labs = track["labs"]
    prev = labs[idx - 1] if idx > 0 else None
    nxt = labs[idx + 1] if idx + 1 < len(labs) else None
    if prev:
        p = (f'<a class="pager-link pager-prev" href="{e(prev["id"])}.html" rel="prev"><span class="pager-k">{icon("arrow-left", "ic ic-sm")}이전 실습</span>'
             f'<span class="pager-t">Lab {e(lab_no(prev))} · {e(prev["title"])}</span></a>')
    else:
        p = (f'<a class="pager-link pager-prev" href="index.html"><span class="pager-k">{icon("arrow-left", "ic ic-sm")}트랙 개요</span>'
             f'<span class="pager-t">{e(track["title"])}</span></a>')
    if nxt:
        n = (f'<a class="pager-link pager-next" href="{e(nxt["id"])}.html" rel="next"><span class="pager-k">다음 실습{icon("arrow", "ic ic-sm")}</span>'
             f'<span class="pager-t">Lab {e(lab_no(nxt))} · {e(nxt["title"])}</span></a>')
    else:
        n = (f'<a class="pager-link pager-next" href="{base}index.html#next"><span class="pager-k">마무리{icon("arrow", "ic ic-sm")}</span>'
             f'<span class="pager-t">오늘부터 이렇게 써 보세요</span></a>')
    return f'<nav class="pager" aria-label="이전·다음 실습">{p}{n}</nav>'


def lab_page(site: dict, tracks: list, track: dict, idx: int, assets: dict) -> str:
    base = "../"
    lab = track["labs"][idx]
    lid = lab["id"]
    steps = lab["steps"]
    v = video_info(lab.get("video")) if ready(lab) else None
    if lab.get("video") and ready(lab) and not v:
        warn(f"{track['id']}/{lid}: video '{lab['video']}' not found in assets/video")
    if v and v.get("chapters"):
        missing = [i + 1 for i in range(len(steps)) if (i + 1) not in v["chapters"]["by_step"]]
        if missing:
            warn(f"{v['name']}.chapters.json has no chapter for step(s) {missing}")
    title = lab["title"]
    chips = [level_chip(lab.get("level")), f'<span class="chip">{icon("clock", "ic ic-xs")}<span>{lab["minutes"]}분</span></span>']
    if steps:
        chips.append(f'<span class="chip">{icon("list", "ic ic-xs")}<span>{len(steps)}단계</span></span>')
    if v and v["secs"]:
        chips.append(f'<span class="chip">{icon("play", "ic ic-xs ic-fill")}<span>영상 {fmt_t(v["secs"])}</span></span>')
    meta = "".join(f"<li>{c}</li>" for c in chips if c)
    sub = f'<p class="lab-sub">{e(lab["subtitle"])}</p>' if lab.get("subtitle") else ""
    goal = (f'<div class="goal">{icon("target", "ic goal-ic")}<div class="goal-b md"><p class="goal-k">이번 실습의 목표</p>'
            f'<p>{md_inline(lab["goal"])}</p></div></div>') if lab.get("goal") else ""
    header = f"""
      {crumbs([("홈", f"{base}index.html"), (track["title"], "index.html"), (f"Lab {lab_no(lab)}", None)])}
      <header class="lab-head">
        <div class="hero-bg" aria-hidden="true"></div>
        {shapes_html(("blue", "yellow", "red", "green"))}
        <div class="lab-head-in">
          <p class="hero-kicker"><span class="gdots" aria-hidden="true"><i></i><i></i><i></i><i></i></span><span class="t-{e(track['id'])} kicker-track">{e(track['title'])}</span><span>LAB {e(lab_no(lab))}</span></p>
          <h1 class="lab-title" id="lab-title">{e(title)}</h1>
          {sub}
          <ul class="lab-meta" aria-label="실습 정보">{meta}</ul>
        </div>
        {goal}
      </header>"""
    nxt = track["labs"][idx + 1] if idx + 1 < len(track["labs"]) else None
    if not ready(lab):
        body = f"""
      <div class="soon-card">{icon('hourglass', 'ic ic-lg')}<div><strong>실습 가이드를 준비하고 있습니다</strong>
        <p>곧 이 자리에 실제 화면 영상과 단계별 가이드가 올라옵니다.</p></div></div>"""
    else:
        steps_html = "".join(step_html(lab, i, s, v, base) for i, s in enumerate(steps))
        body = f"""
      {demo_section(lab, v, base)}
      <div class="steps-head"><h2 class="steps-title">{icon('list', 'ic')}<span>단계별 가이드</span></h2><span class="steps-meta">{len(steps)}단계 · 약 {lab['minutes']}분</span></div>
      <ol class="steps">{steps_html}
      </ol>{more_section(lab)}{checklist_html(track, lab, nxt)}"""
    main = f"""
    <article class="lab" data-lab-section="{e(lid)}" data-track-id="{e(track['id'])}" aria-labelledby="lab-title">{header}{body}
      {pager(track, idx, base)}
    </article>"""
    nav = nav_tree(site, tracks, base, track, current=lid)
    now_n = f"{len(steps)}단계" if steps else ""
    mbar = f"""
<div class="mbar">
  <button type="button" class="mbar-btn" data-open="drawer" aria-haspopup="dialog">
    {icon('menu')}<span class="mbar-k">LAB {e(lab_no(lab))}</span><span class="mbar-now" data-now>개요 · 데모 영상</span>
    <span class="mbar-n" data-now-n>{e(now_n)}</span><span class="sr-only"> — 목차 열기</span>{icon('chev', 'ic ic-sm mbar-chev')}
  </button>
</div>"""
    dock = (f"""
<nav class="stepdock" data-stepdock aria-label="단계 이동" hidden>
  <button type="button" class="dock-btn" data-dock-prev aria-label="이전 단계">{icon('chev-left')}</button>
  <a class="dock-now" href="#s1" data-dock-link>
    <span class="dock-k" data-dock-k>STEP 1 / {len(steps)}</span><span class="dock-t" data-dock-t>{e(steps[0].get('title', ''))}</span>
    <span class="dock-bar" aria-hidden="true"><span class="dock-fill" data-dock-fill></span></span>
  </a>
  <button type="button" class="dock-btn dock-next" data-dock-next aria-label="다음 단계"><span>다음</span>{icon('chev-right')}</button>
</nav>""" if steps and ready(lab) else "")
    desc = plain(lab.get("goal")) or f"{track['title']} Lab {lab_no(lab)} · {title}"
    return (head(f"Lab {lab_no(lab)} · {title} — {track['title']} · {site['title']}", desc, assets, base, track, "lab")
            + topbar(site, tracks, base, track, "lab") + mbar + f"""
<div class="lab-layout">
  <aside class="sidebar" aria-label="실습 내비게이션"><div class="sidebar-in">{nav}</div></aside>
  <main id="main" class="lab-main" tabindex="-1">{main}
  </main>
</div>{dock}""" + footer(site, base) + drawer(site, base, nav) + page_end())


# --------------------------------------------------------------------------- shared cards (home + track)
def lab_thumb(lab: dict) -> dict | None:
    """Representative real screenshot of a lab: lab['thumb'] or the first shot of the middle-most step."""
    stems = []
    if lab.get("thumb"):
        stems.append(lab["thumb"])
    steps = lab.get("steps") or []
    order = sorted(range(len(steps)), key=lambda i: abs(i - (len(steps) - 1) / 2))
    for i in order:
        for s_ in norm_shots(steps[i]):
            if s_.get("stem") and not str(s_["stem"]).startswith("gc_"):
                stems.append(s_["stem"])
    for st in stems:
        p = next((SHOTS_SRC / f"{st}{x}" for x in (".png", ".jpg", ".webp") if (SHOTS_SRC / f"{st}{x}").is_file()), None)
        if p:
            return shot(st)
    return None


def opening_card(track: dict, base: str, *, show_pill: bool = True) -> str:
    op = track.get("opening") or {}
    v = video_info(op.get("video")) if op else None
    if op and op.get("video") and not v:
        warn(f"{track['id']}: opening video '{op['video']}' not found in assets/video")
    pill = f'<span class="pill t-{e(track["id"])}"><span class="dot" aria-hidden="true"></span>{e(track["title"])}</span>' if show_pill else ""
    if not v:
        return f"""
        <div class="opening-card opening-card--soon t-{e(track['id'])}">
          <div class="video-frame video-soon"><div class="soon-in">{icon('present', 'ic ic-lg')}<strong>오프닝 발표 영상 준비 중</strong></div></div>
          <div class="opening-b">{pill}<h3 class="opening-t">{e(op.get('title') or '오프닝 발표')}</h3></div>
        </div>"""
    length = f"{v['secs'] // 60}분 {v['secs'] % 60:02d}초" if v["secs"] else ""
    meta = " · ".join(x for x in (length, "한국어 내레이션", "자막" if v["vtt"] else "") if x)
    desc = f'<p class="opening-d">{e(op["desc"])}</p>' if op.get("desc") else ""
    return f"""
        <div class="opening-card t-{e(track['id'])}">
          <div class="video-frame">{video_tag(v, base, vid_id=f"v-open-{track['id']}", label=f"{track['title']} 오프닝 발표 영상", preload="none")}</div>
          <div class="opening-b">{pill}<h3 class="opening-t">{e(op.get('title') or '오프닝 발표')}</h3>{desc}
            <p class="opening-m">{icon('present', 'ic ic-xs')}<span>{e(meta)}</span></p></div>
        </div>"""


def lab_card(track: dict, lab: dict, base: str, prefix: str) -> str:
    soon = not ready(lab)
    v = video_info(lab.get("video")) if not soon else None
    th = lab_thumb(lab) if not soon else None
    if th:
        dur = (f'<span class="lab-card-dur">{icon("play", "ic ic-xs ic-fill")}<span>{fmt_t(v["secs"])}</span></span>'
               if v and v.get("secs") else "")
        thumb = f'<span class="lab-card-thumb">{img_tag(th, "", base, sizes="(max-width: 640px) 92vw, (max-width: 1100px) 46vw, 360px")}{dur}</span>'
    else:
        thumb = f'<span class="lab-card-thumb lab-card-thumb--empty">{icon("hourglass", "ic ic-lg")}</span>'
    meta = [f'{icon("clock", "ic ic-xs")}<span>{lab["minutes"]}분</span>']
    if lab["steps"]:
        meta.append(f'{icon("list", "ic ic-xs")}<span>{len(lab["steps"])}단계</span>')
    status = level_chip(lab.get("level")) if not soon else '<span class="chip chip-soon">준비 중</span>'
    sub = f'<span class="lab-card-sub">{e(lab["subtitle"])}</span>' if lab.get("subtitle") else ""
    return f"""
        <li><a class="lab-card{' is-soon' if soon else ''}" href="{prefix}{e(lab['id'])}.html" data-checks="{e(' '.join(lab['_keys']))}">
          {thumb}
          <span class="lab-card-b">
            <span class="lab-card-top"><span class="lab-card-no">LAB {e(lab_no(lab))}</span>{status}{state_mark()}</span>
            <span class="lab-card-title">{e(lab['title'])}</span>
            {sub}
            <span class="lab-card-meta">{''.join(f'<span>{m}</span>' for m in meta)}</span>
          </span>
        </a></li>"""


def prep_list(prep: list) -> str:
    if not prep:
        return '<p class="empty">별도 준비물이 없습니다.</p>'
    items = "".join(f'<li><span class="prep-n" aria-hidden="true">{i + 1}</span><p class="md">{md_inline(p)}</p></li>'
                    for i, p in enumerate(prep))
    return f'<ol class="prep-list">{items}</ol>'


def file_list(track: dict, base: str) -> str:
    items = track.get("_files") or []
    if not items:
        return '<p class="empty">실습 파일은 준비되는 대로 이곳에 올라옵니다.</p>'
    bundle = next((it for it in items if it.get("bundle")), None)
    out = []
    if bundle:
        name = bundle["file"].rsplit("/", 1)[-1]
        out.append(f"""
          <a class="bundle" href="{media_url(OUT / bundle['_href'], base)}" download="{e(name)}">
            <span class="bundle-ic">{icon('zip', 'ic ic-lg')}</span>
            <span class="bundle-b"><span class="bundle-k">한 번에 모두 받기 · ZIP {e(human_size(bundle['_size']))}</span>
              <strong class="bundle-t">{e(bundle['title'])}</strong><span class="bundle-d">{e(bundle.get('desc', ''))}</span></span>
            <span class="bundle-dl">{icon('download', 'ic ic-sm')}<span>전체 다운로드</span></span>
          </a>""")
    rows = []
    for it in items:
        if it is bundle:
            continue
        name = it["file"].rsplit("/", 1)[-1]
        pv = it.get("_pv")
        img = (f'<img src="{media_url(OUT / pv[0], base)}" width="{pv[1]}" height="{pv[2]}" alt="" loading="lazy" decoding="async">' if pv else "")
        labs = "".join(f'<span class="file-lab">{e(x.replace("lab", "Lab "))}</span>' for x in it.get("labs") or [])
        kind = it["_kind"].lower()
        rows.append(f"""
            <li><a class="file" href="{media_url(OUT / it['_href'], base)}" download="{e(name)}">
              <span class="file-thumb">{img}<span class="file-kind kind-{e(kind)}">{e(it['_kind'])}</span></span>
              <span class="file-b"><span class="file-t">{e(it['title'])}</span><span class="file-d">{e(it.get('desc', ''))}</span>
                <span class="file-m">{labs}<span class="file-size">{e(human_size(it['_size']))}</span></span></span>
              <span class="file-dl" aria-hidden="true">{icon('download', 'ic ic-sm')}</span>
            </a></li>""")
    return "".join(out) + (f'<ul class="file-list">{"".join(rows)}</ul>' if rows else "")


def resources_block(track: dict, base: str) -> str:
    return f"""
        <div class="res">
          <div class="res-col res-prep" id="prep-{e(track['id'])}">
            <h3 class="res-h">{icon('list', 'ic ic-sm')}<span>시작 전 준비물</span></h3>
            {prep_list(track.get("prep") or [])}
          </div>
          <div class="res-col res-files">
            <h3 class="res-h">{icon('download', 'ic ic-sm')}<span>실습 파일</span></h3>
            {file_list(track, base)}
          </div>
        </div>"""


def faq_html(items: list, track: dict | None = None) -> str:
    out = []
    for it in items:
        tag = (f'<span class="pill pill-xs t-{e(track["id"])}">{e(track.get("short") or track["title"])}</span>' if track else "")
        out.append(f'<details class="faq"><summary>{tag}<span class="faq-q">{e(it["q"])}</span>{icon("chev", "ic faq-chev")}</summary>'
                   f'<div class="faq-a prose">{md_blocks(it["a"])}</div></details>')
    return "".join(out)


def tabs(name: str, label: str, panels: list[tuple[dict, str, int]]) -> str:
    """Accessible tabs, one panel per track. Without JS every panel is shown in sequence (tab list hidden)."""
    if not panels:
        return ""
    btns, bodies = [], []
    for i, (t, body, count) in enumerate(panels):
        tid = e(t["id"])
        sel = i == 0
        n_html = f'<span class="tab-n">{count}</span>' if count else ""
        btns.append(f'<button type="button" class="tab t-{tid}" role="tab" id="tab-{name}-{tid}" aria-controls="panel-{name}-{tid}" '
                    f'aria-selected="{"true" if sel else "false"}" tabindex="{0 if sel else -1}">'
                    f'<span class="dot" aria-hidden="true"></span><span>{e(t["title"])}</span>{n_html}</button>')
        bodies.append(f'<div class="tab-panel" role="tabpanel" id="panel-{name}-{tid}" aria-labelledby="tab-{name}-{tid}" tabindex="0">'
                      f'<p class="tab-panel-h">{e(t["title"])}</p>{body}</div>')
    return (f'<div class="tabs" data-tabs><div class="tab-list" role="tablist" aria-label="{e(label)}">{"".join(btns)}</div>'
            f'{"".join(bodies)}</div>')


def next_section(site: dict, sec_id: str = "next") -> str:
    steps = site.get("next_steps") or []
    refs = [r for r in (site.get("references") or []) if str(r.get("url", "")).startswith("https://")]
    if not steps and not refs:
        return ""
    cards = "".join(f"""
          <li class="next-card"><span class="next-top"><span class="next-no">{e(s.get('no') or f'{i + 1:02d}')}</span><span class="next-k">{e(s.get('kicker', ''))}</span></span>
            <h3 class="next-t">{e(s.get('title', ''))}</h3><p class="next-b md">{md_inline(s.get('body', ''))}</p></li>"""
                    for i, s in enumerate(steps))
    rcards = "".join(f"""
          <li><a class="ref-card" href="{e(r['url'])}" target="_blank" rel="noopener noreferrer">
            <span class="ref-b"><strong>{e(r['title'])}</strong>{f'<span>{e(r["desc"])}</span>' if r.get('desc') else ''}</span>
            {icon('external', 'ic ic-sm')}<span class="sr-only"> (새 탭)</span></a></li>""" for r in refs)
    refs_html = (f'<div class="refs"><h3 class="refs-h">{icon("book", "ic ic-sm")}<span>공식 참고 문서</span></h3>'
                 f'<ul class="ref-grid">{rcards}</ul></div>') if rcards else ""
    return f"""
  <section class="section section-alt" id="{e(sec_id)}" aria-labelledby="{e(sec_id)}-h">
    <div class="container">
      {section_head("Next Steps", "마무리 — 오늘부터 이렇게 써 보세요", f"{sec_id}-h", "실습에서 배운 내용을 내일 업무에 바로 적용할 수 있는 실행 가이드와 공식 문서입니다.")}
      {f'<ol class="next-grid">{cards}</ol>' if cards else ''}
      {refs_html}
    </div>
  </section>"""


# --------------------------------------------------------------------------- track overview
def track_page(site: dict, tracks: list, track: dict, assets: dict) -> str:
    """Track overview in exactly the landing page's language: centred hero (kicker chip · two-line title ·
    CTA pair · big facts) over the same shapes/background, the opening video in the same window 'stage',
    centred section heads, learning path, prep & files, 2-column FAQ and the closing CTA band."""
    base = "../"
    tid = track["id"]
    c = track_counts(track)
    labs_html = "".join(lab_card(track, lab, base, "") for lab in track["labs"])
    op = track.get("opening") or {}
    v = video_info(op.get("video")) if op else None
    if op and op.get("video") and not v:
        warn(f"{tid}: opening video '{op['video']}' not found in assets/video")
    line2 = track.get("hero_line") or op.get("title") or track.get("tagline", "")
    audience = f" · {e(track['audience'])}" if track.get("audience") else ""
    resume = (f'href="{e(first_href(track, ""))}" data-resume="{e(tid)}" data-resume-labs="{resume_attr(track, "")}"')
    second_btn = (f'<a class="btn btn-secondary btn-lg" href="#opening">{icon("play", "ic ic-sm ic-fill")}<span>오프닝 영상 보기</span></a>'
                  if v else f'<a class="btn btn-secondary btn-lg" href="#files">{icon("download", "ic ic-sm")}<span>실습 파일 받기</span></a>')
    stage = ""
    if v:
        length = f"{v['secs'] // 60}분 {v['secs'] % 60:02d}초" if v["secs"] else ""
        stage = f"""
    <div class="container stage-wrap" id="opening">
      <div class="stage stage-video">
        <figure class="win win-video"><span class="win-bar"><i></i><i></i><i></i><span>오프닝 발표 · {e(op.get('title') or track['title'])}{f' · {e(length)}' if length else ''}</span></span>
          <span class="video-frame">{video_tag(v, base, vid_id=f"v-open-{tid}", label=f"{track['title']} 오프닝 발표 영상", preload="none")}</span></figure>
      </div>
    </div>"""
    faq = (f"""
  <section class="section" id="faq" aria-labelledby="faq-h">
    <div class="container faq-wrap">
      {section_head("FAQ", "자주 묻는 질문", "faq-h", f"{track['title']} 실습 중에 많이 묻는 질문을 모았습니다. 원하는 답이 없으면 진행자에게 편하게 물어 주세요.")}
      <div class="faq-list">{faq_html(track["faq"])}</div>
    </div>
  </section>""" if track.get("faq") else "")
    main = f"""
<main id="main" tabindex="-1">
  <section class="hero hero-track" aria-labelledby="track-title">
    <div class="hero-bg" aria-hidden="true"></div>
    {shapes_html()}
    <div class="container hero-in">
      {crumbs([("홈", f"{base}index.html"), (track["title"], None)])}
      <p class="hero-kicker"><span class="gdots" aria-hidden="true"><i></i><i></i><i></i><i></i></span><span class="t-{e(tid)} kicker-track">{e(track.get('short') or tid.upper())} TRACK</span>{audience}</p>
      <h1 class="hero-title" id="track-title"><span class="hero-line">{e(track['title'])} 트랙</span><span class="hero-line grad-text">{e(line2)}</span></h1>
      <p class="hero-sub">{e(track['tagline'])}</p>
      <div class="hero-actions">
        <a class="btn btn-primary btn-lg" {resume}><span class="js-resume-l">시작하기</span>{icon('arrow', 'ic ic-sm ic-arrow-move')}</a>
        {second_btn}
      </div>
      <ul class="hero-facts" aria-label="한눈에 보기">
        <li><strong>{c['labs']}</strong><span>개 Lab</span></li>
        <li><strong>{max(0.5, round(c['minutes'] / 30) / 2):g}</strong><span>시간 분량</span></li>
        <li><strong>{c['videos']}</strong><span>편 데모 영상</span></li>
        <li data-checks="{e(track_keys(track))}"><strong class="js-count">0 / {c['checks']}</strong><span>내 진행률</span></li>
      </ul>
    </div>
    {stage}
  </section>
  <section class="section" id="labs" aria-labelledby="labs-h">
    <div class="container">
      {section_head("Learning Path", "학습 경로", "labs-h", "Lab은 순서대로 이어집니다. 각 Lab은 데모 영상 → 단계별 가이드 → 체크리스트로 진행합니다. 카드를 눌러 시작하세요.", center=True)}
      <ol class="lab-grid">{labs_html}</ol>
    </div>
  </section>
  <section class="section section-alt" id="files" aria-labelledby="files-h">
    <div class="container">
      <span class="anchor" id="prep" aria-hidden="true"></span>
      {section_head("Before You Start", "준비물 & 실습 파일", "files-h", "시작 전에 준비물을 확인하고, 실습에서 쓸 Cymbal 가상 업무 파일을 내려받아 두세요.")}
      {resources_block(track, base)}
    </div>
  </section>{faq}
  <section class="section section-tight" aria-labelledby="cta-h">
    <div class="container">
      <div class="cta-band">
        <h2 id="cta-h">{e(track['title'])} 트랙, 지금 시작해 보세요</h2>
        <p>Lab 01부터 차례로 진행하면 됩니다. 진행 상황은 이 브라우저에 저장되어, 다음에 오면 이어서 할 수 있어요.</p>
        <div class="hero-actions">
          <a class="btn btn-primary btn-lg" {resume}><span class="js-resume-l">시작하기</span>{icon('arrow', 'ic ic-sm ic-arrow-move')}</a>
          <a class="btn btn-secondary btn-lg" href="{base}index.html#tracks"><span>다른 트랙 보기</span></a>
        </div>
      </div>
    </div>
  </section>
</main>"""
    nav = nav_tree(site, tracks, base, track, overview=True)
    return (head(f"{track['title']} 트랙 — {site['title']} · Google Cloud", track["tagline"], assets, base, track, "track")
            + topbar(site, tracks, base, track, "track") + main + footer(site, base) + drawer(site, base, nav) + page_end())


# --------------------------------------------------------------------------- home
def _flower_path(n: int = 8, r: float = 41.0, a: float = 7.0, steps: int = 240) -> str:
    """Scalloped 'cookie' outline (Material 3 expressive shape) centred in a 100×100 box."""
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        rr = r + a * math.cos(n * t)
        pts.append(f"{50 + rr * math.cos(t):.2f} {50 + rr * math.sin(t):.2f}")
    return "M" + " L".join(pts) + " Z"


SHAPES = {
    "blue": '<svg viewBox="0 0 100 100" focusable="false"><circle cx="50" cy="50" r="50" fill="#4285F4"/></svg>',
    "yellow": ('<svg viewBox="0 0 100 92" focusable="false"><polygon points="50,12 90,80 10,80" fill="#FBBC04" '
               'stroke="#FBBC04" stroke-width="18" stroke-linejoin="round"/></svg>'),
    "red": f'<svg viewBox="0 0 100 100" focusable="false"><path d="{_flower_path()}" fill="#EA4335"/></svg>',
    "green": '<svg viewBox="0 0 100 50" focusable="false"><path d="M0 50a50 50 0 0 1 100 0z" fill="#34A853"/></svg>',
    "purple": '<svg viewBox="0 0 100 56" focusable="false"><rect width="100" height="56" rx="28" fill="#A142F4"/></svg>',
    "dots": ('<svg viewBox="0 0 44 44" focusable="false"><circle cx="8" cy="8" r="6" fill="#4285F4"/><circle cx="36" cy="8" r="6" fill="#EA4335"/>'
             '<circle cx="8" cy="36" r="6" fill="#FBBC04"/><circle cx="36" cy="36" r="6" fill="#34A853"/></svg>'),
}


def shapes_html(which: tuple = ("blue", "yellow", "red", "green", "purple", "dots")) -> str:
    """Decorative Google-colour shapes behind a hero (aria-hidden; abstract shapes only — never product logos)."""
    return ('<div class="shapes" aria-hidden="true">'
            + "".join(f'<span class="shape sh-{k}">{SHAPES[k]}</span>' for k in which) + "</div>")


def _shot_if(stem: str) -> dict | None:
    return shot(stem) if any((SHOTS_SRC / f"{stem}{x}").is_file() for x in (".png", ".jpg", ".webp")) else None


DEFAULT_STAGE = [{"stem": "ge_3_32_canvas_ready", "title": "Gemini Enterprise · 데이터 분석 & Canvas"},
                 {"stem": "ag_7v_21_deck_s1", "title": "결과물 · 에이전트가 만든 임원 보고 슬라이드"},
                 {"stem": "ag_4_03_build_done", "title": "Antigravity · 에이전트와 함께 개발"}]


def deck_pos(k: int, cur: int, n: int) -> str:
    """Card k's place when card `cur` is centred: c / l / r, or fl / fr (hidden, waiting off to the side).
    portal.js uses the same rule, so the server-rendered markup is the deck's first frame."""
    off = (k - cur) % n
    if off > n / 2:
        off -= n
    return {0: "c", -1: "l", 1: "r"}.get(off, "fl" if off < 0 else "fr")


def hero_stage(site: dict, base: str) -> str:
    """Real captures in window frames that rotate right → centre → left (SITE['stage']).
    CSS transitions do the motion; portal.js moves data-pos and shows the controls (prev · dots · next · pause).
    Without JS, or with reduced motion before any click, it is the static fan: first item centred."""
    cards = []
    for it in site.get("stage") or DEFAULT_STAGE:
        stem = str(it.get("stem", ""))
        info = _shot_if(stem) if SAFE_STEM.match(stem) else None
        if not info:
            warn(f"stage item skipped (screenshot not found): {stem}")
            continue
        cards.append((info, str(it.get("title", ""))))
    if not cards:
        return ""
    n = len(cards)
    figs, dots = [], []
    for k, (info, title) in enumerate(cards):
        figs.append(f'<figure class="win" data-pos="{deck_pos(k, 0, n)}"><span class="win-bar"><i></i><i></i><i></i>'
                    f'<span>{e(title)}</span></span>'
                    f'{img_tag(info, "", base, sizes="(max-width: 899px) 82vw, 680px", eager=k == 0)}</figure>')
        cur = ' aria-current="true"' if k == 0 else ""
        dots.append(f'<button class="deck-dot" type="button" data-deck-go="{k}" aria-label="{k + 1}. {e(title)}"{cur}>'
                    f'<span class="deck-pill"><span class="deck-fill"></span></span></button>')
    ctrl = "" if n < 2 else f"""
        <div class="deck-ctrl" hidden>
          <button class="deck-btn" type="button" data-deck="prev" aria-label="이전 화면">{icon('chev-left')}</button>
          <div class="deck-dots" role="group" aria-label="화면 고르기">{''.join(dots)}</div>
          <button class="deck-btn" type="button" data-deck="next" aria-label="다음 화면">{icon('chev-right')}</button>
          <button class="deck-btn deck-toggle" type="button" data-deck="toggle" aria-pressed="false" aria-label="자동 넘김 멈추기">{icon('pause', 'ic ic-pause')}{icon('play', 'ic ic-play')}</button>
        </div>"""
    return f"""
    <div class="container stage-wrap">
      <div class="stage" data-deck-root>
        <div class="deck" aria-hidden="true">{''.join(figs)}</div>
        <span class="stage-badge stage-badge-a" aria-hidden="true">{icon('sparkle', 'ic ic-sm')}<span>실제 앱 화면 그대로</span></span>
        <span class="stage-badge stage-badge-b" aria-hidden="true">{icon('check', 'ic ic-sm')}<span>따라 하면 완성되는 결과물</span></span>{ctrl}
      </div>
    </div>"""


def op_class(focus, zoom=None) -> str:
    """'x y' (percent) [+ zoom ≥ 1] → generated classes for cover-cropped showcase images (CSP: no inline style).
    Zoom scales the real capture around the same focus point (a crop, never an edit)."""
    try:
        x, y = (max(0, min(100, int(float(v)))) for v in str(focus).replace("%", " ").split()[:2])
    except ValueError:
        return ""
    cls = f"op-{x}-{y}"
    GEN_CSS.append(f".{cls}{{object-position:{x}% {y}%;--fx:{x}%;--fy:{y}%}}")
    try:
        z = round(float(zoom or 1), 2)
    except (TypeError, ValueError):
        z = 1.0
    if 1 < z <= 3:
        zc = f"zm-{round(z * 100)}"
        GEN_CSS.append(f".{zc}{{scale:{z:g}}}")
        cls += f" {zc}"
    return cls


def showcase_section(site: dict, tracks: list, base: str) -> str:
    """Bento of finished deliverables (real captures) from SITE['showcase'] — each tile opens its lab."""
    items = site.get("showcase") or []
    tmap = {t["id"]: t for t in tracks}
    cards = []
    for it in items:
        t = tmap.get(str(it.get("track", "")))
        info = _shot_if(str(it.get("stem", ""))) if it.get("stem") and SAFE_STEM.match(str(it["stem"])) else None
        if not t or not info:
            warn(f"showcase item skipped (track/stem not found): {it.get('track')}/{it.get('stem')}")
            continue
        lab = next((l for l in t["labs"] if l["id"] == it.get("lab")), None)
        href = f"{e(t['id'])}/{e(lab['id'])}.html" if lab and ready(lab) else f"{e(t['id'])}/index.html"
        try:
            span = max(3, min(12, int(it.get("span", 4))))
        except (TypeError, ValueError):
            span = 4
        size = f" w{span}" + (" is-lg" if span >= 7 else "")
        sizes = f"(max-width: 719px) 92vw, (max-width: 1099px) 46vw, {round(1180 * span / 12)}px"
        img = img_tag(info, "", base, sizes=sizes, cls=op_class(it.get("focus", "50 0"), it.get("zoom")))
        k = f"{t['title']} · Lab {lab_no(lab)}" if lab else t["title"]
        cards.append(f"""
        <li class="bento-item{size} t-{e(t['id'])}"><a class="bento-card" href="{href}">
          <span class="bento-media">{img}</span>
          <span class="bento-b"><span class="bento-k"><span class="dot" aria-hidden="true"></span>{e(k)}</span>
            <strong class="bento-t">{e(it.get('title', ''))}</strong><span class="bento-d">{e(it.get('desc', ''))}</span>
            <span class="bento-go">실습 보러 가기{icon('arrow', 'ic ic-xs')}</span></span>
        </a></li>""")
    if not cards:
        return ""
    return f"""
  <section class="section section-alt" id="showcase" aria-labelledby="showcase-h">
    <div class="container">
      {section_head("What you'll build", "실습을 마치면, 이런 결과물이 남습니다", "showcase-h",
                    "모두 실습 중에 실제 앱에서 만든 화면입니다. 카드를 누르면 그 결과물을 만드는 Lab으로 바로 이동합니다.", center=True)}
      <ul class="bento">{''.join(cards)}</ul>
    </div>
  </section>"""


def home_track_card(t: dict, base: str) -> str:
    c = track_counts(t)
    rl = [l for l in t["labs"] if ready(l)]
    cover_info = shot(str(t["cover"])) if t.get("cover") else None
    if not cover_info:
        cover_lab = next((l for l in rl[2:] + rl[:2] if lab_thumb(l)), None)
        cover_info = lab_thumb(cover_lab) if cover_lab else None
    cover = (f'<a class="track-cover" href="{e(t["id"])}/index.html" tabindex="-1" aria-hidden="true">'
             f'{img_tag(cover_info, "", base, sizes="(max-width: 899px) 92vw, 560px")}</a>') if cover_info else ""
    rows = "".join(
        f'<li><a class="lab-row{"" if ready(l) else " is-soon"}" href="{e(t["id"])}/{e(l["id"])}.html" data-checks="{e(" ".join(l["_keys"]))}">'
        f'<span class="lab-row-no">{e(lab_no(l))}</span><span class="lab-row-t">{e(l["title"])}</span>'
        f'<span class="lab-row-m">{l["minutes"]}분</span>{state_mark()}</a></li>' for l in t["labs"])
    audience = f" · {e(t['audience'])}" if t.get("audience") else ""
    return f"""
        <article class="track-card t-{e(t['id'])}" data-checks="{e(track_keys(t))}" aria-labelledby="tc-{e(t['id'])}">
          {cover}
          <div class="track-card-b">
            <p class="track-kicker"><span class="dot" aria-hidden="true"></span>{e(t.get('short') or t['id'].upper())} TRACK{audience}</p>
            <h3 class="track-title" id="tc-{e(t['id'])}"><a href="{e(t['id'])}/index.html">{e(t['title'])}</a></h3>
            <p class="track-desc">{e(t['tagline'])}</p>
            <ul class="track-facts">
              <li>{icon('list', 'ic ic-xs')}<span>{c['labs']}개 Lab</span></li>
              <li>{icon('clock', 'ic ic-xs')}<span>약 {e(fmt_minutes(c['minutes']))}</span></li>
              <li>{icon('play', 'ic ic-xs ic-fill')}<span>데모 영상 {c['videos']}편</span></li>
            </ul>
            <div class="track-progress"><span class="bar"><span class="bar-fill"></span></span><span class="track-progress-t"><span class="js-count">0 / {c['checks']}</span> 완료</span></div>
            <div class="track-actions">
              <a class="btn btn-primary" href="{e(first_href(t, t['id'] + '/'))}" data-resume="{e(t['id'])}" data-resume-labs="{resume_attr(t, t['id'] + '/')}"><span class="js-resume-l">시작하기</span>{icon('arrow', 'ic ic-sm ic-arrow-move')}</a>
              <a class="btn btn-secondary" href="{e(t['id'])}/index.html">트랙 개요</a>
            </div>
          </div>
          <div class="track-labs">
            <p class="track-labs-h">실습 순서</p>
            <ol class="lab-rows" aria-label="{e(t['title'])} 실습 목록">{rows}</ol>
          </div>
        </article>"""


def video_cards(t: dict, base: str) -> tuple[str, int]:
    cards = []
    for lab in t["labs"]:
        if not ready(lab):
            continue
        v = video_info(lab.get("video"))
        if not v:
            continue
        th = lab_thumb(lab)
        if th:
            img = img_tag(th, "", base, sizes="(max-width: 640px) 92vw, (max-width: 1100px) 46vw, 380px")
        elif v.get("poster"):
            img = f'<img src="{media_url(v["poster"], base)}" alt="" loading="lazy" decoding="async">'
        else:
            img = ""
        cards.append(f"""
            <li><a class="video-card" href="{e(t['id'])}/{e(lab['id'])}.html#demo">
              <span class="video-card-thumb">{img}<span class="video-card-play" aria-hidden="true">{icon('play', 'ic ic-fill')}</span><span class="video-card-dur">{fmt_t(v['secs'])}</span></span>
              <span class="video-card-b"><span class="video-card-k">LAB {e(lab_no(lab))}</span><span class="video-card-t">{e(lab['title'])}</span>
                {f'<span class="video-card-s">{e(lab["subtitle"])}</span>' if lab.get('subtitle') else ''}</span>
            </a></li>""")
    if not cards:
        return "", 0
    return (f'<ul class="video-grid">{"".join(cards)}</ul>'
            f'<p class="tab-more"><a class="link-more" href="{e(t["id"])}/index.html">{e(t["title"])} 트랙 전체 보기{icon("arrow", "ic ic-xs")}</a></p>'), len(cards)


def home_page(site: dict, tracks: list, assets: dict) -> str:
    base = ""
    all_labs = [l for t in tracks for l in t["labs"]]
    n_vid = sum(track_counts(t)["videos"] for t in tracks)
    n_files = sum(len(t.get("_files") or []) for t in tracks)
    total_min = sum(l["minutes"] for l in all_labs)
    stats = site.get("stats") or [
        {"value": str(len(all_labs)), "label": "개 Lab"},
        {"value": str(n_vid), "label": "편 데모 영상"},
        {"value": f"{max(0.5, round(total_min / 30) / 2):g}", "label": "시간 분량"},
        {"value": str(n_files), "label": "종 실습 파일"},
    ]
    facts = "".join(f'<li><strong>{e(s["value"])}</strong><span>{e(s["label"])}</span></li>'
                    for s in stats if str(s.get("value")) not in ("0", ""))
    lines = site["hero_title"] if isinstance(site["hero_title"], (list, tuple)) else [site["hero_title"]]
    hero_lines = "".join(f'<span class="hero-line{" grad-text" if i == len(lines) - 1 and len(lines) > 1 else ""}">{e(x)}</span>'
                         for i, x in enumerate(lines))
    kicker = (f'<p class="hero-kicker"><span class="gdots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>{e(site["hero_kicker"])}</p>'
              if site.get("hero_kicker") else "")
    stage = hero_stage(site, base)
    openings = "".join(opening_card(t, base) for t in tracks if t.get("opening") and video_info(t["opening"].get("video")))
    vid_panels = []
    for t in tracks:
        body, n = video_cards(t, base)
        if n:
            vid_panels.append((t, body, n))
    res_panels = [(t, resources_block(t, base), len(t.get("_files") or [])) for t in tracks]
    faqs = "".join(faq_html(t.get("faq") or [], t) for t in tracks)
    how = [("play", "데모 영상으로 흐름 보기", "실제 화면 녹화 · 한국어 내레이션 · 자막. 단계별 구간을 눌러 필요한 부분만 바로 볼 수 있어요."),
           ("copy", "단계별로 따라 하기", "단계마다 실제 화면 캡처와 강조 표시, 그대로 복사해 붙여 넣을 프롬프트가 준비되어 있어요."),
           ("check", "체크리스트로 마무리", "해낸 항목을 체크하면 진행률이 이 브라우저에 저장되어, 다음에 이어서 할 수 있어요.")]
    how_html = "".join(f'<li class="how-card"><span class="how-ic">{icon(ic, "ic")}</span><span class="how-n">STEP {i + 1}</span>'
                       f'<h3 class="how-t">{e(t_)}</h3><p class="how-d">{e(d)}</p></li>' for i, (ic, t_, d) in enumerate(how))
    opening_sec = f"""
  <section class="section section-alt" id="opening" aria-labelledby="opening-h">
    <div class="container">
      {section_head("Opening", "먼저, 큰 그림부터", "opening-h", "실습을 시작하기 전에 트랙별 오프닝 발표 영상으로 무엇을 만들고 어떻게 일하게 되는지 살펴보세요.", center=True)}
      <div class="opening-grid">{openings}</div>
    </div>
  </section>""" if openings else ""
    videos_sec = f"""
  <section class="section" id="videos" aria-labelledby="videos-h">
    <div class="container">
      {section_head("Demo Videos", "모든 실습을 영상으로 먼저 보세요", "videos-h", "실제 화면 녹화 · 한국어 내레이션 · 자막. 카드를 누르면 해당 실습의 영상으로 바로 이동합니다.")}
      {tabs("videos", "트랙별 데모 영상", vid_panels)}
    </div>
  </section>""" if vid_panels else ""
    cta_btns = "".join(
        f'<a class="btn {"btn-primary" if i == 0 else "btn-secondary"} btn-lg" href="{e(first_href(t, t["id"] + "/"))}" data-resume="{e(t["id"])}" '
        f'data-resume-labs="{resume_attr(t, t["id"] + "/")}"><span>{e(t["title"])}</span><span class="js-resume-l">시작하기</span>'
        f'{icon("arrow", "ic ic-sm ic-arrow-move")}</a>' for i, t in enumerate(tracks))
    main = f"""
<main id="main" tabindex="-1">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-bg" aria-hidden="true"></div>
    {shapes_html()}
    <div class="container hero-in">
      {kicker}
      <h1 class="hero-title" id="hero-title">{hero_lines}</h1>
      <p class="hero-sub">{e(site['hero_sub'])}</p>
      <div class="hero-actions">
        <a class="btn btn-primary btn-lg" href="#tracks"><span>실습 시작하기</span>{icon('arrow', 'ic ic-sm ic-arrow-move')}</a>
        {f'<a class="btn btn-secondary btn-lg" href="#opening">{icon("play", "ic ic-sm ic-fill")}<span>오프닝 영상 보기</span></a>' if openings else
         f'<a class="btn btn-secondary btn-lg" href="#files">{icon("download", "ic ic-sm")}<span>실습 파일 받기</span></a>'}
      </div>
      <ul class="hero-facts" aria-label="한눈에 보기">{facts}</ul>
    </div>
    {stage}
  </section>
  <section class="section" id="tracks" aria-labelledby="tracks-h">
    <div class="container">
      {section_head("Tracks", "두 개의 트랙, 하나의 여정", "tracks-h", "트랙마다 Lab이 순서대로 이어집니다. 처음이라면 Lab 01부터, 진행 중이라면 '이어서 하기'를 누르세요.", center=True)}
      <div class="track-grid">{''.join(home_track_card(t, base) for t in tracks)}</div>
    </div>
  </section>{showcase_section(site, tracks, base)}
  <section class="section" id="how" aria-labelledby="how-h">
    <div class="container">
      {section_head("How it works", "Lab은 이렇게 진행돼요", "how-h", "어느 Lab이든 같은 세 단계로 진행합니다. 막히면 영상의 해당 구간을 다시 보면 됩니다.", center=True)}
      <ol class="how-grid">{how_html}</ol>
    </div>
  </section>{opening_sec}{videos_sec}
  <section class="section section-alt" id="files" aria-labelledby="files-h">
    <div class="container">
      {section_head("Before You Start", "준비물 & 실습 파일", "files-h", "시작 전에 트랙별 준비물을 확인하고, 실습에서 쓸 Cymbal 가상 업무 파일을 한 번에 내려받아 두세요.")}
      {tabs("files", "트랙별 준비물과 실습 파일", res_panels)}
    </div>
  </section>
  <section class="section" id="faq" aria-labelledby="faq-h">
    <div class="container faq-wrap">
      {section_head("FAQ", "자주 묻는 질문", "faq-h", "실습 중에 많이 묻는 질문을 모았습니다. 원하는 답이 없으면 진행자에게 편하게 물어 주세요.")}
      <div class="faq-list">{faqs or '<p class="empty">곧 추가됩니다.</p>'}</div>
    </div>
  </section>
  {next_section(site)}
  <section class="section section-tight" aria-labelledby="cta-h">
    <div class="container">
      <div class="cta-band">
        <h2 id="cta-h">지금 바로 첫 Lab을 시작해 보세요</h2>
        <p>영상으로 흐름을 보고, 프롬프트를 복사해 따라 하고, 체크리스트로 마무리하면 됩니다. 진행 상황은 이 브라우저에 저장됩니다.</p>
        <div class="hero-actions">{cta_btns}</div>
      </div>
    </div>
  </section>
</main>"""
    desc = site.get("description") or site["hero_sub"]
    nav = nav_tree(site, tracks, base)
    return (head(f"{site['title']} · Google Cloud", desc, assets, base, None, "home") + topbar(site, tracks, base, None, "home") + main
            + footer(site, base) + drawer(site, base, nav) + page_end())


def page_404(site: dict, tracks: list, assets: dict) -> str:
    base = "/"
    links = "".join(f'<a class="btn btn-secondary t-{e(t["id"])}" href="/{e(t["id"])}/index.html"><span class="dot" aria-hidden="true"></span>'
                    f'<span>{e(t["title"])}</span></a>' for t in tracks)
    return (head(f"페이지를 찾을 수 없습니다 · {site['title']}", site["hero_sub"], assets, base, None, "404")
            + topbar(site, tracks, base, None, "404") + f"""
<main id="main" class="nf" tabindex="-1">
  <div class="hero-bg" aria-hidden="true"></div>
  {shapes_html(("blue", "yellow", "red", "green"))}
  <div class="container nf-in">
    <p class="nf-code">404</p>
    <h1 class="nf-title">페이지를 찾을 수 없습니다</h1>
    <p class="nf-sub">주소가 바뀌었거나 잘못 입력되었을 수 있어요. 홈에서 다시 시작하거나 검색해 보세요.</p>
    <div class="nf-actions"><a class="btn btn-primary btn-lg" href="/">{icon('home', 'ic ic-sm')}<span>실습 포털 홈으로</span></a>
      <button type="button" class="btn btn-secondary btn-lg" data-cmdk>{icon('search', 'ic ic-sm')}<span>검색</span></button></div>
    <div class="nf-links">{links}</div>
  </div>
</main>""" + footer(site, base) + drawer(site, base, nav_tree(site, tracks, base, home_current=False)) + page_end())


# --------------------------------------------------------------------------- search index
def search_index(site: dict, tracks: list) -> list:
    idx = [{"k": "page", "t": "홈", "s": site["title"], "u": "index.html"},
           {"k": "page", "t": "오프닝 발표", "s": "홈", "u": "index.html#opening"},
           {"k": "page", "t": "준비물 & 실습 파일", "s": "홈", "u": "index.html#files"},
           {"k": "page", "t": "자주 묻는 질문", "s": "홈", "u": "index.html#faq"}]
    for t in tracks:
        tid = t["id"]
        short = t.get("short") or t["title"]
        idx.append({"k": "page", "t": f"{t['title']} 트랙", "s": t["tagline"], "u": f"{tid}/index.html", "tr": tid})
        for lab in t["labs"]:
            u = f"{tid}/{lab['id']}.html"
            idx.append({"k": "lab", "t": f"Lab {lab_no(lab)} · {lab['title']}", "s": f"{short} · {lab.get('subtitle') or ''}".strip(" ·"),
                        "u": u, "tr": tid, "x": plain(lab.get("goal"))[:160]})
            for i, st in enumerate(lab["steps"]):
                n = i + 1
                body = " ".join(plain(b) for b in st.get("body") or [])
                idx.append({"k": "step", "t": st.get("title", ""), "s": f"{short} Lab {lab_no(lab)} · {n}단계", "u": f"{u}#s{n}",
                            "tr": tid, "x": body[:220]})
                if st.get("prompt"):
                    p = str(st["prompt"])
                    idx.append({"k": "prompt", "t": p.split("\n", 1)[0][:90], "s": f"{short} Lab {lab_no(lab)} · {n}단계 프롬프트",
                                "u": f"{u}#s{n}", "tr": tid, "x": p[:400]})
                for c in st["_code"]:
                    idx.append({"k": "code", "t": c["file"] or c["text"].split("\n", 1)[0][:90],
                                "s": f"{short} Lab {lab_no(lab)} · {n}단계 {c['lang']}", "u": f"{u}#s{n}", "tr": tid, "x": c["text"][:300]})
            for m in lab.get("more") or []:
                idx.append({"k": "prompt", "t": str(m).split("\n", 1)[0][:90], "s": f"{short} Lab {lab_no(lab)} · 더 해 보기",
                            "u": f"{u}#more", "tr": tid, "x": str(m)[:400]})
        for f in t.get("faq") or []:
            idx.append({"k": "faq", "t": f["q"], "s": f"{short} · FAQ", "u": f"{tid}/index.html#faq", "tr": tid, "x": plain(f["a"])[:200]})
    return idx


# --------------------------------------------------------------------------- main
def build(fixture: bool, out: Path) -> int:
    global OUT, ASSETS, VIDEO_DIR, _QUIET
    OUT = out.resolve()
    if not inside(OUT, ROOT) or OUT == ROOT or OUT.name in ("site", "production", "deploy", "archive"):
        raise BuildError(f"refusing to write to {OUT} (must be a dedicated directory inside the repo)")
    ASSETS = OUT / "assets"
    VIDEO_DIR = ASSETS / "video"
    content_dir = FIXTURE_DIR if fixture else CONTENT_DIR
    site, tracks = load_content(content_dir)
    print(f"content: {content_dir.relative_to(ROOT)} — " + ", ".join(
        f"{t['id']}: {len(t['labs'])} labs ({sum(1 for l in t['labs'] if ready(l))} ready)" for t in tracks))
    OUT.mkdir(parents=True, exist_ok=True)
    # stale pages from a previous build (labs renamed/removed)
    for t_dir in [p for p in OUT.iterdir() if p.is_dir() and p.name != "assets"]:
        for f in t_dir.glob("*.html"):
            f.unlink()
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    sync_videos(site, tracks)
    collect_files(site, tracks)
    font_css = ensure_fonts()
    copy_brand()
    accent_css(tracks)

    # render pages first (they register generated CSS), then write assets with final hashes
    idx = search_index(site, tracks)
    placeholder = {"portal.css": "assets/css/portal.css", "theme.js": "assets/js/theme.js",
                   "portal.js": "assets/js/portal.js", "search.json": "assets/js/search.json"}
    pages: list[tuple[Path, callable]] = [(OUT / "index.html", lambda a: home_page(site, tracks, a))]
    for t in tracks:
        pages.append((OUT / t["id"] / "index.html", lambda a, t=t: track_page(site, tracks, t, a)))
        for i in range(len(t["labs"])):
            pages.append((OUT / t["id"] / f"{t['labs'][i]['id']}.html", lambda a, t=t, i=i: lab_page(site, tracks, t, i, a)))
    pages.append((OUT / "404.html", lambda a: page_404(site, tracks, a)))
    for _, render in pages:  # dry run: collect GEN_CSS
        render(placeholder)
    gen = list(dict.fromkeys(GEN_CSS))
    GEN_CSS.clear()
    GEN_CSS.extend(gen)
    assets = write_static(font_css, idx)
    _QUIET = True  # second pass repeats the same warnings
    for path, render in pages:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(assets), encoding="utf-8")
    _QUIET = False
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    if fixture:
        (OUT / "FIXTURE_DO_NOT_DEPLOY").write_text("Built from production/content/v2/_fixture — never deploy.\n", encoding="utf-8")
    n_shots = len([v for v in _SHOTS.values() if v])
    css_kb = (ASSETS / "css" / "portal.css").stat().st_size / 1024
    js_kb = (ASSETS / "js" / "portal.js").stat().st_size / 1024
    print(f"wrote {len(pages)} pages → {OUT.relative_to(ROOT)}/ · {n_shots} screenshots · css {css_kb:.0f} KB · js {js_kb:.0f} KB")
    if WARNINGS:
        print(f"{len(WARNINGS)} warning(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", action="store_true", help="build from production/content/v2/_fixture (dev only)")
    ap.add_argument("--out", type=Path, help="output dir (default site_v2/, or site_v2_fixture/ with --fixture)")
    args = ap.parse_args()
    out = args.out or (ROOT / ("site_v2_fixture" if args.fixture else "site_v2"))
    if not out.is_absolute():
        out = Path.cwd() / out
    try:
        return build(args.fixture, out)
    except BuildError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
