from flask import Flask, request, render_template,jsonify,Response
from backend.servo_actuator import ServoActuator  
from backend.touch_sensor import SensorCommunication
import time
from backend.camera import get_frames  # 假设摄像头处理逻辑在这个模块中
from backend.auto_grasp import SmartGrasper  # 假设自动抓取逻辑在这个模块中
# 初始化串口控制
actuator = ServoActuator("/dev/ttyUSB0", 921600)
touch_sensor = SensorCommunication("/dev/ttyACM0", 460800)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')
@app.route("/set_dof", methods=["POST"])
def set_dof():
    dof = int(request.args.get("dof"))
    value = int(request.args.get("value"))
    actuator.set_mode(0, dof)
    actuator.set_position(value*20, dof)
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
    elif cmd == "start_grasp":
        grasper = SmartGrasper(touch_sensor, actuator)
        grasper.grasp()
    else:
        return "Unknown command", 400
    return f"Command executed: {cmd}"
@app.route("/status", methods=["GET"])
def status():
    status_info = {}
    for i in range(1, 7):
        status_info[i] = actuator.read_status(i)
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
        force = touch_sensor.get_force(i)
        if force is not None:
            sensor = {
                "fx": force[0] if force is not None else None,
                "fy": force[1] if force is not None else None,
                "fz": force[2] if force is not None else None,
                "error_code": touch_sensor.error_code.get(i, 0)  # 没有则默认0
            }
        else:
            sensor = {
                "fx": None,
                "fy": None,
                "fz": None,
                "error_code": touch_sensor.error_code.get(i, -1)  # 用 -1 表示掉线
            }
        sensors.append(sensor)

    return jsonify({"sensors": sensors})
@app.route('/video_feed')
def video_feed():
    return Response(get_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        actuator.close()