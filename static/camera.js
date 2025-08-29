function reloadVideo() {
    let video = document.getElementById('video-feed');
    // 重新加载流，避免缓存
    video.src = '/video_feed?reload=' + new Date().getTime();
}
function checkgrasp() {
    fetch("/grasp_status")
        .then(res => res.json())
        .then(data => {
            const status = document.getElementById("grasp-status");

            if (data.status === "已抓取") {
                status.textContent = "已抓取";
                status.classList.remove("text-danger", "text-warning");
                status.classList.add("text-success");
            } else if (data.status === "抓取中") {
                status.textContent = "抓取中";
                status.classList.remove("text-danger", "text-success");
                status.classList.add("text-warning");
            } else {
                status.textContent = "等待状态";
                status.classList.remove("text-success", "text-warning");
                status.classList.add("text-danger");
            }
        })
        .catch(err => {
            const status = document.getElementById("grasp-status");
            status.textContent = "状态未知";
            status.classList.remove("text-success", "text-warning");
            status.classList.add("text-secondary");
        });
}

// 每隔 2 秒刷新一次抓取状态
setInterval(checkgrasp, 500);
checkgrasp();