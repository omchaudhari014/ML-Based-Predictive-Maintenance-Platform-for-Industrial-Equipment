import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_val = '''    # validate
    for df_tmp, name in [(df_baseline, 'baseline'), (df_scenario, 'scenario')]:
        for col in FEATURE_COLS:
            df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')
            if pd.isna(df_tmp[col]).any():
                return jsonify({"error": f"Invalid numeric value for {col} in {name}"}), 400'''

new_val = '''    # validate
    num_cols = [c for c in FEATURE_COLS if c != 'Machine_Family']
    for df_tmp, name in [(df_baseline, 'baseline'), (df_scenario, 'scenario')]:
        for col in num_cols:
            df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')
            if pd.isna(df_tmp[col]).any():
                return jsonify({"error": f"Invalid numeric value for {col} in {name}"}), 400'''

content = content.replace(old_val, new_val)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
