with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_global_load = '''    preprocessor = None
    selected_model_name = METRICS['selected_model']
    selected_model = joblib.load(os.path.join(ML_DIR, 'model_realistic.joblib'))'''

new_global_load = '''    selected_model_name = METRICS['selected_model']
    sel_key = METRICS.get('selected_key', 'gb')
    selected_model = joblib.load(os.path.join(ML_DIR, f'model_{sel_key}.joblib'))
    preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor.joblib'))'''

content = content.replace(old_global_load, new_global_load)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed global model loading!")
