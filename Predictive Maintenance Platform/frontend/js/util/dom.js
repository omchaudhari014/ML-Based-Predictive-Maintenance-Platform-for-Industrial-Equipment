/* util/dom.js — tiny DOM helpers. No framework; just enough to build views.
   ES module, imported by page scripts and app.js. */

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/* el('div', {class:'x', 'data-id':1, onclick:fn}, [child, 'text'])
   - attributes whose key starts with 'on' bind events
   - `class`, `html`, `text`, `dataset` handled specially
   - children may be nodes, strings, or nullish (skipped) */
export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k === 'text') node.textContent = v;
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v === true) node.setAttribute(k, '');
    else node.setAttribute(k, String(v));
  }
  mount(node, children);
  return node;
}

export function mount(parent, children) {
  const list = Array.isArray(children) ? children : [children];
  for (const c of list) {
    if (c == null || c === false) continue;
    parent.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
  }
  return parent;
}

export function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); return node; }

export function on(node, evt, handler, opts) { node.addEventListener(evt, handler, opts); return () => node.removeEventListener(evt, handler, opts); }

/* Build an SVG element (createElement won't set the SVG namespace). */
const SVGNS = 'http://www.w3.org/2000/svg';
export function svgEl(tag, attrs = {}, children = []) {
  const node = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'text') node.textContent = v;
    else node.setAttribute(k, String(v));
  }
  mount(node, children);
  return node;
}

/* Read query-string params as a plain object. */
export function params() { return Object.fromEntries(new URLSearchParams(location.search)); }
