import json
import os
import trimesh

with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)

# Load registry
with open('frontend/assets/config/asset-registry.json', 'r') as f:
    registry = json.load(f)

FRONTEND_DIR = '../frontend' if os.path.exists('../frontend') else 'frontend'
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = 'C:/Predictive Maintenance Platform/frontend'

print("Validating 3D Assets...")

# Cache loaded models to save time across 1000 records sharing 8 models
model_cache = {}

all_pass = True
for i, m in enumerate(catalog['machines']):
    if i % 100 == 0:
        print(f"Validated {i} records...")
        
    img_path = os.path.join(FRONTEND_DIR, m['image'])
    if not os.path.exists(img_path):
        print(f"FAIL: {m['id']} - Image missing {img_path}")
        all_pass = False
        continue

    if m['model3d_type'] != 'unavailable':
        mod_path = os.path.join(FRONTEND_DIR, m['model3d'])
        if not os.path.exists(mod_path):
            print(f"FAIL: {m['id']} - Model missing {mod_path}")
            all_pass = False
            continue
            
        if mod_path not in model_cache:
            try:
                scene = trimesh.load(mod_path)
                geom_names = set(scene.geometry.keys())
                model_cache[mod_path] = geom_names
            except Exception as e:
                print(f"FAIL: {m['id']} - Invalid GLB: {e}")
                all_pass = False
                continue
                
        geom_names = model_cache[mod_path]
        
        reg = registry.get(m['id'])
        if not reg:
            print(f"FAIL: {m['id']} - Missing in asset-registry.json")
            all_pass = False
            continue
            
        for comp in m['components']:
            c_id = comp['id']
            if c_id not in reg['components']:
                print(f"FAIL: {m['id']} - Component {c_id} missing in registry mapping")
                all_pass = False
                break
                
            mapped_nodes = reg['components'][c_id]
            for n in mapped_nodes:
                if n not in geom_names:
                    print(f"FAIL: {m['id']} - Mapped node {n} not found in GLB {mod_path}")
                    all_pass = False
                    break

print("Asset Validation Complete.")
if all_pass:
    print("ALL PASS")
