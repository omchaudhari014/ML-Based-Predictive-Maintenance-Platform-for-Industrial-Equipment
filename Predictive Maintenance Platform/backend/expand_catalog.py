import json
import os
import copy
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(BASE_DIR, 'catalog', 'machines.json')

with open(CATALOG_FILE, 'r') as f:
    catalog = json.load(f)

base_machines = {m['id']: m for m in catalog['machines']}

variants_config = [
    # Motors
    ('motor-001', 'motor-002', 'Bharat Bijlee', 'Flameproof IE3 Motor', '3-Phase AC Induction Motor (Flameproof)', '132kW, 415V, 1490rpm'),
    ('motor-001', 'motor-003', 'CG Power', 'Apex Series Induction Motor', 'High Efficiency Induction Motor', '250kW, 400V, 2980rpm'),
    ('motor-001', 'motor-004', 'Kirloskar Electric', 'Three Phase AC Motor', 'General Purpose AC Motor', '55kW, 415V, 990rpm'),
    ('motor-001', 'motor-005', 'Siemens India', 'SIMOTICS SD', 'Heavy Duty Severe Environment Motor', '315kW, 690V, 1485rpm'),
    ('motor-001', 'motor-006', 'ABB India', 'M3BP 280SMA', 'Process Performance Motor', '90kW, 400V, 1480rpm'),
    
    # Pumps
    ('pump-001', 'pump-002', 'Kirloskar Brothers', 'DB Series Centrifugal', 'End-Suction Centrifugal Pump', '75kW, 250m³/h, 40m head'),
    ('pump-001', 'pump-003', 'KSB India', 'MegaCPK', 'Standardized Chemical Pump', '45kW, 150m³/h, 60m head'),
    ('pump-001', 'pump-004', 'Crompton Greaves', 'Horizontal Split Casing', 'Split Casing Centrifugal Pump', '350kW, 1200m³/h, 80m head'),
    ('pump-001', 'pump-005', 'Jyoti Ltd', 'Vertical Turbine Pump', 'High Capacity Vertical Pump', '500kW, 2000m³/h, 50m head'),
    ('pump-001', 'pump-006', 'WPIL', 'End Suction Water Pump', 'Industrial Water Pump', '110kW, 400m³/h, 45m head'),
    
    # Compressors
    ('compressor-001', 'compressor-002', 'ELGi', 'EG Series 75V', 'Rotary Screw Air Compressor', '75kW, 12.5m³/min, 8 bar'),
    ('compressor-001', 'compressor-003', 'Atlas Copco India', 'GA 55+', 'Oil-injected Rotary Screw Compressor', '55kW, 9.8m³/min, 10 bar'),
    ('compressor-001', 'compressor-004', 'Ingersoll Rand India', 'R-Series 160kW', 'Contact-Cooled Rotary Compressor', '160kW, 28m³/min, 7.5 bar'),
    ('compressor-001', 'compressor-005', 'Kaeser India', 'CSD 125', 'Rotary Screw Compressor with Sigma Profile', '75kW, 12m³/min, 8.5 bar'),
    ('compressor-001', 'compressor-006', 'Chicago Pneumatic', 'CPB 60', 'Industrial Screw Compressor', '45kW, 7.5m³/min, 10 bar'),
    
    # Gearboxes
    ('gearbox-001', 'gearbox-002', 'Elecon', 'Econ Series', 'Helical Gear Reducer', 'Ratio 25:1, 35000Nm'),
    ('gearbox-001', 'gearbox-003', 'Premium Transmission', 'Premium Stephan', 'Helical Bevel Gearbox', 'Ratio 40:1, 55000Nm'),
    ('gearbox-001', 'gearbox-004', 'Flender India', 'FSG Series', 'Heavy Duty Industrial Gearbox', 'Ratio 15:1, 80000Nm'),
    ('gearbox-001', 'gearbox-005', 'SEW Eurodrive', 'X Series', 'Helical-Bevel Industrial Gearbox', 'Ratio 30:1, 48000Nm'),
    ('gearbox-001', 'gearbox-006', 'Bonfiglioli India', 'HDP Series', 'Parallel Shaft Gearbox', 'Ratio 20:1, 25000Nm'),
    
    # CNC
    ('cnc-001', 'cnc-002', 'HMT Machine Tools', 'VMC 850', 'Vertical Machining Center', '3-axis, 850x500x500mm, 8000rpm'),
    ('cnc-001', 'cnc-003', 'Jyoti CNC', 'DX 200', 'CNC Turning Center', '2-axis, 200mm chuck, 4000rpm'),
    ('cnc-001', 'cnc-004', 'BFW', 'Chakra', 'High Performance VMC', '3-axis, 1000x600x600mm, 10000rpm'),
    ('cnc-001', 'cnc-005', 'LMW', 'Smarturn', 'CNC Lathe', '2-axis, 250mm chuck, 3500rpm'),
    ('cnc-001', 'cnc-006', 'Yamazaki Mazak India', 'Nexus', '5-Axis Machining Center', '5-axis, 12000rpm, 40-tool ATC')
]

new_machines = []
for base_id, new_id, mfg, model, label, specs in variants_config:
    if base_id in base_machines:
        m = copy.deepcopy(base_machines[base_id])
        m['id'] = new_id
        m['manufacturer'] = mfg
        m['model'] = model
        m['type_label'] = label
        m['name'] = f"{mfg} {model} {label}"
        
        # update basic specs text if it's a dict or a string. 
        # In our machines.json, specs might be a string or a dict. Let's force it to be a dict or string properly.
        if isinstance(m.get('specifications', {}), dict):
            m['specifications']['Summary'] = specs
        else:
            m['specifications'] = {'Summary': specs}
            
        m['references'] = [{
            'title': f"Official Product Reference - {mfg} {model}",
            'url': f"https://www.google.com/search?q={mfg}+{model}",
            'source_type': "manufacturer_search"
        }]
        
        new_machines.append(m)

catalog['machines'].extend(new_machines)

with open(CATALOG_FILE, 'w') as f:
    json.dump(catalog, f, indent=2)

print(f"Catalog expanded. Total machines: {len(catalog['machines'])}")
