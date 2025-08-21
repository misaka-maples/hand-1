from backend.touch_sensor import SensorCommunication
from backend.servo_actuator import ServoActuator
import time
import math
class SmartGrasper:
    def __init__(self, sensors, actuator):
        self.sensors = sensors
        self.actuator = actuator
        # 力阈值（不同物体可调节）
        self.min_force = 50     # 检测到物体的最小力
        self.max_force = 200    # 安全力，超过可能损坏物体
        self.step = 20           # 每次移动的步长

    def grasp(self):
        """
        智能抓取流程：
        1. 检测是否接触到物体
        2. 慢慢闭合手指，直到达到稳定力
        3. 保持抓取
        """
        print("开始抓取...")
        finger_num = len(self.actuator.get_positions())  # 假设 actuator 有 6 个手指位置

        while True:
            all_forces = self.sensors.get_all_force()  # dict {finger_id: [fx, fy, fz]}
            positions = self.actuator.get_positions()

            grasped = True
            for fid, force_vec in all_forces.items():
                if force_vec is None:
                    continue
                total_force = self.get_force_magnitude(fid)
                print(f"Finger {fid}: {total_force}")
                if total_force < self.min_force:
                    # 力太小 → 说明还没夹紧，手指继续闭合
                    new_pos = positions[fid-1] + self.step
                    self.actuator.set_position(new_pos, fid)
                    print(f"Finger {fid} closed to {new_pos}")
                    grasped = False

                elif total_force > self.max_force:
                    # 力过大 → 说明可能夹坏 → 稍微放松
                    new_pos = positions[fid-1] - self.step
                    self.actuator.set_position(new_pos, fid)

            if grasped:
                print("已稳定抓取 ✅")
                break

            time.sleep(0.01)  # 控制循环频率
    def get_force_magnitude(self, finger_id: int) -> float:
        force_vec = self.sensors.get_force(finger_id)

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
        positions = self.actuator.get_positions()
        for fid, pos in enumerate(positions, start=1):
            self.actuator.set_position(0, fid)  # 全部张开
        print("释放完成 ✅")


if __name__ == "__main__":
    sensors = SensorCommunication("/dev/ttyACM0")
    actuator = ServoActuator()
    grasper = SmartGrasper(sensors, actuator)
    grasper.grasp()