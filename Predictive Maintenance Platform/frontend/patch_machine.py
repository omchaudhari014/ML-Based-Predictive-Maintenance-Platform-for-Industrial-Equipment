import sys

with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_cb = '''onComponentClick: (comp) => {
        if (!comp) {
          compCard.style.display = 'none';
          return;
        }
        compCard.style.display = 'block';
        clear(compCard);
        mount(compCard, el('h3', {}, comp.name || 'Component Info'));
        if (comp.userData && comp.userData.description) {
          mount(compCard, el('p', { style: 'margin-top: var(--s-2)' }, comp.userData.description));
        }
      }'''

new_cb = '''onComponentClick: (compKey) => {
        if (!compKey) {
          compCard.style.display = 'none';
          return;
        }
        // compKey could be an object if updated, or string. Normalize to string id.
        const id = typeof compKey === 'string' ? compKey : compKey.id;
        const c = (machine.components || []).find(x => x.id === id) || { id, name: id, description: 'No description available' };
        
        compCard.style.display = 'block';
        clear(compCard);
        mount(compCard, el('h3', {}, c.name || 'Component Info'));
        mount(compCard, el('p', { style: 'margin-top: var(--s-2)' }, c.description || ''));
      }'''

content = content.replace(old_cb, new_cb)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched machine.html component click handler")
