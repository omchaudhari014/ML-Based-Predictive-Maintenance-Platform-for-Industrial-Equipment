with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '''"values": {col: float(row[col]) for col in FEATURE_COLS}''',
    '''"values": {col: (float(row[col]) if isinstance(row[col], (int, float)) or (isinstance(row[col], str) and row[col].replace('.','',1).isdigit()) else row[col]) for col in FEATURE_COLS}'''
)
content = content.replace(
    '''"values": {col: float(df_features[col].iloc[0]) for col in FEATURE_COLS}''',
    '''"values": {col: (float(df_features[col].iloc[0]) if isinstance(df_features[col].iloc[0], (int, float)) or (isinstance(df_features[col].iloc[0], str) and df_features[col].iloc[0].replace('.','',1).isdigit()) else df_features[col].iloc[0]) for col in FEATURE_COLS}'''
)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
