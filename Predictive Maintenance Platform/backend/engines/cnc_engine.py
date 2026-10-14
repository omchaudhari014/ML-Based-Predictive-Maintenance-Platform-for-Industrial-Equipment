import os
import json
import joblib
import pandas as pd
import numpy as np
import shap
from .base_engine import BaseEngine, get_risk_level

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, 'ml_artifacts')

# Map sensor IDs to AI4I feature names
SENSOR_TO_FEATURE = {
    'air_temperature': 'Air temperature [K]',
    'process_temperature': 'Process temperature [K]',
    'rotational_speed': 'Rotational speed [rpm]',
    'torque': 'Torque [Nm]',
    'tool_wear': 'Tool wear [min]'
}

# Duplicated from server for isolation
FACTOR_MAPPING = {
    'Torque [Nm]': {'label': 'Torque', 'interpretation': 'Elevated mechanical load', 'area': 'drive_motor', 'area_label': 'Drive Motor'},
    'Rotational speed [rpm]': {'label': 'Rotational speed', 'interpretation': 'Rotational stress', 'area': 'spindle', 'area_label': 'Spindle'},
    'Tool wear [min]': {'label': 'Tool wear', 'interpretation': 'Tool degradation', 'area': 'tool_holder', 'area_label': 'Tool Holder'},
    'Air temperature [K]': {'label': 'Air temperature', 'interpretation': 'Ambient thermal stress', 'area': 'coolant_system', 'area_label': 'Coolant System'},
    'Process temperature [K]': {'label': 'Process temperature', 'interpretation': 'Process thermal stress', 'area': 'drive_motor', 'area_label': 'Drive Motor'}
}

class CNCEngine(BaseEngine):
    def __init__(self, machine_def):
        super().__init__(machine_def)
        self.preprocessor = None
        self.model = None
        self._load_ml_artifacts()

    def _load_ml_artifacts(self):
        try:
            self.preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor_cnc.joblib'))
            self.model = joblib.load(os.path.join(ML_DIR, 'model_gradient_boosting.joblib'))
        except Exception as e:
            print(f"Error loading ML artifacts in CNCEngine: {e}")

    def get_explainer(self, model, X_transformed):
        if isinstance(model, (shap.TreeExplainer,)): 
            pass
        try:
            return shap.TreeExplainer(model)
        except:
            masker = shap.maskers.Independent(X_transformed)
            return shap.LinearExplainer(model, masker)

    def predict(self, values):
        if not self.model or not self.preprocessor:
            return super().predict(values) # fallback if model fails
            
        feature_vals = {}
        for sensor_id, feat_name in SENSOR_TO_FEATURE.items():
            feature_vals[feat_name] = values.get(sensor_id, 0.0)
            
        df_features = pd.DataFrame([feature_vals])
        
        # Transform and predict
        X_transformed = self.preprocessor.transform(df_features)
        prob = self.model.predict_proba(X_transformed)[0, 1]
        
        # SHAP
        try:
            explainer = self.get_explainer(self.model, X_transformed)
            shap_values = explainer.shap_values(X_transformed)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            s_vals = shap_values[0]
        except Exception as e:
            print(f"SHAP Error: {e}")
            s_vals = np.zeros(len(SENSOR_TO_FEATURE))
            
        factors = []
        cols = list(df_features.columns)
        for i, col in enumerate(cols):
            s_val = float(s_vals[i])
            actual_val = float(df_features[col].iloc[0])
            
            # Find the corresponding sensor schema
            sensor_id = next(k for k, v in SENSOR_TO_FEATURE.items() if v == col)
            schema = next((s for s in self.machine_def['sensor_schema'] if s['id'] == sensor_id), {})
            
            factors.append({
                "sensor": sensor_id,
                "label": schema.get('name', col),
                "value": actual_val,
                "unit": schema.get('unit', ''),
                "normal_min": schema.get('normal_min', 0),
                "normal_max": schema.get('normal_max', 0),
                "contribution": abs(s_val),
                "shapValue": s_val,
                "status": "warning" if abs(s_val) > 0.1 else "normal", # Simplified status based on SHAP
                "deviation": abs(s_val),
                "direction": "raises_risk" if s_val > 0 else "lowers_risk"
            })
            
        factors = sorted(factors, key=lambda x: x['contribution'], reverse=True)
        top_factor = factors[0]
        
        risk_score = round(float(prob) * 100, 1)
        health_score = max(0, 100 - risk_score)
        
        feat_name = SENSOR_TO_FEATURE[top_factor['sensor']]
        comp_id = FACTOR_MAPPING[feat_name]['area']
        comp = next((c for c in self.machine_def['components'] if c['id'] == comp_id), {})

        response = {
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
            "predicted_component": {
                "id": comp_id,
                "name": comp.get('name', 'Unknown Component'),
                "confidence": "high" if risk_score > 70 else "medium"
            },
            "predicted_failure_mode": FACTOR_MAPPING[feat_name]['interpretation'],
            "causes": ["ML Model Detected Anomaly based on " + top_factor['label']],
            "consequences": ["Potential component failure"],
            "recommendations": [{"priority": "HIGH", "action": "Inspect " + comp.get('name', comp_id)}]
        }
        
        return response
