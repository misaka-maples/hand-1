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

    def grasp(self):
        while self._running.is_set():
            # all_forces = dict(list(self.sensors.force_data.items())[:4])
            all_forces = self.sensors.force_data
            with self.lock:
                positions = dict(list(self.actuator.positions.items())[:4])
                info = dict(list(self.actuator.info.items())[:4])

            # 手指到传感器映射（手指1~4对应实际传感器编号）
            finger_to_sensor = {
                1: 1,  # 手指1 -> 传感器1
                2: None,  # 手指2没有传感器
                3: 3,  # 手指3 -> 传感器3（实际在第四指上）
                4: 3,  # 手指4（大拇指） -> 传感器3
            }

            # 保存每根手指的合力
            finger_forces = {}

            for fid in range(1, 5):  # 遍历手指1~4
                sensor_id = finger_to_sensor.get(fid)
                if sensor_id is None:
                    continue  # 跳过没有传感器的手指

                force_vec = all_forces.get(sensor_id)
                if not force_vec:
                    finger_forces[fid] = 0.0
                    continue

                total_force = self.get_force_magnitude(sensor_id)

                finger_forces[fid] = total_force

                # 控制手指运动
                if total_force < self.min_force:
                    new_pos = positions[fid] + self.step
                    self.actuator.set_position(new_pos, fid)
                elif total_force > self.max_force:
                    new_pos = positions[fid] - self.step
                    self.actuator.set_position(new_pos, fid)

            # 判断抓取是否完成：任意两指合力大于阈值
            sorted_forces = sorted(finger_forces.values(), reverse=True)
            if len(sorted_forces) >= 2 and sum(sorted_forces[:2]) >= self.min_force * 2:
                print("已稳定抓取 ✅",finger_forces)
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