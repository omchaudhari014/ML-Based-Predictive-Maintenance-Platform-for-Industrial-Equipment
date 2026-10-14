import sys

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_render = '''function renderCards(machines) {
  clear(grid);
  if (machines.length === 0) {
    mount(grid, el('div', { class: 'empty' }, 'No machines found.'));
    return;
  }
  
  machines.forEach(m => {'''

new_render = '''
let currentDisplayCount = 50;
let currentList = [];

function renderCards(machines, reset = true) {
  if (reset) {
    currentDisplayCount = 50;
    currentList = machines;
    clear(grid);
  }
  
  const toShow = currentList.slice(0, currentDisplayCount);
  
  if (reset) {
    if (machines.length === 0) {
      mount(grid, el('div', { class: 'empty' }, 'No machines found.'));
      return;
    }
  } else {
    clear(grid);
  }
  
  toShow.forEach(m => {'''

content = content.replace(old_render, new_render)

old_mount = '''mount(grid, card);
  });
}'''

new_mount = '''mount(grid, card);
  });
  
  if (currentDisplayCount < currentList.length) {
    const moreBtn = el('button', { class: 'btn btn--secondary', style: 'grid-column: 1 / -1; margin-top: var(--s-4);' }, Load More (Showing  of ));
    moreBtn.onclick = () => {
      currentDisplayCount += 50;
      renderCards(currentList, false);
    };
    mount(grid, moreBtn);
  }
}'''

content = content.replace(old_mount, new_mount)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added pagination to index.html")
