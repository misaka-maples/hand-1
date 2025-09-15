import * as THREE from './three.module.js';
import { GUI } from './dat.gui.module.js';

// 每个手指的旋转轴
const fingerAxisMap = {
    index: new THREE.Vector3(0, 0, 1),
    middle: new THREE.Vector3(0, 0, 1),
    ring: new THREE.Vector3(0, 0, 1),
    pinky: new THREE.Vector3(0, 0, 1),
    thumb: new THREE.Vector3(1, 0, 0) // 大拇指 bend 轴
};

export function createFingerGUI(bones, fingerMap) {
    const gui = new GUI();
    const fingerParams = {
        thumb: 0,
        thumbSwing: 0,
        index: 0,
        middle: 0,
        ring: 0,
        pinky: 0
    };

    Object.keys(fingerMap).forEach(finger => {
        const folder = gui.addFolder(finger + " finger");

        // bend 控制
        folder.add(fingerParams, finger, 0, 2, 0.01).name("bend").onChange(() => {
            updateFinger(finger);
        });

        // 只给大拇指添加 swing
        if (finger === "thumb") {
            folder.add(fingerParams, "thumbSwing", 0, 3, 0.01).name("swing").onChange(() => {
                updateFinger(finger);
            });
        }

        // 更新手指函数
        function updateFinger(fingerName) {
            const joints = fingerMap[fingerName].map(name => bones[name]).filter(b => b);
            if (!joints.length) return;

            const bendAngles = (fingerName === "thumb")
                ? [0.5, 0.35, 0.25, 0.15]
                : [0.5, 0.8, 0.3];

            const axis = fingerAxisMap[fingerName];
            const swingAxis = new THREE.Vector3(0, 0, 1);

            joints.forEach((bone, i) => {
                // 从初始姿态开始
                bone.quaternion.copy(bone.userData.initQuat);
                
                // bend
                const bendQuat = new THREE.Quaternion();
                bendQuat.setFromAxisAngle(axis, fingerParams[fingerName] * (bendAngles[i] || bendAngles[bendAngles.length - 1]));
                bone.quaternion.multiply(bendQuat);
                console.log(`Finger: ${fingerName}, Joint: ${bone.name}, BendQuat:`, bendQuat, 'Bone quaternion after bend:', bone.quaternion);
                // swing，只影响大拇指最后一节
                if (fingerName === "thumb" && i === joints.length - 1) {
                    const swingQuat = new THREE.Quaternion();
                    swingQuat.setFromAxisAngle(swingAxis, fingerParams.thumbSwing * 0.5);
                    bone.quaternion.multiply(swingQuat);
                }
            });
        }
    });

    return gui;
}
