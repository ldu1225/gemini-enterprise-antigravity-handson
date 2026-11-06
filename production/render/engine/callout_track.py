"""Highlight-box (callout) tracking and verification.

Why: a callout box used to be resolved once (element rect at the click/event time) and then drawn unchanged for
its whole display window. When the page scrolled, a panel opened, a menu covered the target, or the narration
anchor moved the callout away from the event moment, the ring no longer matched the area the viewer should look
at — it overflowed or drifted off the target.

What this does, per callout, on the actual source frames that will be shown:
  1. Reference patch = the target region (unpadded box) on the source frame at the callout's anchor time.
  2. For every output frame in the callout window, template-match that patch in a search window around the
     original position (normalized cross-correlation on a grayscale, 2x-downscaled image).
       - strong match elsewhere  -> the target moved (scroll / layout shift): follow it (dx, dy)
       - weak match, but the original spot still looks like the patch -> content changed in place (typing,
         hover state): keep the box where it is
       - weak everywhere -> the target is covered or gone (menu, page change): hide the ring (fade out)
  3. Offsets are median-smoothed; visibility uses hysteresis + minimum run length so the ring never flickers.
  4. A report entry per callout (min/median score, max drift, visible fraction, out-of-frame) feeds the
     callout QA sheet (render.py --callout-qa) and fails the render on hard problems (render.py --strict-callouts).
"""
from __future__ import annotations

import cv2
import numpy as np

DS = 2                 # downscale factor for matching (speed; recordings are 2x DPR)
SEARCH = 220           # search margin around the original box, source px
FOLLOW_MIN = 0.80      # NCC score that counts as "found the target" (follow it)
STAY_MIN = 0.45        # NCC at the original spot that still counts as "same element, content changed"
HIDE_RUN = 4           # frames of "lost" needed before hiding (hysteresis)
MIN_VAR = 30.0         # template gray variance below this = featureless; don't track, just verify

_GRAY: dict = {}


def _gray(path: str, size) -> np.ndarray:
    g = _GRAY.get(path)
    if g is None:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise IOError(f"cannot read frame {path}")
        if (img.shape[1], img.shape[0]) != tuple(size):
            img = cv2.resize(img, tuple(size), interpolation=cv2.INTER_AREA)
        g = cv2.resize(img, (img.shape[1] // DS, img.shape[0] // DS), interpolation=cv2.INTER_AREA)
        if len(_GRAY) > 400:
            _GRAY.clear()
        _GRAY[path] = g
    return g


def _clip_box(b, sw, sh):
    x, y, w, h = b
    x0, y0 = max(0.0, x), max(0.0, y)
    x1, y1 = min(float(sw), x + w), min(float(sh), y + h)
    return [x0, y0, max(0.0, x1 - x0), max(0.0, y1 - y0)]


def _cursor_mask(tpl_shape, tpl_x, tpl_y, cursor, scale):
    """uint8 mask (1 = use pixel) that removes the injected demo cursor (capture/ge.py install_cursor: 28x28 CSS px
    arrow + drop shadow, tip at the mouse point) from a template whose top-left is (tpl_x, tpl_y) in DS space."""
    th, tw = tpl_shape
    mask = np.ones((th, tw), np.uint8)
    if cursor is None:
        return mask, False
    cx, cy = cursor[0] / DS, cursor[1] / DS
    s = scale / DS
    x0, y0 = int(np.floor(cx - 7 * s)) - tpl_x, int(np.floor(cy - 5 * s)) - tpl_y
    x1, y1 = int(np.ceil(cx + 27 * s)) - tpl_x, int(np.ceil(cy + 31 * s)) - tpl_y
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(tw, x1), min(th, y1)
    if x1 <= x0 or y1 <= y0:
        return mask, False
    mask[y0:y1, x0:x1] = 0
    return mask, True


def track(box_raw, ref_file: str, files: list[str], fidx: np.ndarray, f0: int, f1: int, size,
          cursor=None, cursor_scale: float = 1.0) -> dict:
    """box_raw: unpadded target box (source px) at the anchor frame. Returns per-frame offsets/visibility
    for output frames f0..f1 (inclusive) plus summary stats.
    cursor: demo-cursor tip (source px) at the anchor frame, if known (click/hover events) — masked out of the
    template so the ring cannot lock onto the moving cursor."""
    sw, sh = size
    n = max(0, f1 - f0 + 1)
    out = {"dx": np.zeros(n, np.float32), "dy": np.zeros(n, np.float32), "vis": np.ones(n, bool),
           "score": np.ones(n, np.float32), "mode": "static", "notes": []}
    b = _clip_box(box_raw, sw, sh)
    if n == 0 or b[2] < 6 or b[3] < 6:
        out["notes"].append("box too small or outside frame")
        return out
    ref = _gray(ref_file, size)
    x, y, w, h = (int(round(v / DS)) for v in b)
    w, h = max(3, w), max(3, h)
    tpl = ref[y:y + h, x:x + w]
    if tpl.size == 0:
        out["notes"].append("empty template")
        return out
    # very large targets (whole panels): match a centred core so local changes inside don't break tracking
    max_side = 260 // DS * 2
    if w > max_side or h > max_side:
        cw, ch = min(w, max_side), min(h, max_side)
        cx0, cy0 = x + (w - cw) // 2, y + (h - ch) // 2
        tpl = ref[cy0:cy0 + ch, cx0:cx0 + cw]
        offx, offy = cx0 - x, cy0 - y
    else:
        offx, offy = 0, 0
    th, tw = tpl.shape
    mask, masked = _cursor_mask((th, tw), x + offx, y + offy, cursor, cursor_scale)
    if masked:
        out["notes"].append("demo cursor masked out of the template")
        if mask.mean() < 0.35:
            # the cursor covers most of a small target (typical for the button being clicked): nothing reliable to
            # match against -> static ring at the measured event box (the box is exact at the event moment)
            out["notes"].append("cursor covers the target: static ring (not tracked)")
            return out
    featureless_forced = False
    use = tpl[mask > 0] if masked and mask.any() else tpl
    featureless = featureless_forced or float(use.var()) < MIN_VAR
    m = SEARCH // DS
    raw_dx = np.zeros(n, np.float32)
    raw_dy = np.zeros(n, np.float32)
    lost = np.zeros(n, bool)
    cache: dict[int, tuple] = {}
    for k in range(n):
        fi = int(fidx[f0 + k])
        if fi not in cache:
            img = _gray(files[fi], size)
            ox, oy = x + offx, y + offy
            sx0, sy0 = max(0, ox - m), max(0, oy - m)
            sx1, sy1 = min(img.shape[1], ox + tw + m), min(img.shape[0], oy + th + m)
            win = img[sy0:sy1, sx0:sx1]
            if win.shape[0] < th or win.shape[1] < tw:
                cache[fi] = (0.0, 0.0, 0.0, 0.0)
            else:
                if masked and not featureless_forced:
                    res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED, mask=mask)
                    res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
                else:
                    res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
                _, best, _, loc = cv2.minMaxLoc(res)
                here_x, here_y = ox - sx0, oy - sy0
                here = float(res[here_y, here_x]) if 0 <= here_y < res.shape[0] and 0 <= here_x < res.shape[1] else 0.0
                cache[fi] = (float(best), float((loc[0] - here_x) * DS), float((loc[1] - here_y) * DS), here)
        best, ddx, ddy, here = cache[fi]
        if featureless:
            # nothing to lock onto (flat area): only check the area did not change completely
            lost[k] = here < 0.2 and best < 0.5
            out["score"][k] = max(here, 0.0)
            continue
        # follow only axis-aligned moves (page scroll / panel shift); a diagonal "move" is almost always the
        # demo cursor or an unrelated look-alike, not the target itself
        axis = abs(ddx) <= 4 or abs(ddy) <= 4
        if best >= FOLLOW_MIN and (abs(ddx) > 3 or abs(ddy) > 3) and best - here > 0.06 and axis:
            raw_dx[k], raw_dy[k] = ddx, ddy           # moved: follow
            out["score"][k] = best
        elif here >= STAY_MIN:
            out["score"][k] = here                    # same place (content may have changed in place)
        else:
            lost[k] = True
            out["score"][k] = max(best, here)
    # smooth offsets (median over 5 frames), hold last good offset through lost frames
    for arr in (raw_dx, raw_dy):
        last = 0.0
        for k in range(n):
            if lost[k]:
                arr[k] = last
            else:
                last = arr[k]
    if n >= 5:
        pad_dx = np.pad(raw_dx, 2, mode="edge")
        pad_dy = np.pad(raw_dy, 2, mode="edge")
        out["dx"] = np.array([np.median(pad_dx[k:k + 5]) for k in range(n)], np.float32)
        out["dy"] = np.array([np.median(pad_dy[k:k + 5]) for k in range(n)], np.float32)
    else:
        out["dx"], out["dy"] = raw_dx, raw_dy
    # visibility with hysteresis: hide only after HIDE_RUN consecutive lost frames; never re-show briefly
    vis = np.ones(n, bool)
    run = 0
    for k in range(n):
        run = run + 1 if lost[k] else 0
        if run >= HIDE_RUN:
            vis[k - run + 1:k + 1] = False
    # drop visible islands shorter than 0.4 s after a hide (avoid blink)
    k = 0
    while k < n:
        if vis[k]:
            j = k
            while j < n and vis[j]:
                j += 1
            if k > 0 and (j - k) < 12:
                vis[k:j] = False
            k = j
        else:
            k += 1
    out["vis"] = vis
    out["mode"] = "verify" if featureless else "track"
    if featureless:
        out["notes"].append("featureless target: position verified, not tracked")
    return out


def summarize(c: dict, size) -> dict:
    """QA summary for one callout (expects c['track'] and c['box'] (padded) in source px)."""
    sw, sh = size
    tr = c.get("track")
    if not tr:
        return {"ok": True, "mode": "none"}
    vis = tr["vis"]
    sc = tr["score"][vis] if vis.any() else np.array([0.0])
    drift = float(np.max(np.hypot(tr["dx"], tr["dy"]))) if len(tr["dx"]) else 0.0
    bx, by, bw, bh = c["box"]
    oob = []
    for k in np.flatnonzero(vis)[::max(1, len(vis) // 12) or 1]:
        x0, y0 = bx + tr["dx"][k], by + tr["dy"][k]
        if x0 < -2 or y0 < -2 or x0 + bw > sw + 2 or y0 + bh > sh + 2:
            oob.append(int(k))
    vis_frac = float(vis.mean()) if len(vis) else 1.0
    s = {"mode": tr["mode"], "vis_frac": round(vis_frac, 3), "score_min": round(float(sc.min()), 3),
         "score_med": round(float(np.median(sc)), 3), "drift_px": round(drift, 1), "out_of_frame": bool(oob),
         "notes": tr.get("notes", [])}
    problems, warnings = [], []
    head = vis[: max(1, min(len(vis), 18))]          # first ~0.6 s the viewer sees the ring
    if not head.any():
        problems.append("target not on screen when the ring appears (anchor at the wrong moment?)")
    elif vis_frac < 0.3:
        problems.append("target visible for under 30% of the callout")
    elif vis_frac < 1.0:
        warnings.append(f"ring fades out early ({vis_frac:.0%} visible): target left the screen")
    if s["out_of_frame"]:
        problems.append("box extends outside the recording frame")
    if tr["mode"] == "track" and s["score_med"] < 0.5:
        problems.append("box does not match the target region well")
    s["warnings"] = warnings
    s["problems"] = problems
    s["ok"] = not problems
    return s
