with open('backend/engines/cnc_engine.py', 'r') as f:
    content = f.read()

old_load = '''        try:
            with open(os.path.join(ML_DIR, 'metrics.json'), 'r') as f:
                metrics = json.load(f)
            self.preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor.joblib'))
            model_key = metrics.get('selected_key', 'gradient_boosting')
            self.model = joblib.load(os.path.join(ML_DIR, f'model_{model_key}.joblib'))'''

new_load = '''        try:
            self.preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor_cnc.joblib'))
            self.model = joblib.load(os.path.join(ML_DIR, 'model_gradient_boosting.joblib'))'''

content = content.replace(old_load, new_load)

with open('backend/engines/cnc_engine.py', 'w') as f:
    f.write(content)
print("Patched cnc_engine.py")
