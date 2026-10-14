import trimesh
import numpy as np
import os

os.makedirs('frontend/assets/models', exist_ok=True)
c = [120, 120, 120, 255]

# 1. INDUCTION MOTOR
# Body
body = trimesh.creation.cylinder(radius=0.4, height=1.0)
body.visual.face_colors = [100, 100, 150, 255]
# Stator/Housing represented by body
stator = body.copy()
stator.metadata['name'] = 'stator'

# Shaft
shaft = trimesh.creation.cylinder(radius=0.1, height=1.5)
shaft.apply_translation([0, 0, 0])
shaft.visual.face_colors = [200, 200, 200, 255]
shaft.metadata['name'] = 'shaft'

# Terminal Box
term = trimesh.creation.box(extents=[0.3, 0.3, 0.3])
term.apply_translation([0.4, 0, 0])
term.visual.face_colors = [50, 50, 50, 255]
term.metadata['name'] = 'terminal_box'

# Fan
fan = trimesh.creation.cylinder(radius=0.35, height=0.2)
fan.apply_translation([0, 0, -0.6])
fan.visual.face_colors = [50, 150, 200, 255]
fan.metadata['name'] = 'cooling_fan'

# Bearings
brg_de = trimesh.creation.annulus(r_min=0.1, r_max=0.2, height=0.1)
brg_de.apply_translation([0, 0, 0.5])
brg_de.metadata['name'] = 'bearing_de'

brg_nde = trimesh.creation.annulus(r_min=0.1, r_max=0.2, height=0.1)
brg_nde.apply_translation([0, 0, -0.5])
brg_nde.metadata['name'] = 'bearing_nde'

scene_motor = trimesh.Scene([stator, shaft, term, fan, brg_de, brg_nde])
scene_motor.export('frontend/assets/models/induction_motor.glb')

# 2. CENTRIFUGAL PUMP
motor = trimesh.creation.cylinder(radius=0.4, height=0.8)
motor.apply_translation([0, -0.5, 0])
motor.metadata['name'] = 'motor'

shaft_p = trimesh.creation.cylinder(radius=0.08, height=1.2)
shaft_p.metadata['name'] = 'shaft'

casing = trimesh.creation.icosphere(radius=0.5, subdivisions=3)
casing.apply_translation([0, 0.6, 0])
casing.metadata['name'] = 'casing'

impeller = trimesh.creation.cylinder(radius=0.3, height=0.1)
impeller.apply_translation([0, 0.6, 0])
impeller.metadata['name'] = 'impeller'

seal = trimesh.creation.cylinder(radius=0.15, height=0.15)
seal.apply_translation([0, 0.2, 0])
seal.metadata['name'] = 'mechanical_seal'

scene_pump = trimesh.Scene([motor, shaft_p, casing, impeller, seal])
scene_pump.export('frontend/assets/models/centrifugal_pump.glb')

# 3. AIR COMPRESSOR
housing = trimesh.creation.box(extents=[1.5, 1.0, 1.0])
housing.metadata['name'] = 'housing'

air_end = trimesh.creation.cylinder(radius=0.3, height=0.8)
air_end.apply_translation([0, 0, 0])
air_end.metadata['name'] = 'air_end'

motor_c = trimesh.creation.cylinder(radius=0.25, height=0.6)
motor_c.apply_translation([-0.4, 0, 0])
motor_c.metadata['name'] = 'motor'

cooler = trimesh.creation.box(extents=[0.2, 0.8, 0.8])
cooler.apply_translation([0.65, 0, 0])
cooler.metadata['name'] = 'cooler'

scene_comp = trimesh.Scene([housing, air_end, motor_c, cooler])
scene_comp.export('frontend/assets/models/air_compressor.glb')

# 4. GEARBOX
gb_housing = trimesh.creation.box(extents=[1.0, 0.8, 0.6])
gb_housing.metadata['name'] = 'housing'

gear = trimesh.creation.cylinder(radius=0.35, height=0.2)
gear.metadata['name'] = 'gear_set'

in_shaft = trimesh.creation.cylinder(radius=0.1, height=0.8)
in_shaft.apply_translation([-0.3, 0, 0])
in_shaft.metadata['name'] = 'input_shaft'

out_shaft = trimesh.creation.cylinder(radius=0.15, height=0.8)
out_shaft.apply_translation([0.3, 0, 0])
out_shaft.metadata['name'] = 'output_shaft'

lub = trimesh.creation.box(extents=[0.3, 0.3, 0.3])
lub.apply_translation([0, 0.4, 0])
lub.metadata['name'] = 'lubrication_system'

scene_gb = trimesh.Scene([gb_housing, gear, in_shaft, out_shaft, lub])
scene_gb.export('frontend/assets/models/industrial_gearbox.glb')

# 5. CNC MACHINE
cnc_base = trimesh.creation.box(extents=[2.0, 0.5, 1.5])
cnc_base.apply_translation([0, -0.5, 0])
cnc_base.metadata['name'] = 'base'

column = trimesh.creation.box(extents=[0.5, 1.5, 0.8])
column.apply_translation([-0.7, 0.5, -0.3])
column.metadata['name'] = 'housing'

spindle = trimesh.creation.cylinder(radius=0.15, height=0.6)
spindle.apply_translation([-0.7, 0.8, 0.3])
spindle.metadata['name'] = 'spindle'

table = trimesh.creation.box(extents=[1.0, 0.1, 0.8])
table.apply_translation([0.2, 0, 0.2])
table.metadata['name'] = 'table'

tool = trimesh.creation.cylinder(radius=0.05, height=0.2)
tool.apply_translation([-0.7, 0.4, 0.3])
tool.metadata['name'] = 'tool_holder'

coolant = trimesh.creation.box(extents=[0.2, 0.2, 0.2])
coolant.apply_translation([-0.7, 0.8, 0.6])
coolant.metadata['name'] = 'coolant_system'

scene_cnc = trimesh.Scene([cnc_base, column, spindle, table, tool, coolant])
scene_cnc.export('frontend/assets/models/cnc_machine.glb')

print("Generated realistic diverse 3D models!")
