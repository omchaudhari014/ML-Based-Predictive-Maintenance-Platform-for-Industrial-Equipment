with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_render = '''    if (pred) {
      const diagCard = el('div', { class: 'card' }, [
        el('h3', {}, 'Diagnostic Summary'),
        el('p', { style: 'margin: var(--s-2) 0; font-weight: bold; color: var(--risk-critical);' }, pred.predicted_failure_mode || 'Normal'),
        el('div', { style: 'margin-top: var(--s-4);' }, [
          el('h4', {}, 'Recommendations'),
          el('ul', { style: 'padding-left: var(--s-4); margin-top: var(--s-2);' }, 
            (pred.recommendations||[]).map(r => el('li', { style: 'margin-bottom: var(--s-1)' }, [] ))
          )
        ])
      ]);
      mount(sidePanel, diagCard);
    }'''

new_render = '''    if (pred) {
      const causesHtml = (pred.causes && pred.causes.length) ? 
        el('div', { style: 'margin-top: var(--s-3);' }, [ el('h4', {}, 'Causes'), el('ul', { style: 'padding-left: var(--s-4); margin-top: 4px;' }, pred.causes.map(c => el('li', {}, c))) ]) : null;
        
      const risksHtml = (pred.consequences && pred.consequences.length) ? 
        el('div', { style: 'margin-top: var(--s-3);' }, [ el('h4', {}, 'Risks / Consequences'), el('ul', { style: 'padding-left: var(--s-4); margin-top: 4px;' }, pred.consequences.map(c => el('li', {}, c))) ]) : null;
        
      const diagCard = el('div', { class: 'card', style: 'border-left: 4px solid var(--risk-critical);' }, [
        el('h3', {}, 'Diagnostic Summary'),
        el('div', { style: 'margin: var(--s-2) 0; font-size: 1.1em;' }, [
          el('span', { style: 'font-weight: bold;' }, 'Detected Issue: '),
          el('span', { style: 'color: var(--risk-critical); font-weight: bold;' }, pred.predicted_failure_mode || 'Anomaly Detected')
        ]),
        causesHtml,
        risksHtml,
        el('div', { style: 'margin-top: var(--s-3); padding: var(--s-3); background: var(--surface-2); border-radius: var(--r-sm);' }, [
          el('h4', {}, 'Advices & Recommendations'),
          el('ul', { style: 'padding-left: var(--s-4); margin-top: var(--s-2);' }, 
            (pred.recommendations||[]).map(r => el('li', { style: 'margin-bottom: var(--s-1)' }, [] ))
          )
        ])
      ]);
      mount(sidePanel, diagCard);
    }
    
    // Add machine description
    const descCard = el('div', { class: 'card', style: 'margin-top: var(--s-4);' }, [
      el('h3', {}, 'Machine Overview'),
      el('p', { style: 'margin-top: var(--s-2); line-height: 1.5; color: var(--text-secondary);' }, machine.description || 'No description available for this model.')
    ]);
    mount(sidePanel, descCard);'''

content = content.replace(old_render, new_render)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)
