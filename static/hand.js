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
                tableHTML += `
                    <tr>
                        <td>${dof}</td>
                        <td>${status.temperature_C}</td>
                        <td>${status.current_position}</td>
                        <td>${status.error_code}</td>
                    </tr>
                `;
            }
            document.getElementById("status-table").innerHTML = tableHTML;
        })
        .catch(err => console.error("获取状态失败", err));
}

// 每 1 秒刷新一次状态
setInterval(updateStatusTable, 1000);

// 更新三维力传感器表格
async function updateForceTable() {
    try {
        const response = await fetch('/force_data');  // 向后端请求数据
        if (!response.ok) {
            throw new Error('网络请求失败');
        }
        const data = await response.json();

        if (data.sensors && Array.isArray(data.sensors)) {
            data.sensors.forEach((sensor, index) => {
                const j = index + 1;  // 传感器编号从1开始
                document.getElementById(`fx${j}`).innerText = formatForce(sensor.fx);
                document.getElementById(`fy${j}`).innerText = formatForce(sensor.fy);
                document.getElementById(`fz${j}`).innerText = formatForce(sensor.fz);
                document.getElementById(`err${j}`).innerText = formatError(sensor.error_code);

            });
        }
    } catch (error) {
        console.error("更新力传感器数据失败:", error);
    }
}

// 每 500ms 更新一次
setInterval(updateForceTable, 5000);

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
