from server import app
app.config['TESTING'] = True
with app.test_client() as client:
    rv = client.post('/api/predict', json={
        "machine_id": "pump-001",
        "values": {
            "suction_pressure": 1.0,
            "discharge_pressure": 5.0,
            "flow_rate": 380,
            "vibration_de": 2.0,
            "vibration_nde": 2.0,
            "bearing_temp_de": 50,
            "bearing_temp_nde": 50,
            "motor_current": 150,
            "speed": 1450
        }
    })
    print(rv.data)
