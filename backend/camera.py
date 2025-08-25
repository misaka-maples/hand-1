import cv2
import numpy as np
import cv2
from ultralytics import YOLO
from collections import deque
import argparse
import time
import requests
MODEL_PATH = r"backend/best.onnx"
N = 20
n = 10

# -------------------------
# 加载 YOLO 模型
# -------------------------
model = YOLO(MODEL_PATH)

# -------------------------
# 初始化状态
# -------------------------
is_grasp = False
rock_history = deque(maxlen=N)  # 存放 bool，表示每一帧是否检测到 rock
def send_command(detected_ids):
    global is_grasp, rock_history

    rock_detected = 1 in detected_ids
    rock_history.append(rock_detected)

    count = sum(rock_history)

    if count >= n and not is_grasp:
        is_grasp = True
        notify_server("http://localhost:5000/command?cmd=clear_fault")
        notify_server("http://localhost:5000/grasp","start_grasp")
        print("Rock majority detected -> is_grasp set to True")
    elif count < n and is_grasp:
        is_grasp = False
        notify_server("http://localhost:5000/command?cmd=clear_fault")
        notify_server("http://localhost:5000/grasp","stop_grasp")
        notify_server("http://localhost:5000/command?cmd=clear_fault")
        notify_server("http://localhost:5000/command?cmd=reset")
        print("Rock disappeared -> is_grasp set to False")
    # 否则保持原状态
def notify_server(url = None,cmd :str = None):

    try:
        if cmd is None:
            response = requests.post(url=url)
        else:
            response = requests.post(url=url, json={"cmd": cmd})
        if response.status_code == 200:
            pass
        else:
            print("状态更新失败:", response.text)
    except requests.RequestException as e:
        print("请求失败:", e)

def get_frames():
    cap = cv2.VideoCapture(0)  # 0 表示默认摄像头
    if not cap.isOpened():
        raise RuntimeError("无法打开摄像头")

    print('Camera started')
    while True:
        ret, frame = cap.read()
        if not ret:
            # 读取失败，用随机图像填充
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        # 如果需要翻转（有的摄像头会倒置），可以启用这一行
        frame = cv2.flip(frame, 1)
        results = model(frame, verbose=False)

        # -------------------------
        # 获取当前帧检测到的 object_id
        # -------------------------
        detected_ids = [int(box.cls[0].item()) for box in results[0].boxes]

        # -------------------------
        # 更新 is_grasp 状态
        # -------------------------
        send_command(detected_ids)

        # -------------------------
        # 绘制检测框
        # -------------------------
        annotated_frame = results[0].plot()

        # 在图像上显示当前 is_grasp 状态
        status_text = f"is_grasp: {is_grasp}"
        cv2.putText(annotated_frame, status_text, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, (0,0,255) if is_grasp else (0,255,0), 2)

        # 编码为 JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
