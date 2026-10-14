/* util/format.js — number, percent, date and byte formatting.
   Standardised on en-US grouping (the old prototype used en-IN and rendered
   132,695 as "1,32,695"). Every displayed number goes through here. */

const NF = new Intl.NumberFormat('en-US');
const NF1 = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const int = (n) => (Number.isFinite(n) ? NF.format(Math.round(n)) : '—');

export function num(n, dp = 2) {
  if (!Number.isFinite(n)) return '—';
  return new Intl.NumberFormat('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp }).format(n);
}

/* 0.912 -> "91%" (dp 0) or "91.2%" (dp 1). Input is a fraction in [0,1]. */
export function pct(fraction, dp = 0) {
  if (!Number.isFinite(fraction)) return '—';
  return (fraction * 100).toFixed(dp) + '%';
}

/* Signed percentage-point label for SHAP-style contributions: 0.42 -> "+42%". */
export function pctSigned(fraction, dp = 0) {
  if (!Number.isFinite(fraction)) return '—';
  const v = fraction * 100;
  const s = v >= 0 ? '+' : '−'; // real minus sign
  return s + Math.abs(v).toFixed(dp) + '%';
}

export function bytes(b) {
  if (!Number.isFinite(b)) return '—';
  if (b < 1024) return b + ' B';
  if (b < 1024 * 1024) return NF1.format(b / 1024) + ' KB';
  return NF1.format(b / (1024 * 1024)) + ' MB';
}

/* ISO-ish timestamp -> "2026-08-27 19:14". Accepts a Date, ms number, or ISO string. */
export function dateTime(input) {
  const d = input instanceof Date ? input : new Date(input);
  if (isNaN(d)) return '—';
  const p = (x) => String(x).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function dateOnly(input) {
  const d = input instanceof Date ? input : new Date(input);
  if (isNaN(d)) return '—';
  const p = (x) => String(x).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export const titleCase = (s) => String(s).replace(/\b\w/g, (c) => c.toUpperCase());
