import cv2
from ultralytics import YOLO
from collections import deque
import argparse

# -------------------------
# 解析命令行参数
# -------------------------
parser = argparse.ArgumentParser(description="YOLO Rock-Paper-Scissors Detection")
parser.add_argument("--model", type=str, default="your_model.onnx", help="ONNX model path")
parser.add_argument("--N", type=int, default=5, help="Sliding window size (number of frames)")
parser.add_argument("--n", type=int, default=3, help="Rock threshold in N frames")
args = parser.parse_args()

MODEL_PATH = args.model
N = args.N
n = args.n

# -------------------------
# 加载 YOLO 模型
# -------------------------
model = YOLO(MODEL_PATH)

# -------------------------
# 初始化状态
# -------------------------
is_grasp = False
rock_history = deque(maxlen=N)  # 存放 bool，表示每一帧是否检测到 rock

# -------------------------
# 定义状态更新函数
# -------------------------
def send_command(detected_ids):
    global is_grasp, rock_history

    rock_detected = 1 in detected_ids
    rock_history.append(rock_detected)

    count = sum(rock_history)

    if count >= n and not is_grasp:
        is_grasp = True
        print("Rock majority detected -> is_grasp set to True")
    elif count < n and is_grasp:
        is_grasp = False
        print("Rock disappeared -> is_grasp set to False")
    # 否则保持原状态

# -------------------------
# 打开摄像头
# -------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

print("按 'q' 退出")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # -------------------------
    # YOLO 推理
    # verbose=False 不打印日志
    # -------------------------
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

    cv2.imshow("YOLO ONNX Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# -------------------------
# 关闭资源
# -------------------------
cap.release()
cv2.destroyAllWindows()
del model
model = None
print("YOLO 已关闭")
