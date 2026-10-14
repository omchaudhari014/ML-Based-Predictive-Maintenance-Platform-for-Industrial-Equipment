with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Match the old init exactly using regex to avoid whitespace issues
init_pattern = re.compile(r"async function init\(\) \{[\s\S]*?catch\(e\) \{", re.MULTILINE)

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
        machine = allMachines.find(m => {
           const fname = (rec.features.Machine_Family || '').toLowerCase();
           return m.name.toLowerCase().includes(fname) || fname.includes(m.type_label.toLowerCase());
        }) || allMachines.find(m => m.id === 'cnc-001') || allMachines[0];
        
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
    } catch(e) {'''

content = init_pattern.sub(init_new, content)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Regex patched init function!")
