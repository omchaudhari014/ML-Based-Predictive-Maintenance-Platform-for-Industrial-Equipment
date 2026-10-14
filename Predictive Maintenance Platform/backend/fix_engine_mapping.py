with open('backend/engines/__init__.py', 'r') as f:
    content = f.read()

import re
old_mapping = '''    mtype = machine['type']
    if mtype == 'induction_motor':
        return MotorEngine(machine)
    elif mtype == 'centrifugal_pump':
        return PumpEngine(machine)
    elif mtype == 'air_compressor':
        return CompressorEngine(machine)
    elif mtype == 'industrial_gearbox':
        return GearboxEngine(machine)
    elif mtype == 'cnc_machining_center':
        return CNCEngine(machine)
        
    return None'''

new_mapping = '''    mtype = machine['type']
    # General engineering engine for missing specific engines
    from .base_engine import BaseEngine
    
    if mtype in ['induction_motor', 'generator']:
        return MotorEngine(machine)
    elif mtype in ['centrifugal_pump', 'steam_turbine', 'industrial_boiler']:
        return PumpEngine(machine) # Fallback to pump engine for now
    elif mtype in ['air_compressor', 'screw_compressor']:
        return CompressorEngine(machine)
    elif mtype in ['industrial_gearbox']:
        return GearboxEngine(machine)
    elif mtype in ['cnc_machining_center', 'cnc_milling']:
        return CNCEngine(machine)
        
    return BaseEngine(machine)'''

content = content.replace(old_mapping, new_mapping)

with open('backend/engines/__init__.py', 'w') as f:
    f.write(content)

print("Updated get_engine mapping")
