/* store.js — the ONLY place page-to-page state is read or written.

   The product is a multi-page app with no framework. State handoff between
   pages goes through sessionStorage (cleared when the tab closes); the saved
   analysis history goes through localStorage (persists). Every key lives here
   behind a typed accessor so no page ever touches Web Storage directly and no
   key string is duplicated across files.

   Storage can throw — quota exceeded, private-mode denial, disabled cookies.
   Every write is quota-guarded and every read tolerates absent/corrupt JSON,
   so a storage failure degrades to "no data" and a friendly empty state,
   never a thrown page.

   IMPORTANT: nothing here fabricates data. The store only carries what the
   profiler measured (dataset, profile) and what the API produced (analysis).
   Demo scoring lives in mock/; the store is a dumb, honest courier. */

const SESSION_KEYS = {
  dataset: 'pdm.dataset',   // { name, size, text, isDemo, parsedAt } — raw upload metadata + CSV text
  profile: 'pdm.profile',   // the profiler.profile() output object
  analysis: 'pdm.analysis', // the api.runAnalysis() result (records + summary + models)
  selectedRecordId: 'pdm.selectedRecordId', // which record machine/diagnostic pages show
  currentMachine: 'pdm.currentMachine',
  lastPrediction: 'pdm.lastPrediction',
};
const HISTORY_KEY = 'pdm.history'; // localStorage — array of past-analysis summaries
const HISTORY_MAX = 25;

/* ---- low-level, failure-tolerant Web Storage helpers ------------------- */

function readJSON(storage, key) {
  try {
    const raw = storage.getItem(key);
    if (raw == null) return null;
    return JSON.parse(raw);
  } catch {
    return null; // absent, denied, or corrupt — treat as "nothing there"
  }
}

/* Returns true on success, false if the write was refused (quota/denial).
   Callers that persist large blobs (the CSV text) check the return value. */
function writeJSON(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function remove(storage, key) {
  try { storage.removeItem(key); } catch { /* ignore */ }
}

/* ---- dataset (raw upload) ---------------------------------------------- */

/* The dataset payload carries the raw CSV text so a later page could re-profile
   or re-score without a re-upload. CSV text for 1,000 rows is well under the
   ~5 MB sessionStorage budget, but we still guard the write and report failure
   so the caller can warn instead of silently losing the file. */
export function setDataset(dataset) {
  return writeJSON(sessionStorage, SESSION_KEYS.dataset, dataset);
}
export function getDataset() {
  return readJSON(sessionStorage, SESSION_KEYS.dataset);
}

/* ---- profile (descriptive stats) --------------------------------------- */

export function setProfile(profile) {
  return writeJSON(sessionStorage, SESSION_KEYS.profile, profile);
}
export function getProfile() {
  return readJSON(sessionStorage, SESSION_KEYS.profile);
}

/* ---- analysis (scored result) ------------------------------------------ */

export function setAnalysis(analysis) {
  return writeJSON(sessionStorage, SESSION_KEYS.analysis, analysis);
}
export function getAnalysis() {
  return readJSON(sessionStorage, SESSION_KEYS.analysis);
}

/* ---- selected record (machine / diagnostic pages) ---------------------- */

export function setSelectedRecordId(id) {
  return writeJSON(sessionStorage, SESSION_KEYS.selectedRecordId, id);
}
export function getSelectedRecordId() {
  return readJSON(sessionStorage, SESSION_KEYS.selectedRecordId);
}

/* Find a scored record in the current analysis by id — the machine and
   diagnostic pages resolve their subject through this, so the id contract
   lives in one place. Returns null if there is no analysis or no match. */
export function getRecordById(id) {
  const analysis = getAnalysis();
  if (!analysis || !Array.isArray(analysis.records)) return null;
  return analysis.records.find((r) => String(r.id) === String(id)) || null;
}

/* ---- clearing ---------------------------------------------------------- */

/* Wipe the in-flight dataset/profile/analysis (e.g. "start a new analysis").
   History is untouched — it lives in localStorage and survives on purpose. */
export function clearAnalysisFlow() {
  remove(sessionStorage, SESSION_KEYS.dataset);
  remove(sessionStorage, SESSION_KEYS.profile);
  remove(sessionStorage, SESSION_KEYS.analysis);
  remove(sessionStorage, SESSION_KEYS.selectedRecordId);
}

/* ---- history (localStorage) -------------------------------------------- */

/* A history entry is a SMALL summary, never the full record array — we keep
   at most HISTORY_MAX, newest first, so localStorage never balloons. */
export function getHistory() {
  const list = readJSON(localStorage, HISTORY_KEY);
  return Array.isArray(list) ? list : [];
}

export function saveHistory(entry) {
  const list = getHistory();
  // De-dupe by analysisId so re-visiting results doesn't stack duplicates.
  const filtered = list.filter((e) => e.analysisId !== entry.analysisId);
  filtered.unshift(entry);
  return writeJSON(localStorage, HISTORY_KEY, filtered.slice(0, HISTORY_MAX));
}

export function clearHistory() {
  remove(localStorage, HISTORY_KEY);
}

export function setCurrentMachine(machine) {
  return writeJSON(sessionStorage, SESSION_KEYS.currentMachine, machine);
}
export function getCurrentMachine() {
  return readJSON(sessionStorage, SESSION_KEYS.currentMachine);
}
export function setLastPrediction(prediction) {
  return writeJSON(sessionStorage, SESSION_KEYS.lastPrediction, prediction);
}
export function getLastPrediction() {
  return readJSON(sessionStorage, SESSION_KEYS.lastPrediction);
}
export function savePredictionHistory(entry) {
  const list = getHistory();
  const filtered = list.filter(e => e.analysisId !== entry.analysisId);
  filtered.unshift(entry);
  return writeJSON(localStorage, HISTORY_KEY, filtered.slice(0, HISTORY_MAX));
}
