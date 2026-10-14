import json
with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)
pump = next((m for m in catalog['machines'] if m['id'] == 'pump-001'), None)
for s in pump['sensor_schema']:
    print(s)
