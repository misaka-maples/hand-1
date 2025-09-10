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
        self.min_force = 3     # 检测到物体的最小力
        self.max_force = 200    # 安全力，超过可能损坏物体
        self.max_pos = {1: 1200, 2: 1200, 3: 1200, 4: 1000}  # 可以根据实际调整
        self.min_pos = {1: 0, 2: 0, 3: 0, 4: 0}
        self.grasp_state = "未抓取"
        self.step = 100         # 每次移动的步长
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
    def safe_sum(self, val):
        """
        计算传感器输出的合力模长
        val 可以是:
        - tuple/list: (fx, fy, fz) 或多组向量
        - float/int: 单个数值
        """
        if isinstance(val, (list, tuple)):
            try:
                # 如果是单个三维向量
                if len(val) == 3 and all(isinstance(x, (int, float)) for x in val):
                    fx, fy, fz = val
                    return (fx**2 + fy**2 + fz**2) ** 0.5
                else:
                    # 如果是多个传感器数值，递归计算再相加
                    return sum(self.safe_sum(v) for v in val)
            except Exception as e:
                print(f"[WARN] safe_sum error: {e}")
                return 0.0
        elif isinstance(val, (int, float)):
            return float(val)
        return 0.0
    def check_grasp(self, sensor_values: dict, sensor_count: int) -> bool:
        """
        判断是否抓稳
        :param sensor_values: {1: [...], 2: [...], ...} 传感器值字典
        :param sensor_count: 传感器数量
        :return: True 抓稳, False 未抓稳
        """
        # 1. 定义拇指和指尖、指腹传感器编号
        thumb_id = 7
        fingertip_ids = [2,6,1]  # `假设 2=食指尖, 3=中指尖, 4=无名指尖
        fingerpad_ids = [3, 4,5]  # 剩下的是指腹

        # 2. 获取拇指力
        thumb_val = self.safe_sum(sensor_values.get(thumb_id, 0)['force'])

        # 3. 条件1：拇指 + 任意指尖
        for fid in fingertip_ids:
            tip_val = self.safe_sum(sensor_values.get(fid, 0)['force'])
            if abs(thumb_val + tip_val) > self.min_force:
                return True

        # 4. 条件2：任意指腹
        for fid in fingerpad_ids:
            pad_val = self.safe_sum(sensor_values.get(fid, 0)['force'])
            if abs(pad_val) > self.min_force:
                return True
        return False

    def grasp(self):
        while self._running.is_set():
            # 1. 获取所有传感器数据
            all_forces = self.sensors.force_data  # {id: (fx, fy, fz), ...}
            sensor_count = 5

            with self.lock:
                positions = dict(list(self.actuator.positions.items())[:4])

            finger_forces = {}

            # 2. 遍历每个手指，计算合力模长
            for fid in range(1, 5):
                force_val = all_forces.get(fid, 0)['force']
                total_force = self.safe_sum(force_val)
                finger_forces[fid] = total_force
                print(f"finger {fid}: {total_force:.2f}")

                # 3. 控制手指运动（小于最小力就继续闭合）
                if total_force < self.min_force:
                    new_pos = positions[fid] + self.step
                    new_pos = min(new_pos, self.max_pos[fid])  # 限制最大位置
                    print(f"Moving finger {fid} to {new_pos}")
                    self.actuator.set_pos_with_vel(new_pos, 100, fid)
                    self.grasp_state = "抓取中"

            # 4. 判断是否抓稳（拇指+任意指尖，或任意指腹）
            if self.check_grasp(all_forces, sensor_count):
                print("已稳定抓取 ✅", finger_forces, self.actuator.positions)
                self.grasp_state = "已抓取"
                break

            # 5. 循环间隔
            for _ in range(5):
                if not self._running.is_set():
                    break
                time.sleep(0.1)

    def release(self):
        """张开所有手指，松开物体"""
        positions = dict(list(self.actuator.positions.items())[:4])
        for fid, pos in enumerate(positions, start=1):
            self.actuator.set_position(10, fid)  # 全部张开
        self.grasp_state = "未抓取"
        print("释放完成 ✅")
    

if __name__ == "__main__":
    try:
        sensors = SensorCommunication("/dev/ttyACM0")
        actuator = ServoActuator()
        sensors.start_thread()
        actuator.start_thread()
        for i in range(1,7):
            actuator.clear_fault(i)  # 清除故障
        time.sleep(2)
        grasper = SmartGrasper(sensors, actuator)
        grasper.start_thread()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sensors.stop_thread()
        actuator.stop_thread()
        actuator.reset_grasp()
        print("程序终止")