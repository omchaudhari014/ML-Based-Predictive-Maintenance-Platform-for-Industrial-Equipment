import json

feature_names = {
    "feature_columns": ['Machine_Family', 'Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM'],
    "mode_columns": ['Failure_Mode'],
    "id_columns": ['UDI']
}

with open('backend/ml_artifacts/feature_names.json', 'w') as f:
    json.dump(feature_names, f, indent=2)

print("Updated feature_names.json")
