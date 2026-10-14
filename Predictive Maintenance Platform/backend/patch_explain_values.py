with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_vals = '''"values": {col: (float(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], (int, float)) or (isinstance(df_features[col].iloc[0], str) and df_features[col].iloc[0].replace('.','',1).isdigit()) else df_features[col].iloc[0]) for col in FEATURE_COLS}'''
new_vals = '''"values": {col: str(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], str) else float(df_features[col].iloc[0]) for col in FEATURE_COLS}'''

content = content.replace(old_vals, new_vals)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
