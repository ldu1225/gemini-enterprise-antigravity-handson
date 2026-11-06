/* Pinned color scheme, applied before first paint (blocking, tiny, external → CSP script-src 'self').
 * Default = system preference (CSS @media). A pinned choice lives in localStorage (UI state only). */
(() => {
  'use strict';
  let pinned = null;
  try { pinned = window.localStorage.getItem('hol2:theme'); } catch (_) { /* storage unavailable */ }
  if (pinned !== 'light' && pinned !== 'dark') return;
  const root = document.documentElement;
  root.dataset.theme = pinned;
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) meta.content = pinned;
})();
