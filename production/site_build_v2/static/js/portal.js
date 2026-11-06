/* Hands-on Lab portal — progressive enhancement (2026-10 redesign).
 * CSP: script-src 'self'. DOM is only built via createElement / createElementNS / textContent / classList / dataset;
 * no HTML-string sinks of any kind. localStorage keeps non-sensitive UI state only (checklist ticks, theme, last lab,
 * step-only preference).
 */
(() => {
  'use strict';

  const doc = document;
  const root = doc.documentElement;
  root.classList.remove('no-js');
  root.classList.add('js');
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || '');
  const elementOf = (event) => (event.target instanceof Element ? event.target : null);

  const live = doc.getElementById('live');
  function announce(message) {
    if (!live) return;
    live.textContent = '';
    window.setTimeout(() => { live.textContent = message; }, 40);
  }

  const PREFIX = 'hol2:';
  const store = {
    get(key) {
      try { return window.localStorage.getItem(PREFIX + key); } catch (_) { return null; }
    },
    set(key, value) {
      try {
        if (value === null || value === false || value === '') window.localStorage.removeItem(PREFIX + key);
        else window.localStorage.setItem(PREFIX + key, value === true ? '1' : String(value));
      } catch (_) { /* storage unavailable (private mode) — state stays in-page */ }
    },
  };

  function svgIcon(name, cls) {
    const svg = doc.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', cls || 'ic');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    const use = doc.createElementNS(SVG_NS, 'use');
    use.setAttribute('href', `#i-${name}`);
    svg.appendChild(use);
    return svg;
  }

  /* ------------------------------------------------------------ dialogs: light dismiss fallback + [data-close] */
  const closedBySupported = typeof HTMLDialogElement !== 'undefined' && 'closedBy' in HTMLDialogElement.prototype;
  doc.querySelectorAll('dialog').forEach((dlg) => {
    if (!closedBySupported) {
      dlg.addEventListener('click', (event) => {
        if (event.target !== dlg) return;
        const r = dlg.getBoundingClientRect();
        const inside = r.top <= event.clientY && event.clientY <= r.bottom && r.left <= event.clientX && event.clientX <= r.right;
        if (!inside) dlg.close();
      });
    }
    dlg.querySelectorAll('[data-close]').forEach((btn) => btn.addEventListener('click', () => dlg.close()));
  });
  doc.querySelectorAll('[data-kbd]').forEach((k) => { k.textContent = isMac ? '⌘K' : 'Ctrl K'; });

  /* ------------------------------------------------------------ theme toggle (system ↔ pinned opposite) */
  const darkMq = window.matchMedia('(prefers-color-scheme: dark)');
  const schemeMeta = doc.querySelector('meta[name="color-scheme"]');
  const effectiveTheme = () => root.dataset.theme || (darkMq.matches ? 'dark' : 'light');
  function syncThemeLabels() {
    const next = effectiveTheme() === 'dark' ? '밝은' : '어두운';
    doc.querySelectorAll('[data-theme-toggle]').forEach((b) => b.setAttribute('aria-label', `${next} 테마로 전환`));
  }
  doc.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
      const system = darkMq.matches ? 'dark' : 'light';
      if (next === system) {
        delete root.dataset.theme;
        store.set('theme', null);
        if (schemeMeta) schemeMeta.content = 'light dark';
      } else {
        root.dataset.theme = next;
        store.set('theme', next);
        if (schemeMeta) schemeMeta.content = next;
      }
      syncThemeLabels();
      announce(next === 'dark' ? '어두운 테마로 바꿨습니다.' : '밝은 테마로 바꿨습니다.');
    });
  });
  darkMq.addEventListener('change', syncThemeLabels);
  syncThemeLabels();

  /* ------------------------------------------------------------ drawer (site / lab navigation) */
  doc.querySelectorAll('[data-open]').forEach((btn) => {
    const dlg = doc.getElementById(btn.dataset.open || '');
    if (!dlg || typeof dlg.showModal !== 'function') return;
    btn.addEventListener('click', () => {
      dlg.showModal();
      const cur = dlg.querySelector('.nav-step.is-current') || dlg.querySelector('[aria-current="page"]');
      if (cur) cur.scrollIntoView({ block: 'center' });
    });
  });
  doc.querySelectorAll('dialog.drawer').forEach((dlg) => {
    dlg.addEventListener('click', (event) => {
      const el = elementOf(event);
      if (el && el.closest('a[href]')) dlg.close(); // in-page step links: close so the target is visible
    });
  });

  /* ------------------------------------------------------------ copy buttons */
  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (_) { /* fall through to legacy path */ }
    }
    const buffer = doc.createElement('textarea');
    buffer.value = text;
    buffer.setAttribute('readonly', '');
    buffer.className = 'copy-buffer';
    doc.body.appendChild(buffer);
    buffer.select();
    let ok = false;
    try { ok = doc.execCommand('copy'); } catch (_) { ok = false; }
    buffer.remove();
    return ok;
  }

  doc.addEventListener('click', async (event) => {
    const el = elementOf(event);
    const btn = el ? el.closest('button[data-copy]') : null;
    if (!btn) return;
    const source = doc.getElementById(btn.dataset.copy || '');
    if (!source) return;
    const lines = source.querySelectorAll('.ln');
    const text = lines.length ? Array.from(lines, (l) => l.textContent || '').join('\n') : (source.textContent || '');
    const ok = await copyText(text.replace(/\s+$/, ''));
    const label = btn.querySelector('.copy-label');
    btn.classList.toggle('is-done', ok);
    if (label) label.textContent = ok ? '복사됨' : '직접 복사해 주세요';
    announce(ok ? '복사했습니다. 붙여 넣으세요.' : '자동 복사에 실패했습니다. 텍스트를 선택해 복사해 주세요.');
    window.clearTimeout(Number(btn.dataset.timer || 0));
    btn.dataset.timer = String(window.setTimeout(() => {
      btn.classList.remove('is-done');
      if (label) label.textContent = '복사';
    }, 1800));
  });

  /* ------------------------------------------------------------ lightbox (screenshot gallery per step) */
  const lightbox = doc.getElementById('lightbox');
  if (lightbox && typeof lightbox.showModal === 'function') {
    const stage = lightbox.querySelector('.lb-stage');
    const img = lightbox.querySelector('.lb-img');
    const cap = lightbox.querySelector('.lb-cap');
    const ctx = lightbox.querySelector('[data-lb-ctx]');
    const count = lightbox.querySelector('[data-lb-count]');
    const prev = lightbox.querySelector('[data-lb-prev]');
    const next = lightbox.querySelector('[data-lb-next]');
    const AR = /^ar-\d+x\d+$/;
    let items = [];
    let index = 0;
    let opener = null;
    let arClass = '';

    const show = (i) => {
      if (!items.length || !stage || !img) return;
      index = (i + items.length) % items.length;
      const link = items[index];
      stage.querySelectorAll('.co').forEach((node) => node.remove());
      link.querySelectorAll('.fig-stage .co').forEach((node) => stage.appendChild(node.cloneNode(true)));
      const ar = AR.test(link.dataset.ar || '') ? link.dataset.ar : '';
      if (arClass) stage.classList.remove(arClass);
      if (ar) { stage.classList.add(ar); lightbox.dataset.ar = ar; } else delete lightbox.dataset.ar;
      arClass = ar;
      img.src = link.getAttribute('href') || '';
      img.alt = link.dataset.alt || '';
      if (cap) cap.textContent = link.dataset.caption || '스크린샷';
      const multi = items.length > 1;
      lightbox.classList.toggle('is-single', !multi);
      if (count) count.textContent = multi ? `${index + 1} / ${items.length}` : '';
      lightbox.dispatchEvent(new Event('lightbox:show'));
    };

    doc.addEventListener('click', (event) => {
      const el = elementOf(event);
      const link = el ? el.closest('a[data-zoom]') : null;
      if (!link) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return; // allow "open in new tab"
      event.preventDefault();
      opener = link;
      const group = link.closest('[data-gallery]');
      items = group ? Array.from(group.querySelectorAll('a[data-zoom]')) : [link];
      if (ctx) ctx.textContent = group ? (group.dataset.gallery || '') : '';
      show(Math.max(0, items.indexOf(link)));
      lightbox.showModal();
    });
    if (prev) prev.addEventListener('click', () => show(index - 1));
    if (next) next.addEventListener('click', () => show(index + 1));
    lightbox.addEventListener('keydown', (event) => {
      if (items.length < 2) return;
      if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
      else if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
    });
    lightbox.addEventListener('close', () => {
      if (opener && typeof opener.focus === 'function') opener.focus({ preventScroll: true });
      opener = null;
    });
  }

  /* ------------------------------------------------------------ highlight label chips: always fully visible */
  // The authored placement (above / below / inside, start / end) is tried first; if the chip would be cut off by
  // the screenshot edge at the current width, the other placements are tried, then wrapping. Classes only (CSP).
  const CO_MODS = ['co--in', 'co--below', 'co--end', 'co--wrap'];
  const inside = (tr, sr) => tr.left >= sr.left - 0.5 && tr.right <= sr.right + 0.5 && tr.top >= sr.top - 0.5 && tr.bottom <= sr.bottom + 0.5;
  const covers = (tr, others) => others.some((o) => {
    const r = o.getBoundingClientRect();
    const ix = Math.max(0, Math.min(tr.right, r.right) - Math.max(tr.left, r.left));
    const iy = Math.max(0, Math.min(tr.bottom, r.bottom) - Math.max(tr.top, r.top));
    return r.width * r.height > 0 && (ix * iy) / (r.width * r.height) > 0.25;
  });
  const setMods = (co, mods) => {
    CO_MODS.forEach((m) => co.classList.remove(m));
    mods.forEach((m) => { if (m) co.classList.add(m); });
  };
  const fitTag = (co) => {
    const tag = co.querySelector('.co-tag');
    const stage = co.closest('.fig-stage, .lb-stage');
    if (!tag || !stage) return;
    if (co.dataset.pos === undefined) co.dataset.pos = CO_MODS.filter((m) => co.classList.contains(m)).join(' ');
    const base = co.dataset.pos.split(' ').filter(Boolean);
    const sr = stage.getBoundingClientRect();
    if (!sr.width) return;
    const others = Array.from(stage.querySelectorAll('.co')).filter((o) => o !== co);
    const v0 = base.includes('co--in') ? 'co--in' : base.includes('co--below') ? 'co--below' : '';
    const vertical = [v0, ...['', 'co--below', 'co--in'].filter((v) => v !== v0)];
    const h0 = base.includes('co--end') ? 'co--end' : '';
    const horizontal = [h0, h0 ? '' : 'co--end'];
    let firstVisible = null;
    for (const wrap of ['', 'co--wrap']) {
      for (const v of vertical) {
        for (const h of horizontal) {
          const mods = [v, h, wrap];
          setMods(co, mods);
          const tr = tag.getBoundingClientRect();
          if (!inside(tr, sr)) continue;
          if (!covers(tr, others)) return;
          if (!firstVisible) firstVisible = mods;
        }
      }
    }
    setMods(co, firstVisible || base);
  };
  const fitStage = (stage) => stage.querySelectorAll('.co').forEach(fitTag);
  const stages = Array.from(doc.querySelectorAll('.fig-stage, .lb-stage'));
  if (stages.length) {
    let queued = new Set();
    const flush = () => { queued.forEach(fitStage); queued = new Set(); };
    const ro = typeof ResizeObserver === 'function' ? new ResizeObserver((entries) => {
      if (!queued.size) requestAnimationFrame(flush);
      entries.forEach((en) => queued.add(en.target));
    }) : null;
    stages.forEach((s) => { if (ro) ro.observe(s); else fitStage(s); });
    if (lightbox) {
      const lbStage = lightbox.querySelector('.lb-stage');
      const lbImg = lightbox.querySelector('.lb-img');
      const refit = () => requestAnimationFrame(() => { if (lbStage) fitStage(lbStage); });
      lightbox.addEventListener('lightbox:show', refit);
      if (lbImg) lbImg.addEventListener('load', refit);
    }
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(() => stages.forEach(fitStage));
  }

  /* ------------------------------------------------------------ checklist + progress (rings, bars, counts) */
  const isDone = (key) => store.get(`c:${key}`) === '1';
  const boxes = Array.from(doc.querySelectorAll('input[type="checkbox"][data-check]'));

  function renderProgress() {
    doc.querySelectorAll('[data-checks]').forEach((el) => {
      const keys = (el.dataset.checks || '').split(/\s+/).filter(Boolean);
      el.classList.toggle('has-progress', keys.length > 0);
      if (!keys.length) {
        el.style.setProperty('--p', '0');
        el.classList.remove('is-started', 'is-complete');
        return;
      }
      const done = keys.filter(isDone).length;
      el.style.setProperty('--p', String(done / keys.length));
      el.classList.toggle('is-started', done > 0);
      el.classList.toggle('is-complete', done === keys.length);
      const own = (node) => node.closest('[data-checks]') === el;
      el.querySelectorAll('.js-count').forEach((c) => { if (own(c)) c.textContent = `${done} / ${keys.length}`; });
      el.querySelectorAll('.js-pct').forEach((c) => { if (own(c)) c.textContent = `${Math.round((done / keys.length) * 100)}%`; });
    });
  }

  boxes.forEach((box) => {
    box.checked = isDone(box.dataset.check || '');
    box.addEventListener('change', () => {
      const key = box.dataset.check || '';
      store.set(`c:${key}`, box.checked);
      boxes.forEach((other) => { if (other !== box && other.dataset.check === key) other.checked = box.checked; });
      renderProgress();
      const lab = box.dataset.lab || '';
      const labKeys = new Set(boxes.filter((b) => (b.dataset.lab || '') === lab).map((b) => b.dataset.check));
      if (box.checked && Array.from(labKeys).every(isDone)) announce('이 실습의 체크리스트를 모두 완료했습니다.');
    });
  });

  const labArticle = doc.querySelector('article[data-lab-section]');
  if (labArticle && labArticle.dataset.trackId) store.set(`last:${labArticle.dataset.trackId}`, labArticle.dataset.labSection);

  function renderResume() {
    doc.querySelectorAll('a[data-resume]').forEach((a) => {
      const track = a.dataset.resume || '';
      const labs = (a.dataset.resumeLabs || '').split('|').filter(Boolean).map((s) => {
        const [id, href, ...keys] = s.split(' ');
        return { id, href, keys };
      });
      if (!labs.length) return;
      const complete = (l) => l.keys.length > 0 && l.keys.every(isDone);
      const last = store.get(`last:${track}`);
      const started = Boolean(last) || labs.some((l) => l.keys.some(isDone));
      const allDone = labs.every(complete);
      const target = labs.find((l) => l.id === last && !complete(l)) || labs.find((l) => !complete(l)) || labs[0];
      a.setAttribute('href', target.href);
      const label = a.querySelector('.js-resume-l');
      if (label) label.textContent = allDone ? '다시 보기' : started ? '이어서 하기' : '시작하기';
    });
  }
  renderProgress();
  renderResume();
  window.addEventListener('pageshow', (event) => { if (event.persisted) { renderProgress(); renderResume(); } });

  /* ------------------------------------------------------------ tabs (home: videos, prep & files) */
  const untilFound = 'onbeforematch' in HTMLElement.prototype;
  doc.querySelectorAll('[data-tabs]').forEach((box) => {
    const tabs = Array.from(box.querySelectorAll('[role="tab"]'));
    const panels = tabs.map((t) => doc.getElementById(t.getAttribute('aria-controls') || ''));
    if (!tabs.length || panels.some((p) => !p)) return;
    const select = (i, focus) => {
      tabs.forEach((t, k) => {
        const on = k === i;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
        // inactive panels stay findable with Ctrl/⌘F where hidden="until-found" is supported
        panels[k].hidden = on ? false : (untilFound ? 'until-found' : true);
      });
      if (focus) tabs[i].focus();
    };
    tabs.forEach((t, i) => {
      t.addEventListener('click', () => select(i, false));
      t.addEventListener('keydown', (event) => {
        const last = tabs.length - 1;
        const map = { ArrowRight: i === last ? 0 : i + 1, ArrowLeft: i === 0 ? last : i - 1, Home: 0, End: last };
        if (event.key in map) { event.preventDefault(); select(map[event.key], true); }
      });
    });
    box.addEventListener('beforematch', (event) => {
      const el = elementOf(event);
      const panel = el ? el.closest('[role="tabpanel"]') : null;
      const i = panels.indexOf(panel);
      if (i >= 0) select(i, false);
    });
    select(0, false);
  });

  /* ------------------------------------------------------------ per-step demo video (chapters) */
  // Buttons carry data-lab / data-step / data-seek / data-end / data-title (generated at build time
  // from assets/video/<id>.chapters.json). No chapters file → no buttons → nothing to wire.
  const STEP_ONLY_KEY = 'pref:step-only';
  const players = new Map();
  const toNum = (value) => {
    const n = Number(value);
    return Number.isFinite(n) && n >= 0 ? n : null;
  };
  const stepToggles = Array.from(doc.querySelectorAll('input[data-step-only]'));
  const stepOnly = () => stepToggles.some((input) => input.checked);

  function stickyOffset() {
    let h = 0;
    doc.querySelectorAll('.topbar, .mbar').forEach((bar) => {
      const r = bar.getBoundingClientRect();
      if (r.height && getComputedStyle(bar).display !== 'none') h = Math.max(h, r.bottom);
    });
    return h + 12;
  }

  function revealVideo(video) {
    const frame = video.closest('.video-frame') || video;
    const rect = frame.getBoundingClientRect();
    const top = stickyOffset();
    if (rect.top >= top && rect.bottom <= window.innerHeight) return;
    const room = window.innerHeight - top;
    const y = window.scrollY + rect.top - top - Math.max(0, (room - rect.height) / 2);
    window.scrollTo({ top: Math.max(0, y), behavior: reduceMotion.matches ? 'auto' : 'smooth' });
  }

  function chapterAt(p, t) {
    let found = null;
    p.chapters.forEach((c) => {
      if (t + 0.05 >= c.start && t < c.end && (!found || c.start >= found.start)) found = c;
    });
    return found;
  }

  function setActive(p, c) {
    if (p.current === c) return;
    p.current = c;
    p.stepEls.forEach((li) => {
      li.classList.remove('is-playing');
      li.removeAttribute('aria-current');
    });
    p.buttons.forEach((b) => {
      const on = Boolean(c) && Number(b.dataset.step) === c.step;
      b.classList.toggle('is-active', on);
      if (on) b.setAttribute('aria-current', 'true');
      else b.removeAttribute('aria-current');
    });
    if (p.chip) {
      p.chip.hidden = !c;
      if (c && p.chipN) p.chipN.textContent = `STEP ${c.step}`;
      if (c && p.chipT) p.chipT.textContent = c.title;
    }
    if (c) {
      const li = p.article.querySelector(`.steps > .step[data-step="${c.step}"]`);
      if (li) {
        li.classList.add('is-playing');
        li.setAttribute('aria-current', 'step');
      }
    }
  }

  function stopIfDone(p) {
    const stopAt = toNum(p.video.dataset.stopAt);
    if (stopAt === null || p.video.paused) return;
    if (p.video.currentTime >= stopAt - 0.04) {
      p.video.pause();
      delete p.video.dataset.stopAt;
      announce('이 단계 영상을 끝까지 재생했습니다.');
    }
  }

  function watchStop(p) {
    // timeupdate fires only every ~250 ms; poll per frame while a step boundary is armed
    if (p.raf) window.cancelAnimationFrame(p.raf);
    const tick = () => {
      p.raf = 0;
      if (toNum(p.video.dataset.stopAt) === null || p.video.paused) return;
      stopIfDone(p);
      if (toNum(p.video.dataset.stopAt) !== null) p.raf = window.requestAnimationFrame(tick);
    };
    p.raf = window.requestAnimationFrame(tick);
  }

  function seekAndPlay(p, t) {
    const v = p.video;
    const apply = () => {
      const max = Number.isFinite(v.duration) && v.duration > 0 ? Math.max(0, v.duration - 0.05) : t;
      const target = Math.min(t, max);
      v.dataset.programmatic = '1';
      v.currentTime = target;
      setActive(p, chapterAt(p, target));
    };
    if (v.readyState >= 1) apply();
    else v.addEventListener('loadedmetadata', apply, { once: true });
    const playing = v.play();
    if (playing && typeof playing.catch === 'function') {
      playing.catch(() => { /* playback blocked: the seek still applies and the user can press play */ });
    }
  }

  doc.querySelectorAll('video[data-lab]').forEach((video) => {
    const lab = video.dataset.lab || '';
    const article = video.closest('[data-lab-section]');
    if (!lab || !article) return;
    const buttons = Array.from(article.querySelectorAll('button[data-seek]'));
    if (!buttons.length) return;
    const chapters = new Map();
    buttons.forEach((b) => {
      const step = Number(b.dataset.step);
      const start = toNum(b.dataset.seek);
      const end = toNum(b.dataset.end);
      if (!Number.isInteger(step) || start === null || end === null || end <= start) return;
      const key = `${step}@${start}`;
      if (!chapters.has(key)) chapters.set(key, { step, start, end, title: b.dataset.title || '' });
    });
    const chip = article.querySelector('[data-vchip]');
    const p = {
      lab, video, article, buttons, chip,
      chapters: Array.from(chapters.values()),
      chipN: chip ? chip.querySelector('.vchip-n') : null,
      chipT: chip ? chip.querySelector('.vchip-t') : null,
      stepEls: Array.from(article.querySelectorAll('.steps > .step')),
      current: undefined,
      raf: 0,
    };
    players.set(lab, p);

    video.addEventListener('timeupdate', () => {
      stopIfDone(p);
      setActive(p, chapterAt(p, video.currentTime));
    });
    video.addEventListener('seeking', () => {
      if (video.dataset.programmatic === '1') return;
      delete video.dataset.stopAt; // manual scrubbing → stop enforcing the step boundary
    });
    video.addEventListener('seeked', () => {
      delete video.dataset.programmatic;
      setActive(p, chapterAt(p, video.currentTime));
    });
    video.addEventListener('play', () => {
      if (toNum(video.dataset.stopAt) !== null) watchStop(p);
    });
    video.addEventListener('ended', () => {
      delete video.dataset.stopAt;
      setActive(p, null);
    });
  });

  doc.addEventListener('click', (event) => {
    const el = elementOf(event);
    const btn = el ? el.closest('button[data-seek]') : null;
    if (!btn) return;
    const p = players.get(btn.dataset.lab || '');
    const start = toNum(btn.dataset.seek);
    if (!p || start === null) return;
    const end = toNum(btn.dataset.end);
    if (stepOnly() && end !== null && end > start) p.video.dataset.stopAt = String(end);
    else delete p.video.dataset.stopAt;
    revealVideo(p.video);
    if (btn.hasAttribute('data-reveal')) p.video.focus({ preventScroll: true });
    seekAndPlay(p, start);
    if (toNum(p.video.dataset.stopAt) !== null) watchStop(p);
  });

  const savedStepOnly = store.get(STEP_ONLY_KEY) === '1';
  stepToggles.forEach((input) => {
    input.checked = savedStepOnly;
    input.addEventListener('change', () => {
      stepToggles.forEach((other) => { other.checked = input.checked; });
      store.set(STEP_ONLY_KEY, input.checked);
      players.forEach((p) => {
        if (input.checked && p.current && !p.video.paused) {
          p.video.dataset.stopAt = String(p.current.end);
          watchStop(p);
        } else if (!input.checked) {
          delete p.video.dataset.stopAt;
        }
      });
    });
  });

  /* ------------------------------------------------------------ scrollspy: sidebar steps · drawer · mobile step bar */
  // Desktop sidebar links use native `scroll-target-group` + :target-current where supported (CSS); an
  // IntersectionObserver keeps the drawer links, the sticky "current step" bar and unsupported browsers in sync.
  if (labArticle) {
    const sections = Array.from(labArticle.querySelectorAll('.steps > .step, #more, #checklist'));
    const total = labArticle.querySelectorAll('.steps > .step').length;
    const nowT = doc.querySelector('[data-now]');
    const nowN = doc.querySelector('[data-now-n]');
    const nativeSpy = Boolean(window.CSS && CSS.supports && CSS.supports('scroll-target-group: auto'));
    const sideLinks = Array.from(doc.querySelectorAll('.sidebar .nav-step'));
    const drawerLinks = Array.from(doc.querySelectorAll('.drawer .nav-step'));
    const ioLinks = nativeSpy ? drawerLinks : sideLinks.concat(drawerLinks);
    const defaultT = nowT ? nowT.textContent : '';
    const defaultN = nowN ? nowN.textContent : '';
    let current;

    const dock = doc.querySelector('[data-stepdock]');
    const dockK = dock ? dock.querySelector('[data-dock-k]') : null;
    const dockT = dock ? dock.querySelector('[data-dock-t]') : null;
    const dockLink = dock ? dock.querySelector('[data-dock-link]') : null;
    const dockFill = dock ? dock.querySelector('[data-dock-fill]') : null;
    const dockPrev = dock ? dock.querySelector('[data-dock-prev]') : null;
    const dockNext = dock ? dock.querySelector('[data-dock-next]') : null;
    if (dock) dock.hidden = false; // JS present: the dock is shown/hidden with .is-on (animated)

    function updateDock(sec) {
      if (!dock) return;
      dock.classList.toggle('is-on', Boolean(sec));
      if (!sec) return;
      const i = sections.indexOf(sec);
      const isStep = sec.classList.contains('step');
      if (dockK) dockK.textContent = isStep ? `STEP ${sec.dataset.step} / ${total}` : (sec.id === 'more' ? 'BONUS' : 'FINISH');
      if (dockT) dockT.textContent = isStep ? (sec.dataset.title || '') : (sec.id === 'more' ? '더 해 보기' : '체크리스트');
      if (dockLink) dockLink.setAttribute('href', `#${sec.id}`);
      if (dockFill) dockFill.style.setProperty('--p', String(isStep ? Number(sec.dataset.step) / total : 1));
      if (dockPrev) dockPrev.disabled = i <= 0;
      if (dockNext) dockNext.disabled = i < 0 || i >= sections.length - 1;
    }
    const go = (delta) => {
      const i = current ? sections.indexOf(current) : -1;
      const target = sections[Math.max(0, Math.min(sections.length - 1, i + delta))];
      if (!target) return;
      target.scrollIntoView({ behavior: reduceMotion.matches ? 'auto' : 'smooth', block: 'start' });
      if (target.id) history.replaceState(null, '', `#${target.id}`);
    };
    if (dockPrev) dockPrev.addEventListener('click', () => go(-1));
    if (dockNext) dockNext.addEventListener('click', () => go(1));

    const setCurrent = (sec) => {
      if (sec === current) return;
      current = sec;
      updateDock(sec);
      const href = sec ? `#${sec.id}` : '';
      ioLinks.forEach((a) => {
        const on = Boolean(href) && a.getAttribute('href') === href;
        a.classList.toggle('is-current', on);
        if (on) a.setAttribute('aria-current', 'step');
        else a.removeAttribute('aria-current');
      });
      if (!nowT) return;
      if (!sec) {
        nowT.textContent = defaultT;
        if (nowN) nowN.textContent = defaultN;
      } else if (sec.classList.contains('step')) {
        nowT.textContent = sec.dataset.title || '';
        if (nowN) nowN.textContent = `${sec.dataset.step} / ${total}`;
      } else {
        nowT.textContent = sec.id === 'more' ? '더 해 보기' : '체크리스트';
        if (nowN) nowN.textContent = '';
      }
    };

    if ('IntersectionObserver' in window && sections.length) {
      const visible = new Set();
      const io = new IntersectionObserver((entries) => {
        entries.forEach((en) => { if (en.isIntersecting) visible.add(en.target); else visible.delete(en.target); });
        const hit = sections.find((s) => visible.has(s));
        if (hit) setCurrent(hit);
        else if (sections[0].getBoundingClientRect().top > window.innerHeight * 0.4) setCurrent(null);
      }, { rootMargin: '-40% 0px -59% 0px', threshold: 0 });
      sections.forEach((s) => io.observe(s));
    }
    if (nativeSpy && sideLinks.length) {
      const sync = () => {
        const cur = doc.querySelector('.sidebar .nav-step:target-current');
        sideLinks.forEach((a) => {
          if (a === cur) a.setAttribute('aria-current', 'step');
          else a.removeAttribute('aria-current');
        });
      };
      sync();
      doc.addEventListener('scrollend', sync);
    }
    // keep the active lab's step list in view inside the scrollable sidebar
    const sideCur = doc.querySelector('.sidebar .nav-lab[aria-current="page"]');
    const sideScroller = doc.querySelector('.sidebar-in');
    if (sideCur && sideScroller) {
      const r = sideCur.getBoundingClientRect();
      const s = sideScroller.getBoundingClientRect();
      if (r.top < s.top || r.bottom > s.bottom - 120) sideScroller.scrollTop += r.top - s.top - 80;
    }
  }

  /* ------------------------------------------------------------ ⌘K command palette */
  const cmdk = doc.getElementById('cmdk');
  if (cmdk && typeof cmdk.showModal === 'function') {
    const input = cmdk.querySelector('#cmdk-q');
    const list = cmdk.querySelector('#cmdk-list');
    const base = root.dataset.base || '';
    const currentTrack = root.dataset.track || '';
    const KIND = {
      page: ['페이지', 'grid'], lab: ['실습', 'list'], step: ['단계', 'corner'],
      prompt: ['프롬프트', 'sparkle'], code: ['코드', 'terminal'], faq: ['FAQ', 'info'],
    };
    const ORDER = ['page', 'lab', 'step', 'prompt', 'code', 'faq'];
    let index = null;
    let loading = null;
    let options = [];
    let active = -1;
    let opener = null;

    const norm = (s) => String(s || '').toLowerCase();
    function load() {
      if (index) return Promise.resolve(index);
      if (!loading) {
        loading = fetch(root.dataset.search || '', { credentials: 'same-origin' })
          .then((r) => (r.ok ? r.json() : []))
          .catch(() => [])
          .then((data) => {
            index = (Array.isArray(data) ? data : []).filter((it) => it && typeof it.u === 'string' && KIND[it.k]).map((it) => {
              const hay = norm(`${it.t} ${it.s || ''} ${it.x || ''}`);
              return { ...it, _t: norm(it.t), _s: norm(it.s), _h: hay, _c: hay.replace(/\s+/g, '') };
            });
            return index;
          });
      }
      return loading;
    }

    function toUrl(u) {
      // index URLs are site-root relative; never follow absolute/protocol URLs from the index
      if (/^[a-z][a-z0-9+.-]*:|^\/\//i.test(u)) return null;
      try { return new URL(base + u, window.location.href).href; } catch (_) { return null; }
    }

    function highlight(el, text, tokens) {
      el.replaceChildren();
      const lower = norm(text);
      let i = 0;
      const ranges = [];
      tokens.forEach((tok) => {
        if (!tok) return;
        const at = lower.indexOf(tok);
        if (at >= 0) ranges.push([at, at + tok.length]);
      });
      ranges.sort((a, b) => a[0] - b[0]);
      ranges.forEach(([s, e]) => {
        if (s < i) return;
        if (s > i) el.appendChild(doc.createTextNode(text.slice(i, s)));
        const m = doc.createElement('mark');
        m.textContent = text.slice(s, e);
        el.appendChild(m);
        i = e;
      });
      if (i < text.length) el.appendChild(doc.createTextNode(text.slice(i)));
    }

    function search(q) {
      const tokens = norm(q).split(/\s+/).filter(Boolean);
      if (!tokens.length) {
        const quick = index.filter((it) => it.k === 'page' || (it.k === 'lab' && (!currentTrack || it.tr === currentTrack)));
        return { items: quick.slice(0, 16), tokens };
      }
      const scored = [];
      index.forEach((it) => {
        let score = 0;
        for (const tok of tokens) {
          if (!(it._h.includes(tok) || it._c.includes(tok))) return;
          if (it._t.startsWith(tok)) score += 30;
          else if (it._t.includes(tok)) score += 20;
          else if (it._s.includes(tok)) score += 8;
          else score += 2;
        }
        if (it._t.includes(norm(q).trim())) score += 25;
        score += { lab: 24, page: 18, step: 6, prompt: 4, code: 4, faq: 3 }[it.k] || 0;
        if (currentTrack && it.tr === currentTrack) score += 3;
        scored.push([score, it]);
      });
      scored.sort((a, b) => b[0] - a[0]);
      return { items: scored.slice(0, 40).map((x) => x[1]), tokens };
    }

    function select(i, scroll) {
      if (!options.length) { active = -1; input.removeAttribute('aria-activedescendant'); return; }
      active = (i + options.length) % options.length;
      options.forEach((o, k) => o.setAttribute('aria-selected', k === active ? 'true' : 'false'));
      input.setAttribute('aria-activedescendant', options[active].id);
      if (scroll) options[active].scrollIntoView({ block: 'nearest' });
    }

    function render() {
      if (!index) return;
      const { items, tokens } = search(input.value);
      list.replaceChildren();
      options = [];
      if (!items.length) {
        const empty = doc.createElement('p');
        empty.className = 'cmdk-empty';
        empty.textContent = `‘${input.value.trim()}’에 대한 결과가 없습니다.`;
        list.appendChild(empty);
        select(-1);
        return;
      }
      const groups = new Map();
      items.forEach((it) => { if (!groups.has(it.k)) groups.set(it.k, []); groups.get(it.k).push(it); });
      const order = tokens.length ? Array.from(groups.keys()) : ORDER.filter((k) => groups.has(k));
      order.forEach((k) => {
        const head = doc.createElement('div');
        head.className = 'cmdk-g';
        head.setAttribute('role', 'presentation');
        head.textContent = KIND[k][0];
        list.appendChild(head);
        groups.get(k).slice(0, tokens.length ? 8 : 16).forEach((it) => {
          const href = toUrl(it.u);
          if (!href) return;
          const a = doc.createElement('a');
          a.className = 'cmdk-o';
          a.id = `cmdk-o-${options.length}`;
          a.href = href;
          a.tabIndex = -1;
          a.setAttribute('role', 'option');
          a.setAttribute('aria-selected', 'false');
          const ic = doc.createElement('span');
          ic.className = 'cmdk-ic';
          ic.appendChild(svgIcon(KIND[k][1]));
          const tx = doc.createElement('span');
          tx.className = 'cmdk-tx';
          const t = doc.createElement('span');
          t.className = 'cmdk-t';
          highlight(t, it.t, tokens);
          const s = doc.createElement('span');
          s.className = 'cmdk-s';
          highlight(s, it.s || '', tokens);
          tx.append(t, s);
          a.append(ic, tx, svgIcon('arrow', 'ic ic-sm cmdk-go'));
          const idx = options.length;
          a.addEventListener('mousemove', () => { if (active !== idx) select(idx, false); });
          a.addEventListener('click', () => cmdk.close());
          list.appendChild(a);
          options.push(a);
        });
      });
      select(0, false);
    }

    function open() {
      if (cmdk.open) return;
      doc.querySelectorAll('dialog[open]').forEach((d) => { if (d !== cmdk) d.close(); });
      opener = doc.activeElement;
      input.value = '';
      list.replaceChildren();
      cmdk.showModal();
      input.focus();
      load().then(render);
    }

    cmdk.addEventListener('close', () => {
      if (opener && typeof opener.focus === 'function' && doc.contains(opener)) opener.focus({ preventScroll: true });
      opener = null;
    });
    input.addEventListener('input', render);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown') { event.preventDefault(); select(active + 1, true); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); select(active - 1, true); }
      else if (event.key === 'Enter' && !event.isComposing) {
        event.preventDefault();
        const o = options[active];
        if (!o) return;
        const href = o.href;
        cmdk.close();
        window.location.assign(href);
      }
    });
    doc.querySelectorAll('[data-cmdk]').forEach((b) => b.addEventListener('click', open));
    doc.addEventListener('keydown', (event) => {
      if ((event.metaKey || event.ctrlKey) && !event.altKey && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        if (cmdk.open) cmdk.close(); else open();
        return;
      }
      if (event.key === '/' && !event.metaKey && !event.ctrlKey && !cmdk.open) {
        const t = event.target;
        if (t instanceof HTMLElement && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
        if (doc.querySelector('dialog[open]')) return;
        event.preventDefault();
        open();
      }
    });
  }

  /* ------------------------------------------------------------ stalled-audio fallback */
  // When the OS audio output stops answering (e.g. macOS coreaudiod restarted while the browser stayed open),
  // Chrome keeps an unmuted <video> "playing" at 0:00 forever, while muted playback (null audio sink) still works.
  // Detect that state and fall back to muted playback — captions are on by default — with a short explanation.
  const STALL_MS = 2500;
  function stallNotice(video) {
    const frame = video.closest('.video-frame') || video;
    const next = frame.nextElementSibling;
    if (next && next.classList.contains('vstall')) return;
    const note = doc.createElement('p');
    note.className = 'vstall';
    note.setAttribute('role', 'status');
    note.textContent = '이 PC의 소리 출력이 응답하지 않아 음소거로 재생합니다. 자막으로 따라오시거나, '
      + '브라우저를 완전히 종료(Mac ⌘Q · Windows Alt+F4)한 뒤 다시 열면 소리가 나옵니다.';
    frame.insertAdjacentElement('afterend', note);
  }
  doc.querySelectorAll('video').forEach((video) => {
    let timer = 0;
    const arm = () => {
      window.clearTimeout(timer);
      if (video.muted) return;
      const t0 = video.currentTime;
      timer = window.setTimeout(() => {
        if (video.paused || video.seeking || video.muted || video.ended || video.readyState < 3) return;
        if (Math.abs(video.currentTime - t0) > 0.05) return; // clock is moving → healthy
        video.muted = true; // muted media renders to a null sink, so the clock runs again
        stallNotice(video);
        announce('소리 출력 문제로 음소거 재생으로 전환했습니다.');
        const t1 = video.currentTime;
        window.setTimeout(() => { // still frozen → rebuild the pipeline while muted
          if (video.paused || Math.abs(video.currentTime - t1) > 0.05) return;
          const at = video.currentTime;
          video.addEventListener('loadedmetadata', () => {
            video.currentTime = at;
            const pr = video.play();
            if (pr && typeof pr.catch === 'function') pr.catch(() => {});
          }, { once: true });
          video.load();
        }, 2000);
      }, STALL_MS);
    };
    video.addEventListener('play', arm);
    video.addEventListener('playing', arm);
    video.addEventListener('seeked', () => { if (!video.paused) arm(); });
    video.addEventListener('pause', () => window.clearTimeout(timer));
  });

  // only one video plays at a time (home has two opening videos)
  doc.addEventListener('play', (event) => {
    doc.querySelectorAll('video').forEach((v) => { if (v !== event.target && !v.paused) v.pause(); });
  }, true);

  // ------------------------------------------------------------------ home hero deck
  // Real captures glide right → centre → left. JS only moves data-pos (same rule as build.py deck_pos) and
  // aria-current; CSS does the motion. The active dot's fill animation is the timer (animationend → next), so
  // hover, keyboard focus, the pause button and going off-screen pause the deck and its progress together.
  // Reduced motion: no autoplay and no tilt; prev / next / dots still work.
  const deckRoot = doc.querySelector('[data-deck-root]');
  const deckEl = deckRoot ? deckRoot.querySelector('.deck') : null;
  const deckCards = deckEl ? Array.from(deckEl.children).filter((c) => c.classList.contains('win')) : [];
  const deckCtrl = deckRoot ? deckRoot.querySelector('.deck-ctrl') : null;
  if (deckEl && deckCtrl && deckCards.length > 1) {
    const n = deckCards.length;
    const dots = Array.from(deckCtrl.querySelectorAll('.deck-dot'));
    const toggle = deckCtrl.querySelector('[data-deck="toggle"]');
    let cur = 0;
    const place = (i) => {
      cur = ((i % n) + n) % n;
      deckCards.forEach((card, k) => {
        let off = (k - cur + n) % n;
        if (off > n / 2) off -= n;
        card.dataset.pos = off === 0 ? 'c' : off === -1 ? 'l' : off === 1 ? 'r' : off < 0 ? 'fl' : 'fr';
      });
      dots.forEach((d, k) => {
        if (k === cur) d.setAttribute('aria-current', 'true');
        else d.removeAttribute('aria-current');
      });
    };
    const syncLive = () => deckRoot.classList.toggle('is-live', !reduceMotion.matches);
    syncLive();
    if (typeof reduceMotion.addEventListener === 'function') reduceMotion.addEventListener('change', syncLive);
    deckCtrl.hidden = false;

    dots.forEach((d, k) => {
      const fill = d.querySelector('.deck-fill');
      if (fill) fill.addEventListener('animationend', () => { if (k === cur) place(cur + 1); });
    });
    deckCtrl.addEventListener('click', (event) => {
      const b = elementOf(event) && elementOf(event).closest('button');
      if (!b) return;
      if (b.dataset.deck === 'prev') place(cur - 1);
      else if (b.dataset.deck === 'next') place(cur + 1);
      else if (b.dataset.deckGo !== undefined) place(Number(b.dataset.deckGo));
      else if (b === toggle) {
        const paused = toggle.getAttribute('aria-pressed') !== 'true';
        toggle.setAttribute('aria-pressed', String(paused));
        toggle.setAttribute('aria-label', paused ? '자동 넘김 재생' : '자동 넘김 멈추기');
        deckRoot.classList.toggle('is-paused', paused);
      }
    });

    if ('IntersectionObserver' in window) {
      new IntersectionObserver((entries) => {
        entries.forEach((en) => deckRoot.classList.toggle('is-offscreen', !en.isIntersecting));
      }, { threshold: 0.15 }).observe(deckRoot);
    }

    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      let raf = 0;
      let px = 0;
      let py = 0;
      const tilt = () => {
        raf = 0;
        const on = !reduceMotion.matches;
        deckEl.style.setProperty('--tilt-y', `${on ? (-px * 7).toFixed(2) : 0}deg`);
        deckEl.style.setProperty('--tilt-x', `${on ? (py * 4).toFixed(2) : 0}deg`);
      };
      deckRoot.addEventListener('pointermove', (event) => {
        const r = deckRoot.getBoundingClientRect();
        px = (event.clientX - r.left) / r.width - 0.5;
        py = (event.clientY - r.top) / r.height - 0.5;
        if (!raf) raf = window.requestAnimationFrame(tilt);
      });
      deckRoot.addEventListener('pointerleave', () => {
        px = 0;
        py = 0;
        if (!raf) raf = window.requestAnimationFrame(tilt);
      });
    }
  }
})();
