with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("container.textContent = 'Failed to load diagnostics.';", "container.textContent = err.message || 'Failed to load diagnostics.';")

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)

