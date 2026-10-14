with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_val = '''"actualValue": float(df_features[col].iloc[0])'''
new_val = '''"actualValue": float(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], (int, float)) or (isinstance(df_features[col].iloc[0], str) and df_features[col].iloc[0].replace('.','',1).isdigit()) else df_features[col].iloc[0]'''

content = content.replace(old_val, new_val)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
