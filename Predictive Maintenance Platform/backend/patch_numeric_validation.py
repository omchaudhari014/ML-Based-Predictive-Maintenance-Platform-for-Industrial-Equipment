import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_val = '''    # Validate numeric
    for col in FEATURE_COLS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Try to convert
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if df[FEATURE_COLS].isna().any().any():
        return jsonify({"error": "Dataset contains non-numeric or missing values in feature columns."}), 400'''

new_val = '''    # Validate numeric for numeric columns only
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for col in num_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Try to convert
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if df[num_cols].isna().any().any():
        return jsonify({"error": "Dataset contains non-numeric or missing values in numeric feature columns."}), 400'''

content = content.replace(old_val, new_val)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
