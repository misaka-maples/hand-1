from backend.realsense_camera import RealSenseCamera
import cv2
import numpy as np
import time
def get_frames():
    camera = RealSenseCamera()
    camera.start()
    print('Camera started')
    while True:
        color_image, depth_image = camera.get_images()
        if color_image is None or depth_image is None:
            # 还没准备好，返回黑屏或等待
            color_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            depth_image = np.random.randint(0, 256, (480, 640), dtype=np.uint16)
            color_image = cv2.flip(color_image, 0)
            depth_image = cv2.flip(depth_image, 0)
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_TURBO
            )
            images = np.hstack((color_image, depth_colormap))
            ret, buffer = cv2.imencode('.jpg', images)
        else:
            images = camera.get_combined_frame()
            ret, buffer = cv2.imencode('.jpg', images)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

