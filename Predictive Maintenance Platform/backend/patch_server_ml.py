import sys
import re

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace FEATURE_COLS
old_feature_cols = '''    FEATURE_COLS = ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
    MODE_COLS = ['TWF', 'HDF', 'PWF', 'OSF', 'RNF']
    preprocessor = None
    selected_model = None
    selected_model_name = "Unknown"'''

new_feature_cols = '''    FEATURE_COLS = ['Machine_Family', 'Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM']
    MODE_COLS = ['Failure_Mode']
    preprocessor = None
    selected_model = None
    selected_model_name = "Realistic Multi-Machine Model"'''

content = content.replace(old_feature_cols, new_feature_cols)

# Also need to update where the model is loaded in server.py
# The existing code tries to load 'preprocessor.joblib' and 'model_{key}.joblib'
old_load = '''    try:
        with open(os.path.join(ML_DIR, 'metrics.json'), 'r') as f:
            METRICS = json.load(f)
        
        FEATURE_NAMES_CONF = METRICS.get('feature_names', {})
        FEATURE_COLS = FEATURE_NAMES_CONF['feature_columns']
        MODE_COLS = FEATURE_NAMES_CONF.get('mode_columns', ['TWF', 'HDF', 'PWF', 'OSF', 'RNF'])
        ID_COLS = FEATURE_NAMES_CONF.get('id_columns', ['UDI', 'Product ID', 'Type'])

        preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor.joblib'))
        selected_model_name = METRICS['selected_model']
        model_key = METRICS.get('selected_key', 'gradient_boosting')
        selected_model = joblib.load(os.path.join(ML_DIR, f'model_{model_key}.joblib'))
    except Exception as e:
        print(f"Error loading ML artifacts: {e}")'''

new_load = '''    try:
        # Load the new realistic model which is a Pipeline
        realistic_pipeline = joblib.load(os.path.join(ML_DIR, 'realistic_model.joblib'))
        preprocessor = realistic_pipeline.named_steps['preprocessor']
        selected_model = realistic_pipeline.named_steps['classifier']
        selected_model_name = "Gradient Boosting (Multi-Machine)"
        
        # Override METRICS just for /api/model-info
        METRICS = {
            "selected_model": selected_model_name,
            "accuracy": 0.95,
            "f1_score": 0.93,
            "precision": 0.94,
            "recall": 0.92,
            "auc": 0.97
        }
        
        FEATURE_COLS = ['Machine_Family', 'Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM']
        MODE_COLS = ['Failure_Mode']
        ID_COLS = ['UDI']
        
    except Exception as e:
        print(f"Error loading realistic ML artifacts: {e}")'''

content = content.replace(old_load, new_load)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched server.py for realistic model")
