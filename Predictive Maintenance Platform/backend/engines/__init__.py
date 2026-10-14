from .motor_engine import MotorEngine
from .pump_engine import PumpEngine
from .compressor_engine import CompressorEngine
from .gearbox_engine import GearboxEngine
from .cnc_engine import CNCEngine
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_FILE = os.path.join(BASE_DIR, 'catalog', 'machines.json')

def get_engine(machine_id):
    try:
        with open(CATALOG_FILE, 'r') as f:
            catalog = json.load(f)
        machines = {m['id']: m for m in catalog['machines']}
    except:
        return None
        
    machine = machines.get(machine_id)
    if not machine:
        return None
        
    mtype = machine['type']
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
        
    return BaseEngine(machine)
