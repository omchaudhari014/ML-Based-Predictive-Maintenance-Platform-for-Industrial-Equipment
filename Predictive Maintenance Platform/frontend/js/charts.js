/* charts.js — SVG chart primitives + risk gauges/pills.

   Every chart on every page is built here, so the dataviz rules are enforced in
   ONE place: one axis only, categorical hues in fixed order (never cycled),
   status colours reserved and always paired with a label, a legend for ≥2
   series, direct value labels, a table-view toggle as the documented relief for
   the sub-3:1 series colours, and a hover tooltip layer. The class names and SVG
   geometry match css/components.css and the component reference exactly.

   These functions return detached DOM nodes; the caller mounts them. Numbers are
   formatted through util/format.js so grouping/percent are consistent. */

import { el, svgEl, clear } from './util/dom.js';
import { int, num, pct } from './util/format.js';

/* ── ChartFrame ──────────────────────────────────────────────────────────────
   Wraps a plot + its table view and wires the [Table view] toggle. `plot` is the
   SVG node; `table` is the accessible table node; `legend` is an optional array
   of { label, color } swatches; `note` is optional foot text. */
let _frameSeq = 0;
export function chartFrame({ title, sub, legend, plot, table, note, shapLegend }) {
  const id = `cf-${++_frameSeq}`;
  const toggle = el('button', {
    class: 'chart-toggle', type: 'button', 'aria-pressed': 'false',
  }, 'Table view');

  const frame = el('div', { class: 'chart-frame', id }, [
    el('div', { class: 'chart-frame__head' }, [
      el('div', {}, [
        el('div', { class: 'chart-frame__title' }, title),
        sub ? el('div', { class: 'chart-frame__sub' }, sub) : null,
      ]),
      table ? toggle : null,
    ]),
    legend && legend.length
      ? el('div', { class: 'chart-frame__legend' }, legend.map((l) =>
          el('span', { class: 'legend-item' }, [
            el('span', { class: 'legend-item__swatch', style: `background:${l.color}` }),
            l.label,
          ])))
      : null,
    el('div', { class: 'chart-frame__plot' }, plot),
    table ? el('div', { class: 'chart-frame__table' }, table) : null,
    shapLegend
      ? el('div', { class: 'shap-legend' }, [
          el('span', {}, '◂ reduces predicted risk'),
          el('span', {}, 'raises predicted risk ▸'),
        ])
      : null,
    note
      ? el('div', { class: 'chart-frame__foot' }, [el('span', { class: 'chart-frame__note' }, note)])
      : null,
  ]);

  if (table) {
    toggle.addEventListener('click', () => {
      const on = frame.classList.toggle('is-table');
      toggle.setAttribute('aria-pressed', String(on));
      toggle.textContent = on ? 'Chart view' : 'Table view';
    });
  }
  return frame;
}

/* ── Hover tooltip layer ─────────────────────────────────────────────────────
   Attaches one tooltip to a plot and shows it while a hover target is hovered.
   `targets` is [{ node, title, rows:[[key,val]] }]. Positioned from the plot's
   bounding box so it works regardless of SVG coordinate quirks. */
function attachHover(plotNode, targets) {
  const tip = el('div', { class: 'tooltip', role: 'presentation' });
  tip.style.display = 'none';
  plotNode.appendChild(tip);

  const show = (t, evt) => {
    clear(tip);
    tip.appendChild(el('div', { class: 'tooltip__title' }, t.title));
    for (const [k, v] of t.rows) {
      tip.appendChild(el('div', { class: 'tooltip__row' }, [
        el('span', {}, k), el('span', { class: 'tooltip__val' }, v),
      ]));
    }
    tip.style.display = 'block';
    move(evt);
  };
  const move = (evt) => {
    const r = plotNode.getBoundingClientRect();
    let x = evt.clientX - r.left + 12;
    let y = evt.clientY - r.top + 12;
    // keep inside the plot
    const tr = tip.getBoundingClientRect();
    if (x + tr.width > r.width) x = r.width - tr.width - 4;
    if (y + tr.height > r.height) y = evt.clientY - r.top - tr.height - 8;
    tip.style.left = `${Math.max(0, x)}px`;
    tip.style.top = `${Math.max(0, y)}px`;
  };
  const hide = () => { tip.style.display = 'none'; };

  for (const t of targets) {
    t.node.addEventListener('pointerenter', (e) => show(t, e));
    t.node.addEventListener('pointermove', move);
    t.node.addEventListener('pointerleave', hide);
  }
}

/* ── Horizontal bar chart (categorical or status) ────────────────────────────
   items: [{ label, value, cls, display }]  cls = a mark-* class.
   `max` sets the scale; `unit`/`fmt` control value labels and the table. */
export function horizontalBars({ items, max, fmt = int, width = 420, labelW = 118,
  ariaLabel, tableHead = ['Category', 'Value'] }) {
  const rowH = 30, barH = 14, top = 7;
  const plotL = labelW;
  const plotR = width - 44;
  const plotW = plotR - plotL;
  const scaleMax = max || Math.max(1, ...items.map((d) => d.value));
  const height = items.length * rowH + 30;
  const baseY = top + items.length * rowH - (rowH - barH);

  const svg = svgEl('svg', {
    class: 'chart-svg', viewBox: `0 0 ${width} ${height}`, role: 'img',
    'aria-label': ariaLabel || 'Bar chart',
  });

  // gridlines at quarter fractions
  const grid = svgEl('g', { class: 'chart-grid' });
  for (const f of [0.25, 0.5, 0.75, 1]) {
    const x = plotL + f * plotW;
    grid.appendChild(svgEl('line', { x1: x, y1: top - 3, x2: x, y2: baseY }));
  }
  svg.appendChild(grid);

  const hoverTargets = [];
  items.forEach((d, i) => {
    const y = top + i * rowH;
    const w = Math.max(0, (d.value / scaleMax) * plotW);
    const cat = svgEl('text', { class: 'chart-cat-label', x: 0, y: y + 10 }); cat.textContent = d.label; svg.appendChild(cat);
    if (w > 0) svg.appendChild(svgEl('rect', { class: `chart-bar ${d.cls}`, x: plotL, y, width: w, height: barH }));
    const vl = svgEl('text', { class: 'chart-value-label', x: plotL + w + 6, y: y + 10 });
    vl.textContent = d.display != null ? d.display : fmt(d.value);
    svg.appendChild(vl);

    // full-row transparent hover target
    const ht = svgEl('rect', { class: 'chart-hover-target', x: plotL, y: y - 2, width: plotW, height: rowH - 4 });
    svg.appendChild(ht);
    hoverTargets.push({ node: ht, title: d.label, rows: [['Value', d.display != null ? d.display : fmt(d.value)]] });
  });

  // baseline + ticks
  svg.appendChild(svgEl('line', { class: 'chart-baseline', x1: plotL, y1: top - 3, x2: plotL, y2: baseY }));
  const tickY = height - 10;
  const t0 = svgEl('text', { class: 'chart-tick', x: plotL, y: tickY }); t0.textContent = fmt(0); svg.appendChild(t0);
  const tm = svgEl('text', { class: 'chart-tick', x: plotL + plotW / 2, y: tickY, 'text-anchor': 'middle' }); tm.textContent = fmt(scaleMax / 2); svg.appendChild(tm);
  const tM = svgEl('text', { class: 'chart-tick', x: plotR, y: tickY, 'text-anchor': 'middle' }); tM.textContent = fmt(scaleMax); svg.appendChild(tM);

  const table = buildTable(tableHead, items.map((d) => [d.label, d.display != null ? d.display : fmt(d.value)]));
  return { svg, table, hoverTargets };
}

/* ── Diverging bar chart (SHAP-style contributions) ──────────────────────────
   items: [{ label, contribution }] where contribution is a signed fraction.
   Colours: by magnitude tier (0.75 / 0.375 thresholds) and sign. */
export function divergingBars({ items, width = 420, labelW = 96, ariaLabel }) {
  const rowH = 28, barH = 13, top = 10;
  const centerX = labelW + (width - labelW - 20) / 2;
  const halfW = Math.min(centerX - labelW - 6, width - centerX - 46);
  const maxAbs = Math.max(1e-6, ...items.map((d) => Math.abs(d.contribution)));
  const height = items.length * rowH + 14;

  const svg = svgEl('svg', {
    class: 'chart-svg', viewBox: `0 0 ${width} ${height}`, role: 'img',
    'aria-label': ariaLabel || 'Feature contributions',
  });
  svg.appendChild(svgEl('line', { class: 'chart-zeroline', x1: centerX, y1: top - 4, x2: centerX, y2: height - 4 }));

  const tierClass = (c) => {
    const r = Math.abs(c) / maxAbs;
    const tier = r >= 0.75 ? 3 : r >= 0.375 ? 2 : 1;
    return c >= 0 ? `mark-div-pos-${tier}` : `mark-div-neg-${tier}`;
  };

  const hoverTargets = [];
  items.forEach((d, i) => {
    const y = top + i * rowH;
    const w = Math.abs(d.contribution) / maxAbs * halfW;
    const lbl = svgEl('text', { class: 'chart-cat-label', x: 0, y: y + 10 }); lbl.textContent = d.label; svg.appendChild(lbl);
    const x = d.contribution >= 0 ? centerX : centerX - w;
    svg.appendChild(svgEl('rect', { class: `chart-bar ${tierClass(d.contribution)}`, x, y, width: Math.max(1, w), height: barH }));
    const disp = pctSignedLocal(d.contribution);
    const vl = svgEl('text', { class: 'chart-value-label', y: y + 10 });
    if (d.contribution >= 0) { vl.setAttribute('x', centerX + w + 6); }
    else { vl.setAttribute('x', centerX - w - 6); vl.setAttribute('text-anchor', 'end'); }
    vl.textContent = disp; svg.appendChild(vl);

    const ht = svgEl('rect', { class: 'chart-hover-target', x: labelW, y: y - 2, width: width - labelW, height: rowH - 4 });
    svg.appendChild(ht);
    hoverTargets.push({ node: ht, title: d.label, rows: [['Contribution', disp], ['Direction', d.contribution >= 0 ? 'Raises risk' : 'Reduces risk']] });
  });

  const table = buildTable(['Feature', 'Contribution', 'Direction'],
    items.map((d) => [d.label, pctSignedLocal(d.contribution), d.contribution >= 0 ? 'Raises risk' : 'Reduces risk']));
  return { svg, table, hoverTargets };
}

/* ── Line chart (ROC / PR curves) ─────────────────────────────────────────────
   series: [{ name, cls, points:[[x,y]] }] with x,y in [0,1]. Optional dashed
   reference diagonal. One y-axis only. */
export function lineChart({ series, xLabel, yLabel, reference, width = 420, height = 210, ariaLabel }) {
  const plotL = 46, plotR = 270, plotT = 20, plotB = 164;
  const X = (x) => plotL + x * (plotR - plotL);
  const Y = (y) => plotB - y * (plotB - plotT);

  const svg = svgEl('svg', {
    class: 'chart-svg', viewBox: `0 0 ${width} ${height}`, role: 'img',
    'aria-label': ariaLabel || 'Line chart',
  });

  const grid = svgEl('g', { class: 'chart-grid' });
  for (const f of [0.25, 0.5, 0.75, 1]) {
    const y = Y(f);
    grid.appendChild(svgEl('line', { x1: plotL, y1: y, x2: plotR, y2: y }));
  }
  svg.appendChild(grid);

  if (reference) {
    svg.appendChild(svgEl('line', { class: 'chart-reference', x1: X(0), y1: Y(0), x2: X(1), y2: Y(1) }));
    const rl = svgEl('text', { class: 'chart-tick', x: X(0.62), y: Y(0.5) }); rl.textContent = 'chance'; svg.appendChild(rl);
  }

  const hoverTargets = [];
  series.forEach((s, si) => {
    const d = s.points.map((p, i) => `${i === 0 ? 'M' : 'L'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join(' ');
    svg.appendChild(svgEl('path', { class: `chart-line ${s.cls}`, d }));
    const lbl = svgEl('text', { class: 'chart-series-label', x: plotR + 6, y: plotT + 4 + si * 15 }); lbl.textContent = s.name; svg.appendChild(lbl);
    // hover markers at each vertex
    s.points.forEach((p) => {
      const m = svgEl('circle', { class: `chart-marker ${s.cls}`, cx: X(p[0]), cy: Y(p[1]), r: 4, fill: 'var(--surface)' });
      m.style.stroke = 'currentColor';
      svg.appendChild(m);
      hoverTargets.push({ node: m, title: s.name, rows: [[xLabel || 'x', num(p[0], 2)], [yLabel || 'y', num(p[1], 2)]] });
    });
  });

  svg.appendChild(svgEl('line', { class: 'chart-baseline', x1: plotL, y1: plotB, x2: plotR, y2: plotB }));
  svg.appendChild(svgEl('line', { class: 'chart-baseline', x1: plotL, y1: plotT, x2: plotL, y2: plotB }));
  if (xLabel) { const t = svgEl('text', { class: 'chart-axis-label', x: plotL, y: plotB + 20 }); t.textContent = `${xLabel} →`; svg.appendChild(t); }
  if (yLabel) { const t = svgEl('text', { class: 'chart-axis-label', x: 10, y: (plotT + plotB) / 2, transform: `rotate(-90 10 ${(plotT + plotB) / 2})` }); t.textContent = `${yLabel} →`; svg.appendChild(t); }

  return { svg, hoverTargets };
}

/* ── Confusion matrix (sequential) ───────────────────────────────────────────
   m: { tp, fp, fn, tn }. One hue, light→dark by cell count. */
export function confusionMatrix({ tp, fp, fn, tn, width = 360, height = 190 }) {
  const svg = svgEl('svg', {
    class: 'chart-svg matrix', viewBox: `0 0 ${width} ${height}`, style: 'max-width:360px', role: 'img',
    'aria-label': `Confusion matrix: ${tn} true negatives, ${fp} false positives, ${fn} false negatives, ${tp} true positives.`,
  });
  const maxV = Math.max(1, tp, fp, fn, tn);
  const seq = (v) => {
    const r = v / maxV;
    if (r >= 0.85) return { bg: 'var(--seq-700)', ink: 'var(--surface)' };
    if (r >= 0.6) return { bg: 'var(--seq-500)', ink: 'var(--surface)' };
    if (r >= 0.35) return { bg: 'var(--seq-300)', ink: 'var(--ink)' };
    if (r >= 0.12) return { bg: 'var(--seq-200)', ink: 'var(--ink)' };
    return { bg: 'var(--seq-100)', ink: 'var(--ink)' };
  };

  const addLabel = (x, y, txt, cls = 'chart-tick', anchor) => {
    const t = svgEl('text', { class: cls, x, y, ...(anchor ? { 'text-anchor': anchor } : {}) }); t.textContent = txt; svg.appendChild(t);
  };
  const pt = svgEl('text', { class: 'chart-axis-label', x: 110, y: 12 }); pt.textContent = 'Predicted'; svg.appendChild(pt);
  addLabel(150, 30, 'No failure', 'chart-tick', 'middle');
  addLabel(250, 30, 'Failure', 'chart-tick', 'middle');
  const at = svgEl('text', { class: 'chart-axis-label', x: 8, y: 110, transform: 'rotate(-90 8 110)' }); at.textContent = 'Actual'; svg.appendChild(at);
  addLabel(96, 72, 'No failure', 'chart-tick', 'end');
  addLabel(96, 142, 'Failure', 'chart-tick', 'end');

  const cell = (x, y, v) => {
    const c = seq(v);
    svg.appendChild(svgEl('rect', { class: 'matrix__cell', x, y, width: 92, height: 60, fill: c.bg }));
    const t = svgEl('text', { class: 'matrix__cell-label', x: x + 46, y: y + 35, 'text-anchor': 'middle', fill: c.ink }); t.textContent = int(v); svg.appendChild(t);
  };
  cell(104, 40, tn); cell(204, 40, fp); cell(104, 110, fn); cell(204, 110, tp);

  const table = buildTable(['Outcome', 'Count'], [
    ['True negative', int(tn)], ['False positive', int(fp)],
    ['False negative — a missed failure', int(fn)], ['True positive', int(tp)],
  ]);
  return { svg, table };
}

/* ── Risk arc meter ──────────────────────────────────────────────────────────
   probability in [0,1], level = critical|high|medium|low. Semicircle arc,
   length π·55 ≈ 172.79; dash = fraction · length. No needle, no glow. */
const ARC_LEN = Math.PI * 55;
export function riskArcMeter(probability, level, caption = 'Failure Risk Score') {
  const dash = (Math.max(0, Math.min(1, probability)) * ARC_LEN).toFixed(1);
  const figure = el('div', { class: 'risk-meter__figure' });
  const svg = svgEl('svg', { width: 150, height: 92, viewBox: '0 0 150 92', 'aria-hidden': 'true' }, [
    svgEl('path', { class: 'risk-meter__arc-track', d: 'M 20 82 A 55 55 0 1 1 130 82', 'stroke-width': 10 }),
    svgEl('path', { class: 'risk-meter__arc-value', d: 'M 20 82 A 55 55 0 1 1 130 82', 'stroke-width': 10, 'stroke-dasharray': `${dash} ${(ARC_LEN).toFixed(1)}` }),
  ]);
  figure.appendChild(svg);
  figure.appendChild(el('div', { class: 'risk-meter__value' }, [
    el('div', { class: 'risk-meter__pct', html: `${num(probability * 100, 1)}` }),
  ]));
  return el('div', { class: 'risk-meter', dataset: { risk: level } }, [
    figure,
    el('div', { class: 'cluster', style: 'justify-content:center' }, [riskPill(level, { lg: true })]),
    el('p', { class: 'risk-meter__caption' }, caption),
  ]);
}

/* ── Risk pill ───────────────────────────────────────────────────────────────
   Colour + shape + label — never colour alone. `withRisk` appends " risk". */
const LEVEL_LABEL = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low', neutral: 'Not assessed' };
export function riskPill(level, { lg = false, withRisk = false } = {}) {
  const label = (LEVEL_LABEL[level] || 'Not assessed') + (withRisk && level !== 'neutral' ? ' risk' : '');
  return el('span', { class: `pill pill--${level}${lg ? ' pill--lg' : ''}` }, [
    el('span', { class: 'pill__dot', 'aria-hidden': 'true' }),
    label,
  ]);
}

/* Map a mark class for a categorical series index (fixed order, never cycled). */
export const SERIES_CLASS = ['mark-s1', 'mark-s2', 'mark-s3', 'mark-s4'];
export const SERIES_STROKE = ['stroke-s1', 'stroke-s2', 'stroke-s3', 'stroke-s4'];
export const SERIES_COLOR = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)'];

/* Status mark class for a risk level. */
export const RISK_MARK = { critical: 'mark-critical', high: 'mark-high', medium: 'mark-medium', low: 'mark-low' };

/* ── small helpers ──────────────────────────────────────────────────────────*/

function buildTable(head, rows) {
  const thead = el('thead', {}, el('tr', {}, head.map((h, i) =>
    el('th', { scope: 'col', ...(i > 0 ? { class: 'num' } : {}) }, h))));
  const tbody = el('tbody', {}, rows.map((r) =>
    el('tr', {}, r.map((c, i) => el('td', i > 0 ? { class: 'num' } : {}, String(c))))));
  return el('table', { class: 'table' }, [thead, tbody]);
}

/* Local signed-percent for contributions expressed as fractions in [-1,1]. */
function pctSignedLocal(fraction) {
  const v = fraction;
  const s = v >= 0 ? '+' : '−';
  return s + Math.abs(v).toFixed(3);
}

/* Convenience: build a frame from a primitive result and wire its hover. */
export function frameFrom(primitive, opts) {
  const frame = chartFrame({ ...opts, plot: primitive.svg, table: primitive.table });
  if (primitive.hoverTargets && primitive.hoverTargets.length) {
    const plot = frame.querySelector('.chart-frame__plot');
    attachHover(plot, primitive.hoverTargets);
  }
  return frame;
}
