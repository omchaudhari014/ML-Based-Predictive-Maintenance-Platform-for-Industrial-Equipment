import json
import os
import trimesh

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(BASE_DIR, 'catalog', 'machines.json')
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

with open(CATALOG_FILE, 'r') as f:
    catalog = json.load(f)

for machine in catalog['machines']:
    print(f"\nVerifying {machine['id']}...")
    model_path = os.path.join(FRONTEND_DIR, machine['model3d'].replace('/', os.sep))
    image_path = os.path.join(FRONTEND_DIR, machine['image'].replace('/', os.sep))
    
    if not os.path.exists(image_path):
        print(f"FAIL: Image missing at {image_path}")
        continue
        
    if not os.path.exists(model_path):
        print(f"FAIL: 3D model missing at {model_path}")
        continue
        
    try:
        scene = trimesh.load(model_path)
        node_names = set(scene.graph.nodes_geometry)
        
        # In our procedural generation, node names are keys in scene.geometry or similar,
        # let's just extract all available string keys from geometry.
        geom_names = set(scene.geometry.keys())
        
        missing_components = []
        for comp in machine['components']:
            if comp['id'] not in geom_names:
                missing_components.append(comp['id'])
                
        if missing_components:
            print(f"FAIL: Components missing in GLB: {missing_components}")
            print(f"Available in GLB: {geom_names}")
        else:
            print(f"PASS: {machine['id']}")
            
    except Exception as e:
        print(f"FAIL: Error loading model: {e}")

