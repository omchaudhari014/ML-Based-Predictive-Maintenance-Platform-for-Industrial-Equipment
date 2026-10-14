with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We will just rewrite the initialization block
old_block = '''    preprocessor = joblib.load(os.path.join(ML_DIR, 'preprocessor.joblib'))
    selected_model_name = METRICS['selected_model']
    selected_model_key = METRICS.get('selected_key', 'gradient_boosting')
    selected_model = joblib.load(os.path.join(ML_DIR, f'model_{selected_model_key}.joblib'))'''

new_block = '''    preprocessor = None
    selected_model_name = METRICS['selected_model']
    selected_model = joblib.load(os.path.join(ML_DIR, 'model_realistic.joblib'))'''

content = content.replace(old_block, new_block)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
