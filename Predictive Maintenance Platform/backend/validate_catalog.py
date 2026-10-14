import json
import os

with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)

machines = catalog['machines']

manufacturers = set()
families = set()
images = set()
assets = set()
asset_types = {"exact_asset": 0, "parametric": 0, "illustrative": 0, "unavailable": 0}
engines = set()

for m in machines:
    manufacturers.add(m.get('manufacturer'))
    families.add(m.get('family'))
    if m.get('image'): images.add(m.get('image'))
    if m.get('model3d'): assets.add(m.get('model3d'))
    atype = m.get('model3d_type', 'unavailable')
    asset_types[atype] = asset_types.get(atype, 0) + 1
    engines.add(m.get('assessment_method'))

print(f"Machine records: {len(machines)}")
print(f"Manufacturers: {len(manufacturers)}")
print(f"Families: {len(families)}")
print(f"Images: {len(images)}")
print(f"3D assets: {len(assets)}")
print(f"Exact assets: {asset_types.get('exact_asset', 0)}")
print(f"Parametric assets: {asset_types.get('parametric', 0)}")
print(f"Illustrative assets: {asset_types.get('illustrative', 0)}")
print(f"Diagnostic engines: {len(engines)}")
