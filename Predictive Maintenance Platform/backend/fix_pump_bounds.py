import json

with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)

for m in catalog['machines']:
    if m['family'] == 'centrifugal_pump':
        for s in m['sensor_schema']:
            if s['id'] == 'suction_pressure':
                s['warning_min'] = 0.3
                s['critical_min'] = 0.1

with open('backend/catalog/machines.json', 'w') as f:
    json.dump(catalog, f, indent=2)

print("Fixed pump schema min bounds")
