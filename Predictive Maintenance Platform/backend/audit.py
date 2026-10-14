import json
import os

catalog_file = 'backend/catalog/machines.json'
with open(catalog_file, 'r') as f:
    catalog = json.load(f)

print(f"Machine records: {len(catalog['machines'])}")

families = set(m['type'] for m in catalog['machines'])
print(f"Machine families: {len(families)}")

images = set(m['image'] for m in catalog['machines'])
print(f"Images: {len(images)}")
