import os
import json
import uuid
import datetime
import math
import pandas as pd
import numpy as np
import joblib
import shap
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from engines import get_engine

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# --- Configuration & Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.join(BASE_DIR, 'ml_artifacts')
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')
DEMO_CSV = os.path.join(FRONTEND_DIR, 'assets', 'data', 'demo-equipment-1000.csv')
DEMO_DATA_JSON = os.path.join(FRONTEND_DIR, 'mock', 'demo-data.json')

CATALOG_FILE = os.path.join(BASE_DIR, 'catalog', 'machines.json')
try:
    with open(CATALOG_FILE, 'r') as f:
        MACHINE_CATALOG = json.load(f)
    MACHINES = {m['id']: m for m in MACHINE_CATALOG['machines']}
except Exception as e:
    print(f'Warning: Could not load machine catalog: {e}')
    MACHINES = {}

# --- Load ML Artifacts (Once at startup) ---
try:
    with open(os.path.join(ML_DIR, 'metrics.json'), 'r') as f:
        METRICS = json.load(f)
    
    with open(os.path.join(ML_DIR, 'feature_names.json'), 'r') as f:
        FEATURE_NAMES_CONF = json.load(f)
        
    FEATURE_COLS = FEATURE_NAMES_CONF['feature_columns']
    MODE_COLS = FEATURE_NAMES_CONF.get('mode_columns', ['TWF', 'HDF', 'PWF', 'OSF', 'RNF'])
    ID_COLS = FEATURE_NAMES_CONF.get('id_columns', ['UDI', 'Product ID', 'Type'])

    selected_model_name = METRICS['selected_model']
    sel_key = METRICS.get('selected_key', 'gb')
    selected_model = joblib.load(os.path.join(ML_DIR, f'model_{sel_key}.joblib'))
    preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor.joblib'))
except Exception as e:
    print(f"Error loading ML artifacts: {e}")
    # Defaulting variables for safety if failed to load
    METRICS = {}
    FEATURE_COLS = ['Machine_Family', 'Age_Days', 'Power_kW', 'Sensor_Vibration_mm_s', 'Sensor_Temperature_C', 'Sensor_Pressure_bar', 'Sensor_Current_A', 'Sensor_Speed_RPM']
    MODE_COLS = ['Failure_Mode']
    preprocessor = None
    selected_model = None
    selected_model_name = "Realistic Multi-Machine Model"

# --- Load Demo Mode Content ---
try:
    with open(DEMO_DATA_JSON, 'r') as f:
        DEMO_CONTENT = json.load(f)
        MODE_CONTENT = DEMO_CONTENT.get('modeContent', {})
except Exception:
    MODE_CONTENT = {}

FACTOR_MAPPING = {
    'Torque [Nm]': {'label': 'Torque', 'interpretation': 'Elevated mechanical load', 'area': 'drive_assembly', 'area_label': 'Drive / Tool Assembly'},
    'Rotational speed [rpm]': {'label': 'Rotational speed', 'interpretation': 'Rotational stress', 'area': 'spindle', 'area_label': 'Spindle'},
    'Tool wear [min]': {'label': 'Tool wear', 'interpretation': 'Tool degradation', 'area': 'tool_holder', 'area_label': 'Tool Holder'},
    'Air temperature [K]': {'label': 'Air temperature', 'interpretation': 'Ambient thermal stress', 'area': 'coolant_line', 'area_label': 'Coolant Line'},
    'Process temperature [K]': {'label': 'Process temperature', 'interpretation': 'Process thermal stress', 'area': 'motor', 'area_label': 'Drive Motor'},
    'Machine_Family': {'label': 'Machine Type', 'interpretation': 'Inherent design risk', 'area': 'system', 'area_label': 'General System'},
    'Age_Days': {'label': 'Operating Age', 'interpretation': 'General wear and tear', 'area': 'system', 'area_label': 'General System'},
    'Power_kW': {'label': 'Rated Power', 'interpretation': 'Heavy electrical load', 'area': 'motor', 'area_label': 'Drive Motor'},
    'Sensor_Vibration_mm_s': {'label': 'Vibration (mm/s)', 'interpretation': 'Mechanical imbalance or bearing wear', 'area': 'bearing', 'area_label': 'Bearings'},
    'Sensor_Temperature_C': {'label': 'Temperature (C)', 'interpretation': 'Thermal overload', 'area': 'cooling', 'area_label': 'Cooling System'},
    'Sensor_Pressure_bar': {'label': 'Pressure (bar)', 'interpretation': 'Fluid dynamic issues like cavitation', 'area': 'impeller', 'area_label': 'Impeller / Compressor Element'},
    'Sensor_Current_A': {'label': 'Current (A)', 'interpretation': 'Electrical overload', 'area': 'motor', 'area_label': 'Drive Motor'},
    'Sensor_Speed_RPM': {'label': 'Speed (RPM)', 'interpretation': 'Rotational anomaly', 'area': 'shaft', 'area_label': 'Main Shaft'}
}

def get_risk_level(score):
    if score < 20: return "low"
    if score < 45: return "medium"
    if score < 75: return "high"
    return "critical"

def get_model_status(level):
    if level in ["low", "medium"]: return "Normal Operation"
    return "At Risk"

def get_explainer(model, X_transformed):
    # Depending on model type, return the appropriate explainer
    if isinstance(model, (shap.TreeExplainer,)): # Just a check, actually we test class name
        pass
    
    # Try tree explainer first
    try:
        explainer = shap.TreeExplainer(model)
        # Check if it initialized properly
        return explainer
    except Exception:
        # Fallback to linear explainer
        # For linear explainer we typically need the data or masker
        masker = shap.maskers.Independent(X_transformed)
        explainer = shap.LinearExplainer(model, masker)
        return explainer

def compute_shap_batch(df_features, model=None):
    if model is None: model = selected_model
    
    X_transformed = df_features
    if preprocessor:
        X_transformed = preprocessor.transform(df_features)
        
    explainer = get_explainer(model, X_transformed)
    
    # Calculate shap values
    shap_values = explainer.shap_values(X_transformed)
    
    # shap_values could be a list (multi-class or some tree models) or array
    if isinstance(shap_values, list):
        shap_values = shap_values[1] # Assume binary classification, take positive class
        
    return shap_values, explainer.expected_value

@app.route('/api/machines', methods=['GET'])
def get_machines():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 1000))
    start = (page - 1) * limit
    
    # Group machines by family/type to interleave them
    by_family = {}
    for m in MACHINES.values():
        fam = m.get('family', m.get('type', 'other'))
        by_family.setdefault(fam, []).append({
            "id": m["id"],
            "name": m["name"],
            "type": m["type"],
            "type_label": m["type_label"],
            "manufacturer": m["manufacturer"],
            "model": m["model"],
            "description": m.get("description", ""),
            "image": m["image"],
            "assessment_method": m["assessment_method"]
        })
    
    # Round-robin interleave so adjacent cards show diverse equipment types & images
    summary = []
    max_len = max(len(lst) for lst in by_family.values()) if by_family else 0
    for idx in range(max_len):
        for fam_list in by_family.values():
            if idx < len(fam_list):
                summary.append(fam_list[idx])
    
    total = len(summary)
    summary = summary[start:start+limit]
    return jsonify({"machines": summary, "total": total, "page": page, "limit": limit})

@app.route('/api/machines/search', methods=['GET'])
def search_machines():
    query = request.args.get('q', '').lower()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    
    results = []
    for m in MACHINES.values():
        searchable_text = f"{m['name']} {m.get('family', '')} {m['type']} {m['manufacturer']} {m['model']} {m['id']} {' '.join(m.get('application', []))}".lower()
        if not query or query in searchable_text:
            results.append({
                "id": m["id"],
                "name": m["name"],
                "type": m["type"],
                "type_label": m["type_label"],
                "manufacturer": m["manufacturer"],
                "model": m["model"],
                "description": m.get("description", ""),
                "image": m["image"],
                "assessment_method": m["assessment_method"]
            })
            
    total = len(results)
    results = results[start:start+limit]
    return jsonify({"machines": results, "total": total, "page": page, "limit": limit})

@app.route('/api/machines/<machine_id>', methods=['GET'])
def get_machine(machine_id):
    if machine_id in MACHINES:
        return jsonify(MACHINES[machine_id])
    return jsonify({"error": "Machine not found"}), 404

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'machine_id' not in data or 'values' not in data:
        return jsonify({"error": "Missing machine_id or values"}), 400
        
    machine_id = data['machine_id']
    values = data['values']
    
    if machine_id not in MACHINES:
        return jsonify({"error": "Machine not found"}), 404
        
    engine = get_engine(machine_id)
    if not engine:
        return jsonify({"error": "Diagnostic engine not found for this machine type"}), 500
        
    try:
        response = engine.predict(values)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    is_demo = False
    filename = "unknown.csv"
    
    # Check if demo
    if request.is_json and request.get_json().get('demo'):
        is_demo = True
        filename = "demo-equipment-1000.csv"
        try:
            df = pd.read_csv(DEMO_CSV)
        except Exception as e:
            return jsonify({"error": f"Could not read demo file: {e}"}), 500
    else:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Invalid file type. Only CSV is allowed."}), 400
            
        filename = secure_filename(file.filename)
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({"error": f"Error parsing CSV: {e}"}), 400

    if df.empty:
        return jsonify({"error": "The uploaded file is empty."}), 400

    # Validate columns
    missing_cols = [c for c in FEATURE_COLS if c not in df.columns]
    if missing_cols:
        return jsonify({"error": f"Missing required columns: {', '.join(missing_cols)}"}), 400

    if is_demo and len(df) > 1000:
        df = df.head(1000)
    elif len(df) > 1000:
        return jsonify({"error": "Exceeded maximum of 1000 records. Please upload a smaller dataset."}), 400

    # Validate numeric for numeric columns only
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for col in num_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Try to convert
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if df[num_cols].isna().any().any():
        return jsonify({"error": "Dataset contains non-numeric or missing values in numeric feature columns."}), 400

    df_features = df[FEATURE_COLS].copy()
    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')
        
    req_model = request.form.get('model') or (request.get_json().get('model') if request.is_json else None) or 'auto'
    
    # Load specific model if requested
    active_model = selected_model
    active_model_name = selected_model_name
    if req_model and req_model != 'auto':
        # Find the model key by name in METRICS
        for m in METRICS['models']:
            if m['name'] == req_model:
                try:
                    active_model = joblib.load(os.path.join(ML_DIR, f"model_{m['id']}.joblib"))
                    active_model_name = req_model
                except Exception as e:
                    return jsonify({"error": f"Requested model artifact unavailable: {e}"}), 400
                break
        else:
            return jsonify({"error": "Invalid model requested."}), 400
    
    # Transform and predict
    X_transformed = df_features
    if preprocessor:
        X_transformed = preprocessor.transform(df_features)
    probas = active_model.predict_proba(X_transformed)[:, 1]
    
    # Calculate SHAP in batch
    try:
        shap_values_batch, expected_value = compute_shap_batch(df_features, active_model)
    except Exception as e:
        print(f"Error computing SHAP: {e}")
        shap_values_batch = np.zeros(X_transformed.shape)

    analysis_id = f"an-{datetime.datetime.now().strftime('%Y%md%H%M%S')}-{uuid.uuid4().hex[:6]}"
    
    records = []
    summary = {"analysed": len(df), "critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for idx, row in df.iterrows():
        prob = float(probas[idx])
        risk_score = round(prob * 100, 1)
        risk_level = get_risk_level(risk_score)
        
        summary[risk_level] += 1
        
        # ID logic
        equip_id = f"EQ-{idx+1}"
        if 'Product ID' in row and pd.notna(row['Product ID']):
            equip_id = str(row['Product ID'])
        elif 'UDI' in row and pd.notna(row['UDI']):
            equip_id = str(row['UDI'])
            
        equip_type = str(row.get('Type', 'Unknown'))
        
        # Observed mode logic
        observed_mode = None
        for mode in MODE_COLS:
            if mode in row and pd.notna(row[mode]):
                val = row[mode]
                try:
                    if float(val) == 1.0:
                        observed_mode = mode
                        break
                except:
                    if isinstance(val, str) and val.lower() not in ['none', '0', 'false', '']:
                        observed_mode = val
                        break
                
        # SHAP processing
        s_vals = shap_values_batch[idx]
        
        factors = []
        for i, col in enumerate(FEATURE_COLS):
            s_val = float(s_vals[i])
            try: actual_val = float(row[col])
            except: actual_val = row[col]
            
            factors.append({
                "feature": col,
                "label": FACTOR_MAPPING.get(col, {}).get('label', col),
                "contribution": abs(s_val),
                "direction": "raises" if s_val > 0 else "lowers",
                "shapValue": s_val,
                "actualValue": actual_val
            })
            
        factors = sorted(factors, key=lambda x: x['contribution'], reverse=True)
        top_factor = factors[0]
        
        # Mode content
        use_mode = observed_mode if observed_mode else 'none'
        mod_info = MODE_CONTENT.get(use_mode, MODE_CONTENT.get('none', {}))
        
        records.append({
            "id": equip_id,
            "type": equip_type,
            "probability": prob,
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "modelStatus": get_model_status(risk_level),
            "observedFailureMode": observed_mode,
            "factors": factors,
            "topFactor": top_factor['label'],
            "inspectionArea": FACTOR_MAPPING.get(top_factor['feature'], {}).get('area', 'unknown'),
            "inspectionAreaLabel": FACTOR_MAPPING.get(top_factor['feature'], {}).get('area_label', 'Unknown Area'),
            "interpretation": FACTOR_MAPPING.get(top_factor['feature'], {}).get('interpretation', 'Unknown issue'),
            "consequence": mod_info.get("consequence", ""),
            "recommendation": mod_info.get("recommendation", {}),
            "values": {col: (float(row[col]) if isinstance(row[col], (int, float)) or (isinstance(row[col], str) and row[col].replace('.','',1).isdigit()) else row[col]) for col in FEATURE_COLS}
        })

    risk_dist = [
        {"level": "critical", "label": "Critical", "count": summary["critical"]},
        {"level": "high", "label": "High", "count": summary["high"]},
        {"level": "medium", "label": "Medium", "count": summary["medium"]},
        {"level": "low", "label": "Low", "count": summary["low"]}
    ]

    return jsonify({
        "analysisId": analysis_id,
        "datasetName": filename,
        "isDemo": is_demo,
        "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
        "model": active_model_name,
        "summary": summary,
        "riskDistribution": risk_dist,
        "records": records,
        "models": METRICS.get("models", []),
        "selection": {
            "selected": selected_model_name,
            "criterion": METRICS.get("selection_criterion", "highest PR-AUC"),
            "criterionKey": METRICS.get("selection_criterion_key", "prAuc")
        }
    })

@app.route('/api/explain', methods=['POST'])
def explain():
    data = request.get_json()
    if not data or 'values' not in data:
        return jsonify({"error": "Missing 'values' in payload"}), 400
        
    values = data['values']
    
    # Validate
    for col in FEATURE_COLS:
        if col not in values:
            return jsonify({"error": f"Missing feature: {col}"}), 400
            
    df_features = pd.DataFrame([values])[FEATURE_COLS]
    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')
    
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for col in num_cols:
        df_features[col] = pd.to_numeric(df_features[col], errors='coerce')
        if pd.isna(df_features[col]).any():
            return jsonify({"error": f"Invalid numeric value for {col}"}), 400
            
    X_transformed = preprocessor.transform(df_features)
    prob = selected_model.predict_proba(X_transformed)[0, 1]
    
    try:
        shap_values_batch, _ = compute_shap_batch(df_features)
        s_vals = shap_values_batch[0]
    except Exception as e:
        s_vals = np.zeros(len(FEATURE_COLS))

    factors = []
    for i, col in enumerate(FEATURE_COLS):
        s_val = float(s_vals[i])
        factors.append({
            "feature": col,
            "label": FACTOR_MAPPING[col]['label'],
            "contribution": abs(s_val),
            "direction": "raises" if s_val > 0 else "lowers",
            "shapValue": s_val,
            "actualValue": str(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], str) else float(df_features[col].iloc[0])
        })
        
    factors = sorted(factors, key=lambda x: x['contribution'], reverse=True)
    top_factor = factors[0]

    risk_score = round(float(prob) * 100, 1)
    risk_level = get_risk_level(risk_score)
    
    # We don't have observed mode, default to 'none' for content
    mod_info = MODE_CONTENT.get('none', {})
    
    res = {
        "probability": float(prob),
        "riskScore": risk_score,
        "riskLevel": risk_level,
        "modelStatus": get_model_status(risk_level),
        "factors": factors,
        "topFactor": top_factor['label'],
        "inspectionArea": FACTOR_MAPPING.get(top_factor['feature'], {}).get('area', 'unknown'),
        "inspectionAreaLabel": FACTOR_MAPPING.get(top_factor['feature'], {}).get('area_label', 'Unknown Area'),
        "interpretation": FACTOR_MAPPING.get(top_factor['feature'], {}).get('interpretation', 'Unknown issue'),
        "consequence": mod_info.get("consequence", ""),
        "recommendation": mod_info.get("recommendation", {}),
        "values": {col: str(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], str) else float(df_features[col].iloc[0]) for col in FEATURE_COLS}
    }
    
    return jsonify(res)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    if not data or 'baseline' not in data or 'scenario' not in data:
        return jsonify({"error": "Missing baseline or scenario in payload"}), 400
        
    baseline = data['baseline']
    scenario = data['scenario']
    req_model = data.get('model', 'auto')

    active_model = selected_model
    if req_model and req_model != 'auto':
        for m in METRICS['models']:
            if m['name'] == req_model:
                try:
                    active_model = joblib.load(os.path.join(ML_DIR, f"model_{m['id']}.joblib"))
                except:
                    pass
                break
    
    df_baseline = pd.DataFrame([baseline])[FEATURE_COLS]
    df_scenario = pd.DataFrame([scenario])[FEATURE_COLS]
    
    if 'Machine_Family' in df_baseline.columns:
        df_baseline['Machine_Family'] = df_baseline['Machine_Family'].astype('category')
        df_scenario['Machine_Family'] = df_scenario['Machine_Family'].astype('category')
        
    # validate
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for df_tmp, name in [(df_baseline, 'baseline'), (df_scenario, 'scenario')]:
        for col in num_cols:
            df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')
            if pd.isna(df_tmp[col]).any():
                return jsonify({"error": f"Invalid numeric value for {col} in {name}"}), 400

    base_prob = active_model.predict_proba(preprocessor.transform(df_baseline))[0, 1]
    scen_prob = active_model.predict_proba(preprocessor.transform(df_scenario))[0, 1]
    
    base_score = round(float(base_prob) * 100, 1)
    scen_score = round(float(scen_prob) * 100, 1)
    
    change = round(scen_score - base_score, 1)
    direction = "increase" if change > 0 else "decrease" if change < 0 else "no change"
    
    return jsonify({
        "baselineScore": base_score,
        "baselineLevel": get_risk_level(base_score),
        "scenarioScore": scen_score,
        "scenarioLevel": get_risk_level(scen_score),
        "change": abs(change),
        "changeDirection": direction
    })

@app.route('/api/model-info', methods=['GET'])
def model_info():
    return jsonify(METRICS)

@app.route('/api/firebase-config', methods=['GET'])
def firebase_config():
    config_str = os.environ.get('FIREBASE_CONFIG')
    if config_str:
        try:
            return jsonify(json.loads(config_str))
        except:
            return jsonify({"configured": False})
    return jsonify({"configured": False})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "model": selected_model_name,
        "features": len(FEATURE_COLS)
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
