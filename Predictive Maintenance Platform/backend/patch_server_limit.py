import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_val = '''    if len(df) > 1000:
        return jsonify({"error": "Exceeded maximum of 1000 records. Please upload a smaller dataset."}), 400'''

new_val = '''    if is_demo and len(df) > 1000:
        df = df.head(1000)
    elif len(df) > 1000:
        return jsonify({"error": "Exceeded maximum of 1000 records. Please upload a smaller dataset."}), 400'''

content = content.replace(old_val, new_val)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched server.py to limit demo df to 1000 rows")
