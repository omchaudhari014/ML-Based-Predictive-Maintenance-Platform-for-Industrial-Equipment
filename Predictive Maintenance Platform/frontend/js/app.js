/* app.js — the application shell. Imported (for side effects) by every page.

   ONE source of truth for the top bar and footer. Instead of every page
   hand-copying the same 40 lines of <header> markup — the #1 way parallel-built
   pages drift apart — each page ships only:

     <body data-page="results">
       <a class="skip-link" href="#main">Skip to content</a>
       <header id="site-topbar"></header>
       <main class="main" id="main"> … page content … </main>
       <footer id="site-footer"></footer>

   …and this module fills #site-topbar / #site-footer on DOMContentLoaded,
   reading body.dataset.page to mark the active nav item. Change the chrome once,
   here, and all ten pages change together.

   It also:
     · renders the persistent DEMO SCORING / LIVE API source badge (getMode),
     · shows the current dataset chip when a dataset is loaded,
     · reflects optional auth state (avatar / Sign in),
     · injects the shared texture <defs> and a global toast region,
     · exports toast() and a texture toggle for pages to use. */

import { el, mount, clear } from './util/dom.js';
import { int } from './util/format.js';
import { getMode } from './api.js';
import { getDataset } from './store.js';

/* The primary nav. `page` matches body.dataset.page for active marking. Upload
   is the primary product action and leads the nav; the dashboard/results is NOT
   first (§ "dashboard must not be the first thing the user sees"). */
const NAV = [
  { page: 'home', label: 'Home', href: 'index.html' },
  { page: 'upload', label: 'Bulk Analysis', href: 'upload.html' },
  { page: 'models', label: 'Models', href: 'model-performance.html' },
  { page: 'history', label: 'History', href: 'history.html' },
];

/* Which body.dataset.page values map onto each nav item's active state (some
   pages share a nav home — analysis belongs under Upload, machine/diagnostic
   under Results). */
const NAV_ALIASES = {
  home: 'home',
  profile: 'home',
  predict: 'home',
  machine: 'home',
  upload: 'upload',
  analysis: 'upload',
  results: 'upload',
  models: 'models',
  history: 'history',
};

function wordmark() {
  return el('a', { class: 'topbar__wordmark', href: 'index.html' }, [
    svgLogo(),
    'Sentinel PdM',
  ]);
}

function svgLogo() {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '18'); svg.setAttribute('height', '18');
  svg.setAttribute('viewBox', '0 0 18 18'); svg.setAttribute('aria-hidden', 'true');
  svg.innerHTML =
    '<rect x="1.5" y="1.5" width="15" height="15" rx="3" fill="none" stroke="var(--accent-solid)" stroke-width="1.6"/>' +
    '<path d="M5 11.5 L7.6 7 L10.2 10 L13 5.5" fill="none" stroke="var(--accent-solid)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>';
  return svg;
}

/* The dataset chip — only shown when a dataset is loaded. Links to results. */
function datasetChip() {
  const ds = getDataset();
  if (!ds) return null;
  const records = safeRecordCount();
  return el('a', { class: 'dataset-chip', href: 'results.html', title: ds.name }, [
    el('span', { class: 'dataset-chip__name' }, ds.name),
    records != null ? el('span', {}, int(records)) : null,
  ]);
}

function safeRecordCount() {
  try {
    const raw = sessionStorage.getItem('pdm.profile');
    if (!raw) return null;
    return JSON.parse(raw).counts.records;
  } catch { return null; }
}

/* The right-hand cluster: just the dataset chip. Auth and source badges removed. */
function rightCluster() {
  const wrap = el('div', { class: 'topbar__right' });

  const rebuild = () => {
    clear(wrap);
    const chip = datasetChip();
    if (chip) wrap.appendChild(chip);
  };

  rebuild();
  return wrap;
}

function buildTopbar(activePage) {
  const active = NAV_ALIASES[activePage] || null;
  const nav = el('nav', { class: 'topbar__nav', 'aria-label': 'Primary' },
    NAV.map((item) => el('a', {
      href: item.href,
      ...(item.page === active ? { 'aria-current': 'page' } : {}),
    }, item.label)),
  );
  return el('header', { class: 'topbar' }, [
    wordmark(),
    nav,
    el('span', { class: 'topbar__spacer' }),
    rightCluster(),
  ]);
}

function buildFooter() {
  return el('div', { class: 'footer__inner' }, [
    el('span', {}, 'Sentinel PdM · machine-adaptive predictive-maintenance framework'),
    el('span', {}, 'Decision support for maintenance planning — not a guaranteed engineering verdict.'),
  ]);
}

/* ── Toast ───────────────────────────────────────────────────────────────── */

let toastRegion = null;
function ensureToastRegion() {
  if (toastRegion && document.body.contains(toastRegion)) return toastRegion;
  toastRegion = el('div', { class: 'toast-region', id: 'toast-region', role: 'status', 'aria-live': 'polite' });
  document.body.appendChild(toastRegion);
  return toastRegion;
}

/* Show a transient message. variant: 'success' | 'error' | undefined (accent). */
export function toast(message, variant) {
  const region = ensureToastRegion();
  const t = el('div', { class: `toast${variant ? ` toast--${variant}` : ''}` }, message);
  region.appendChild(t);
  setTimeout(() => t.remove(), 4200);
  return t;
}

/* ── Texture defs + toggle ───────────────────────────────────────────────── */

const TEXTURE_DEFS = `
<svg width="0" height="0" aria-hidden="true" style="position:absolute">
  <defs>
    <pattern id="texture-lines-45-p" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="6" height="6" fill="#fff"/><line x1="0" y1="0" x2="0" y2="6" stroke="#000" stroke-width="2.4"/>
    </pattern>
    <mask id="texture-lines-45" maskContentUnits="userSpaceOnUse"><rect x="0" y="0" width="4000" height="4000" fill="url(#texture-lines-45-p)"/></mask>
    <pattern id="texture-lines-135-p" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(135)">
      <rect width="6" height="6" fill="#fff"/><line x1="0" y1="0" x2="0" y2="6" stroke="#000" stroke-width="2.4"/>
    </pattern>
    <mask id="texture-lines-135" maskContentUnits="userSpaceOnUse"><rect x="0" y="0" width="4000" height="4000" fill="url(#texture-lines-135-p)"/></mask>
  </defs>
</svg>`;

function injectTextureDefs() {
  if (document.getElementById('texture-lines-45')) return;
  const holder = el('div');
  holder.innerHTML = TEXTURE_DEFS;
  const svg = holder.firstElementChild;
  if (svg) document.body.appendChild(svg);
}

/* Toggle the accessibility texture channel on the whole document. Pages that
   host charts can wire a button to this. Returns the new on/off state. */
export function toggleTexture() {
  const on = document.documentElement.getAttribute('data-texture') !== 'on';
  document.documentElement.setAttribute('data-texture', on ? 'on' : 'off');
  return on;
}

/* ── Boot ────────────────────────────────────────────────────────────────── */

function boot() {
  const page = document.body.dataset.page || '';

  const topbarSlot = document.getElementById('site-topbar');
  if (topbarSlot) topbarSlot.replaceWith(buildTopbar(page));

  const footerSlot = document.getElementById('site-footer');
  if (footerSlot) {
    footerSlot.className = 'footer';
    clear(footerSlot);
    footerSlot.appendChild(buildFooter());
  }

  injectTextureDefs();
  ensureToastRegion();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
