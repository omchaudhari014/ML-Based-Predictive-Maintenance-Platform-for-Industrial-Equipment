import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r"\}\,\s*Load More \(Showing\s+of\s*\)\);",
    "}, Load More (Showing  of ));",
    content
)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
