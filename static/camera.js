function reloadVideo() {
    let video = document.getElementById('video-feed');
    // 重新加载流，避免缓存
    video.src = '/video_feed?reload=' + new Date().getTime();
}
