import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_val = '''    # Transform and predict
    X_transformed = preprocessor.transform(df_features)
    probas = active_model.predict_proba(X_transformed)[:, 1]'''

new_val = '''    # Transform and predict
    X_transformed = df_features
    if preprocessor:
        X_transformed = preprocessor.transform(df_features)
    probas = active_model.predict_proba(X_transformed)[:, 1]'''

content = content.replace(old_val, new_val)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
