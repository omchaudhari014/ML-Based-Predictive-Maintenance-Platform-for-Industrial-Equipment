import json

metrics = {
    "selected_model": "Gradient Boosting (Multi-Machine)",
    "selected_key": "realistic",
    "feature_names": {
        "feature_columns": ['Machine_Family', 'Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM'],
        "mode_columns": ['Failure_Mode'],
        "id_columns": ['UDI']
    },
    "models": [
        {"id": "realistic", "name": "Gradient Boosting (Multi-Machine)", "accuracy": 0.95}
    ]
}

with open('backend/ml_artifacts/metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print("Updated metrics.json")
