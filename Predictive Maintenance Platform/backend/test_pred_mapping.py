import json
from server import app

app.config['TESTING'] = True

with open('backend/catalog/machines.json', 'r') as f:
    catalog = json.load(f)

with open('frontend/assets/config/asset-registry.json', 'r') as f:
    registry = json.load(f)

def run_test(machine_id, values, expected_risk, expected_comp):
    with app.test_client() as client:
        rv = client.post('/api/predict', json={
            "machine_id": machine_id,
            "values": values
        })
        data = json.loads(rv.data)
        if expected_risk:
            assert data['risk_level'] == expected_risk, f"Expected {expected_risk}, got {data['risk_level']}"
        if expected_comp:
            comp_id = data.get('predicted_component', {}).get('id')
            assert comp_id == expected_comp, f"Expected comp {expected_comp}, got {comp_id}"
            
            # verify it matches asset registry
            reg = registry.get(machine_id)
            assert reg, f"Missing asset registry for {machine_id}"
            assert comp_id in reg['components'], f"Component {comp_id} not in asset registry for {machine_id}"

print("Testing prediction mapping...")
# Find one pump, one motor, one compressor
pump = next(m for m in catalog['machines'] if m['family'] == 'centrifugal_pump')['id']
motor = next(m for m in catalog['machines'] if m['family'] == 'induction_motor')['id']
cnc = next(m for m in catalog['machines'] if m['family'] == 'cnc_milling')['id']

# normal pump
run_test(pump, {
    "suction_pressure": 1.0, "discharge_pressure": 6.0, "vibration": 2.0, "bearing_temp": 50
}, "low", None)

# cavitation pump
run_test(pump, {
    "suction_pressure": 0.2, "discharge_pressure": 6.0, "vibration": 8.0, "bearing_temp": 50
}, None, "impeller")

# normal motor
run_test(motor, {
    "vibration": 1.0, "stator_temp": 80, "current": 50
}, "low", None)

# bearing motor
run_test(motor, {
    "vibration": 6.0, "stator_temp": 80, "current": 50
}, None, "bearing_de")

print("Prediction tests passed!")
