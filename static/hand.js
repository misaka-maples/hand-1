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

const btn = document.getElementById("graspBtn");
let isGrasping = false; // 本地状态

// 点击按钮触发抓取/停止
btn.addEventListener("click", async () => {
    const cmd = isGrasping ? "stop_grasp" : "start_grasp";

    try {
        const resp = await fetch("/grasp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cmd: cmd })
        });
        const data = await resp.json();

        if (data.status === "ok") {
            // 根据后端返回状态同步前端按钮
            isGrasping = data.is_grasping;
            updateButton();
        } else {
            alert("命令发送失败: " + data.msg);
        }
    } catch (err) {
        console.error("抓取命令发送失败", err);
        alert("抓取命令发送失败，请检查网络");
    }
});

// 封装按钮更新函数
function updateButton() {
    const statusText = document.getElementById("grasp-status");

    if (isGrasping) {
        btn.textContent = "停止抓取";
        btn.classList.remove("btn-success");
        btn.classList.add("btn-danger");

        // 更新状态文字
        statusText.textContent = "正在抓取...";
        statusText.classList.remove("text-secondary");
        statusText.classList.add("text-success");
    } else {
        btn.textContent = "开始抓取";
        btn.classList.remove("btn-danger");
        btn.classList.add("btn-success");

        // 更新状态文字
        statusText.textContent = "等待状态...";
        statusText.classList.remove("text-success");
        statusText.classList.add("text-secondary");
    }
}

// 页面加载时初始化按钮状态
updateButton();

document.addEventListener("DOMContentLoaded", () => {

    const container = document.getElementById("force-image-container");
    const updateInterval = 500;

    // 色块在图片上的相对位置（百分比）
    const positions = [
        { left: 85, top: 5 },  // 传感器1
        { left: 67, top: 5 },  // 传感器2
        { left: 50, top: 5 },  // 传感器3
        { left: 10, top: 75 }, // 传感器4
    ];

    async function updateForceBlocks() {
        try {
            const response = await fetch('/force_data');
            if (!response.ok) throw new Error('网络请求失败');
            const data = await response.json();

            if (!data.sensors || data.sensors.length === 0) return;

            // --- 更新色块 ---
            const oldBoxes = container.querySelectorAll(".force-box");
            oldBoxes.forEach(b => b.remove());
            data.sensors.forEach((sensor, index) => {
                const fx = sensor.fx || 0;
                const fy = sensor.fy || 0;
                const fz = sensor.fz || 0;

                const box = document.createElement("div");
                box.className = "force-box";

                const threshold = 20;  // 阈值，比如 50N

                // 判断是否任意一个分量超过阈值
                if (Math.abs(fx) >= threshold || Math.abs(fy) >= threshold || Math.abs(fz) >= threshold) {
                    box.style.backgroundColor = "rgb(255,0,0)";  // 红色
                } else {
                    box.style.backgroundColor = "rgb(0,255,0)";  // 绿色
                }

                const pos = positions[index] || { left: 0, top: 0 };
                box.style.left = pos.left + "%";
                box.style.top = pos.top + "%";

                container.appendChild(box);
            });


            // --- 更新表格 ---
            const tableBody = document.getElementById("force-table");
            tableBody.innerHTML = "";  // 清空旧数据

            data.sensors.forEach((sensor, index) => {
                const fx = sensor.fx || 0;
                const fy = sensor.fy || 0;
                const fz = sensor.fz || 0;
                const error = sensor.error || 0;

                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${fx.toFixed(2)}</td>
                    <td>${fy.toFixed(2)}</td>
                    <td>${fz.toFixed(2)}</td>
                    <td>${error}</td>
                `;
                tableBody.appendChild(row);
            });

        } catch (err) {
            console.error("力数据更新失败:", err);
        }
    }

    setInterval(updateForceBlocks, updateInterval);
});



// 每 500ms 更新一次
setInterval(updateForceTable, 100);

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
