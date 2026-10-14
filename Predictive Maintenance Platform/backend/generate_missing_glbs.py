import trimesh
import os

models_dir = '../frontend/assets/models/'
os.makedirs(models_dir, exist_ok=True)

def create_model(name, components):
    scene = trimesh.Scene()
    for comp in components:
        mesh = trimesh.creation.box(extents=comp['extents'])
        mesh.apply_translation(comp['pos'])
        scene.add_geometry(mesh, node_name=comp['id'])
    scene.export(os.path.join(models_dir, f'{name}.glb'))

# Screw compressor
create_model('screw_compressor', [
    {'id': 'casing', 'extents': [2, 1, 1], 'pos': [0, 0.5, 0]},
    {'id': 'rotor', 'extents': [1.8, 0.5, 0.5], 'pos': [0, 0.5, 0]},
    {'id': 'bearing_de', 'extents': [0.2, 0.6, 0.6], 'pos': [1.1, 0.5, 0]}
])
# CNC Milling
create_model('cnc_milling', [
    {'id': 'spindle', 'extents': [0.5, 1, 0.5], 'pos': [0, 1.5, 0]},
    {'id': 'drive_motor', 'extents': [0.6, 0.6, 0.6], 'pos': [0, 2.3, 0]},
    {'id': 'tool_holder', 'extents': [0.2, 0.4, 0.2], 'pos': [0, 0.8, 0]}
])
# Steam Turbine
create_model('steam_turbine', [
    {'id': 'casing', 'extents': [3, 1.5, 1.5], 'pos': [0, 0.75, 0]},
    {'id': 'rotor', 'extents': [3.2, 0.8, 0.8], 'pos': [0, 0.75, 0]},
    {'id': 'bearing_de', 'extents': [0.3, 1, 1], 'pos': [1.7, 0.75, 0]}
])
# Industrial Boiler
create_model('industrial_boiler', [
    {'id': 'casing', 'extents': [4, 4, 2], 'pos': [0, 2, 0]},
    {'id': 'rotor', 'extents': [1, 1, 1], 'pos': [0, 2, 0]}, # dummy
    {'id': 'bearing_de', 'extents': [1, 1, 1], 'pos': [0, 2, 0]} # dummy
])
# Generator
create_model('generator', [
    {'id': 'casing', 'extents': [2.5, 1.2, 1.2], 'pos': [0, 0.6, 0]},
    {'id': 'rotor', 'extents': [2.6, 0.8, 0.8], 'pos': [0, 0.6, 0]},
    {'id': 'bearing_de', 'extents': [0.2, 1, 1], 'pos': [1.4, 0.6, 0]}
])
print("Generated missing GLBs.")
