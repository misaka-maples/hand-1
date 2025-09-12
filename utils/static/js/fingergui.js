// fingerGUI.js
import * as THREE from './three.module.js';
import { GUI } from './dat.gui.module.js';

// 每个手指的旋转轴
const fingerAxisMap = {
    index: new THREE.Vector3(0, 0, 1),
    middle: new THREE.Vector3(0, 0, 1),
    ring: new THREE.Vector3(0, 0, 1),
    pinky: new THREE.Vector3(0, 0, 1),
    thumb: new THREE.Vector3(1, 0, 0) // 大拇指
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

            // 大拇指4节，其他3节
            const angles = (finger === "thumb")
                ? [0.5, 0.35, 0.25, 0.15]
                : [0.5, 0.8, 0.3];

            const axis = fingerAxisMap[finger];

            joints.forEach((bone, i) => {
                const q = new THREE.Quaternion();
                q.setFromAxisAngle(axis, val * (angles[i] || angles[angles.length - 1]));

                // 保持零位：在初始四元数基础上叠加
                bone.quaternion.copy(bone.userData.initQuat).multiply(q);
            });
        });
    });

    return gui;
}
