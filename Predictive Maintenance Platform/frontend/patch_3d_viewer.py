with open('frontend/js/3d-viewer.js', 'r', encoding='utf-8') as f:
    content = f.read()

import_block = '''import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';'''
content = content.replace('''import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';''', import_block)

# Initialize label renderer
init_code = '''    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.container.appendChild(this.renderer.domElement);
    
    // Add CSS2DRenderer for text labels
    this.labelRenderer = new CSS2DRenderer();
    this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.labelRenderer.domElement.style.position = 'absolute';
    this.labelRenderer.domElement.style.top = '0px';
    this.labelRenderer.domElement.style.pointerEvents = 'none'; // Don't block orbit controls
    this.container.appendChild(this.labelRenderer.domElement);
    
    // Ensure container has position relative
    this.container.style.position = 'relative';'''
content = content.replace('''    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.container.appendChild(this.renderer.domElement);''', init_code)

# Add animate render labelRenderer
render_code = '''    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    this.labelRenderer.render(this.scene, this.camera);'''
content = content.replace('''    this.controls.update();
    this.renderer.render(this.scene, this.camera);''', render_code)

# Add resize listener
resize_code = '''  resize() {
    if (!this.container) return;
    this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    if (this.labelRenderer) {
      this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
  }'''
content = content.replace('''  resize() {
    if (!this.container) return;
    this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
  }''', resize_code)

# Now attach labels to nodes
traverse_code = '''          child.material = child.material.clone();
          
          if (child.userData && child.userData.name) {
            const partName = child.userData.name;
            if (!this.components[partName]) this.components[partName] = [];
            this.components[partName].push(child);
            
            // Create a label
            const div = document.createElement('div');
            div.className = 'label-3d';
            div.textContent = partName.replace(/_/g, ' ').toUpperCase();
            div.style.color = '#ffffff';
            div.style.background = 'rgba(0,0,0,0.6)';
            div.style.padding = '2px 5px';
            div.style.borderRadius = '3px';
            div.style.fontSize = '10px';
            div.style.fontFamily = 'monospace';
            div.style.pointerEvents = 'none';
            
            const label = new CSS2DObject(div);
            // position it slightly above the center
            child.geometry.computeBoundingBox();
            const center = new THREE.Vector3();
            child.geometry.boundingBox.getCenter(center);
            label.position.copy(center);
            child.add(label);
            
            // Make node interactive
            child.userData.isComponent = true;
            child.userData.compId = partName;
          }'''
content = content.replace('''          child.material = child.material.clone();
          if (child.userData && child.userData.name) {
            const compId = child.userData.name;
            if (!this.components[compId]) this.components[compId] = [];
            this.components[compId].push(child);
            child.userData.isComponent = true;
            child.userData.compId = compId;
          }''', traverse_code)

with open('frontend/js/3d-viewer.js', 'w', encoding='utf-8') as f:
    f.write(content)
