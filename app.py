from flask import Flask, request, render_template,jsonify,Response
from backend.servo_actuator import ServoActuator  
from backend.touch_sensor import SensorCommunication
import time
from backend.camera import get_frames  # 假设摄像头处理逻辑在这个模块中
from backend.SmartGrasper import SmartGrasper  # 假设自动抓取逻辑在这个模块中
# 初始化串口控制
actuator = ServoActuator("/dev/ttyUSB0", 921600)
touch_sensor = SensorCommunication("/dev/ttyACM0", 460800)
grasping = SmartGrasper(touch_sensor, actuator)
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')
@app.route("/set_dof", methods=["POST"])
def set_dof():
    dof = int(request.args.get("dof"))
    value = int(request.args.get("value"))
    actuator.set_mode(0, dof)
    actuator.set_position(value, dof)
    return f"Set DOF{dof} to {value}"

@app.route("/command", methods=["POST"])
def command():
    cmd = request.args.get("cmd")
    if cmd == "reset":
        for i in range(1, 7):
            actuator.set_position(0, i)
        actuator.set_position(2000, 6)  # Reset all DOFs to 0
    elif cmd == "clear_fault":
        for i in range(1, 7):
            actuator.clear_fault(i)
    else:
        return "Unknown command", 400
    return f"Command executed: {cmd}"
@app.route("/status", methods=["GET"])
def status():
    status_info = actuator.info
    if not status_info:
        return 
    else:
        # print(f"status_info: {status_info}")
        return jsonify({
            "DOF1": status_info[1],
            "DOF2": status_info[2],
            "DOF3": status_info[3],
            "DOF4": status_info[4],
            "DOF5": status_info[5],
            "DOF6": status_info[6]
        })


@app.route("/force_data")
def force_data():
    sensors = []
    
    # force = touch_sensor.get_all_force()
    for i in range(1, 7):  # 1~6 共6个传感器
        force = touch_sensor.force_data[i]
        
        # print(f"force: {force}")
        if force is not None:
            sensor = {
                "fx": force[0] if force is not None else None,
                "fy": force[1] if force is not None else None,
                "fz": force[2] if force is not None else None,
                "error_code":0
                # "error_code": touch_sensor.error_code.get(i, 0)  # 没有则默认0
            }
        else:
            sensor = {
                "fx": None,
                "fy": None,
                "fz": None,
                "error_code":0
                # "error_code": touch_sensor.error_code.get(i, -1)  # 用 -1 表示掉线
            }
        sensors.append(sensor)
    return jsonify({"sensors": sensors})
@app.route('/video_feed')
def video_feed():
    return Response(get_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/grasp", methods=["POST"])
def grasp():
    global is_grasping
    data = request.json
    cmd = data.get("cmd")
    print(cmd)
    if cmd == "start_grasp":
        is_grasping = True
        grasping.start_thread()
        print("开始抓取")
    elif cmd == "stop_grasp":
        is_grasping = False
        grasping.stop_thread()
        print("停止抓取")
    else:
        print("---------------------")
        return jsonify({"status": "error", "msg": "未知命令"}), 400
    print(f"Grasping status: {is_grasping}")
    return jsonify({"status": "ok", "is_grasping": is_grasping})

if __name__ == "__main__":
    try:
        touch_sensor.start_thread()
        actuator.start_thread()
        # while True:
        #     pass
        #     print(touch_sensor.force_data,actuator.positions)
        time.sleep(2)  # 等待传感器初始化
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        actuator.stop_thread()
        touch_sensor.stop_thread()
    finally:
        actuator.close()