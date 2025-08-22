from backend.touch_sensor import SensorCommunication
from backend.servo_actuator import ServoActuator
import time
import math
import threading
class SmartGrasper:
    def __init__(self, sensors, actuator):
        self.sensors :SensorCommunication= sensors
        self.actuator :ServoActuator = actuator
        # 力阈值（不同物体可调节）
        self.min_force = 50     # 检测到物体的最小力
        self.max_force = 200    # 安全力，超过可能损坏物体
        self.step = 20         # 每次移动的步长
        self._running = threading.Event()  # 正确的运行标志
        self._thread = None
        self.lock = threading.RLock()
    def start_thread(self):
        if self._thread is None or not self._thread.is_alive():
            self._running.set()
            self._thread = threading.Thread(target=self.grasp, daemon=True)
            self._thread.start()

    def stop_thread(self):
        self._running.clear()  # 通知线程退出
        # 避免线程在自己里面 join 自己
        if self._thread is not None and threading.current_thread() != self._thread:
            self._thread.join()
        self._thread = None
    def safe_sum(self,val):
        if isinstance(val, (list, tuple)):
            return sum(val)
        elif isinstance(val, (int, float)):
            return val
        return 0
    def check_grasp(self,sensor_values: dict, threshold: int = 225) -> bool:
        """
        判断是否抓稳
        :param sensor_values: {1: [..], 2: [..], ...} 传感器值字典
        :param threshold: 阈值
        :return: True 抓稳, False 未抓稳
        """
        sensor3_val = sensor_values.get(4)
        if sensor3_val is None:
            return False  

        for sid, val in sensor_values.items():
            if sid == 4 or val is None:
                continue
            if self.safe_sum(sensor3_val) > self.min_force and self.safe_sum(val) > self.min_force:
                return True  # 找到一个满足条件的传感器
        return False

    def grasp(self):
        while self._running.is_set():
            all_forces = self.sensors.force_data
            with self.lock:
                positions = dict(list(self.actuator.positions.items())[:4])
                info = dict(list(self.actuator.info.items())[:4])

            # 手指到传感器映射（支持多个传感器）
            finger_to_sensor = {
                1: [1, 4],   # 手指1 -> 传感器1 和 4
                2: [5],       # 手指2没有传感器
                3: [2,6],      # 手指3 -> 传感器2
                4: [3],      # 手指4（大拇指） -> 传感器3
            }

            finger_forces = {}

            for fid in range(1, 5):
                sensor_ids = finger_to_sensor.get(fid, [])
                if not sensor_ids:
                    continue  # 没传感器就跳过

                total_force = 0.0
                for sid in sensor_ids:
                    force_vec = all_forces.get(sid)
                    if not force_vec:
                        continue
                    total_force += self.get_force_magnitude(sid)

                finger_forces[fid] = total_force
                sorted_finger_forces = sorted(finger_forces.values(), reverse=True)

                # 控制手指运动
                if total_force < self.min_force :
                    # if sum(sorted_finger_forces)<self.min_force-10:
                    #     new_pos = positions[fid] + self.step+20
                    #     self.actuator.set_position(new_pos, fid)
                    # else:
                        new_pos = positions[fid] + self.step
                        self.actuator.set_position(new_pos, fid)
                elif total_force > self.max_force:
                    new_pos = positions[fid] - self.step
                    self.actuator.set_position(new_pos, fid)

            # 判断抓取是否完成：任意两指合力大于阈值
            sorted_forces = sorted(finger_forces.values(), reverse=True)
            if len(sorted_forces) >= 2 and self.check_grasp(finger_forces, self.min_force * 2):
                print("已稳定抓取 ✅", finger_forces)
                break

            # sleep 可分段以响应停止信号
            for _ in range(5):
                if not self._running.is_set():
                    break
                time.sleep(0.1)

    def get_force_magnitude(self, finger_id: int) -> float:
        force_vec = self.sensors.force_data.get(finger_id)

        if not force_vec:  # None 或 空元组
            return 0.0  

        try:
            fx, fy, fz = force_vec
            return (fx**2 + fy**2 + fz**2) ** 0.5
        except Exception as e:
            print(f"[WARN] finger {finger_id} force read error: {e}, set as 0")
            return 0.0
    def release(self):
        """张开所有手指，松开物体"""
        positions = dict(list(self.actuator.positions.items())[:4])
        for fid, pos in enumerate(positions, start=1):
            self.actuator.set_position(10, fid)  # 全部张开
        print("释放完成 ✅")


if __name__ == "__main__":
    sensors = SensorCommunication("/dev/ttyACM0")
    actuator = ServoActuator()
    sensors.start_thread()
    actuator.start_thread()
    for i in range(1,7):
        actuator.clear_fault(i)  # 清除故障
    time.sleep(2)
    grasper = SmartGrasper(sensors, actuator)
    grasper.grasp()