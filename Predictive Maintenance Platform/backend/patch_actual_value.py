with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Replace the complicated actualValue line
pattern = re.compile(r'\"actualValue\": float\(df_features\[col\]\.iloc\[0\]\).*?\n', re.DOTALL)
new_actual_value = '''"actualValue": str(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], str) else float(df_features[col].iloc[0])\n'''
content = pattern.sub(new_actual_value, content)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched actualValue safely")
