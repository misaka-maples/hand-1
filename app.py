from flask import Flask, request, render_template, jsonify, Response
from backend.servo_actuator import ServoActuator  
from backend.touch_sensor import SensorCommunication
import time
# from backend.camera import get_frames
from backend.SmartGrasper import SmartGrasper  
import logging

# 获取 werkzeug logger
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# 初始化硬件
actuator = ServoActuator("/dev/ttyUSB0", 921600)
touch_sensor = SensorCommunication("/dev/ttyACM0", 460800)
grasping = SmartGrasper(touch_sensor, actuator)

app = Flask(__name__)

# ----------------------
# 页面路由
# ----------------------
@app.route("/")
def index():
    """主页面：视频流 + 状态表 + 力传感器 + 控制按钮"""
    return render_template("index.html")

@app.route("/control")
def control():
    """子页面：自由度控制"""
    return render_template("control.html")

@app.route("/grasp_status")
def grasp_status():
    grasp_state = {"status": grasping.grasp_state}  # 也可以是 "抓取中" / "完成"
    return jsonify(grasp_state)

# ----------------------
# API 接口
# ----------------------
@app.route("/set_dof", methods=["POST"])
def set_dof():
    """设置自由度角度"""
    dof = int(request.args.get("dof"))
    value = int(request.args.get("value"))
    actuator.set_mode(0, dof)
    actuator.set_pos_with_vel(value, 300, dof)
    return f"Set DOF{dof} to {value}"

@app.route("/command", methods=["POST"])
def command():
    """执行控制命令"""
    data = request.get_json()  # 解析 JSON
    if not data or "cmd" not in data:
        return jsonify({"status": "error", "msg": "缺少 cmd"}), 400

    cmd = data["cmd"]
    if cmd == "reset_grasp":
        print("Resetting...")
        grasping.stop_thread()
        actuator.clear_fault()
        actuator.reset_grasp()
        grasping.grasp_state = "等待状态"
        is_grasping = False
    elif cmd == "clear_fault":
        actuator.clear_fault()
    else:
        return "Unknown command", 400
    return jsonify({"status": "ok", "is_grasping": is_grasping})
@app.route("/status", methods=["GET"])
def status():
    """查询关节状态"""
    status_info = actuator.info
    dict = {
            1: status_info[1]["temperature_C"],
            2: status_info[2]["temperature_C"],
            3: status_info[3]["temperature_C"],
            4: status_info[4]["temperature_C"],
            5: status_info[5]["temperature_C"],
            6: status_info[6]["temperature_C"]
        }
    print(dict)
    if not status_info:
        return jsonify({"error": "no data"})
    return jsonify({
        "DOF1": status_info[1],
        "DOF2": status_info[2],
        "DOF3": status_info[3],
        "DOF4": status_info[4],
        "DOF5": status_info[5],
        "DOF6": status_info[6]
    })

@app.route("/force_data", methods=["GET"])
def force_data():
    """获取三维力传感器数据"""
    sensors = []
    for i in range(1, 5):  # 假设有4个传感器
        if len(touch_sensor.force_data) == 4:
            force = touch_sensor.force_data[i]
            if force is not None:
                sensor = {"fx": force[0], "fy": force[1], "fz": force[2], "error_code": 0}
            else:
                sensor = {"fx": None, "fy": None, "fz": None, "error_code": 0}
        else:
            sensor = {"fx": None, "fy": None, "fz": None, "error_code": 0}
        sensors.append(sensor)
    return jsonify({"sensors": sensors})

# @app.route("/video_feed")
# def video_feed():
#     """视频流接口"""
#     return Response(get_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/grasp", methods=["POST"])
def grasp():
    data = request.get_json()
    if not data or "cmd" not in data:
        return jsonify({"status": "error", "msg": "缺少 cmd"}), 400

    cmd = data["cmd"]
    if cmd == "start_grasp":
        is_grasping = True
        actuator.clear_fault()
        grasping.start_thread()
        grasping.grasp_state = "抓取中"
        print("开始抓取")
    elif cmd == "stop_grasp":
        is_grasping = False
        actuator.clear_fault()
        grasping.stop_thread()
        print("停止抓取")
    else:
        return jsonify({"status": "error", "msg": "未知命令"}), 400
    return jsonify({"status": "ok", "is_grasping": is_grasping})

# ----------------------
# 主入口
# ----------------------
if __name__ == "__main__":
    try:
        # 启动硬件线程
        touch_sensor.start_thread()
        actuator.start_thread()
        time.sleep(2)  # 等待传感器初始化
        # 启动Web服务
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("程序终止")
    finally:
        actuator.stop_thread()
        touch_sensor.stop_thread()
        actuator.close()
