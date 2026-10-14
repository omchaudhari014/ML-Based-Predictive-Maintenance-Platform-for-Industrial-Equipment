import json

def get_risk_level(score):
    if score < 20: return "low"
    if score < 45: return "medium"
    if score < 75: return "high"
    return "critical"

class BaseEngine:
    def __init__(self, machine_def):
        self.machine_def = machine_def

    def evaluate_sensors(self, values, sensor_schema):
        states = []
        total_deviation = 0
        
        for schema in sensor_schema:
            sensor_id = schema['id']
            val = values.get(sensor_id)
            if val is None:
                continue
                
            status = "normal"
            deviation = 0.0
            direction = "none"
            
            # Check thresholds
            if schema.get('critical_max') is not None and val > schema['critical_max']:
                status = "critical"
                deviation = 1.0
                direction = "high"
            elif schema.get('critical_min') is not None and val < schema['critical_min']:
                status = "critical"
                deviation = 1.0
                direction = "low"
            elif schema.get('warning_max') is not None and val > schema['warning_max']:
                status = "warning"
                deviation = 0.5 + 0.5 * (val - schema['warning_max']) / ((schema.get('critical_max') if schema.get('critical_max') is not None else (val + 1)) - schema['warning_max'])
                direction = "high"
            elif schema.get('warning_min') is not None and val < schema['warning_min']:
                status = "warning"
                deviation = 0.5 + 0.5 * (schema['warning_min'] - val) / (schema['warning_min'] - (schema.get('critical_min') if schema.get('critical_min') is not None else (val - 1)))
                direction = "low"
            else:
                status = "normal"
                deviation = 0.0 # simplified
                
            deviation = min(max(deviation, 0.0), 1.0)
            total_deviation += deviation
            
            states.append({
                "sensor": sensor_id,
                "label": schema['name'],
                "value": val,
                "unit": schema.get('unit', ''),
                "normal_min": schema.get('normal_min'),
                "normal_max": schema.get('normal_max'),
                "status": status,
                "deviation": deviation,
                "direction": "raises_risk" if deviation > 0 else "neutral",
                "threshold_direction": direction
            })
            
        states = sorted(states, key=lambda x: x['deviation'], reverse=True)
        return states

    def match_rules(self, sensor_states, rules):
        state_map = {s['sensor']: s for s in sensor_states}
        matched = []
        
        for rule in rules:
            conditions_met = 0
            for cond in rule['conditions']:
                sensor = cond['sensor']
                direction = cond['direction']
                if sensor in state_map:
                    s_state = state_map[sensor]
                    # Check if threshold direction matches and status is at least warning
                    if s_state['status'] in ['warning', 'critical'] and s_state['threshold_direction'] == direction:
                        conditions_met += 1
                        
            is_match = False
            if rule['logic'] == 'all' and conditions_met == len(rule['conditions']):
                is_match = True
            elif rule['logic'] == 'any' and conditions_met > 0:
                is_match = True
                
            if is_match:
                matched.append(rule)
                
        # Sort by severity and priority
        severity_val = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        matched = sorted(matched, key=lambda r: (severity_val.get(r.get('severity', 'low'), 0), -r.get('priority', 99)), reverse=True)
        return matched

    def predict(self, values):
        sensor_states = self.evaluate_sensors(values, self.machine_def['sensor_schema'])
        
        # Calculate scores based on engineering rules
        total_dev = sum(s['deviation'] for s in sensor_states)
        max_dev = max((s['deviation'] for s in sensor_states), default=0)
        
        # Weighted risk score
        risk_score = min(100, (max_dev * 60) + (total_dev * 10))
        health_score = max(0, 100 - risk_score)
        
        matched_rules = self.match_rules(sensor_states, self.machine_def.get('diagnostic_rules', []))
        top_rule = matched_rules[0] if matched_rules else None
        
        response = {
            "machine_id": self.machine_def['id'],
            "machine_type": self.machine_def['type'],
            "machine_name": self.machine_def['name'],
            "assessment_method": self.machine_def['assessment_method'],
            "assessment_label": self.machine_def['assessment_label'],
            "health_score": round(health_score),
            "risk_score": round(risk_score),
            "risk_level": get_risk_level(risk_score),
            "top_factors": [s for s in sensor_states if s['deviation'] > 0][:3],
            "sensor_analysis": sensor_states,
        }
        
        if top_rule:
            comp = next((c for c in self.machine_def['components'] if c['id'] == top_rule['component_id']), {})
            response.update({
                "predicted_component": {
                    "id": top_rule['component_id'],
                    "name": comp.get('name', 'Unknown Component'),
                    "confidence": "high" if top_rule.get('severity') in ['critical', 'high'] else "medium"
                },
                "predicted_failure_mode": top_rule['failure_mode'],
                "causes": top_rule.get('causes', []),
                "consequences": top_rule.get('consequences', []),
                "recommendations": top_rule.get('recommendations', [])
            })
            
        return response
