// 滑块事件绑定
for (let i = 1; i <= 6; i++) {
    const slider = document.getElementById(`dof${i}`);
    const label = document.getElementById(`val${i}`);
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

btn.addEventListener("click", async () => {
    const cmd = isGrasping ? "stop_grasp" : "start_grasp";

    const resp = await fetch("/grasp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cmd: cmd })
    });
    const data = await resp.json();

    if (data.status === "ok") {
        isGrasping = !isGrasping;
        updateButton();
    } else {
        alert("命令发送失败: " + data.msg);
    }
});

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


// 更新三维力传感器表格
async function updateForceTable() {
    try {
        const response = await fetch('/force_data');  // 向后端请求数据
        if (!response.ok) throw new Error('网络请求失败');
        const data = await response.json();

        if (data.sensors && Array.isArray(data.sensors)) {
            const tbody = document.getElementById("force-table");
            tbody.innerHTML = "";  // 清空旧内容

            data.sensors.forEach((sensor, index) => {
                const j = index + 1;
                const row = `
                    <tr>
                        <td>传感器 ${j}</td>
                        <td>${formatForce(sensor.fx)}</td>
                        <td>${formatForce(sensor.fy)}</td>
                        <td>${formatForce(sensor.fz)}</td>
                        <td>${formatError(sensor.error_code)}</td>
                    </tr>
                `;
                tbody.insertAdjacentHTML("beforeend", row);
            });
        }
    } catch (error) {
        console.error("更新力传感器数据失败:", error);
    }
}
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
