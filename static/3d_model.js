import * as THREE from '/static/3d_js/three.module.js';
import { GLTFLoader } from '/static/3d_js/GLTFLoader.js';
import { OrbitControls } from '/static/3d_js/OrbitControls.js';
import { createFingerGUI } from '/static/3d_js/fingergui.js';

// ---------------------------
// 动态创建画布容器
// ---------------------------
const threeContainer = document.getElementById('three-container-wrapper');
threeContainer.style.width = '50%';
threeContainer.style.height = '360px'; // 和视频高度一致


const width = threeContainer.clientWidth;
const height = threeContainer.clientHeight;

// ---------------------------
// Three.js 初始化
// ---------------------------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a1a3f); // 深蓝科技背景

const camera = new THREE.PerspectiveCamera(65, width / height, 0.1, 1000);
camera.position.set(0.3, 0.15, 0.25);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(width, height);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
threeContainer.appendChild(renderer.domElement);

// 控制器
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.1, 0);
controls.update();

// ---------------------------
// 灯光
// ---------------------------
const keyLight = new THREE.DirectionalLight(0x55aaff, 1.2);
keyLight.position.set(2, 2, 2);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x4488ff, 0.8);
fillLight.position.set(-2, 1, -1);
scene.add(fillLight);

scene.add(new THREE.AmbientLight(0x101040, 0.6));

// ---------------------------
// 地面发光圆盘
// ---------------------------
const floorGeometry = new THREE.CircleGeometry(0.5, 64);
const floorMaterial = new THREE.MeshPhongMaterial({
    color: 0x111133,
    emissive: 0x2244ff,
    emissiveIntensity: 0.5,
    transparent: true,
    opacity: 0.85,
    side: THREE.DoubleSide
});
const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.02;
scene.add(floor);

// ---------------------------
// 粒子特效
// ---------------------------
const particles = new THREE.Group();
const particleGeometry = new THREE.SphereGeometry(0.003, 8, 8);
const particleMaterial = new THREE.MeshBasicMaterial({ color: 0x44aaff });

for (let i = 0; i < 200; i++) {
    const p = new THREE.Mesh(particleGeometry, particleMaterial);
    p.position.set(
        (Math.random() - 0.5) * 2,
        Math.random() * 1.5,
        (Math.random() - 0.5) * 2
    );
    particles.add(p);
}
scene.add(particles);

// ---------------------------
// 加载 GLB 模型
// ---------------------------
const loader = new GLTFLoader();
loader.load('/static/LEFTHAND.glb', gltf => {
    const model = gltf.scene;

    model.traverse(obj => {
        if (obj.isMesh) {
            // 网格透明线框
            obj.material = new THREE.MeshPhongMaterial({
                color: 0x111111,
                emissive: 0x00ffff,
                emissiveIntensity: 0.3,
                transparent: true,
                opacity: 0.3
            });

            const edges = new THREE.EdgesGeometry(obj.geometry, 15);
            const line = new THREE.LineSegments(
                edges,
                new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8 })
            );
            obj.add(line);
        }
        if (obj.type === "Bone") {
            obj.userData.initQuat = obj.quaternion.clone();
            const axesHelper = new THREE.AxesHelper(0.015);
            obj.add(axesHelper);
        }
    });

    scene.add(model);

    // 骨骼映射
    const bones = {};
    model.traverse(obj => { if (obj.type === "Bone") bones[obj.name] = obj; });

    const fingerMap = {
        thumb: ["thumb01", "thumb02", "thumb03", "thumb04"],
        index: ["index01", "index02", "index03"],
        middle: ["middle01", "middle02", "middle03"],
        ring: ["ring01", "ring02", "ring03"],
        pinky: ["pinky01", "pinky02", "pinky03"]
    };

    createFingerGUI(bones, fingerMap);
});

// ---------------------------
// 动画循环
// ---------------------------
function animate() {
    requestAnimationFrame(animate);

    // 粒子缓慢上下浮动
    particles.children.forEach((p, i) => {
        p.position.y += Math.sin(Date.now() * 0.001 + i) * 0.0005;
    });

    renderer.render(scene, camera);
}
animate();

// ---------------------------
// 窗口自适应
// ---------------------------
window.addEventListener('resize', () => {
    const width = threeContainer.clientWidth;
    const height = threeContainer.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
});
