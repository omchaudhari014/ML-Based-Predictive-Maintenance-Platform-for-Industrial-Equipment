/* api.js — the service seam. THE single boundary between the UI and "the model".
   This file communicates EXCLUSIVELY with the Flask backend.
*/

import { profile as profileText, readiness, MAX_RECORDS } from './profiler.js';
import * as store from './store.js';
import { saveAnalysisToHistory } from './firebase-module.js';

let MODE = 'live';

export function getMode() {
  return MODE;
}

let _machineProfilesPromise = null;

function loadMachineProfiles() {
  if (!_machineProfilesPromise) {
    _machineProfilesPromise = fetch('./assets/config/machine-profiles.json').then((r) => {
      if (!r.ok) throw new Error('Could not load the machine component map.');
      return r.json();
    });
  }
  return _machineProfilesPromise;
}

async function activeMachineProfile(typeId) {
  const cfg = await loadMachineProfiles();
  const id = typeId || cfg.defaultProfile;
  return cfg.profiles[id] || cfg.profiles[cfg.defaultProfile];
}

/* ── PROFILE ────────────────────────────────────────────────────────────────
   Profiles data client-side for immediate feedback. */
export async function profileDataset(input) {
  let text, name, size, isDemo = false, fileObj = null;
  let demoSize = input ? input.demoSize : null;

  if (input && input.demo) {
    isDemo = true;
    name = `demo-equipment-${demoSize || 1000}.csv`;
    const res = await fetch('./assets/data/demo-equipment-1000.csv');
    if (!res.ok) throw new Error('Could not load the demo dataset.');
    text = await res.text();
    
    // Slice if a specific size is requested
    if (demoSize) {
      const lines = text.split('\n');
      const header = lines[0];
      const body = lines.slice(1).filter(l => l.trim().length > 0);
      text = [header, ...body.slice(0, demoSize)].join('\n');
    }
    
    size = new Blob([text]).size;
  } else if (input instanceof File) {
    name = input.name;
    size = input.size;
    text = await input.text();
    fileObj = input;
  } else {
    throw new Error('No file was provided.');
  }

  const parsedAt = new Date().toISOString();
  const prof = profileText(text, { name, size, parsedAt });

  if (prof.counts.records > MAX_RECORDS) {
    const err = new Error(
      `This file contains ${prof.counts.records.toLocaleString('en-US')} records. ` +
      `The current limit is ${MAX_RECORDS.toLocaleString('en-US')}. No rows have been ` +
      `discarded — please supply a smaller file.`
    );
    err.code = 'RECORD_LIMIT';
    throw err;
  }

  const dataset = { name, size, text, isDemo, parsedAt, fileObj };
  store.setDataset(dataset);
  store.setProfile(prof);

  return { dataset, profile: prof, readiness: readiness(prof) };
}

// Compute Risk Distribution
function riskDistribution(summary) {
  return [
    { label: 'Normal / Low', level: 'low', count: summary.low },
    { label: 'Medium', level: 'medium', count: summary.medium },
    { label: 'High', level: 'high', count: summary.high },
    { label: 'Critical', level: 'critical', count: summary.critical }
  ];
}

// Compute Failure Distribution
function failureDistribution(records, machineProfile) {
  const modes = Object.keys(machineProfile.modeLabels).filter(k => k !== 'none');
  const dist = modes.map(m => ({ label: machineProfile.modeLabels[m], mode: m, count: 0 }));
  let noneCount = 0;
  for (const r of records) {
    if (!r.observedFailureMode || r.observedFailureMode === 'none') {
      noneCount++;
    } else {
      const entry = dist.find(d => d.mode === r.observedFailureMode);
      if (entry) entry.count++;
    }
  }
  return [
    { label: 'No failure predicted', mode: 'none', count: noneCount },
    ...dist.filter(d => d.count > 0).sort((a, b) => b.count - a.count)
  ];
}

/* ── RUN ANALYSIS ──────────────────────────────────────────────────────────── */
export async function runAnalysis(onStep = () => {}) {
  const dataset = store.getDataset();
  const prof = store.getProfile();
  if (!dataset || !prof) throw new Error('No dataset has been profiled yet. Upload a dataset first.');

  const step = (key, state) => onStep({ key, state });
  step('load', 'done');
  step('validate', 'done');
  step('preprocess', 'active');
  
  let formData = new FormData();
  const blob = new Blob([dataset.text], { type: 'text/csv' });
  formData.append('file', blob, dataset.name);
  
  const modelStrategy = sessionStorage.getItem('pdm.selectedModel') || 'auto';
  formData.append('model', modelStrategy);
  
  // POST to /api/analyze
  const res = await fetch('/api/analyze', {
    method: 'POST',
    body: formData
  });
  
  step('preprocess', 'done');
  step('features', 'done');
  step('compare', 'done');
  
  if (!res.ok) {
    const errJson = await res.json().catch(()=>({}));
    throw new Error(errJson.error || 'Backend analysis failed');
  }
  
  const analysis = await res.json();
  analysis.mode = 'live';
  
  // Derive frontend-specific chart structures
  const machineProfile = await activeMachineProfile();
  analysis.riskDistribution = riskDistribution(analysis.summary);
  analysis.failureDistribution = failureDistribution(analysis.records, machineProfile);
  
  store.setAnalysis(analysis);
  saveAnalysisToHistory(analysis);
  step('done', 'done');
  return analysis;
}

/* ── SIMULATE SCENARIO ─────────────────────────────────────────────────────── */
export async function simulateScenario(baselineValues, scenarioValues) {
  const modelStrategy = sessionStorage.getItem('pdm.selectedModel') || 'auto';
  const res = await fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseline: baselineValues, scenario: scenarioValues, model: modelStrategy })
  });
  if (!res.ok) throw new Error('Simulation failed');
  return await res.json();
}

/* ── EXPLANATION ───────────────────────────────────────────────────────────── */
export async function getExplanation(id) {
  const activeRecord = store.getRecordById(id);
  if (!activeRecord) throw new Error("Explanation requires the record to be in the active session.");
  
  // Make a real POST to /api/explain
  const res = await fetch('/api/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ values: activeRecord.features })
  });
  
  if (!res.ok) throw new Error("Explanation failed");
  const data = await res.json();
  
  // Merge explanation into record
  activeRecord.explanation = data.factors;
  activeRecord.expected_value = data.expected_value;
  return activeRecord;
}

/* ── READ-BACK GETTERS ─────────────────────────────────────────────────────── */
export function getResults() {
  return store.getAnalysis();
}

export function getRecord(id) {
  return store.getRecordById(id);
}

export async function getModelPerformance() {
  try {
    const res = await fetch('/api/model-info');
    if (res.ok) {
      const metrics = await res.json();
      return { models: metrics.models, selection: { selected: metrics.selected_model } };
    }
    throw new Error("Could not fetch model metrics");
  } catch (e) {
    throw new Error("Backend unavailable for model metrics");
  }
}

export async function getMachineProfile(typeId) {
  return activeMachineProfile(typeId);
}

export function getHistory() {
  return store.getHistory();
}

export function clearFlow() {
  store.clearAnalysisFlow();
}

// Fetch all machines
export async function getMachines() {
  const res = await fetch('/api/machines?limit=1000');
  if (!res.ok) throw new Error('Could not load machines');
  return (await res.json()).machines;
}

// Search machines
export async function searchMachines(query) {
  const res = await fetch(`/api/machines/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error('Search failed');
  return (await res.json()).machines;
}

// Get full machine record
export async function getMachineById(machineId) {
  const res = await fetch(`/api/machines/${machineId}`);
  if (!res.ok) throw new Error('Machine not found');
  return res.json();
}

// Run machine-specific prediction
export async function predictCondition(machineId, values) {
  const res = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ machine_id: machineId, values })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Prediction failed');
  }
  return res.json();
}
