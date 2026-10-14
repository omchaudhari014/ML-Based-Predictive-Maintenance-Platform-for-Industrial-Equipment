with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("Load More (Showing  of )", "Load More (Showing  of )")

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
