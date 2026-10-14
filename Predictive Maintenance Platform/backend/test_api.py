import pytest
from server import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert json.loads(rv.data)['status'] == 'ok'

def test_get_machines(client):
    rv = client.get('/api/machines')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'machines' in data
    assert len(data['machines']) >= 30

def test_search_machines(client):
    rv = client.get('/api/machines/search?q=pump')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'machines' in data
    assert any('pump' in m['type'].lower() or 'pump' in m['name'].lower() for m in data['machines'])

def test_get_machine(client):
    rv = client.get('/api/machines/motor-001')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['id'] == 'motor-001'

def test_predict_pump_normal(client):
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
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['risk_level'] == 'low'

def test_predict_pump_cavitation(client):
    rv = client.post('/api/predict', json={
        "machine_id": "pump-001",
        "values": {
            "suction_pressure": 0.2, # below warning
            "discharge_pressure": 5.0,
            "flow_rate": 380,
            "vibration_de": 8.0, # above warning
            "vibration_nde": 2.0,
            "bearing_temp_de": 50,
            "bearing_temp_nde": 50,
            "motor_current": 150,
            "speed": 1450
        }
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    # the exact output depends on what rules were set in machines.json. 
    # But it should be at least medium/high risk
    assert data['risk_level'] in ['medium', 'high', 'critical']
    
def test_predict_cnc(client):
    rv = client.post('/api/predict', json={
        "machine_id": "cnc-001",
        "values": {
            "air_temperature": 300,
            "process_temperature": 310,
            "rotational_speed": 1500,
            "torque": 40,
            "tool_wear": 100
        }
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['assessment_method'] == 'ml_prediction'

