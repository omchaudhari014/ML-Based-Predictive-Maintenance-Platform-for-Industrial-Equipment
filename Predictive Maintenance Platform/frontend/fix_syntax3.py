with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Load More (Showing" in line:
        lines[i] = "    const moreBtn = el('button', { class: 'btn btn--secondary', style: 'grid-column: 1 / -1; margin-top: var(--s-4);' }, Load More (Showing  of ));\n"

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
