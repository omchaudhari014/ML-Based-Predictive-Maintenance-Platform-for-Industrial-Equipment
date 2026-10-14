with open('frontend/results.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('href: machine.html?id=', 'href: machine.html?recordId=')

with open('frontend/results.html', 'w', encoding='utf-8') as f:
    f.write(content)
