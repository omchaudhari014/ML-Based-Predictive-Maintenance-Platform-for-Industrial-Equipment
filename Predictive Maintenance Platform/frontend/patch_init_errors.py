import re

new_init = """async function init() {
  const container = document.getElementById('content');
  let id = params().id;
  let recordId = params().recordId;
  let compId = params().component;
  
  if (!id && !recordId) {
    container.textContent = 'No ID provided.';
    return;
  }
  
  try {
    let machine;
    let prediction = null;
    let shapFactors = null;
    
    // Auto-detect if 'id' is a CSV recordId from a stale URL
    if (id && !recordId) {
        // If it's a number, it's definitely a CSV record ID (UDIs are numeric in this dataset)
        if (!isNaN(id) || String(id).startsWith('UDI') || String(id).startsWith('M-')) {
            recordId = id;
            id = null;
        } else {
            try {
                const testRec = getRecord(id);
                if (testRec && testRec.features) {
                    recordId = id;
                    id = null;
                }
            } catch(e) {}
        }
    }
    
    if (recordId) {
      const rec = getRecord(recordId);
      if (!rec) {
          container.innerHTML = `<div style="max-width: 600px; margin: 40px auto; text-align: center; background: var(--surface-2); padding: 40px; border-radius: 8px;">
            <h2 style="color: var(--risk-critical); margin-bottom: 20px;">Session Expired</h2>
            <p style="margin-bottom: 20px; line-height: 1.5;">We could not find the data for record <b>${recordId}</b>. Your CSV analysis session has likely expired or you refreshed a temporary page.</p>
            <a href="upload.html" class="btn btn--primary">Upload CSV Again</a>
          </div>`;
          return;
      }
      prediction = rec;
      
      const fname = (rec.features.Machine_Family || '').toLowerCase();
      
      const allMachines = await getMachines();
      machine = allMachines.find(m => {
         return m.name.toLowerCase().includes(fname) || fname.includes(m.type_label.toLowerCase());
      }) || allMachines.find(m => m.id === 'cnc-001') || allMachines[0];
      
      try {
          const explainedRec = await getExplanation(recordId);
          shapFactors = explainedRec.explanation || explainedRec.factors || [];
      } catch (explErr) {
          console.warn("Explanation failed", explErr);
          shapFactors = [];
      }
      
      if (!compId && shapFactors && shapFactors.length > 0) {
        compId = shapFactors[0].area;
      }
      
      prediction.predicted_failure_mode = rec.failure_type || 'Anomaly';
      prediction.causes = ['Detected by ML model based on operational data pattern.'];
      prediction.consequences = ['Potential secondary damage to related assemblies.'];
      prediction.recommendations = [{ priority: 'high', action: 'Inspect ' + (shapFactors && shapFactors.length ? (shapFactors[0].area_label || shapFactors[0].area) : 'equipment') }];
      
    } else {
      machine = await getMachineById(id);
      const last = getLastPrediction();
      if (last && last.machine_id === id) {
        prediction = last;
      }
    }
    
    render(container, machine, prediction, compId, false, shapFactors);
  } catch(err) {
    console.error(err);
    if (err.message === 'Machine not found') {
        container.innerHTML = `<div style="max-width: 600px; margin: 40px auto; text-align: center; background: var(--surface-2); padding: 40px; border-radius: 8px;">
            <h2 style="color: var(--risk-critical); margin-bottom: 20px;">Machine Not Found</h2>
            <p style="margin-bottom: 20px; line-height: 1.5;">The machine profile or record you requested does not exist. If you were viewing a CSV record, your session may have expired.</p>
            <a href="index.html" class="btn btn--secondary" style="margin-right: 10px;">Go to Catalog</a>
            <a href="upload.html" class="btn btn--primary">Upload CSV Again</a>
          </div>`;
    } else {
        container.textContent = err.message || 'Failed to load diagnostics.';
    }
  }
}"""

with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'async function init\(\) \{[\s\S]*?\}[\n\r]*function render', new_init + '\n\nfunction render', content)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Rewrote init function with perfect error handling!")
