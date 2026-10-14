with open('backend/engines/cnc_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_res = '''        response = {
            "machine_id": self.machine_def['id'],
            "machine_type": self.machine_def['type'],
            "machine_name": self.machine_def['name'],
            "assessment_method": self.machine_def['assessment_method'],
            "assessment_label": self.machine_def['assessment_label'],
            "health_score": round(health_score),
            "risk_score": round(risk_score),
            "risk_level": get_risk_level(risk_score),
            "top_factors": factors[:3],
            "sensor_analysis": factors,
            "recommendations": [{"priority": "HIGH", "action": "Inspect " + comp.get('name', comp_id)}]
        }'''

new_res = '''        response = {
            "machine_id": self.machine_def['id'],
            "machine_type": self.machine_def['type'],
            "machine_name": self.machine_def['name'],
            "assessment_method": self.machine_def['assessment_method'],
            "assessment_label": self.machine_def['assessment_label'],
            "health_score": round(health_score),
            "risk_score": round(risk_score),
            "risk_level": get_risk_level(risk_score),
            "top_factors": factors[:3],
            "sensor_analysis": factors,
            "predicted_failure_mode": "Tool Wear/Thermal Anomaly",
            "causes": ["High rotational friction", "Inadequate coolant flow", "Dull cutting tool"],
            "consequences": ["Surface finish degradation", "Tool breakage", "Spindle overload"],
            "predicted_component": {
                "id": comp_id,
                "name": comp.get('name', comp_id),
                "confidence": "high"
            },
            "recommendations": [{"priority": "HIGH", "action": "Inspect " + comp.get('name', comp_id)}]
        }'''

content = content.replace(old_res, new_res)

with open('backend/engines/cnc_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
