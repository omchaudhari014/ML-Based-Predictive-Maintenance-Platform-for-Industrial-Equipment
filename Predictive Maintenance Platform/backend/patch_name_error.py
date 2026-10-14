import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("active_model_name = selected_model_key", "active_model_name = selected_model_name")

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched selected_model_key variable")
