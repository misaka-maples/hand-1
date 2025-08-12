import pyrealsense2 as rs
import numpy as np
import cv2

# 配置 RealSense 管道
pipeline = rs.pipeline()
config = rs.config()

# 开启彩色和深度流（根据相机支持的分辨率调整）
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# 启动
pipeline.start(config)

try:
    while True:
        # 获取一帧数据
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # 转换成 numpy 数组
        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = cv2.flip(color_image, 0)   # 0 表示上下翻转
        depth_colormap = cv2.flip(depth_image, 0)

        # 深度图可视化（使用颜色映射）
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_colormap, alpha=0.03),
            cv2.COLORMAP_TURBO
        )

        # 拼接左右显示（彩色 + 深度）
        images = np.hstack((color_image, depth_colormap))

        # 显示
        cv2.imshow('RealSense Color & Depth', images)

        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 停止管道
    pipeline.stop()
    cv2.destroyAllWindows()
