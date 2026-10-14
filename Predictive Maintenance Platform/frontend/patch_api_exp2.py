with open('frontend/js/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("activeRecord.explanation = data.explanation;", "activeRecord.explanation = data.factors;")

with open('frontend/js/api.js', 'w', encoding='utf-8') as f:
    f.write(content)
