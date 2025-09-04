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
        self.min_force = 30     # 检测到物体的最小力
        self.max_force = 200    # 安全力，超过可能损坏物体
        self.max_pos = {1: 1000, 2: 1000, 3: 980, 4: 850}  # 可以根据实际调整
        self.min_pos = {1: 0, 2: 0, 3: 0, 4: 0}
        self.grasp_state = "未抓取"
        self.step = 1000         # 每次移动的步长
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

            finger_to_sensor = {
                1: [1],
                2: [2],
                3: [3],
                4: [4],
            }

            finger_forces = {}

            for fid in range(1, 5):
                sensor_ids = finger_to_sensor.get(fid, [])
                if not sensor_ids:
                    continue

                total_force = 0.0
                for sid in sensor_ids:
                    total_force += self.get_force_magnitude(sid)

                finger_forces[fid] = total_force
                sorted_finger_forces = sorted(finger_forces.values(), reverse=True)
                # 控制手指运动，加入最大/最小位置限制
                if total_force < self.min_force:
                    new_pos = positions[fid] + self.step
                    new_pos = min(new_pos, self.max_pos[fid])  # 限制最大位置
                    self.actuator.set_pos_with_vel(new_pos, 500, fid)
                    self.grasp_state = "抓取中"
                # elif total_force > self.max_force:
                #     new_pos = positions[fid] - self.step
                #     new_pos = max(new_pos, self.min_pos[fid])  # 限制最小位置
                #     self.actuator.set_pos_with_vel(new_pos, 800, fid)

            # 判断抓取是否完成
            sorted_forces = sorted(finger_forces.values(), reverse=True)
            if len(sorted_forces) >= 2 and self.check_grasp(finger_forces, self.min_force * 2):
                print("已稳定抓取 ✅", finger_forces, self.grasp_state)
                self.grasp_state = "已抓取"
                break

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
        self.grasp_state = "未抓取"
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