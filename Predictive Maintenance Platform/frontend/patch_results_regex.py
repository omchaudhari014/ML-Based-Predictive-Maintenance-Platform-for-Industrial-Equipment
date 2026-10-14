with open('frontend/results.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Find any href targeting machine.html with id
content = re.sub(r'href: machine\.html\?id=\$\{r\.id\}', r'href: machine.html?recordId=', content)

with open('frontend/results.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Regex patched results.html")
