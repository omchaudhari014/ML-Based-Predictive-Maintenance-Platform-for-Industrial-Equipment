import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

export class MachineViewer {
  constructor(container) {
    this.container = typeof container === 'string' ? document.getElementById(container) : container;
    this.components = {};
    this.highlightSets = {};
    
    this._initScene();
  }
  
  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1b1f27);
    this.scene.fog = new THREE.Fog(0x1b1f27, 10, 50);
    
    this.camera = new THREE.PerspectiveCamera(45, this.container.clientWidth / this.container.clientHeight, 0.1, 100);
    this.camera.position.set(5, 5, 5);
    
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.container.appendChild(this.renderer.domElement);
    
    // Add CSS2DRenderer for text labels
    this.labelRenderer = new CSS2DRenderer();
    this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.labelRenderer.domElement.style.position = 'absolute';
    this.labelRenderer.domElement.style.top = '0px';
    this.labelRenderer.domElement.style.pointerEvents = 'none'; // Don't block orbit controls
    this.container.appendChild(this.labelRenderer.domElement);
    
    // Ensure container has position relative
    this.container.style.position = 'relative';
    
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6);
    hemiLight.position.set(0, 10, 0);
    this.scene.add(hemiLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 5);
    dirLight.castShadow = true;
    this.scene.add(dirLight);
    
    const grid = new THREE.GridHelper(20, 20, 0x888888, 0x444444);
    this.scene.add(grid);
    
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(20, 20),
      new THREE.MeshStandardMaterial({ color: 0x111111, depthWrite: false })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);
    
    this.resizeObserver = new ResizeObserver(() => this._onResize());
    this.resizeObserver.observe(this.container);
    
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.renderer.domElement.addEventListener('mousemove', this._onMouseMove.bind(this));
    this.renderer.domElement.addEventListener('click', this._onClick.bind(this));
    
    this._createUI();
    
    this.isPlaying = true;
    this.animate = this.animate.bind(this);
    this.animate();
  }
  
  _createUI() {
    this.tooltip = document.createElement('div');
    this.tooltip.style.position = 'absolute';
    this.tooltip.style.display = 'none';
    this.tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    this.tooltip.style.color = 'white';
    this.tooltip.style.padding = '5px 10px';
    this.tooltip.style.borderRadius = '4px';
    this.tooltip.style.pointerEvents = 'none';
    this.tooltip.style.zIndex = '10';
    this.container.appendChild(this.tooltip);
    
    this.label = document.createElement('div');
    this.label.style.position = 'absolute';
    this.label.style.top = '10px';
    this.label.style.left = '10px';
    this.label.style.color = 'white';
    this.label.style.fontSize = '18px';
    this.label.style.fontWeight = 'bold';
    this.label.style.zIndex = '10';
    this.container.appendChild(this.label);
    
    const controlsBar = document.createElement('div');
    controlsBar.style.position = 'absolute';
    controlsBar.style.bottom = '10px';
    controlsBar.style.left = '10px';
    controlsBar.style.zIndex = '10';
    
    this.playBtn = document.createElement('button');
    this.playBtn.innerText = 'Pause';
    this.playBtn.onclick = () => this.togglePlay();
    controlsBar.appendChild(this.playBtn);
    
    const resetBtn = document.createElement('button');
    resetBtn.innerText = 'Reset View';
    resetBtn.style.marginLeft = '5px';
    resetBtn.onclick = () => this.resetView();
    controlsBar.appendChild(resetBtn);
    
    this.container.appendChild(controlsBar);
  }
  
  _formatName(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
  
  async loadModel(url) {
    if (this.modelRoot) {
      this.scene.remove(this.modelRoot);
    }
    
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(url);
    this.modelRoot = gltf.scene;
    this.scene.add(this.modelRoot);
    
    const box = new THREE.Box3().setFromObject(this.modelRoot);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    
    this.camera.position.set(center.x + maxDim * 1.5, center.y + maxDim, center.z + maxDim * 1.5);
    this.controls.target.copy(center);
    this.camera.lookAt(center);
    
    this.componentMap = {};
    this.highlightSets = {};
    this.originalMaterials = new Map();
    
    this.modelRoot.traverse(node => {
      if (node.isMesh && node.name) {
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
      }
    });
  }
  
  highlight(componentId) {
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
  }
  
  clearHighlight() {
    if (this.highlightedComponent) {
      const nodes = this.highlightSets[this.highlightedComponent];
      if (nodes) {
        nodes.forEach(node => {
          node.material = this.originalMaterials.get(node);
        });
      }
      this.highlightedComponent = null;
      this.label.innerText = '';
    }
  }
  
  focusComponent(componentId) {
    const nodes = this.highlightSets[componentId];
    if (nodes && nodes.length > 0) {
      const box = new THREE.Box3();
      nodes.forEach(node => box.expandByObject(node));
      const center = box.getCenter(new THREE.Vector3());
      this.controls.target.copy(center);
      this.highlight(componentId);
    }
  }
  
  resetView() {
    if (this.modelRoot) {
      const box = new THREE.Box3().setFromObject(this.modelRoot);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      this.camera.position.set(center.x + maxDim * 1.5, center.y + maxDim, center.z + maxDim * 1.5);
      this.controls.target.copy(center);
    }
  }
  
  togglePlay() {
    this.isPlaying = !this.isPlaying;
    this.playBtn.innerText = this.isPlaying ? 'Play' : 'Pause';
  }
  
  getComponentList() {
    return Object.keys(this.componentMap).map(k => ({
      id: k,
      name: this._formatName(k)
    }));
  }
  
  _onResize() {
    if (this.camera && this.renderer) {
      this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
      if (this.labelRenderer) {
        this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
      }
    }
  }
  }
  
  _onMouseMove(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    
    if (this.modelRoot) {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObject(this.modelRoot, true);
      
      let found = null;
      for (let i = 0; i < intersects.length; i++) {
        if (intersects[i].object.userData.componentKey) {
          found = intersects[i].object;
          break;
        }
      }
      
      if (found) {
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = (event.clientX + 10) + 'px';
        this.tooltip.style.top = (event.clientY + 10) + 'px';
        this.tooltip.innerText = found.userData.componentName;
        this.renderer.domElement.style.cursor = 'pointer';
      } else {
        this.tooltip.style.display = 'none';
        this.renderer.domElement.style.cursor = 'default';
      }
    }
  }
  
  _onClick(event) {
    if (this.modelRoot) {
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObject(this.modelRoot, true);
      
      let found = null;
      for (let i = 0; i < intersects.length; i++) {
        if (intersects[i].object.userData.componentKey) {
          found = intersects[i].object;
          break;
        }
      }
      
      if (found) {
        const key = found.userData.componentKey;
        this.highlight(key);
        if (this.onComponentClick) {
          this.onComponentClick(key);
        }
      }
    }
  }
  
  animate() {
    this.reqFrame = requestAnimationFrame(this.animate);
    this.controls.update();
    if (this.isPlaying && this.modelRoot) {
      this.modelRoot.rotation.y += 0.005;
    }
    this.renderer.render(this.scene, this.camera);
    if (this.labelRenderer) {
      this.labelRenderer.render(this.scene, this.camera);
    }
  }
    this.renderer.render(this.scene, this.camera);
  }
  
  dispose() {
    cancelAnimationFrame(this.reqFrame);
    this.resizeObserver.disconnect();
    this.renderer.dispose();
    this.container.innerHTML = '';
  }
}

export async function initViewer(containerId, options) {
  const viewer = new MachineViewer(containerId);
  
  if (typeof options === 'string') {
    await viewer.loadModel('assets/models/cnc_machine.glb');
    viewer.highlight(options);
  } else if (options) {
    if (options.modelUrl) {
      await viewer.loadModel(options.modelUrl);
    } else {
      await viewer.loadModel('assets/models/cnc_machine.glb');
    }
    
    if (options.highlightComponent) {
      viewer.highlight(options.highlightComponent);
    }
    
    if (options.onComponentClick) {
      viewer.onComponentClick = options.onComponentClick;
    }
  } else {
    await viewer.loadModel('assets/models/cnc_machine.glb');
  }
  
  return viewer;
}
