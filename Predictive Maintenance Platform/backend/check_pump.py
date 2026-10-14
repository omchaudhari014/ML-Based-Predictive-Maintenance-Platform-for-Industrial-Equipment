import json
with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)
pump = next((m for m in catalog['machines'] if m['id'] == 'pump-001'), None)
for s in pump['sensor_schema']:
    print(f"{s['id']}: min={s.get('normal_min')} max={s.get('normal_max')} val={s.get('name')}")
