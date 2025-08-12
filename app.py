from flask import Flask, request, render_template,jsonify,Response
from backend.servo_actuator import ServoActuator  
from backend.camera import get_frames  # 假设摄像头处理逻辑在这个模块中
# 初始化串口控制
actuator = ServoActuator("/dev/ttyUSB0", 921600)

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



@app.route('/video_feed')
def video_feed():
    return Response(get_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        actuator.close()