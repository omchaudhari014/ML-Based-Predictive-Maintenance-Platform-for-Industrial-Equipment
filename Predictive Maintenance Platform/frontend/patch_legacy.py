import sys

with open('frontend/results.html', 'r', encoding='utf-8') as f:
    res_content = f.read()

res_content = res_content.replace('href: machine.html?id=', 'href: machine.html?id=&mode=legacy')

with open('frontend/results.html', 'w', encoding='utf-8') as f:
    f.write(res_content)

with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    mach_content = f.read()

import re

old_try = '''      try {
        machine = await getMachineById(id);
        const last = getLastPrediction();
        if (last && last.machine_id === id) {
          prediction = last;
        }
      } catch(e) {
        // Fallback to old mode
        const rec = getRecord(id);
        if (!rec) throw new Error('Not found');
        const profile = await getMachineProfile(rec.machineType);
        machine = {
          id: rec.id,
          name: rec.id,
          type_label: rec.machineType,
          model3d: profile.model3d
        };
        prediction = {
          risk_level: rec.riskLevel,
          predicted_component: { id: rec.inspectionArea, name: rec.inspectionAreaLabel },
          top_factors: []
        };
        isOldMode = true;
      }'''

new_try = '''      const isLegacy = params.get('mode') === 'legacy';
      
      if (isLegacy) {
        const rec = getRecord(id);
        if (!rec) throw new Error('Legacy record not found');
        const profile = await getMachineProfile(rec.machineType);
        machine = {
          id: rec.id,
          name: rec.id,
          type_label: rec.machineType,
          model3d: profile.model3d
        };
        prediction = {
          risk_level: rec.riskLevel,
          predicted_component: { id: rec.inspectionArea, name: rec.inspectionAreaLabel },
          top_factors: []
        };
        isOldMode = true;
      } else {
        try {
          machine = await getMachineById(id);
          const last = getLastPrediction();
          if (last && last.machine_id === id) {
            prediction = last;
          }
        } catch(e) {
          throw new Error('Machine not found in the equipment catalog.');
        }
      }'''

mach_content = mach_content.replace(old_try, new_try)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(mach_content)

print("Patched machine.html and results.html to strictly separate legacy mode")
