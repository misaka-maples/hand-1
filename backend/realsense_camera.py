# camera.py
import threading
import time
import pyrealsense2 as rs
import numpy as np
import cv2

class RealSenseCamera:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)

        self.color_frame = None
        self.depth_frame = None
        self.depth_colormap = None
        self.depth = None
        self.running = False

    def start(self):
        try:
            self.pipeline.start(self.config)
            # 预热
            print("Warm up the camera...")
            for _ in range(30):
                self.pipeline.wait_for_frames()
            self.running = True
            self.thread = threading.Thread(target=self.update_frames, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"Camera start error: {e}")

    def update_frames(self):
        while self.running:
            try:
                frames = self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                if not color_frame or not depth_frame:
                    print("frame is none")
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())
                # 翻转
                color_image = cv2.flip(color_image, 0)
                depth_image = cv2.flip(depth_image, 0)
                self.depth_colormap = depth_image
                # 深度伪彩色
                depth_colormap = cv2.applyColorMap(
                    cv2.convertScaleAbs(depth_image, alpha=0.03),
                    cv2.COLORMAP_TURBO
                )
                self.color_frame = color_image
                self.depth = depth_colormap

            except Exception as e:
                print(f"Camera thread error: {e}")
                time.sleep(0.1)

    def get_combined_frame(self):
        time.sleep(1/self.fps)
        if self.color_frame is None or self.depth_colormap is None:
            return None
        combined = np.hstack((self.color_frame, self.depth))
        return combined

    def get_images(self):
        time.sleep(1/self.fps)
        return self.color_frame, self.depth_colormap

    def stop(self):
        self.running = False
        self.thread.join(timeout=2)
        self.pipeline.stop()


if __name__ == "__main__":
    realsensecamera = RealSenseCamera()
    realsensecamera.start()
    try:
        while True:
            combined_frame = realsensecamera.get_combined_frame()
            if combined_frame is not None:
                cv2.imshow("RealSense", combined_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        realsensecamera.stop()