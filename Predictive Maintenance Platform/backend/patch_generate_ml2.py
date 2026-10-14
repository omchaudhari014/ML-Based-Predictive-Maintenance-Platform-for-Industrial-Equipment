with open('backend/generate_ml2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('backend/generate_ml2.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if 'FunctionTransformer' in line or 'dummy_preprocessor' in line:
            continue
        f.write(line)
