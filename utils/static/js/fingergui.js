    // fingerGUI.js
    import * as THREE from './three.module.js';
    import { GUI } from './dat.gui.module.js'; // 或本地路径
    const fingerAxisMap = {
        index: new THREE.Vector3(0, 0, -1),
        middle: new THREE.Vector3(0, 0, -1),
        ring: new THREE.Vector3(0, 0, -1),
        pinky: new THREE.Vector3(0, 0, -1),
        thumb: new THREE.Vector3(1, 0, 0)
    };

    export function createFingerGUI(bones, fingerMap) {
        const gui = new GUI();
        const fingerParams = {};
        Object.keys(fingerMap).forEach(finger => {
            fingerParams[finger] = 0;

            const folder = gui.addFolder(finger + " finger");
            folder.add(fingerParams, finger, 0, 2, 0.01).name("bend").onChange(val => {
                const joints = fingerMap[finger].map(name => bones[name]).filter(b => b);
                if (joints.length === 0) return;

                const angles = [0.5, 0.3, 0.2]; // 每节骨头旋转幅度
                let parentQuat = new THREE.Quaternion();
                const axis = fingerAxisMap[finger]; // 使用手指对应旋转轴

                joints.forEach((bone, i) => {
                    const q = new THREE.Quaternion();
                    q.setFromAxisAngle(axis, val * angles[i]);
                    bone.quaternion.copy(parentQuat).multiply(q);
                    parentQuat.copy(bone.quaternion);
                });
            });
        });


        return gui;
    }
