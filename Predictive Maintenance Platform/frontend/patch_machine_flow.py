with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We need to import getRecord, getExplanation, getMachines
import_old = "import { getMachineById, getLastPrediction } from './js/api.js';"
import_new = "import { getMachineById, getLastPrediction, getRecord, getExplanation, getMachines } from './js/api.js';"
content = content.replace(import_old, import_new)

init_old = '''async function init() {
    const container = document.getElementById('content');
    const id = params().id;
    const compId = params().component;
    
    if (!id) {
      container.textContent = 'No ID provided.';
      return;
    }
    
    try {
      let machine;
      let prediction = null;
      let isOldMode = false;
      
      try {
        machine = await getMachineById(id);
        const last = getLastPrediction();
        if (last && last.machine_id === id) {
          prediction = last;
        }
      } catch (e) {'''
      
init_new = '''async function init() {
    const container = document.getElementById('content');
    const id = params().id;
    const recordId = params().recordId;
    let compId = params().component;
    
    if (!id && !recordId) {
      container.textContent = 'No ID provided.';
      return;
    }
    
    try {
      let machine;
      let prediction = null;
      let isOldMode = false;
      let shapFactors = null;
      
      try {
        if (recordId) {
          const rec = await getRecord(recordId);
          prediction = rec;
          // Find machine by family name
          const allMachines = await getMachines();
          machine = allMachines.find(m => m.name.includes(rec.features.Machine_Family) || rec.features.Machine_Family.includes(m.type_label) || m.id === 'cnc-001') || allMachines[0];
          
          // Get dynamic explanation
          const explainedRec = await getExplanation(recordId);
          shapFactors = explainedRec.explanation; // Assuming the backend returns explanation
          
          if (!compId && shapFactors && shapFactors.length > 0) {
            compId = shapFactors[0].area;
          }
          
          // Map backend prediction to expected format
          prediction.predicted_failure_mode = rec.failure_type || 'Anomaly';
          prediction.causes = ['Detected by ML model based on operational data pattern.'];
          prediction.consequences = ['Potential secondary damage to related assemblies.'];
          prediction.recommendations = [{ priority: 'high', action: 'Inspect ' + (shapFactors && shapFactors.length ? shapFactors[0].area_label : 'equipment') }];
          
        } else {
          machine = await getMachineById(id);
          const last = getLastPrediction();
          if (last && last.machine_id === id) {
            prediction = last;
          }
        }
      } catch (e) {'''
content = content.replace(init_old, init_new)

# Modify render to accept shapFactors and display them
render_old = "function render(container, machine, pred, compId, isOldMode) {"
render_new = "function render(container, machine, pred, compId, isOldMode, shapFactors) {"
content = content.replace("render(container, machine, prediction, compId, isOldMode);", "render(container, machine, prediction, compId, isOldMode, shapFactors);")
content = content.replace(render_old, render_new)

# Add SHAP factors to UI
shap_html = '''        causesHtml,
        risksHtml,
        
        (shapFactors && shapFactors.length > 0) ? el('div', { style: 'margin-top: var(--s-4);' }, [
          el('h4', {}, 'ML Feature Contributions (SHAP)'),
          el('div', { style: 'margin-top: var(--s-2); background: var(--surface-2); padding: var(--s-2); border-radius: var(--r-sm);' }, 
            shapFactors.map(f => el('div', { style: 'display: flex; justify-content: space-between; margin-bottom: 4px; border-bottom: 1px solid var(--surface-3); padding-bottom: 4px;' }, [
              el('span', {}, f.feature),
              el('span', { style: color: ; font-weight: bold; }, ${f.direction === 'raises' ? '+' : ''})
            ]))
          )
        ]) : null,
'''
content = content.replace("        causesHtml,\n        risksHtml,", shap_html)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)
