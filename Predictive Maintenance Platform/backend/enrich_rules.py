import json

with open('backend/catalog/machines.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

rich_dict = {
    "Overheating": {
        "causes": ["Blocked cooling vents", "High ambient temperature", "Overloading beyond rated capacity", "Friction from degraded lubrication"],
        "consequences": ["Insulation breakdown", "Thermal expansion leading to seizing", "Fire hazard", "Reduced lifespan"],
        "recommendations": [{"priority": "high", "action": "Clear all cooling vents and fans"}, {"priority": "medium", "action": "Check lubrication levels"}, {"priority": "high", "action": "Reduce load immediately"}]
    },
    "Vibration": {
        "causes": ["Rotor imbalance", "Shaft misalignment", "Bearing failure", "Loose mounting bolts"],
        "consequences": ["Catastrophic mechanical failure", "Shattered bearings", "Structural fatigue", "High noise levels"],
        "recommendations": [{"priority": "critical", "action": "Stop machine and check alignment"}, {"priority": "high", "action": "Tighten base bolts"}, {"priority": "medium", "action": "Schedule bearing replacement"}]
    },
    "Cavitation": {
        "causes": ["Low suction pressure", "Fluid temperature too high", "Clogged suction filter", "Excessive pump speed"],
        "consequences": ["Impeller pitting and erosion", "Violent vibrations", "Seal failure", "Loss of pumping efficiency"],
        "recommendations": [{"priority": "critical", "action": "Increase suction head pressure"}, {"priority": "high", "action": "Clean suction strainers"}, {"priority": "medium", "action": "Throttle discharge valve"}]
    },
    "Electrical Overload": {
        "causes": ["Short circuit in windings", "Phase imbalance", "Mechanical jamming", "Voltage surges"],
        "consequences": ["Burnt stator windings", "Tripped breakers", "Total motor failure", "Arc flash risk"],
        "recommendations": [{"priority": "critical", "action": "Isolate power supply"}, {"priority": "high", "action": "Test winding insulation resistance"}, {"priority": "high", "action": "Check for mechanical jams"}]
    }
}

for m in data.get('machines', []):
    for r in m.get('diagnostic_rules', []):
        fm = r.get('failure_mode', '')
        
        # Determine closest match
        match = "Vibration"
        if "heat" in fm.lower() or "temp" in fm.lower(): match = "Overheating"
        if "cavit" in fm.lower() or "leak" in fm.lower(): match = "Cavitation"
        if "elect" in fm.lower() or "curr" in fm.lower() or "power" in fm.lower(): match = "Electrical Overload"
        
        r['causes'] = rich_dict[match]['causes']
        r['consequences'] = rich_dict[match]['consequences']
        r['recommendations'] = rich_dict[match]['recommendations']

with open('backend/catalog/machines.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print("Enriched diagnostic rules with realistic causes and risks")
