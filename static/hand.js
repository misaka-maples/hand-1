// 滑块事件绑定
for (let i = 1; i <= 6; i++) {
    const slider = document.getElementById(`dof${i}`);
    const label = document.getElementById(`val${i}`);
    if (!slider || !label) continue; // 如果不存在就跳过

    slider.addEventListener('input', () => {
        label.innerText = slider.value;
        sendSliderValue(i, slider.value);
    });
}

function sendSliderValue(dof, value) {
    fetch(`/set_dof?dof=${dof}&value=${value}`, { method: 'POST' })
        .then(res => res.text())
        .then(data => console.log(`DOF${dof} -> ${value}`, data))
        .catch(err => console.error(err));
}

function sendCommand(cmd) {
    fetch(`/command?cmd=${cmd}`, { method: 'POST' })
        .then(res => res.text())
        .then(data => console.log(`Command: ${cmd}`, data))
        .catch(err => console.error(err));
}

function updateStatusTable() {
    fetch('/status')
        .then(res => res.json())
        .then(data => {
            let tableHTML = "";
            for (let dof = 1; dof <= 6; dof++) {
                const status = data[`DOF${dof}`];
                if (!status) continue;

                // 表格
                tableHTML += `
                    <tr>
                        <td>${dof}</td>
                        <td>${status.temperature_C}</td>
                        <td>${status.current_position}</td>
                        <td>${status.error_code}</td>
                    </tr>
                `;

                // === 新增：更新滑动条和 label ===
                const slider = document.getElementById(`dof${dof}`);
                const label = document.getElementById(`val${dof}`);
                if (slider && label) {
                    slider.value = status.current_position;   // 设置滑块位置
                    label.innerText = status.current_position; // 设置右侧数值
                }
            }
            document.getElementById("status-table").innerHTML = tableHTML;
        })
        .catch(err => console.error("获取状态失败", err));
}

// 每 100 毫秒刷新一次状态
setInterval(updateStatusTable, 100);

// 点击按钮触发抓取/停止
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("graspBtn");
    let isGrasping = false;
    let graspInterval = null;

    function updateButton() {
        if (isGrasping) {
            btn.textContent = "停止抓取";
            btn.classList.remove("btn-success");
            btn.classList.add("btn-danger");
        } else {
            btn.textContent = "开始抓取";
            btn.classList.remove("btn-danger");
            btn.classList.add("btn-success");
        }
    }

    async function sendGraspCommand(cmd) {
        try {
            const resp = await fetch("/grasp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ cmd: cmd })
            });
            const data = await resp.json();
            if (data.status === "ok") {
                // isGrasping = data.is_grasping;
                updateButton();
            } else {
                console.warn("命令失败: ", data.msg);
            }
        } catch (err) {
            console.error("抓取命令发送失败", err);
        }
    }
    async function sendresetCommand(cmd) {
        try {
            const resp = await fetch("/command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ cmd: cmd })
            });
            const data = await resp.json();
            if (data.status === "ok") {
                // isGrasping = data.is_grasping;
                updateButton();
            } else {
                console.warn("命令失败: ", data.msg);
            }
        } catch (err) {
            console.error("抓取命令发送失败", err);
        }
    }
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    btn.addEventListener("click", () => {
        if (!isGrasping) {
            isGrasping = true;
            updateButton();

            async function graspLoop() {
                while (isGrasping) {
                    await sendGraspCommand("start_grasp");   // 执行抓取
                    await sleep(5000);                        // 延时 500ms
                    await sendresetCommand("reset_grasp");   // 执行复位
                    await sleep(7000);                       // 延时剩余时间，总间隔约 7000ms
                }
            }

            graspLoop();  // 启动循环
        } else {
            // 停止循环
            isGrasping = false;
            updateButton();
        }
    });
});

// 封装按钮更新函数
// function updateButton() {
//     const statusText = document.getElementById("grasp-status");

//     if (isGrasping) {
//         btn.textContent = "停止抓取";
//         btn.classList.remove("btn-success");
//         btn.classList.add("btn-danger");

//         // 更新状态文字
//         statusText.textContent = "正在抓取...";
//         statusText.classList.remove("text-secondary");
//         statusText.classList.add("text-success");
//     } else {
//         btn.textContent = "开始抓取";
//         btn.classList.remove("btn-danger");
//         btn.classList.add("btn-success");
// ``
//         // 更新状态文字
//         statusText.textContent = "等待状态...";
//         statusText.classList.remove("text-success");
//         statusText.classList.add("text-secondary");
//     }
// }

// 页面加载时初始化按钮状态
// updateButton();
document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("force-image-container");
    const img = document.getElementById("force-image");
    const updateInterval = 300; // ms

    // 色块在图片上的相对位置（百分比）
    const positions = [
        { left: 85, top: 5 },
        { left: 67, top: 5 },
        { left: 50, top: 5 },
        { left: 10, top: 75 },
    ];

    // 保证容器高度与图片一致
    function updateContainerHeight() {
        container.style.height = img.clientHeight + "px";
        container.style.width = img.clientWidth + "px";
    }

    if (img.complete) {
        updateContainerHeight();
    } else {
        img.onload = updateContainerHeight;
    }

    async function updateForceBlocks() {
        try {
            const response = await fetch('/force_data');
            if (!response.ok) throw new Error('网络请求失败');
            const data = await response.json();
            if (!data.sensors || data.sensors.length === 0) return;

            // 清空旧色块
            container.querySelectorAll(".force-box").forEach(b => b.remove());

            // 添加新色块
            data.sensors.forEach((sensor, index) => {
                const fx = sensor.fx || 0;
                const fy = sensor.fy || 0;
                const fz = sensor.fz || 0;

                const box = document.createElement("div");
                box.className = "force-box";

                const threshold = 10;
                box.style.backgroundColor =
                    Math.abs(fx) >= threshold || Math.abs(fy) >= threshold || Math.abs(fz) >= threshold
                        ? "rgb(255,0,0)"
                        : "rgb(0,255,0)";

                const pos = positions[index] || { left: 0, top: 0 };
                box.style.left = img.clientWidth * (pos.left / 100) + "px";
                box.style.top = img.clientHeight * (pos.top / 100) + "px";

                container.appendChild(box);
            });

            // 更新 Fz 表
            const fzTableBody = document.getElementById("fz-table");
            if (fzTableBody) {
                fzTableBody.innerHTML = "";
                data.sensors.forEach((sensor, index) => {
                    const fx = sensor.fx || 0;
                    const fy = sensor.fy || 0;
                    const fz = sensor.fz || 0;
                    const force_total = Math.sqrt(fx ** 2 + fy ** 2 + fz ** 2);

                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>传感器 ${index + 1}</td>
                        <td>${(force_total * 0.1).toFixed(2)}</td>
                    `;
                    fzTableBody.appendChild(row);
                });
            }

        } catch (err) {
            console.error("力数据更新失败:", err);
        }
    }

    setInterval(updateForceBlocks, updateInterval);
    window.addEventListener("resize", updateContainerHeight);
});

// function updateForceTable() {
//     updateForceBlocks();  // 实际调用已有的函数
// }
// // 每 500ms 更新一次
// setInterval(updateForceTable, 100);

function formatForce(val) {
    if (val === null || val === -1) {
        return 0;  // -1 或 null 显示为0
    }
    return val.toFixed ? val.toFixed(2) : val;
}


function formatError(code) {
    if (typeof code !== "number") {
        return "--";
    }
    return code.toString(16).toUpperCase().padStart(2, "0");  // 转16进制，大写，补齐2位
}
