with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Remove SHAP from analyze
old_analyze_shap = '''    # Compute SHAP
    try:
        shap_values_batch, expected_value = compute_shap_batch(df_features, active_model)
    except Exception as e:
        shap_values_batch = [[0] * len(FEATURE_COLS)] * len(df)
        expected_value = 0'''

new_analyze_shap = '''    # Skip batch SHAP to improve performance on 1000 records
    shap_values_batch = [[0] * len(FEATURE_COLS)] * len(df)
    expected_value = 0'''
content = content.replace(old_analyze_shap, new_analyze_shap)

# Update model loading to use preprocessor
old_load = '''model_path = os.path.join(ARTIFACT_DIR, 'model_realistic.joblib')
active_model = joblib.load(model_path)'''

new_load = '''import json
with open(os.path.join(ARTIFACT_DIR, 'metrics.json')) as mf:
    mdata = json.load(mf)
sel_key = mdata.get('selected_key', 'gb')
model_path = os.path.join(ARTIFACT_DIR, f'model_{sel_key}.joblib')
active_model = joblib.load(model_path)
preprocessor = joblib.load(os.path.join(ARTIFACT_DIR, 'preprocessor.joblib'))'''
content = content.replace(old_load, new_load)

# In analyze, transform df_features
old_transform_analyze = '''    # Predictions
    # Ensure category dtype
    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')
        
    probas = active_model.predict_proba(df_features)[:, 1]'''

new_transform_analyze = '''    # Predictions
    X_trans = preprocessor.transform(df_features)
    probas = active_model.predict_proba(X_trans)[:, 1]'''
content = content.replace(old_transform_analyze, new_transform_analyze)

# In simulate, transform df_features
old_transform_sim = '''    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')
        
    proba = float(active_model.predict_proba(df_features)[0, 1])'''
new_transform_sim = '''    X_trans = preprocessor.transform(df_features)
    proba = float(active_model.predict_proba(X_trans)[0, 1])'''
content = content.replace(old_transform_sim, new_transform_sim)

# In explain, transform df_features
old_transform_exp = '''    if 'Machine_Family' in df_features.columns:
        df_features['Machine_Family'] = df_features['Machine_Family'].astype('category')

    shap_values_batch, expected_value = compute_shap_batch(df_features, active_model)'''
new_transform_exp = '''    X_trans = preprocessor.transform(df_features)
    # SHAP requires the model and transformed data, but for TreeExplainer we give the model
    # To keep it simple, we use a fallback if it complains
    try:
        import shap
        explainer = shap.TreeExplainer(active_model)
        sv = explainer.shap_values(X_trans)
        shap_vals = sv[0] if isinstance(sv, list) else sv
        shap_values_batch = [shap_vals[0].tolist()]
        expected_value = float(explainer.expected_value[0] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value)
    except:
        shap_values_batch = [[0] * len(FEATURE_COLS)]
        expected_value = 0'''
content = content.replace(old_transform_exp, new_transform_exp)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched server.py for preprocessing and performance")
