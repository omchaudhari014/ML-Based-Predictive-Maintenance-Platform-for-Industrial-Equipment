import sys

with open('frontend/js/3d-viewer.js', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Add error handling in loadModel
old_load = '''    async loadModel(modelUrl) {
      return new Promise((resolve, reject) => {
        const loader = new GLTFLoader();
        loader.load(
          modelUrl,
          (gltf) => {
            if (this.modelRoot) {
              this.scene.remove(this.modelRoot);
            }
            this.modelRoot = gltf.scene;
            
            // Normalize scale and position
            const box = new THREE.Box3().setFromObject(this.modelRoot);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 5 / maxDim;
            this.modelRoot.scale.setScalar(scale);
            
            this.modelRoot.position.sub(center.clone().multiplyScalar(scale));
            
            this.scene.add(this.modelRoot);
            this.resetView();
            
            resolve();
          },
          undefined,
          (error) => {
            console.error('Error loading model:', error);
            reject(error);
          }
        );
      });
    }'''

new_load = '''    async loadModel(modelUrl) {
      return new Promise((resolve, reject) => {
        // loading state
        const loadMsg = document.createElement('div');
        loadMsg.style.position = 'absolute';
        loadMsg.style.top = '50%';
        loadMsg.style.left = '50%';
        loadMsg.style.transform = 'translate(-50%, -50%)';
        loadMsg.style.color = 'white';
        loadMsg.innerText = 'Loading 3D Model...';
        loadMsg.id = 'load-msg';
        this.container.appendChild(loadMsg);

        const loader = new GLTFLoader();
        loader.load(
          modelUrl,
          (gltf) => {
            if (this.modelRoot) {
              this.scene.remove(this.modelRoot);
            }
            this.modelRoot = gltf.scene;
            
            // Normalize scale and position
            const box = new THREE.Box3().setFromObject(this.modelRoot);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            const maxDim = Math.max(size.x, size.y, size.z);
            const scale = 5 / maxDim;
            this.modelRoot.scale.setScalar(scale);
            
            this.modelRoot.position.sub(center.clone().multiplyScalar(scale));
            
            this.scene.add(this.modelRoot);
            this.resetView();
            
            const msg = document.getElementById('load-msg');
            if (msg) msg.remove();
            
            resolve();
          },
          undefined,
          (error) => {
            console.error('Error loading model:', error);
            const msg = document.getElementById('load-msg');
            if (msg) {
                msg.innerText = '3D model failed to load.';
                msg.style.color = '#ff3333';
            }
            reject(error);
          }
        );
      });
    }'''

content = content.replace(old_load, new_load)

# Add missing mapping warning in highlight
old_highlight = '''  highlight(componentId) {
    this.clearHighlight();
    const nodes = this.highlightSets[componentId];
    if (nodes) {
      nodes.forEach(node => {
        const mat = node.material.clone();
        mat.emissive = new THREE.Color(0xff3333);
        mat.emissiveIntensity = 0.5;
        node.material = mat;
      });
      this.label.innerText = this._formatName(componentId);
      this.highlightedComponent = componentId;
    }
  }'''

new_highlight = '''  highlight(componentId) {
    this.clearHighlight();
    const nodes = this.highlightSets[componentId];
    if (nodes && nodes.length > 0) {
      nodes.forEach(node => {
        const mat = node.material.clone();
        mat.emissive = new THREE.Color(0xff3333);
        mat.emissiveIntensity = 0.5;
        node.material = mat;
      });
      this.label.innerText = this._formatName(componentId);
      this.highlightedComponent = componentId;
    } else {
      console.warn('3D model loaded, but component localization is unavailable for:', componentId);
      this.label.innerText = 'Component visualization unavailable';
    }
  }'''

content = content.replace(old_highlight, new_highlight)

with open('frontend/js/3d-viewer.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched 3D Viewer error handling")
