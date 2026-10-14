with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("let currentDisplayCount = 50;", "let currentDisplayCount = 300;")
content = content.replace("currentDisplayCount = 50;", "currentDisplayCount = 300;")
content = content.replace("currentDisplayCount += 50;", "currentDisplayCount += 300;")

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
