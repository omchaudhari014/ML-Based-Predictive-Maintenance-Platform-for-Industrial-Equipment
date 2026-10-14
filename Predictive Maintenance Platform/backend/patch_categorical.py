import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_val = '''    df_features = df[FEATURE_COLS]
    
    req_model = request.form.get('model') or (request.get_json().get('model') if request.is_json else None) or 'auto'
'''

new_val = '''    df_features = df[FEATURE_COLS].copy()
    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')
        
    req_model = request.form.get('model') or (request.get_json().get('model') if request.is_json else None) or 'auto'
'''

content = content.replace(old_val, new_val)

old_val2 = '''    df_features = pd.DataFrame([values])[FEATURE_COLS]
    for col in FEATURE_COLS:
        df_features[col] = pd.to_numeric(df_features[col], errors='coerce')'''

new_val2 = '''    df_features = pd.DataFrame([values])[FEATURE_COLS]
    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')
    
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for col in num_cols:
        df_features[col] = pd.to_numeric(df_features[col], errors='coerce')'''

content = content.replace(old_val2, new_val2)

old_val3 = '''    df_baseline = pd.DataFrame([baseline])[FEATURE_COLS]
    df_scenario = pd.DataFrame([scenario])[FEATURE_COLS]
    
    # validate
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for df_tmp, name in [(df_baseline, 'baseline'), (df_scenario, 'scenario')]:
        for col in num_cols:
            df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')
            if pd.isna(df_tmp[col]).any():
                return jsonify({"error": f"Invalid numeric value for {col} in {name}"}), 400'''

new_val3 = '''    df_baseline = pd.DataFrame([baseline])[FEATURE_COLS]
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
                return jsonify({"error": f"Invalid numeric value for {col} in {name}"}), 400'''

content = content.replace(old_val3, new_val3)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched server.py for categorical casting")
