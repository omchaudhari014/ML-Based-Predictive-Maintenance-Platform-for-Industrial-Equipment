import json
import os

CATALOG_FILE = 'backend/catalog/machines.json'
with open(CATALOG_FILE, 'r') as f:
    catalog = json.load(f)

for m in catalog['machines']:
    for s in m['sensor_schema']:
        if s.get('normal_max') is not None and s.get('warning_max') is not None:
            if s['warning_max'] < s['normal_max']:
                # The subagent confused max and min or didn't understand the bounds.
                # E.g. speed warning_max = 1440, normal_max = 1460.
                s['warning_max'] = s['normal_max'] + (s['normal_max'] - s['normal_min'])

with open(CATALOG_FILE, 'w') as f:
    json.dump(catalog, f, indent=2)

print("Fixed speed and other invalid upper bounds in catalog.")
