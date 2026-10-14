with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re

new_render = '''function render(container, machine, pred, compId, isOldMode, shapFactors) {
  clear(container);
  
  const header = el('div', { class: 'page-header' }, [
    el('div', { class: 'page-header__text' }, [
      el('h1', { class: 'page-header__title' }, machine.name),
      el('span', { class: 'badge', style: 'margin-top: var(--s-2); display: inline-block;' }, machine.type_label)
    ]),
    el('div', { class: 'cluster' }, [
      isOldMode ? null : el('a', { class: 'btn btn--secondary btn--sm', href: profile.html?id= }, 'View Profile'),
      isOldMode ? null : el('a', { class: 'btn btn--primary btn--sm', href: predict.html?id= }, 'Run Prediction')
    ].filter(Boolean))
  ]);
  
  const viewerWrap = el('div', { class: 'viewer-wrap', id: 'viewer-3d' });
  const sidePanel = el('div', { class: 'side-panel' });
  
  if (pred) {
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
      
      (shapFactors && shapFactors.length > 0) ? el('div', { style: 'margin-top: var(--s-4);' }, [
        el('h4', {}, 'ML Feature Contributions (SHAP)'),
        el('div', { style: 'margin-top: var(--s-2); background: var(--surface-2); padding: var(--s-2); border-radius: var(--r-sm);' }, 
          shapFactors.map(f => el('div', { style: 'display: flex; justify-content: space-between; margin-bottom: 4px; border-bottom: 1px solid var(--surface-3); padding-bottom: 4px;' }, [
            el('span', {}, f.feature),
            el('span', { style: color: ; font-weight: bold; }, ${f.direction === 'raises' ? '+' : ''})
          ]))
        )
      ]) : null,

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
  mount(sidePanel, descCard);

  const compCard = el('div', { class: 'card', id: 'comp-card', style: 'display: none;' });
  mount(sidePanel, compCard);
  
  const grid = el('div', { class: 'mach-grid section' }, [viewerWrap, sidePanel]);
  
  mount(container, header);
  mount(container, grid);
  
  // Load 3D viewer
  import('./js/3d-viewer.js').then(m => {
    m.initViewer('viewer-3d', {
      modelUrl: machine.model3d,
      highlightComponent: compId || null,
      onComponentClick: (compKey) => {
        if (!compKey) {
          compCard.style.display = 'none';
          return;
        }
        const id = typeof compKey === 'string' ? compKey : compKey.id;
        const c = (machine.components || []).find(x => x.id === id) || { id, name: id, description: 'No description available' };
        
        compCard.style.display = 'block';
        clear(compCard);
        mount(compCard, el('h3', {}, c.name || 'Component Info'));
        mount(compCard, el('p', { style: 'margin-top: var(--s-2)' }, c.description || ''));
      }
    });
  });
}'''

content = re.sub(r'function render\(container, machine, pred, compId, isOldMode, shapFactors\) \{[\s\S]*?\}\);[\n\r]\s*\}\);[\n\r]\}', new_render, content)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Rewrote render function!")
