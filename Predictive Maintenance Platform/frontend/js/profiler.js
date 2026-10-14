/* profiler.js — REAL descriptive profiling of an uploaded CSV, in the browser.

   This is the only place the user's actual file is inspected. It computes
   ONLY descriptive statistics — counts, missingness, duplicates, IQR outliers,
   type inference, class balance, per-column summaries. There is NO model
   fitting, NO scoring, NO SHAP here. Those are server-side concerns (§29), and
   the mock surrogate that stands in for them lives in mock/, never here.

   The output shape is the contract every downstream page reads. Keep it stable.

   RECORD LIMIT: MAX_RECORDS is a hard rule. We never silently truncate — the
   caller is expected to reject an over-limit file and show the real count. */

import { parseCSV, toNumber, isMissing } from './util/csv.js';

export const MAX_RECORDS = 1000;

/* Column-name heuristics. Deliberately conservative: we detect by name, and a
   miss is reported as "not detected" rather than guessed wrong. */
const ID_PATTERNS = [/^udi$/i, /\bid\b/i, /machine.?id/i, /unit.?id/i, /equipment.?id/i, /serial/i, /product.?id/i];
const TIME_PATTERNS = [/time/i, /date/i, /timestamp/i, /\bts\b/i];
const TARGET_PATTERNS = [/machine\s*failure/i, /^failure$/i, /\btarget\b/i, /\blabel\b/i, /fail/i, /\bfault\b/i];
const TYPE_PATTERNS = [/^type$/i, /machine.?type/i, /category/i, /variant/i, /class$/i];
/* AI4I per-mode failure flags, so we can build a failure-mode distribution. */
const MODE_COLUMNS = ['TWF', 'HDF', 'PWF', 'OSF', 'RNF'];
const MODE_LABELS = {
  TWF: 'Tool wear (TWF)', HDF: 'Heat dissipation (HDF)', PWF: 'Power (PWF)',
  OSF: 'Overstrain (OSF)', RNF: 'Random (RNF)',
};

function firstMatch(header, patterns) {
  for (const p of patterns) {
    const hit = header.find((h) => p.test(h));
    if (hit) return hit;
  }
  return null;
}

function quantile(sortedNums, q) {
  const n = sortedNums.length;
  if (n === 0) return null;
  const pos = (n - 1) * q;
  const lo = Math.floor(pos), hi = Math.ceil(pos);
  if (lo === hi) return sortedNums[lo];
  return sortedNums[lo] + (sortedNums[hi] - sortedNums[lo]) * (pos - lo);
}

/* Build a per-column summary and decide numeric vs categorical. A column is
   numeric when >= 80% of its non-missing values parse as numbers. */
function summarizeColumn(name, values) {
  const total = values.length;
  let missing = 0;
  const nums = [];
  const distinct = new Set();
  for (const v of values) {
    if (isMissing(v)) { missing++; continue; }
    distinct.add(String(v).trim());
    const n = toNumber(v);
    if (n !== null) nums.push(n);
  }
  const present = total - missing;
  const numericShare = present > 0 ? nums.length / present : 0;
  const isNumeric = numericShare >= 0.8 && present > 0;

  const col = {
    name,
    kind: isNumeric ? 'numeric' : 'categorical',
    missing,
    missingPct: total > 0 ? missing / total : 0,
    distinct: distinct.size,
    constant: distinct.size <= 1,
  };

  if (isNumeric && nums.length) {
    const sorted = nums.slice().sort((a, b) => a - b);
    const q1 = quantile(sorted, 0.25);
    const q3 = quantile(sorted, 0.75);
    const iqr = q3 - q1;
    const lo = q1 - 1.5 * iqr, hi = q3 + 1.5 * iqr;
    let outliers = 0;
    let sum = 0;
    for (const n of nums) { sum += n; if (n < lo || n > hi) outliers++; }
    col.min = sorted[0];
    col.max = sorted[sorted.length - 1];
    col.mean = sum / nums.length;
    // Sample standard deviation — a descriptive statistic (no model involved).
    // Downstream demo scoring z-scores each sensor using this; exposing it here
    // keeps that computation transparent and out of any ML path.
    let ss = 0; for (const n of nums) ss += (n - col.mean) ** 2;
    col.std = nums.length > 1 ? Math.sqrt(ss / (nums.length - 1)) : 0;
    col.median = quantile(sorted, 0.5);
    col.q1 = q1; col.q3 = q3;
    col.outliers = outliers;
  } else {
    // Top categories for a categorical column.
    const counts = new Map();
    for (const v of values) { if (isMissing(v)) continue; const k = String(v).trim(); counts.set(k, (counts.get(k) || 0) + 1); }
    col.top = Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([value, count]) => ({ value, count }));
    col.outliers = 0;
  }
  return col;
}

/* Count exact duplicate rows (all cells equal). */
function countDuplicates(rows) {
  const seen = new Set();
  let dup = 0;
  for (const r of rows) {
    const key = r.join('');
    if (seen.has(key)) dup++; else seen.add(key);
  }
  return dup;
}

/* The main entry point. Returns a rich profile object, or throws a friendly
   Error the caller can render in place. `text` is the raw file contents. */
export function profile(text, meta = {}) {
  const { header, rows, errors } = parseCSV(text);

  if (!header.length) throw new Error('This file has no header row. A CSV with column names in the first row is required.');
  if (!rows.length) throw new Error('This file has a header but no data rows.');

  // Detect key roles.
  const idCol = firstMatch(header, ID_PATTERNS);
  const timeCol = firstMatch(header, TIME_PATTERNS);
  const targetCol = firstMatch(header, TARGET_PATTERNS);
  const typeCol = firstMatch(header, TYPE_PATTERNS);

  // Per-column data.
  const columnValues = header.map((_, i) => rows.map((r) => r[i]));
  const columns = header.map((name, i) => summarizeColumn(name, columnValues[i]));

  const numericCols = columns.filter((c) => c.kind === 'numeric');
  const categoricalCols = columns.filter((c) => c.kind === 'categorical');

  // Missing / duplicate / outlier / constant totals across the sheet.
  const totalMissing = columns.reduce((a, c) => a + c.missing, 0);
  const totalOutliers = numericCols.reduce((a, c) => a + (c.outliers || 0), 0);
  const constantCols = columns.filter((c) => c.constant).map((c) => c.name);
  const duplicates = countDuplicates(rows);

  // Distinct machine IDs (if an ID column exists).
  let idCount = null;
  if (idCol) { const idx = header.indexOf(idCol); idCount = new Set(rows.map((r) => r[idx]).filter((v) => !isMissing(v))).size; }

  // Class balance from the target column.
  let classBalance = null;
  if (targetCol) {
    const idx = header.indexOf(targetCol);
    const counts = new Map();
    for (const r of rows) { const v = String(r[idx]).trim(); if (isMissing(v)) continue; counts.set(v, (counts.get(v) || 0) + 1); }
    const entries = Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
    if (entries.length >= 2) {
      // Positive = the smaller class (the failure). Map common encodings to labels.
      const [big, small] = [entries[0], entries[entries.length - 1]];
      classBalance = {
        classes: entries.map(([value, count]) => ({ value, count })),
        majority: { value: big[0], count: big[1] },
        minority: { value: small[0], count: small[1] },
        ratio: small[1] > 0 ? big[1] / small[1] : Infinity,
        imbalanced: small[1] > 0 ? big[1] / small[1] >= 5 : true,
      };
    } else if (entries.length === 1) {
      classBalance = { classes: entries.map(([value, count]) => ({ value, count })), singleClass: true };
    }
  }

  // Failure-mode distribution, if the AI4I mode flag columns are present.
  let failureModes = null;
  const presentModes = MODE_COLUMNS.filter((m) => header.includes(m));
  if (presentModes.length) {
    failureModes = presentModes.map((m) => {
      const idx = header.indexOf(m);
      const count = rows.reduce((a, r) => a + (toNumber(r[idx]) === 1 ? 1 : 0), 0);
      return { key: m, label: MODE_LABELS[m] || m, count };
    }).sort((a, b) => b.count - a.count);
  }

  return {
    source: { name: meta.name || 'dataset.csv', size: meta.size ?? null, parsedAt: meta.parsedAt || null },
    counts: {
      records: rows.length,
      features: header.length,
      numeric: numericCols.length,
      categorical: categoricalCols.length,
      idCount,
    },
    detected: { idCol, timeCol, targetCol, typeCol },
    quality: {
      missing: totalMissing,
      duplicates,
      outliers: totalOutliers,
      constantCols,
      invalid: 0, // reserved; the parser already coerces, so no invalid-type count yet
    },
    classBalance,
    failureModes,
    columns,
    header,
    parseErrors: errors,
  };
}

/* Readiness assessment as a transparent RULE LIST (§9) — no invented score.
   Each rule states its own verdict and reason; the overall status is derived. */
export function readiness(prof) {
  const rules = [];
  const q = prof.quality, c = prof.counts, cb = prof.classBalance;

  rules.push({
    key: 'records',
    pass: c.records > 0 && c.records <= MAX_RECORDS ? true : (c.records > MAX_RECORDS ? false : 'warn'),
    text: `Record count within the ${MAX_RECORDS.toLocaleString('en-US')} limit`,
    why: `${c.records.toLocaleString('en-US')} record(s) present.`,
  });
  rules.push({
    key: 'target',
    pass: !!prof.detected.targetCol,
    text: 'A target / failure column was detected',
    why: prof.detected.targetCol ? `Using "${prof.detected.targetCol}".` : 'No column matched a failure/target name; supervised evaluation will not be possible.',
  });
  rules.push({
    key: 'classes',
    pass: cb ? (cb.singleClass ? false : true) : false,
    text: 'At least two outcome classes are present',
    why: cb ? (cb.singleClass ? 'Only one class is present — nothing to distinguish.' : `${cb.classes.length} classes present.`) : 'No target column, so classes could not be counted.',
  });
  const missingShare = c.records * c.features > 0 ? q.missing / (c.records * c.features) : 0;
  rules.push({
    key: 'missing',
    pass: missingShare < 0.05 ? true : (missingShare < 0.2 ? 'warn' : false),
    text: 'Missing values below 5% of all cells',
    why: `${q.missing.toLocaleString('en-US')} missing cell(s) — ${(missingShare * 100).toFixed(1)}% of the sheet.`,
  });
  if (cb && cb.ratio && cb.imbalanced) {
    rules.push({
      key: 'imbalance',
      pass: 'warn',
      text: 'Class balance is suitable for accuracy alone',
      why: `Ratio ${cb.ratio === Infinity ? '∞' : cb.ratio.toFixed(1)} : 1 — strongly imbalanced, so evaluation will emphasise recall / F1 / PR-AUC over accuracy.`,
    });
  }
  if (q.duplicates > 0) {
    rules.push({
      key: 'duplicates',
      pass: 'warn',
      text: 'No duplicate rows',
      why: `${q.duplicates} duplicate row(s) will be dropped before analysis.`,
    });
  }

  // Overall: any hard fail -> not ready; else if any warn -> ready with attention.
  const anyFail = rules.some((r) => r.pass === false);
  const anyWarn = rules.some((r) => r.pass === 'warn');
  const status = anyFail ? 'blocked' : anyWarn ? 'attention' : 'ready';
  return { status, rules };
}
