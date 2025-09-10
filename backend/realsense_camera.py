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
        self.pipeline = None
        self.config = None
        self.color_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.depth_frame = np.zeros((self.height, self.width), dtype=np.uint8)
        self.depth_colormap = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.depth = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.running = False
        self.thread = None
        self.device_connected = False  # 新增标志

        # 检查设备
        try:
            import pyrealsense2 as rs
            ctx = rs.context()
            connected_devices = ctx.query_devices()
            if len(connected_devices) == 0:
                print("[WARN] No RealSense device connected!")
                self.device_connected = False
            else:
                self.device_connected = True
                self.pipeline = rs.pipeline()
                self.config = rs.config()
                self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
                self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
                print(f"[INFO] Found {len(connected_devices)} RealSense device(s). Ready to start.")
        except Exception as e:
            print(f"[WARN] pyrealsense2 not available or error: {e}")
            self.device_connected = False

    def start(self):
        if not self.device_connected or not self.pipeline:
            print("[INFO] Camera not started, using placeholder frames.")
            self.running = False
            return

        try:
            self.pipeline.start(self.config)
            # 预热
            for _ in range(30):
                self.pipeline.wait_for_frames()
            self.running = True
            self.thread = threading.Thread(target=self.update_frames, daemon=True)
            self.thread.start()
            print("Camera started successfully.")
        except Exception as e:
            print(f"[ERROR] Camera start failed: {e}")
            self.running = False

    def update_frames(self):
        import pyrealsense2 as rs
        while self.running:
            try:
                frames = self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                if not color_frame or not depth_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = cv2.flip(color_image, 0)
                depth_image = cv2.flip(depth_image, 0)
                self.depth_colormap = depth_image
                depth_colormap = cv2.applyColorMap(
                    cv2.convertScaleAbs(depth_image, alpha=0.03),
                    cv2.COLORMAP_TURBO
                )
                self.color_frame = color_image
                self.depth = depth_colormap
            except Exception as e:
                print(f"[WARN] Camera thread error: {e}")
                time.sleep(0.1)

    def get_combined_frame(self):
        if not self.running or not self.device_connected:
            # 返回占位黑画面
            return np.hstack((self.color_frame, self.depth))
        import time
        time.sleep(1 / self.fps)
        return np.hstack((self.color_frame, self.depth))

    def get_images(self):
        if not self.running or not self.device_connected:
            return self.color_frame, self.depth_colormap
        import time
        time.sleep(1 / self.fps)
        return self.color_frame, self.depth_colormap

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.pipeline:
            self.pipeline.stop()
        print("Camera stopped.")

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
        cv2.destroyAllWindows()
