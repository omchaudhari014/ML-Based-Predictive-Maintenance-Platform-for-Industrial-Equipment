/* mock/mock-api.js — the DEMO SCORING surrogate.

   ══════════════════════════════════════════════════════════════════════════
   READ THIS FIRST — what this file is, and what it is NOT.
   ══════════════════════════════════════════════════════════════════════════

   This module stands in for a backend that does not exist yet. In production,
   per-record risk, SHAP explanations and model selection come from a trained
   Python pipeline (§29). Until that backend is wired in, every "prediction"
   on screen is produced HERE, by a transparent, documented surrogate — never a
   pre-baked answer key, and never a real model.

   Three honesty rules govern this file:

   1. THE SCORES ARE DERIVED FROM THE USER'S OWN DATA. The surrogate reads the
      real column statistics the profiler measured from the uploaded CSV and
      scores each real row. An uploaded file is NEVER shown demo numbers from
      demo-data.json — those illustrative model-comparison metrics are the only
      thing read from disk, and they are clearly labelled as benchmark figures.

   2. THE METHOD IS FULLY DOCUMENTED. The scorer is a logistic function over
      z-scored sensor deviations with a fixed, visible weight vector. Anyone can
      read the weights below and reproduce any score by hand. There is no hidden
      lookup, no randomness, no "magic number" tuned to a specific machine.

   3. IT IS LABELLED EVERYWHERE. Every result carries scoringNote / mode:'mock',
      and the UI shows a persistent DEMO SCORING badge. Nothing here may be read
      as trained-model output.

   This is the ONLY file in the app permitted to import demo-data.json or to
   compute a risk number. No UI file scatters ML numbers (§ master prompt). */

import { parseCSV, toObjects, toNumber } from '../js/util/csv.js';

/* Where the surrogate looks for each physical quantity, by fuzzy column name.
   We resolve against the ACTUAL headers of the uploaded file, so a dataset
   that names torque "Torque [Nm]" or just "torque" both resolve correctly. */
const SENSOR_MATCHERS = {
  airTemp:      /air.*temp/i,
  processTemp:  /process.*temp/i,
  rotSpeed:     /rot.*speed|rpm|speed/i,
  torque:       /torque/i,
  toolWear:     /tool.*wear|wear/i,
};

/* The surrogate's weight vector — the heart of the "why". Each weight is the
   signed influence of a +1σ deviation of that sensor on the failure logit.
   Positive raises predicted risk, negative lowers it. These encode ordinary
   machining physics and are deliberately legible:
     · torque, tool wear   → strong positive (mechanical overstrain, wear-out)
     · process temperature → positive       (heat not being carried away)
     · air temperature     → small positive
     · rotational speed    → negative        (higher speed at equal torque means
                                              lower cutting load per revolution)
   Change a weight here and every explanation in the app changes with it — there
   is nowhere else risk is decided. */
const WEIGHTS = {
  torque:      1.15,
  toolWear:    0.95,
  processTemp: 0.65,
  airTemp:     0.20,
  rotSpeed:   -0.45,
};

/* Sensor → human label and the factor key the component map keys off. */
const SENSOR_LABELS = {
  torque:      'Torque',
  toolWear:    'Tool wear',
  processTemp: 'Process temperature',
  airTemp:     'Air temperature',
  rotSpeed:    'Rotational speed',
};

/* Logistic calibration. stress = Σ wᵢ·zᵢ is centred near 0 for an average row;
   a and b map it into a probability with a sensible base rate. b is negative so
   a perfectly average machine sits well below the decision threshold. */
const LOGIT_SCALE = 1.0;   // a
const LOGIT_BIAS  = -2.15; // b  → sigmoid(-2.15) ≈ 0.10 base rate for an average row

/* Risk-level thresholds on the probability. Documented and fixed (§ master). */
const RISK_THRESHOLDS = { critical: 0.75, high: 0.45, medium: 0.20 };

/* The decision threshold. At or above this probability the surrogate CLAIMS a
   predicted failure — it names a specific failure mode, a probable inspection
   area, and a consequence/recommendation. Below it, no failure is claimed (the
   record still carries a probability, a risk level and its contributing factors,
   but calling a low/medium score a "failure" would overstate it).

   This single rule keeps the whole product coherent: "predicted failures" =
   records with a claimed mode = high + critical count = the failure-distribution
   total. They can never disagree, because they are all the same set. */
const DECISION_THRESHOLD = RISK_THRESHOLDS.high; // 0.45

const sigmoid = (x) => 1 / (1 + Math.exp(-x));

function riskLevelFor(p) {
  if (p >= RISK_THRESHOLDS.critical) return 'critical';
  if (p >= RISK_THRESHOLDS.high) return 'high';
  if (p >= RISK_THRESHOLDS.medium) return 'medium';
  return 'low';
}

/* Resolve which real column holds each sensor, using the profile's column list.
   Returns { sensorKey: { name, mean, std } } for every sensor we could find. */
function resolveSensors(profile) {
  const numericByName = new Map(
    profile.columns.filter((c) => c.kind === 'numeric').map((c) => [c.name, c]),
  );
  const resolved = {};
  for (const [sensor, re] of Object.entries(SENSOR_MATCHERS)) {
    // First numeric column whose name matches, that has a usable spread.
    for (const [name, col] of numericByName) {
      if (re.test(name) && col.std > 0) {
        resolved[sensor] = { name, mean: col.mean, std: col.std };
        break;
      }
    }
  }
  return resolved;
}

/* AI4I-style failure-mode attribution. Given the z-scores and the raw values,
   decide the single most likely mode. This mirrors the physical rules used to
   label the reference dataset, so the mode agrees with the leading factor.
   Returns one of TWF/HDF/PWF/OSF/none (RNF is reserved for the ground-truth
   label only and is never predicted by the surrogate). */
function predictMode(z, vals) {
  const hot = (z.processTemp ?? 0);
  const wear = (z.toolWear ?? 0);
  const torque = (z.torque ?? 0);
  const speed = (z.rotSpeed ?? 0);

  // Overstrain: high torque AND high wear together — the compound stress case.
  if (torque > 1.0 && wear > 0.6) return 'OSF';
  // Tool wear: wear dominant and advanced.
  if (wear > 1.2 && wear >= torque) return 'TWF';
  // Heat dissipation: process temperature elevated with low airflow proxy.
  if (hot > 1.0 && speed < 0) return 'HDF';
  // Power: torque high while speed is unusually low or high (off the safe band).
  if (torque > 1.1 && Math.abs(speed) > 1.0) return 'PWF';
  // Otherwise no specific mode.
  return 'none';
}

/* Build the signed contribution list (the SHAP-style "why"). Each contribution
   is wᵢ·zᵢ; we normalise the magnitudes to signed shares of the total absolute
   contribution so the bars read as percentages that sum to 100% in magnitude.
   Sorted by absolute contribution, strongest first. */
function contributionsFor(z) {
  const raw = [];
  for (const sensor of Object.keys(WEIGHTS)) {
    if (z[sensor] == null) continue;
    raw.push({ sensor, value: WEIGHTS[sensor] * z[sensor] });
  }
  const totalAbs = raw.reduce((a, r) => a + Math.abs(r.value), 0) || 1;
  return raw
    .map((r) => ({
      feature: r.sensor,
      label: SENSOR_LABELS[r.sensor],
      contribution: r.value / totalAbs, // signed fraction in [-1, 1]
      direction: r.value >= 0 ? 'raises' : 'reduces',
    }))
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
}

/* Score one row → the frozen record contract. `obj` is the row as a name→value
   map; `sensors` is the resolved stats; `id`/`type` come from detected columns;
   `machineProfile`, `demoContent` supply the mapping and copy. */
function scoreRow(obj, sensors, ids, machineProfile, demoContent) {
  // z-score each resolved sensor from the dataset's own mean/std.
  const z = {};
  const values = {};
  for (const [sensor, stat] of Object.entries(sensors)) {
    const v = toNumber(obj[stat.name]);
    values[stat.name] = v;
    z[sensor] = v == null ? null : (v - stat.mean) / stat.std;
  }

  const stress = Object.keys(WEIGHTS).reduce(
    (sum, s) => sum + (z[s] == null ? 0 : WEIGHTS[s] * z[s]), 0,
  );
  const probability = sigmoid(LOGIT_SCALE * stress + LOGIT_BIAS);
  const riskLevel = riskLevelFor(probability);
  const predictedMode = predictMode(z, values);

  const factors = contributionsFor(z);
  const topFactor = factors[0] ? factors[0].label : null;

  // WHERE: mode maps to a component; if no mode, fall back to the top raising
  // factor's component. Deterministic — never random (§17).
  let inspectionArea = machineProfile.modeToComponent[predictedMode] ?? null;
  if (!inspectionArea && topFactor) {
    inspectionArea = machineProfile.factorToComponent[topFactor] ?? null;
  }
  const areaComp = machineProfile.components.find((c) => c.id === inspectionArea) || null;

  const content = demoContent[predictedMode] || demoContent.none;

  const idVal = ids.idCol ? obj[ids.idCol] : null;
  const typeVal = ids.typeCol ? obj[ids.typeCol] : null;

  return {
    id: idVal != null && String(idVal).trim() !== '' ? String(idVal).trim() : null,
    type: typeVal != null ? String(typeVal).trim() : null,
    typeLabel: typeVal != null ? String(typeVal).trim() : null,
    machineClass: machineProfile.id,
    probability,
    riskLevel,
    predictedMode,
    predictedModeLabel: machineProfile.modeLabels[predictedMode] || predictedMode,
    factors,
    topFactor,
    inspectionArea,
    inspectionAreaLabel: areaComp ? areaComp.label : null,
    consequence: content.consequence,
    recommendation: content.recommendation,
    consequenceChain: content.chain,
    values,
  };
}

/* Public: score a whole profiled dataset. `csvText` is the raw upload; `profile`
   is the profiler output; `machineProfile` is one profile from machine-profiles;
   `demoData` is demo-data.json. Returns { records, summary, scoringNote }.
   EVERY valid row up to the profiled record count is scored (§ "analyse every
   record"). No truncation happens here — the profiler already enforced the cap. */
export function scoreDataset(csvText, profile, machineProfile, demoData) {
  const objects = parseToObjects(csvText, profile);
  const sensors = resolveSensors(profile);
  const ids = {
    idCol: profile.detected.idCol,
    typeCol: profile.detected.typeCol,
  };

  const records = objects.map((obj, i) => {
    const rec = scoreRow(obj, sensors, ids, machineProfile, demoData.modeContent);
    // Guarantee a stable id even if the dataset has no ID column.
    if (!rec.id) rec.id = `row-${i + 1}`;
    return rec;
  });

  const summary = summarise(records);
  return {
    records,
    summary,
    resolvedSensors: Object.fromEntries(
      Object.entries(sensors).map(([k, v]) => [k, v.name]),
    ),
    scoringNote:
      'Demo scoring — a documented transparent surrogate (logistic function over ' +
      'standardised sensor deviations), not a trained model. See mock/mock-api.js.',
  };
}

/* Re-parse the raw CSV into row objects. We keep the raw text in the store and
   re-parse here rather than threading parsed rows through sessionStorage, so the
   scorer always works from the same bytes the profiler saw. profile.header is
   the fallback if a re-parse somehow yields no header. */
function parseToObjects(csvText, profile) {
  const { header, rows } = parseCSV(csvText);
  const head = header && header.length ? header : profile.header;
  return toObjects(head, rows);
}

/* Roll per-record risk up into the results-page summary counts. */
function summarise(records) {
  const s = { analysed: records.length, critical: 0, high: 0, medium: 0, low: 0, predictedFailures: 0 };
  for (const r of records) {
    s[r.riskLevel]++;
    if (r.predictedMode !== 'none') s.predictedFailures++;
  }
  return s;
}

/* Build the risk-distribution series (status-coloured bars). Fixed order. */
export function riskDistribution(summary) {
  return [
    { level: 'critical', label: 'Critical', count: summary.critical },
    { level: 'high', label: 'High', count: summary.high },
    { level: 'medium', label: 'Medium', count: summary.medium },
    { level: 'low', label: 'Low', count: summary.low },
  ];
}

/* Build the failure-mode distribution from scored records (predicted modes),
   in the fixed AI4I order, labelled from the machine profile. */
export function failureDistribution(records, machineProfile) {
  const order = ['TWF', 'HDF', 'PWF', 'OSF'];
  const counts = new Map(order.map((m) => [m, 0]));
  for (const r of records) {
    if (counts.has(r.predictedMode)) counts.set(r.predictedMode, counts.get(r.predictedMode) + 1);
  }
  return order.map((m) => ({
    mode: m,
    label: machineProfile.modeLabels[m] || m,
    count: counts.get(m),
  }));
}

/* Model comparison + DERIVED selection. The winner is chosen by reducing over
   the configured criterion key (default PR-AUC) — NEVER hard-coded to a name
   (§11). Change demo-data.json's selection.criterionKey and the winner changes
   with no code edit. */
export function selectModel(demoData) {
  const models = demoData.models.slice();
  const key = demoData.selection.criterionKey;
  const selected = models.reduce((best, m) => (m[key] > best[key] ? m : best), models[0]);
  return {
    models,
    selection: {
      criterion: demoData.selection.criterion,
      criterionKey: key,
      note: demoData.selection.note,
      classImbalanceNote: demoData.classImbalanceNote,
      selected: selected.name,
    },
  };
}

export const RISK_THRESHOLDS_DOC = RISK_THRESHOLDS;
export const WEIGHTS_DOC = WEIGHTS;
