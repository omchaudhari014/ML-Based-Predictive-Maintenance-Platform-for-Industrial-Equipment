import json

with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)

for m in catalog['machines']:
    if m['family'] == 'cnc_milling':
        has_coolant = any(c['id'] == 'coolant_system' for c in m['components'])
        if not has_coolant:
            m['components'].append({
                "id": "coolant_system",
                "name": "Coolant System"
            })

with open('backend/catalog/machines.json', 'w') as f:
    json.dump(catalog, f, indent=2)

print("Added coolant_system to CNC components")
