import trimesh
scene = trimesh.load('frontend/assets/models/induction_motor.glb')
print([geom.metadata.get('name', 'none') for name, geom in scene.geometry.items()])
