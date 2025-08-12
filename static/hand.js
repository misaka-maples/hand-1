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