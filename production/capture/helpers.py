"""Shared capture helpers (import-safe: no side effects at import time)."""

DUMP_JS = r"""
() => {
  const out = [];
  function walk(root, depth) {
    for (const e of root.querySelectorAll('*')) {
      if (e.shadowRoot) walk(e.shadowRoot, depth + 1);
      const tag = e.tagName.toLowerCase();
      const role = e.getAttribute('role') || '';
      const al = e.getAttribute('aria-label') || '';
      const isBtn = tag === 'button' || role === 'button' || role === 'menuitem' || role === 'tab' || tag === 'a' || role === 'option' || role === 'link';
      if (!isBtn) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      const txt = (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60);
      out.push({tag, role, al: al.slice(0, 60), txt, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)});
    }
  }
  walk(document, 0);
  return out;
}
"""

FIND_TEXT_JS = r"""
([needle, maxW, maxH, minY]) => {
  if (minY === undefined) minY = 50;
  const res = [];
  function scan(root) {
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeValue && n.nodeValue.trim() === needle) {
        const el = n.parentElement;
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 4 && r.height > 4 && r.width <= maxW && r.height <= maxH && r.y > minY && r.y < 790)
          res.push({x: r.x, y: r.y, w: r.width, h: r.height});
      }
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) scan(e.shadowRoot);
  }
  scan(document);
  return res;
}
"""

MEDIA_JS = r"""
() => {
  let imgs = 0, vids = 0;
  function walk(root) {
    for (const e of root.querySelectorAll('img, video')) {
      const r = e.getBoundingClientRect();
      if (e.tagName === 'IMG' && e.naturalWidth >= 400 && r.width >= 200) imgs++;
      if (e.tagName === 'VIDEO' && r.width >= 200) vids++;
    }
    for (const e of root.querySelectorAll('*')) if (e.shadowRoot) walk(e.shadowRoot);
  }
  walk(document);
  return {imgs, vids};
}
"""


async def type_prompt(ge, text, delay=22):
    """Type line by line (Shift+Enter between lines so the prompt is not sent early)."""
    p = ge.page
    lines = text.split("\n")
    ge.mark("type_start", label="prompt", chars=len(text))
    for i, line in enumerate(lines):
        await p.keyboard.type(line, delay=delay)
        if i < len(lines) - 1:
            await p.keyboard.down("Shift"); await p.keyboard.press("Enter"); await p.keyboard.up("Shift")
    ge.mark("type_end", label="prompt")


async def smooth_scroll(ge, total, step=120, pause=110):
    p = ge.page
    moved = 0
    while moved < abs(total):
        await p.mouse.wheel(0, step if total > 0 else -step)
        moved += step
        await p.wait_for_timeout(pause)


async def click_xy(ge, box, label):
    """Click the centre of a {x,y,w,h} box with a visible eased cursor move."""
    p = ge.page
    x, y = box['x'] + box['w'] / 2, box['y'] + box['h'] / 2
    await p.mouse.move(x, y, steps=20)
    await p.wait_for_timeout(300)
    ge.mark('click', label=label, box={'x': box['x'], 'y': box['y'], 'width': box['w'], 'height': box['h']})
    await p.mouse.down(); await p.wait_for_timeout(70); await p.mouse.up()


async def click_text(ge, words, label, maxw=320, maxh=56, wait=1200):
    """Find the first visible element whose own text equals one of `words` and click it."""
    for w in ([words] if isinstance(words, str) else words):
        hits = await ge.page.evaluate(FIND_TEXT_JS, [w, maxw, maxh])
        if hits:
            await click_xy(ge, hits[0], label)
            await ge.page.wait_for_timeout(wait)
            return True
    return False


async def submit(ge, label="제출"):
    """Click the composer's send button (aria-label '제출')."""
    btn = await ge.vis('[aria-label="제출"]', timeout=8000)
    await ge.click(btn, label=label)
    ge.mark("submit", label=label)
