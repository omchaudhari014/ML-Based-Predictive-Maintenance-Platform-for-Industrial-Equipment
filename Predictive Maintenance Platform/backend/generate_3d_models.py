import trimesh
import numpy as np
import os

OUT_DIR = "c:/Predictive Maintenance Platform/frontend/assets/models/"
os.makedirs(OUT_DIR, exist_ok=True)

def create_motor():
    scene = trimesh.Scene()
    
    # MOTOR: horizontal cylinder
    # housing (gray)
    housing = trimesh.creation.cylinder(radius=1.0, height=3.0)
    housing.visual.face_colors = [128, 128, 128, 255]
    housing.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    scene.add_geometry(housing, node_name='housing', geom_name='housing')
    
    # stator (copper)
    stator = trimesh.creation.cylinder(radius=0.9, height=2.8)
    stator.visual.face_colors = [184, 115, 51, 255]
    stator.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    scene.add_geometry(stator, node_name='stator', geom_name='stator')
    
    # rotor (dark gray)
    rotor = trimesh.creation.cylinder(radius=0.7, height=2.8)
    rotor.visual.face_colors = [64, 64, 64, 255]
    rotor.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    scene.add_geometry(rotor, node_name='rotor', geom_name='rotor')
    
    # shaft (silver)
    shaft = trimesh.creation.cylinder(radius=0.2, height=4.0)
    shaft.visual.face_colors = [192, 192, 192, 255]
    shaft.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    scene.add_geometry(shaft, node_name='shaft', geom_name='shaft')
    
    # bearing_de (silver)
    bearing_de = trimesh.creation.annulus(r_min=0.2, r_max=0.4, height=0.2)
    bearing_de.visual.face_colors = [192, 192, 192, 255]
    bearing_de.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    bearing_de.apply_translation([1.5, 0, 0])
    scene.add_geometry(bearing_de, node_name='bearing_de', geom_name='bearing_de')
    
    # bearing_nde
    bearing_nde = trimesh.creation.annulus(r_min=0.2, r_max=0.4, height=0.2)
    bearing_nde.visual.face_colors = [192, 192, 192, 255]
    bearing_nde.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    bearing_nde.apply_translation([-1.5, 0, 0])
    scene.add_geometry(bearing_nde, node_name='bearing_nde', geom_name='bearing_nde')
    
    # cooling_fan
    fan = trimesh.creation.cylinder(radius=0.8, height=0.2)
    fan.visual.face_colors = [255, 255, 255, 255]
    fan.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    fan.apply_translation([-1.7, 0, 0])
    scene.add_geometry(fan, node_name='cooling_fan', geom_name='cooling_fan')
    
    # terminal_box
    box = trimesh.creation.box(extents=[0.5, 0.5, 0.5])
    box.visual.face_colors = [0, 0, 255, 255]
    box.apply_translation([0, 1.0, 0])
    scene.add_geometry(box, node_name='terminal_box', geom_name='terminal_box')
    
    scene.export(os.path.join(OUT_DIR, 'induction_motor.glb'), file_type='glb')

def create_pump():
    scene = trimesh.Scene()
    
    motor = trimesh.creation.cylinder(radius=1.0, height=2.0)
    motor.visual.face_colors = [0, 0, 255, 255]
    motor.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    motor.apply_translation([-1.5, 0, 0])
    scene.add_geometry(motor, node_name='motor', geom_name='motor')
    
    coupling = trimesh.creation.cylinder(radius=0.4, height=0.3)
    coupling.visual.face_colors = [255, 255, 0, 255]
    coupling.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    coupling.apply_translation([-0.35, 0, 0])
    scene.add_geometry(coupling, node_name='coupling', geom_name='coupling')
    
    shaft = trimesh.creation.cylinder(radius=0.1, height=4.0)
    shaft.visual.face_colors = [192, 192, 192, 255]
    shaft.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    scene.add_geometry(shaft, node_name='shaft', geom_name='shaft')
    
    bearing_de = trimesh.creation.annulus(r_min=0.1, r_max=0.3, height=0.2)
    bearing_de.visual.face_colors = [192, 192, 192, 255]
    bearing_de.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    bearing_de.apply_translation([0.2, 0, 0])
    scene.add_geometry(bearing_de, node_name='bearing_de', geom_name='bearing_de')
    
    bearing_nde = trimesh.creation.annulus(r_min=0.1, r_max=0.3, height=0.2)
    bearing_nde.visual.face_colors = [192, 192, 192, 255]
    bearing_nde.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    bearing_nde.apply_translation([-0.2, 0, 0])
    scene.add_geometry(bearing_nde, node_name='bearing_nde', geom_name='bearing_nde')
    
    impeller = trimesh.creation.cone(radius=0.8, height=0.4)
    impeller.visual.face_colors = [205, 127, 50, 255]
    impeller.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [0, 0, 1]))
    impeller.apply_translation([1.0, 0, 0])
    scene.add_geometry(impeller, node_name='impeller', geom_name='impeller')
    
    casing = trimesh.creation.cylinder(radius=1.2, height=1.0)
    casing.visual.face_colors = [100, 128, 100, 255]
    casing.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    casing.apply_translation([1.0, 0, 0])
    scene.add_geometry(casing, node_name='casing', geom_name='casing')
    
    seal = trimesh.creation.annulus(r_min=0.1, r_max=0.2, height=0.1)
    seal.visual.face_colors = [32, 32, 32, 255]
    seal.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    seal.apply_translation([0.5, 0, 0])
    scene.add_geometry(seal, node_name='mechanical_seal', geom_name='mechanical_seal')
    
    scene.export(os.path.join(OUT_DIR, 'centrifugal_pump.glb'), file_type='glb')

def create_compressor():
    scene = trimesh.Scene()
    
    housing = trimesh.creation.box(extents=[3.0, 2.0, 2.0])
    housing.visual.face_colors = [64, 64, 64, 200]
    scene.add_geometry(housing, node_name='housing', geom_name='housing')
    
    motor = trimesh.creation.cylinder(radius=0.6, height=1.2)
    motor.visual.face_colors = [0, 0, 255, 255]
    motor.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    motor.apply_translation([-0.8, -0.4, 0])
    scene.add_geometry(motor, node_name='motor', geom_name='motor')
    
    air_end = trimesh.creation.cylinder(radius=0.5, height=1.0)
    air_end.visual.face_colors = [0, 255, 0, 255]
    air_end.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    air_end.apply_translation([0.6, -0.4, 0])
    scene.add_geometry(air_end, node_name='air_end', geom_name='air_end')
    
    element = trimesh.creation.cylinder(radius=0.3, height=0.8)
    element.visual.face_colors = [32, 32, 32, 255]
    element.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    element.apply_translation([0.6, -0.4, 0])
    scene.add_geometry(element, node_name='compressor_element', geom_name='compressor_element')
    
    shaft = trimesh.creation.cylinder(radius=0.1, height=1.0)
    shaft.visual.face_colors = [192, 192, 192, 255]
    shaft.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    shaft.apply_translation([-0.1, -0.4, 0])
    scene.add_geometry(shaft, node_name='shaft', geom_name='shaft')
    
    bearing = trimesh.creation.annulus(r_min=0.1, r_max=0.2, height=0.1)
    bearing.visual.face_colors = [192, 192, 192, 255]
    bearing.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    bearing.apply_translation([0.1, -0.4, 0])
    scene.add_geometry(bearing, node_name='bearing', geom_name='bearing')
    
    sep = trimesh.creation.cylinder(radius=0.4, height=1.5)
    sep.visual.face_colors = [128, 128, 128, 255]
    sep.apply_translation([-1.0, 0.2, -0.5])
    scene.add_geometry(sep, node_name='oil_separator', geom_name='oil_separator')
    
    cooler = trimesh.creation.box(extents=[0.5, 1.0, 1.5])
    cooler.visual.face_colors = [192, 192, 192, 255]
    cooler.apply_translation([1.0, 0.2, 0])
    scene.add_geometry(cooler, node_name='cooler', geom_name='cooler')
    
    valve = trimesh.creation.cylinder(radius=0.2, height=0.4)
    valve.visual.face_colors = [200, 200, 200, 255]
    valve.apply_translation([0.6, 0.4, 0])
    scene.add_geometry(valve, node_name='intake_valve', geom_name='intake_valve')
    
    scene.export(os.path.join(OUT_DIR, 'air_compressor.glb'), file_type='glb')

def create_gearbox():
    scene = trimesh.Scene()
    
    housing = trimesh.creation.box(extents=[2.0, 1.5, 1.5])
    housing.visual.face_colors = [128, 128, 128, 255]
    scene.add_geometry(housing, node_name='housing', geom_name='housing')
    
    ishaft = trimesh.creation.cylinder(radius=0.15, height=1.5)
    ishaft.visual.face_colors = [192, 192, 192, 255]
    ishaft.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    ishaft.apply_translation([-1.2, 0.2, 0])
    scene.add_geometry(ishaft, node_name='input_shaft', geom_name='input_shaft')
    
    oshaft = trimesh.creation.cylinder(radius=0.25, height=1.5)
    oshaft.visual.face_colors = [192, 192, 192, 255]
    oshaft.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    oshaft.apply_translation([1.2, -0.2, 0])
    scene.add_geometry(oshaft, node_name='output_shaft', geom_name='output_shaft')
    
    g1 = trimesh.creation.cylinder(radius=0.6, height=0.2)
    g1.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    g1.apply_translation([-0.3, 0.2, 0])
    g2 = trimesh.creation.cylinder(radius=0.8, height=0.3)
    g2.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    g2.apply_translation([0.3, -0.2, 0])
    gear_set = trimesh.util.concatenate([g1, g2])
    gear_set.visual.face_colors = [205, 127, 50, 255]
    scene.add_geometry(gear_set, node_name='gear_set', geom_name='gear_set')
    
    ibear = trimesh.creation.annulus(r_min=0.15, r_max=0.3, height=0.2)
    ibear.visual.face_colors = [192, 192, 192, 255]
    ibear.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    ibear.apply_translation([-1.0, 0.2, 0])
    scene.add_geometry(ibear, node_name='input_bearing', geom_name='input_bearing')
    
    obear = trimesh.creation.annulus(r_min=0.25, r_max=0.4, height=0.2)
    obear.visual.face_colors = [192, 192, 192, 255]
    obear.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    obear.apply_translation([1.0, -0.2, 0])
    scene.add_geometry(obear, node_name='output_bearing', geom_name='output_bearing')
    
    seal = trimesh.creation.annulus(r_min=0.25, r_max=0.35, height=0.1)
    seal.visual.face_colors = [32, 32, 32, 255]
    seal.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    seal.apply_translation([0.9, -0.2, 0])
    scene.add_geometry(seal, node_name='seal', geom_name='seal')
    
    lube = trimesh.creation.box(extents=[1.0, 0.4, 0.8])
    lube.visual.face_colors = [0, 0, 128, 255]
    lube.apply_translation([0, -0.9, 0])
    scene.add_geometry(lube, node_name='lubrication_system', geom_name='lubrication_system')
    
    scene.export(os.path.join(OUT_DIR, 'industrial_gearbox.glb'), file_type='glb')

def create_cnc():
    scene = trimesh.Scene()
    
    base = trimesh.creation.box(extents=[3.0, 1.0, 2.0])
    base.apply_translation([0, 0.5, 0])
    pillar = trimesh.creation.box(extents=[1.0, 3.0, 1.0])
    pillar.apply_translation([-1.0, 2.0, -0.5])
    arm = trimesh.creation.box(extents=[2.0, 1.0, 1.0])
    arm.apply_translation([0.5, 3.0, -0.5])
    frame = trimesh.util.concatenate([base, pillar, arm])
    frame.visual.face_colors = [64, 64, 64, 255]
    scene.add_geometry(frame, node_name='machine_frame', geom_name='machine_frame')
    
    wt = trimesh.creation.box(extents=[1.5, 0.2, 1.5])
    wt.visual.face_colors = [128, 128, 128, 255]
    wt.apply_translation([0.5, 1.1, 0.5])
    scene.add_geometry(wt, node_name='worktable', geom_name='worktable')
    
    spindle = trimesh.creation.cylinder(radius=0.2, height=1.0)
    spindle.visual.face_colors = [192, 192, 192, 255]
    spindle.apply_translation([1.0, 2.0, -0.5])
    scene.add_geometry(spindle, node_name='spindle', geom_name='spindle')
    
    sb = trimesh.creation.annulus(r_min=0.2, r_max=0.3, height=0.2)
    sb.visual.face_colors = [192, 192, 192, 255]
    sb.apply_translation([1.0, 2.3, -0.5])
    scene.add_geometry(sb, node_name='spindle_bearing', geom_name='spindle_bearing')
    
    th = trimesh.creation.cone(radius=0.15, height=0.3)
    th.visual.face_colors = [128, 128, 128, 255]
    th.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    th.apply_translation([1.0, 1.4, -0.5])
    scene.add_geometry(th, node_name='tool_holder', geom_name='tool_holder')
    
    dm = trimesh.creation.cylinder(radius=0.3, height=0.6)
    dm.visual.face_colors = [0, 0, 255, 255]
    dm.apply_translation([1.0, 3.0, -0.5])
    scene.add_geometry(dm, node_name='drive_motor', geom_name='drive_motor')
    
    cp = trimesh.creation.cylinder(radius=0.05, height=2.0)
    cp.visual.face_colors = [173, 216, 230, 255]
    cp.apply_translation([1.4, 2.0, -0.2])
    scene.add_geometry(cp, node_name='coolant_system', geom_name='coolant_system')
    
    scene.export(os.path.join(OUT_DIR, 'cnc_machine.glb'), file_type='glb')

if __name__ == '__main__':
    create_motor()
    create_pump()
    create_compressor()
    create_gearbox()
    create_cnc()
    print("Done generating models.")
