import re

with open('frontend/js/3d-viewer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add CSS2DRenderer Import
if 'CSS2DRenderer' not in content:
    content = content.replace(
        "import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';",
        "import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';\nimport { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';"
    )

# Add CSS2DRenderer init
init_render_str = '''    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
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
if 'this.labelRenderer = new CSS2DRenderer();' not in content:
    content = content.replace('''    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.container.appendChild(this.renderer.domElement);''', init_render_str)

# Update _onResize
resize_str = '''  _onResize() {
    if (this.camera && this.renderer) {
      this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
      if (this.labelRenderer) {
        this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
      }
    }
  }'''
content = re.sub(r'  _onResize\(\) \{[\s\S]*?  \}', resize_str, content)

# Update animate
anim_str = '''  animate() {
    this.reqFrame = requestAnimationFrame(this.animate);
    this.controls.update();
    if (this.isPlaying && this.modelRoot) {
      this.modelRoot.rotation.y += 0.005;
    }
    this.renderer.render(this.scene, this.camera);
    if (this.labelRenderer) {
      this.labelRenderer.render(this.scene, this.camera);
    }
  }'''
content = re.sub(r'  animate\(\) \{[\s\S]*?  \}', anim_str, content)

# Add CSS2DObject attaching in traverse
node_logic_old = '''      if (node.isMesh && node.name) {
        const key = node.name;
        this.componentMap[key] = node;
        if (!this.highlightSets[key]) {
          this.highlightSets[key] = [];
        }
        this.highlightSets[key].push(node);
        node.userData.componentKey = key;
        node.userData.componentName = this._formatName(key);
        
        node.castShadow = true;
        node.receiveShadow = true;
        
        this.originalMaterials.set(node, node.material);
      }'''
      
node_logic_new = '''      if (node.isMesh && node.name) {
        const key = node.name;
        this.componentMap[key] = node;
        if (!this.highlightSets[key]) {
          this.highlightSets[key] = [];
        }
        this.highlightSets[key].push(node);
        node.userData.componentKey = key;
        node.userData.componentName = this._formatName(key);
        
        node.castShadow = true;
        node.receiveShadow = true;
        
        this.originalMaterials.set(node, node.material.clone());
        
        // Add 3D text label
        const div = document.createElement('div');
        div.className = 'label-3d';
        div.textContent = node.userData.componentName;
        div.style.color = '#ffffff';
        div.style.background = 'rgba(0,0,0,0.7)';
        div.style.padding = '2px 6px';
        div.style.borderRadius = '3px';
        div.style.fontSize = '12px';
        div.style.fontFamily = 'monospace';
        div.style.pointerEvents = 'none';
        div.style.border = '1px solid rgba(255,255,255,0.3)';
        div.style.whiteSpace = 'nowrap';
        
        const label = new CSS2DObject(div);
        node.geometry.computeBoundingBox();
        const center = new THREE.Vector3();
        node.geometry.boundingBox.getCenter(center);
        
        // Push label slightly outward to not clip
        center.y += (node.geometry.boundingBox.max.y - node.geometry.boundingBox.min.y) / 2 + 0.1;
        label.position.copy(center);
        node.add(label);
        
        // Store label reference to hide/show later
        node.userData.labelObj = label;
      }'''

if 'CSS2DObject' not in content:
    content = content.replace(node_logic_old, node_logic_new)

with open('frontend/js/3d-viewer.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched 3d-viewer.js with CSS2D labels")
