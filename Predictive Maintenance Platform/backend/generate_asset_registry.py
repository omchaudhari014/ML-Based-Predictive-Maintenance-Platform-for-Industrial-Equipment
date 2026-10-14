import json
import os

catalog_file = 'backend/catalog/machines.json'
with open(catalog_file, 'r') as f:
    catalog = json.load(f)

registry = {}
for m in catalog['machines']:
    comp_map = {c['id']: [c['id']] for c in m['components']}
    registry[m['id']] = {
        "model": "/" + m['model3d'],
        "components": comp_map
    }

os.makedirs('frontend/assets/config', exist_ok=True)
with open('frontend/assets/config/asset-registry.json', 'w') as f:
    json.dump(registry, f, indent=2)

print("Created asset registry.")
