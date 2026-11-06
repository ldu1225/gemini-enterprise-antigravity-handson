#!/usr/bin/env python3
"""QA for the v2 portal: serve the built site on 127.0.0.1, screenshot home / track / lab pages at
desktop (1440) · tablet (820) · mobile (390) in light and dark, exercise ⌘K palette, lightbox (+ gallery
navigation), tabs, copy, checklist persistence, theme toggle, scrollspy and per-step chapter seeking; check
console/CSP errors, failed requests, broken images, horizontal overflow, text contrast (WCAG AA), static CSP
hygiene and leftover (unrendered) markdown in the built pages.

    python3 production/site_build_v2/qa.py --fixture     # site_v2_fixture/ → production/site_build_v2/qa/
    python3 production/site_build_v2/qa.py               # site_v2/
"""
from __future__ import annotations

import argparse
import contextlib
import functools
import html as html_lib
import http.server
import json
import os
import re
import socket
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    """Static handler with single 'Range: bytes=' support (progressive MP4 seeking, like production nginx)."""

    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".vtt": "text/vtt", ".webp": "image/webp", ".woff2": "font/woff2", ".mp4": "video/mp4",
                      ".json": "application/json"}
    _remaining: int | None = None

    def log_message(self, format, *args):  # noqa: A002
        pass

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        self._remaining = None
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or os.path.isdir(path):
            return super().send_head()
        m = re.fullmatch(r"\s*bytes=(\d*)-(\d*)\s*", rng)
        try:
            f = open(path, "rb")  # noqa: SIM115
        except OSError:
            self.send_error(404, "File not found")
            return None
        size = os.fstat(f.fileno()).st_size
        if not m or not (m.group(1) or m.group(2)):
            f.close()
            return super().send_head()
        if m.group(1):
            start, end = int(m.group(1)), (int(m.group(2)) if m.group(2) else size - 1)
        else:
            start, end = max(0, size - int(m.group(2))), size - 1
        if start >= size:
            f.close()
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        end = min(end, size - 1)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        f.seek(start)
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        if self._remaining is None:
            with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                super().copyfile(source, outputfile)
            return
        remaining = self._remaining
        while remaining > 0:
            chunk = source.read(min(256 * 1024, remaining))
            if not chunk:
                break
            try:
                outputfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                break
            remaining -= len(chunk)


class QuietServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass


def start_server(site: Path):
    port = free_port()
    server = QuietServer(("127.0.0.1", port), functools.partial(RangeHandler, directory=str(site)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{port}/"


# --------------------------------------------------------------------------- static checks
_MD_PATTERNS = [
    (re.compile(r"\*\*"), "**"),
    (re.compile(r"`"), "backtick"),
    (re.compile(r"(?<![\w*])\*(?![\s*])[^*\n]{1,80}?(?<![\s*])\*(?![\w*])"), "*emphasis*"),
    (re.compile(r"\]\(https?://"), "[link](url)"),
]


def md_leftovers(page_html: str) -> list[str]:
    """Visible text (outside <pre>/<code>/<svg>/<script>) that still carries md syntax, plus numbered
    paragraphs that should have been rendered as an <ol>."""
    t = re.sub(r"<(pre|code|svg|script|style)\b[\s\S]*?</\1>", " ", page_html)
    found = [f"numbered paragraph: {html_lib.unescape(m.group(1))[:60]!r}"
             for m in re.finditer(r"<p>(\d{1,2}[.)]\s[^<]{0,60})", t)]
    t = re.sub(r"<[^>]+>", "\n", t)
    for line in t.split("\n"):
        line = html_lib.unescape(line).strip()
        if not line:
            continue
        for rx, label in _MD_PATTERNS:
            if rx.search(line):
                found.append(f"{label}: {line[:70]!r}")
                break
    return found[:8]


def static_checks(site: Path) -> list[str]:
    problems = []
    for page in sorted(site.rglob("*.html")):
        name = page.relative_to(site).as_posix()
        text = page.read_text(encoding="utf-8")
        if re.search(r"\sstyle\s*=", text):
            problems.append(f"{name}: inline style attribute")
        if re.search(r"<script(?![^>]*\bsrc=)[^>]*>", text):
            problems.append(f"{name}: inline <script>")
        if re.search(r"\son[a-z]+\s*=", text):
            problems.append(f"{name}: inline event handler")
        if re.search(r"<style[\s>]", text):
            problems.append(f"{name}: <style> element")
        if re.search(r"\ssrc=\"(?:https?:)?//", text):
            problems.append(f"{name}: external resource (src)")
        for m in re.finditer(r"<a\s[^>]*href=\"https?://[^\"]*\"[^>]*>", text):
            tag = m.group(0)
            if 'rel="noopener noreferrer"' not in tag or 'target="_blank"' not in tag:
                problems.append(f"{name}: external link without target/rel: {tag[:80]}")
        if re.search(r"href=\"(?:javascript|data):", text, re.I):
            problems.append(f"{name}: javascript:/data: URL")
        problems += [f"{name}: unrendered markdown — {m}" for m in md_leftovers(text)]
    for js in (site / "assets" / "js").glob("*.js"):
        src = js.read_text(encoding="utf-8")
        for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
            if sink in src:
                problems.append(f"{js.name} uses {sink}")
    return problems


# --------------------------------------------------------------------------- in-page probes
LAYOUT_JS = """() => {
  const d = document.documentElement;
  const wide = [];
  if (d.scrollWidth > d.clientWidth + 1) {
    document.querySelectorAll('body *').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width && r.right > d.clientWidth + 1 && !el.closest('.code-pre, .chapter-list, .tab-list, .sprite, dialog')) wide.push((el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ' ' + Math.round(r.right));
    });
  }
  return {page_h: d.scrollHeight, overflow: d.scrollWidth > d.clientWidth + 1, wide: wide.slice(0, 6)};
}"""

CONTRAST_JS = """() => {
  const parse = (c) => { const m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
    const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const blend = (top, bot) => ({r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1});
  const bgOf = (el) => { const stack = []; let n = el;
    while (n && n.nodeType === 1) { const cs = getComputedStyle(n); const c = parse(cs.backgroundColor); if (!c && cs.backgroundColor !== 'transparent') return null; // color-mix()/oklab: not measurable here
      if (cs.backgroundImage && cs.backgroundImage !== 'none' && !n.matches('.hero, .track-hero, .nf')) return null; // gradient/image: skip
      if (c && c.a > 0) { stack.push(c); if (c.a >= 0.99) break; } n = n.parentElement; }
    let base = {r: 255, g: 255, b: 255, a: 1};
    if (!stack.length || stack[stack.length - 1].a < 0.99) { const rb = parse(getComputedStyle(document.body).backgroundColor); if (rb) base = rb; }
    for (let i = stack.length - 1; i >= 0; i--) base = blend(stack[i], base.a ? base : base);
    return base; };
  const out = []; let checked = 0;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode; if (!t.textContent.trim()) continue;
    const el = t.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
    if (el.closest('.sprite, .sr-only, dialog:not([open]), .video-frame, .fig-stage, [hidden], .skip-link, .co-tag, script')) continue;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || Number(cs.opacity) < 0.5) continue;
    if (cs.webkitBackgroundClip === 'text' || cs.backgroundClip === 'text' || cs.color === 'rgba(0, 0, 0, 0)') continue;
    if (el.closest('.check:has(input:checked)')) continue; // completed (struck-through) items are intentionally muted
    const fg = parse(cs.color); const bg = bgOf(el); if (!fg && cs.color) continue; if (!fg || !bg) continue;
    const f = fg.a < 1 ? blend(fg, bg) : fg;
    const L1 = lum(f), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = Number(cs.fontWeight) >= 700;
    const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5; checked++;
    if (ratio + 0.05 < need) out.push({text: t.textContent.trim().slice(0, 40), cls: String(el.className || el.tagName).slice(0, 40), ratio: Math.round(ratio * 100) / 100, need});
  }
  return {checked, fails: out.slice(0, 25), n_fail: out.length};
}"""


def settle(page) -> None:
    page.evaluate("document.fonts.ready.then(() => true)")
    page.wait_for_timeout(250)


def scroll_through(page) -> None:
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(80)
        y += 800
        h = page.evaluate("document.documentElement.scrollHeight")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(250)


def pick_pages(site: Path) -> dict:
    """home, a track page, a GE lab with chapters + callouts, an AG lab with code blocks."""
    pages = {"home": "index.html"}
    tracks = sorted(p.name for p in site.iterdir() if p.is_dir() and (p / "index.html").is_file() and p.name != "assets")
    if tracks:
        pages["track"] = f"{tracks[0]}/index.html"
    best = None
    for t in tracks:
        for f in sorted((site / t).glob("*.html")):
            if f.name == "index.html":
                continue
            txt = f.read_text(encoding="utf-8")
            score = txt.count('class="step-play"') * 3 + txt.count('class="co ') + (5 if 'class="chapters"' in txt else 0)
            if best is None or score > best[0]:
                best = (score, f"{t}/{f.name}")
            if 'class="code' in txt and "code_lab" not in pages:
                pages["code_lab"] = f"{t}/{f.name}"
    if best:
        pages["lab"] = best[1]
    return pages


# --------------------------------------------------------------------------- callout geometry (hard gate)
# Every highlight box must land exactly where the content coordinates say (capture CSS px → rendered image px),
# its label chip must be fully visible inside the screenshot, and a chip must not cover another highlighted target.
CALLOUT_JS = """(scope) => {
  const out = [];
  const root = scope ? document.querySelector(scope) : document;
  if (!root) return out;
  root.querySelectorAll('.co[data-box]').forEach((co) => {
    const stage = co.closest('.fig-stage, .lb-stage');
    const img = stage && stage.querySelector('img');
    if (!img) { out.push({err: 'callout outside a screenshot stage'}); return; }
    const [x, y, w, h] = co.dataset.box.split(',').map(Number);
    const [cw, ch] = co.dataset.cap.split('x').map(Number);
    const ir = img.getBoundingClientRect(), r = co.getBoundingClientRect(), sr = stage.getBoundingClientRect();
    const sx = ir.width / cw, sy = ir.height / ch;
    const exp = {l: ir.left + x * sx, t: ir.top + y * sy, w: w * sx, h: h * sy};
    const d = Math.max(Math.abs(r.left - exp.l), Math.abs(r.top - exp.t), Math.abs(r.width - exp.w), Math.abs(r.height - exp.h));
    const ar = img.naturalWidth && img.naturalHeight ? Math.abs((img.naturalWidth / img.naturalHeight) - (ir.width / ir.height)) : 0;
    const tag = co.querySelector('.co-tag');
    let clipped = false, covers = [];
    if (tag) {
      const tr = tag.getBoundingClientRect();
      clipped = tr.left < sr.left - 1 || tr.top < sr.top - 1 || tr.right > sr.right + 1 || tr.bottom > sr.bottom + 1;
      stage.querySelectorAll('.co[data-box]').forEach((o) => {
        if (o === co) return;
        const orr = o.getBoundingClientRect();
        const ix = Math.max(0, Math.min(tr.right, orr.right) - Math.max(tr.left, orr.left));
        const iy = Math.max(0, Math.min(tr.bottom, orr.bottom) - Math.max(tr.top, orr.top));
        if (orr.width * orr.height > 0 && (ix * iy) / (orr.width * orr.height) > 0.25) covers.push((o.querySelector('.co-tag') || {}).textContent || '?');
      });
    }
    const fig = co.closest('.fig');
    const src = (img.currentSrc || img.src || '').split('/').pop().split('?')[0];
    out.push({label: tag ? tag.textContent : '', img: src, step: (co.closest('.step') || {}).id || 'lightbox',
              delta: Math.round(d * 10) / 10, ar_skew: Math.round(ar * 1000) / 1000, clipped, covers,
              shown: r.width > 0 && r.height > 0 && ir.width > 0});
  });
  return out;
}"""


def callout_geometry_checks(browser, base: str, site: Path, out: Path, report: dict) -> None:
    """Hard gate: all lab pages × (desktop, mobile) × (inline, lightbox for every figure with callouts)."""
    res: dict = {"checked": 0, "failures": [], "warnings": []}
    report["callouts"] = res
    lab_pages = [p_.relative_to(site).as_posix() for t in sorted(site.iterdir()) if t.is_dir() and t.name != "assets"
                 for p_ in sorted(t.glob("*.html")) if p_.name != "index.html" and 'class="co ' in p_.read_text(encoding="utf-8")]
    for vname, vp, dsf in (("desktop", {"width": 1440, "height": 900}, 1), ("mobile", {"width": 390, "height": 844}, 2)):
        ctx = browser.new_context(viewport=vp, device_scale_factor=dsf, reduced_motion="reduce")
        page = ctx.new_page()
        for path in lab_pages:
            page.goto(base + path, wait_until="networkidle")
            settle(page)
            scroll_through(page)  # load every lazy image so its rendered size is final
            page.wait_for_function("() => Array.from(document.querySelectorAll('.fig-stage img')).every(i => i.complete)", timeout=20000)
            rows = page.evaluate(CALLOUT_JS, None)
            for r in rows:
                res["checked"] += 1
                where = f"[{vname}] {path} {r.get('step')} {r.get('img')} «{r.get('label')}»"
                if r.get("err"):
                    res["failures"].append(f"{where}: {r['err']}")
                elif not r["shown"]:
                    res["failures"].append(f"{where}: not rendered")
                elif r["delta"] > 1.5:
                    res["failures"].append(f"{where}: box is {r['delta']}px away from its content coordinates")
                elif r["ar_skew"] > 0.01:
                    res["failures"].append(f"{where}: screenshot is stretched (aspect skew {r['ar_skew']})")
                if r.get("clipped"):
                    res["failures"].append(f"{where}: label chip is cut off by the screenshot edge")
                if r.get("covers"):
                    res["warnings"].append(f"{where}: label chip covers {r['covers']}")
            if vname != "desktop":
                continue
            n = page.locator(".fig-link:has(.co)").count()
            for i in range(n):
                link = page.locator(".fig-link:has(.co)").nth(i)
                link.scroll_into_view_if_needed()
                link.click()
                page.wait_for_function("() => { const i = document.querySelector('#lightbox .lb-img'); return document.getElementById('lightbox').open && i && i.complete && i.naturalWidth > 0; }", timeout=15000)
                page.wait_for_timeout(120)
                for r in page.evaluate(CALLOUT_JS, "#lightbox"):
                    res["checked"] += 1
                    where = f"[lightbox] {path} fig{i + 1} {r.get('img')} «{r.get('label')}»"
                    if r.get("err") or not r.get("shown") or r.get("delta", 99) > 1.5:
                        res["failures"].append(f"{where}: {r.get('err') or ('off by ' + str(r.get('delta')) + 'px')}")
                    if r.get("clipped"):
                        res["failures"].append(f"{where}: label chip is cut off by the screenshot edge")
                page.keyboard.press("Escape")
                page.wait_for_timeout(120)
        ctx.close()


# --------------------------------------------------------------------------- media (chapters)
H264 = 'video/mp4; codecs="avc1.640028, mp4a.40.2"'


def media_browser(p, res: dict):
    """Playwright's Chromium has no H.264 → use WebKit (AVFoundation on macOS) or a headless Google Chrome."""
    for name, launch in (("webkit", lambda: p.webkit.launch()), ("chrome", lambda: p.chromium.launch(channel="chrome"))):
        try:
            browser = launch()
        except Exception as exc:
            res.setdefault("engine_errors", []).append(f"{name}: {str(exc)[:160]}")
            continue
        page = browser.new_page()
        if page.evaluate("(t) => document.createElement('video').canPlayType(t)", H264):
            res["engine"] = name
            page.close()
            return browser
        browser.close()
    return None


def media_checks(p, base: str, site: Path, lab_pages: list[str], out: Path, report: dict) -> None:
    res: dict = {"labs": {}, "failures": []}
    report["chapters"] = res
    browser = media_browser(p, res)
    if not browser:
        res["failures"].append("no H.264-capable engine available for media checks")
        return
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    page = ctx.new_page()
    page.on("pageerror", lambda exc: report["console"].append(f"[media] pageerror: {exc}"))
    tested_toggle = False
    for path in lab_pages:
        page.goto(base + path, wait_until="networkidle")
        info = page.evaluate("""() => { const a = document.querySelector('article[data-lab-section]'); if (!a) return null;
            const src = a.querySelector('video[data-lab] source');
            return {id: a.dataset.labSection, video: src ? src.getAttribute('src').split('?')[0].split('/').pop().replace(/\\.mp4$/, '') : null,
                    steps: a.querySelectorAll('.steps > .step').length, stepButtons: a.querySelectorAll('.step-play').length,
                    listButtons: a.querySelectorAll('.chapter').length}; }""")
        if not info:
            continue
        lid = info["id"]
        res["labs"][path] = info
        cj = site / "assets" / "video" / f"{info['video']}.chapters.json" if info["video"] else None
        if not (cj and cj.is_file()):
            if info["stepButtons"] or info["listButtons"]:
                res["failures"].append(f"{path}: chapter buttons without a chapters file")
            continue
        chapters = json.loads(cj.read_text(encoding="utf-8")).get("chapters", [])
        covered = {int(c["step"]) for c in chapters if int(c["step"]) <= info["steps"]}
        info["count_ok"] = info["stepButtons"] == len(covered)
        if not info["count_ok"]:
            res["failures"].append(f"{path}: {info['stepButtons']} step buttons for {len(covered)} chaptered steps")
        vid = f"v-{lid}"
        page.evaluate("(id) => { const v = document.getElementById(id); v.muted = true; v.pause(); }", vid)

        def seek_check(locator, label: str) -> dict:
            start = float(locator.get_attribute("data-seek"))
            step = int(locator.get_attribute("data-step"))
            locator.click()
            o = {"start": start, "step": step}
            try:
                page.wait_for_function("""([id, s]) => { const v = document.getElementById(id);
                    return v.readyState >= 1 && !v.seeking && Math.abs(v.currentTime - s) <= 0.5; }""", arg=[vid, start], timeout=10000)
                o["ok"] = True
            except Exception:
                o["ok"] = False
            state = page.evaluate("""(id) => { const v = document.getElementById(id); v.pause();
                const chip = document.querySelector('[data-vchip]');
                const cur = document.querySelector('.steps > .step[aria-current="step"]');
                return {t: v.currentTime, chip: chip && !chip.hidden ? chip.textContent : null, current: cur ? cur.id : null}; }""", vid)
            o.update(state)
            o["chip_ok"] = bool(state["chip"]) and state["chip"].startswith(f"STEP {step}")
            o["current_ok"] = state["current"] == f"s{step}"
            if not (o["ok"] and o["chip_ok"] and o["current_ok"]):
                res["failures"].append(f"{path} {label}: {o}")
            return o

        n = page.locator(".chapter").count()
        info["list_seek"] = seek_check(page.locator(".chapter").nth(min(1, n - 1)), "chapter-chip")
        last = page.locator(".step-play").last
        last.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        info["step_seek"] = seek_check(last, "step-button")
        page.wait_for_timeout(900)
        info["step_seek"]["inView_after"] = page.evaluate(
            "(id) => { const r = document.getElementById(id).closest('.video-frame').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; }", vid)
        if not info["step_seek"]["inView_after"]:
            res["failures"].append(f"{path}: video not revealed after step-button click")
        if not tested_toggle:
            tested_toggle = True
            page.screenshot(path=str(out / "desktop_chapters.png"))
            report["shots"].append(str(out / "desktop_chapters.png"))
            page.locator(".switch").first.click()
            durs = page.evaluate("() => Array.from(document.querySelectorAll('.chapter')).map(b => Number(b.dataset.end) - Number(b.dataset.seek))")
            k = min(range(len(durs)), key=lambda i: durs[i])
            btn = page.locator(".chapter").nth(k)
            end = float(btn.get_attribute("data-end"))
            btn.click()
            page.evaluate("(id) => { document.getElementById(id).playbackRate = 4; }", vid)
            with contextlib.suppress(Exception):
                page.wait_for_function("(id) => document.getElementById(id).paused", arg=vid, timeout=int((durs[k] / 4 + 6) * 1000))
            t = page.evaluate("(id) => document.getElementById(id).currentTime", vid)
            res["step_only"] = {"lab": path, "end": end, "t": round(t, 3), "ok": abs(t - end) <= 0.6}
            if not res["step_only"]["ok"]:
                res["failures"].append(f"step-only auto-pause: {res['step_only']}")
            page.locator(".switch").first.click()
            page.evaluate("(id) => { const v = document.getElementById(id); v.playbackRate = 1; }", vid)
            page.evaluate("""() => { const li = document.querySelector('.steps > .step[aria-current="step"]');
                if (li) window.scrollTo(0, li.getBoundingClientRect().top + window.scrollY - 120); }""")
            page.wait_for_timeout(500)
            page.screenshot(path=str(out / "desktop_step_playing.png"))
            report["shots"].append(str(out / "desktop_step_playing.png"))
        page.evaluate("(id) => document.getElementById(id).pause()", vid)
    ctx.close()
    browser.close()


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", action="store_true")
    ap.add_argument("--site", type=Path)
    ap.add_argument("--out", type=Path, default=HERE / "qa")
    ap.add_argument("--no-media", action="store_true")
    ap.add_argument("--callouts-only", action="store_true", help="only the callout geometry gate (fast)")
    args = ap.parse_args()
    site = (args.site or ROOT / ("site_v2_fixture" if args.fixture else "site_v2")).resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.callouts_only:
        report = {"site": str(site)}
        server, base = start_server(site)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                callout_geometry_checks(browser, base, site, out, report)
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
        res = report["callouts"]
        print(json.dumps({"checked": res["checked"], "failures": res["failures"], "warnings": res["warnings"]}, ensure_ascii=False, indent=1))
        return 1 if res["failures"] else 0
    for old in out.glob("*.png"):
        old.unlink()
    pages = pick_pages(site)
    report = {"site": str(site), "pages": pages, "shots": [], "console": [], "failed_requests": [], "broken_images": [],
              "problems": static_checks(site), "layout": {}, "contrast": {}, "interactions": {}}
    server, base = start_server(site)

    def shot(page, name: str, full: bool = False):
        path = out / f"{name}.png"
        page.screenshot(path=str(path), full_page=full)
        report["shots"].append(str(path))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            configs = [("desktop", {"width": 1440, "height": 900}, 1), ("tablet", {"width": 820, "height": 1180}, 1),
                       ("mobile", {"width": 390, "height": 844}, 2)]
            for name, vp, dsf in configs:
                for scheme in ("light", "dark"):
                    if name == "tablet" and scheme == "dark":
                        continue
                    tag = f"{name}_{scheme}"
                    touch = name != "desktop"
                    ctx = browser.new_context(viewport=vp, device_scale_factor=dsf, reduced_motion="reduce", color_scheme=scheme,
                                              is_mobile=touch, has_touch=touch)
                    page = ctx.new_page()
                    page.on("console", lambda m, n=tag: report["console"].append(f"[{n}] {m.type}: {m.text}") if m.type in ("error", "warning") else None)
                    page.on("pageerror", lambda exc, n=tag: report["console"].append(f"[{n}] pageerror: {exc}"))
                    page.on("response", lambda r, n=tag: report["failed_requests"].append(f"[{n}] {r.status} {r.url.replace(base, '/')}") if r.status >= 400 else None)
                    for key, path in pages.items():
                        page.goto(base + path, wait_until="networkidle")
                        settle(page)
                        scroll_through(page)
                        report["layout"][f"{tag}:{key}"] = page.evaluate(LAYOUT_JS)
                        report["broken_images"] += [f"[{tag}] {b}" for b in page.evaluate(
                            "() => Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0 && i.getAttribute('src')).map(i => i.getAttribute('src'))")]
                        if name != "tablet":
                            report["contrast"][f"{tag}:{key}"] = page.evaluate(CONTRAST_JS)
                        shot(page, f"{tag}_{key}")
                        if key == "home" and scheme == "light" and name != "tablet":
                            shot(page, f"{tag}_home_full", full=True)
                        if key == "lab":
                            page.evaluate("() => { const s = document.querySelector('#s2') || document.querySelector('.step'); if (s) s.scrollIntoView({block: 'start'}); }")
                            page.wait_for_timeout(300)
                            shot(page, f"{tag}_lab_step")
                            if name == "desktop" and scheme == "light":
                                shot(page, f"{tag}_lab_full", full=True)
                        if key == "code_lab":
                            page.evaluate("() => { const c = document.querySelectorAll('.code')[1] || document.querySelector('.code'); if (c) c.scrollIntoView({block: 'center'}); }")
                            page.wait_for_timeout(300)
                            shot(page, f"{tag}_code")
                        if key == "home" and name == "desktop":
                            page.evaluate("() => document.getElementById('files').scrollIntoView({block: 'start'})")
                            page.wait_for_timeout(300)
                            shot(page, f"{tag}_home_files")
                    if name == "mobile" and "lab" in pages:
                        page.goto(base + pages["lab"], wait_until="networkidle")
                        settle(page)
                        page.locator(".mbar-btn").click()
                        page.wait_for_timeout(400)
                        shot(page, f"{tag}_drawer")
                        report["interactions"][f"{tag}_drawer_open"] = page.evaluate("document.getElementById('drawer').open")
                        page.keyboard.press("Escape")
                    ctx.close()

            # ---------------- interactions (desktop, light, motion on)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="light")
            ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=base.rstrip("/"))
            page = ctx.new_page()
            page.on("console", lambda m: report["console"].append(f"[interact] {m.type}: {m.text}") if m.type in ("error", "warning") else None)
            page.on("pageerror", lambda exc: report["console"].append(f"[interact] pageerror: {exc}"))
            it = report["interactions"]
            lab = pages.get("lab")
            page.goto(base + lab, wait_until="networkidle")
            settle(page)
            # ⌘K palette
            page.keyboard.press("Meta+k")
            page.wait_for_timeout(300)
            it["cmdk_open_kbd"] = page.evaluate("document.getElementById('cmdk').open")
            if not it["cmdk_open_kbd"]:
                page.keyboard.press("Control+k")
                page.wait_for_timeout(300)
                it["cmdk_open_kbd"] = page.evaluate("document.getElementById('cmdk').open")
            page.wait_for_selector(".cmdk-o", timeout=5000)
            shot(page, "desktop_light_cmdk_empty")
            page.keyboard.type("에이전트")
            page.wait_for_timeout(300)
            it["cmdk_results"] = page.locator(".cmdk-o").count()
            page.keyboard.press("ArrowDown")
            page.keyboard.press("ArrowDown")
            it["cmdk_active"] = page.evaluate("document.getElementById('cmdk-q').getAttribute('aria-activedescendant')")
            shot(page, "desktop_light_cmdk")
            target = page.evaluate("document.getElementById(document.getElementById('cmdk-q').getAttribute('aria-activedescendant')).href")
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(400)
            it["cmdk_navigated"] = page.url == target
            # dark palette screenshot
            page.goto(base + "index.html", wait_until="networkidle")
            page.locator("[data-theme-toggle]").first.click()
            page.wait_for_timeout(200)
            it["theme_pinned"] = page.evaluate("document.documentElement.dataset.theme || ''")
            page.reload(wait_until="networkidle")
            it["theme_persisted"] = page.evaluate("document.documentElement.dataset.theme || ''")
            it["theme_meta"] = page.evaluate("document.querySelector('meta[name=color-scheme]').content")
            page.locator(".topbar [data-cmdk]").click()
            page.wait_for_selector(".cmdk-o", timeout=5000)
            page.keyboard.type("프롬프트")
            page.wait_for_timeout(300)
            shot(page, "desktop_dark_cmdk")
            page.keyboard.press("Escape")
            page.locator("[data-theme-toggle]").first.click()  # back to system (light)
            page.wait_for_timeout(200)
            it["theme_reset"] = page.evaluate("document.documentElement.dataset.theme || 'system'")
            # home tabs (demo videos): the second tab shows its panel and hides the first one
            tabs = page.locator("#videos [role=tab]")
            if tabs.count() > 1:
                tabs.nth(1).click()
                page.wait_for_timeout(200)
                it["tabs_switch"] = page.evaluate("""() => { const t = document.querySelectorAll('#videos [role=tab]');
                    const p0 = document.getElementById(t[0].getAttribute('aria-controls'));
                    const p1 = document.getElementById(t[1].getAttribute('aria-controls'));
                    return t[1].getAttribute('aria-selected') === 'true' && !p1.hidden && Boolean(p0.hidden); }""")
                tabs.nth(1).focus()
                page.keyboard.press("ArrowLeft")
                it["tabs_keyboard"] = page.evaluate("document.querySelectorAll('#videos [role=tab]')[0].getAttribute('aria-selected')") == "true"
            # lightbox + copy + checklist on the lab page
            page.goto(base + lab, wait_until="networkidle")
            settle(page)
            page.locator(".prompt").first.scroll_into_view_if_needed()
            page.locator(".prompt .copy-btn").first.click()
            page.wait_for_timeout(300)
            it["copy_label"] = page.locator(".prompt .copy-btn .copy-label").first.text_content()
            it["clipboard_head"] = page.evaluate("navigator.clipboard.readText()")[:40]
            link = page.locator(".fig-link:has(.co)").first
            if not link.count():
                link = page.locator(".fig-link").first
            if link.count():  # a build without stills (e.g. a fresh clone) has no figures → skip these checks
                link.scroll_into_view_if_needed()
                link.click()
                page.wait_for_timeout(500)
                it["lightbox_open"] = page.evaluate("document.getElementById('lightbox').open")
                it["lightbox_callouts"] = page.locator("#lightbox .co").count()
                shot(page, "desktop_light_lightbox")
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            else:
                it["lightbox_open"] = "skipped: no screenshots in this build"
            gallery = page.locator(".figs:has(.fig + .fig) .fig-link").first
            if gallery.count():
                gallery.scroll_into_view_if_needed()
                gallery.click()
                page.wait_for_timeout(400)
                before = page.evaluate("document.querySelector('#lightbox .lb-img').getAttribute('src')")
                page.keyboard.press("ArrowRight")
                page.wait_for_timeout(300)
                it["lightbox_next"] = page.evaluate("document.querySelector('#lightbox .lb-img').getAttribute('src')") != before
                it["lightbox_count"] = page.locator("#lightbox [data-lb-count]").text_content()
                shot(page, "desktop_light_lightbox_gallery")
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            it["lightbox_closed"] = not page.evaluate("document.getElementById('lightbox').open")
            first_chk = page.locator(".checklist .check").first
            first_chk.scroll_into_view_if_needed()
            first_chk.click()
            page.wait_for_timeout(200)
            page.reload(wait_until="networkidle")
            it["checklist_persisted"] = page.evaluate("document.querySelector('.checklist input[data-check]').checked")
            it["checklist_pct"] = page.locator(".checklist .js-pct").text_content()
            it["side_progress"] = page.locator(".sidebar .nav-progress .js-count").text_content()
            it["side_ring_started"] = page.evaluate("document.querySelector('.sidebar .nav-lab[aria-current=page]').classList.contains('is-started')")
            page.goto(base + "index.html", wait_until="networkidle")
            it["home_resume_label"] = page.locator(".track-card .js-resume-l").first.text_content()
            it["home_resume_href"] = page.locator(".track-card [data-resume]").first.get_attribute("href")
            page.goto(base + lab, wait_until="networkidle")
            page.locator(".checklist .check").first.click()  # reset
            page.evaluate("document.getElementById('s3') && document.getElementById('s3').scrollIntoView()")
            page.wait_for_timeout(900)
            it["toc_current"] = page.evaluate("(document.querySelector('.sidebar .nav-step[aria-current]') || document.querySelector('.sidebar .nav-step.is-current') || {}).textContent || ''")[:30]
            page.evaluate("localStorage.clear()")
            ctx.close()
            callout_geometry_checks(browser, base, site, out, report)
            browser.close()
            if not args.no_media:
                lab_pages = [p_.relative_to(site).as_posix() for t in site.iterdir() if t.is_dir() and t.name != "assets"
                             for p_ in sorted(t.glob("*.html")) if p_.name != "index.html" and 'class="chapters"' in p_.read_text(encoding="utf-8")]
                media_checks(p, base, site, lab_pages, out, report)
    finally:
        server.shutdown()
        server.server_close()

    overflow = [k for k, v in report["layout"].items() if v.get("overflow")]
    contrast_fail = {k: v for k, v in report["contrast"].items() if v.get("n_fail")}
    co = report.get("callouts") or {}
    report["summary"] = {
        "static_problems": len(report["problems"]), "console": len(report["console"]), "failed_requests": len(report["failed_requests"]),
        "broken_images": len(report["broken_images"]), "overflow_pages": overflow,
        "contrast_failures": {k: v["n_fail"] for k, v in contrast_fail.items()},
        "chapter_failures": len((report.get("chapters") or {}).get("failures") or []), "shots": len(report["shots"]),
        "callouts_checked": co.get("checked", 0), "callout_failures": len(co.get("failures") or []),
    }
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("shots", "layout", "contrast")}, ensure_ascii=False, indent=1))
    print("contrast fails:", json.dumps({k: v["fails"][:6] for k, v in contrast_fail.items()}, ensure_ascii=False, indent=1))
    bad = (report["problems"] or report["broken_images"] or overflow or report["failed_requests"]
           or any("error" in c or "pageerror" in c for c in report["console"]) or report["summary"]["chapter_failures"]
           or report["summary"]["callout_failures"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
