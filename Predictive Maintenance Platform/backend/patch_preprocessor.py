import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace compute_shap_batch
old_compute = '''def compute_shap_batch(df_features, model=None):
    if model is None: model = selected_model
    X_transformed = preprocessor.transform(df_features)
    explainer = get_explainer(model, X_transformed)
    
    # Calculate shap values
    shap_values = explainer.shap_values(X_transformed)'''

new_compute = '''def compute_shap_batch(df_features, model=None):
    if model is None: model = selected_model
    
    X_transformed = df_features
    if preprocessor:
        X_transformed = preprocessor.transform(df_features)
        
    explainer = get_explainer(model, X_transformed)
    
    # Calculate shap values
    shap_values = explainer.shap_values(X_transformed)'''

content = content.replace(old_compute, new_compute)

# And loading preprocessor
old_load = '''        realistic_pipeline = joblib.load(os.path.join(ML_DIR, 'realistic_model.joblib'))
        preprocessor = realistic_pipeline.named_steps['preprocessor']
        selected_model = realistic_pipeline.named_steps['classifier']'''

new_load = '''        preprocessor = None
        selected_model = joblib.load(os.path.join(ML_DIR, 'model_realistic.joblib'))'''

content = content.replace(old_load, new_load)

# Fix where simulate calls preprocessor directly
old_sim = '''base_prob = active_model.predict_proba(preprocessor.transform(df_baseline))[0, 1]
    scenario_prob = active_model.predict_proba(preprocessor.transform(df_scenario))[0, 1]'''

new_sim = '''
    X_base = preprocessor.transform(df_baseline) if preprocessor else df_baseline
    X_scen = preprocessor.transform(df_scenario) if preprocessor else df_scenario
    base_prob = active_model.predict_proba(X_base)[0, 1]
    scenario_prob = active_model.predict_proba(X_scen)[0, 1]'''

content = content.replace(old_sim, new_sim)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched server.py for preprocessor tolerance")
