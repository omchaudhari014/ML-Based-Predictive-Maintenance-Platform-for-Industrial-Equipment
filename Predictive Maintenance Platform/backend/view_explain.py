with open('backend/server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_explain = False
for line in lines:
    if "def explain" in line:
        in_explain = True
    if in_explain:
        print(line, end='')
    if in_explain and "return jsonify" in line and "expected_value" in line:
        break
