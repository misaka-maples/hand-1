import serial
import struct
import time
import threading
class ServoActuator:
    FRAME_HEAD_CMD = b'\x55\xAA'
    FRAME_HEAD_ACK = b'\xAA\x55'

    CMD_RD_STATUS = 0x30
    CMD_RD_REGISTER = 0x31
    CMD_WR_REGISTER = 0x32

    def __init__(self, port="/dev/ttyUSB0", baudrate=921600, timeout=0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.positions = {}
        self.info = {}
        self._running = threading.Event()  # 正确的运行标志
        self._thread = None
        self.lock = threading.RLock()
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
    def run(self):
        while self._running.is_set():
            time.sleep(0.1)
            self.get_positions()
            # print("-")
        else:
            time.sleep(0.1)
    def start_thread(self):
        if self._thread is None or not self._thread.is_alive():
            self._running.set()
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()

    def stop_thread(self):
        self._running.clear()  # 通知线程退出
        # 避免线程在自己里面 join 自己
        if self._thread is not None and threading.current_thread() != self._thread:
            self._thread.join()
        self._thread = None

    @staticmethod
    def checksum(data: bytes) -> int:
        """计算校验和（除帧头外）"""
        return sum(data) & 0xFF
    def _build_cmd(self, cmd: int, reg_addr=None, values=None, id_addr=None):
        # 优先使用调用时指定的id_addr，否则用默认id_addr
        if id_addr is None:
            raise ValueError("ID地址不能为空，请指定id_addr参数")
        data = bytearray()
        data.append(id_addr)
        data.append(cmd)

        if cmd == self.CMD_RD_STATUS:
            if reg_addr is None:
                L = 1  # ID(1) + CMD(1)
            else:
                L = 3
            body = bytes([L]) + data
            cs = self.checksum(body)
            return self.FRAME_HEAD_CMD + body + bytes([cs])

        elif cmd == self.CMD_RD_REGISTER:
            addr_l = reg_addr & 0xFF
            addr_h = (reg_addr >> 8) & 0xFF
            num_regs = values if values else 1
            L = 4
            body = bytes([L]) + data + bytes([addr_l, addr_h, num_regs])
            cs = self.checksum(body)
            return self.FRAME_HEAD_CMD + body + bytes([cs])

        elif cmd == self.CMD_WR_REGISTER:
            addr_l = reg_addr & 0xFF
            addr_h = (reg_addr >> 8) & 0xFF
            payload = bytes([addr_l, addr_h])
            for v in values:
                payload += struct.pack("<H", v)  # 小端存储，每个寄存器值2字节

            n = len(values)  # 寄存器个数
            L = 3 + n * 2    # 3 = 命令字1字节 + 地址2字节，n*2是数据字节数
            body = bytes([L]) + data + payload
            cs = self.checksum(body)
            return self.FRAME_HEAD_CMD + body + bytes([cs])

        else:
            raise ValueError("未知指令类型")

    def _send_cmd(self, cmd_bytes: bytes):
        with self.lock:
            self.ser.write(cmd_bytes)
            time.sleep(0.01)  # 文档建议 ≥1ms
            return self.ser.read_all()

    def read_status(self,id_addr=None):
        """读取电缸状态"""
        cmd = self._build_cmd(self.CMD_RD_STATUS,id_addr=id_addr)
        resp = self._send_cmd(cmd)
        return self._parse_status_frame(resp)

    def _parse_status_frame(self, frame: bytes):
        """解析读状态应答帧"""
        if frame is None:
            print("[WARN] received empty frame")
            return None
        if not frame.startswith(self.FRAME_HEAD_ACK):
            return None
        if len(frame) < 20:  # 应答帧至少要够
            return None
        # 帧结构参考文档：
        # 帧头(2B) + 数据长度(1B) + ID(1B) + 指令类型(1B) + 保留(1B) + 保留(1B)
        # 目标位置(2B, 有符号) + 实际位置(2B, 有符号) + 实际电流(2B, 无符号)
        # 力传感器数值(2B, 有符号) + 力传感器原始值(2B, 无符号)
        # 温度(1B, 有符号) + 故障码(1B, 无符号) + 校验(1B)
        # print(frame)
        # 提取字段
        id_addr = frame[3]
        cmd = f"0x{frame[4]:02X}"  # 十六进制格式
        target_position = struct.unpack("<h", frame[7:9])[0]
        current_position = struct.unpack("<h", frame[9:11])[0]
        current_current = struct.unpack("<H", frame[11:13])[0]
        force_sensor = struct.unpack("<h", frame[13:15])[0]
        force_adc = struct.unpack("<H", frame[15:17])[0]
        temperature = struct.unpack("<b", frame[17:18])[0]
        error_code = struct.unpack("<B", frame[18:19])[0]

        return {
            "id": id_addr,
            "cmd": cmd,
            "target_position": target_position,
            "current_position": current_position,
            "current_current_mA": current_current,
            "force_g": force_sensor,
            "force_adc_raw": force_adc,
            "temperature_C": temperature,
            "error_code": error_code
        }

    # ---------------- 常用指令封装 ----------------
    def set_mode(self, mode: int, id_addr=None):
        """设置控制模式 (0-定位,1-伺服,2-速度,4-电压)"""
        cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x25, [mode], id_addr=id_addr)
        # print(cmd.hex())
        return self._send_cmd(cmd)
    def send_message(self,cmd,mode,message,id_addr=None):
        with self.lock:
            cmd = self._build_cmd(cmd, mode, message, id_addr=id_addr)
            print(cmd.hex())
            return self._send_cmd(cmd)
    def set_pos_with_vel(self,position:int,velocity:int,id_addr=None):
        """设置目标位置和速度（步）"""
        with self.lock:
            cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x25, [0X0002,0X0000,0X0000, velocity,position], id_addr=id_addr)
            # print(cmd.hex())
            return self._send_cmd(cmd)

    def set_position(self, position: int, id_addr=None):
        """设置目标位置（步）"""
        with self.lock:
            cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x29, [position], id_addr=id_addr)
            print(cmd.hex())
            return self._send_cmd(cmd)

    def set_speed(self, speed: int, position: int, id_addr=None):
        """设置目标速度（步/s）"""
        with self.lock:
            cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x23, [speed, position], id_addr=id_addr)
            print(cmd.hex())
            return self._send_cmd(cmd)

    def set_voltage(self, voltage: int, id_addr=None):
        """设置电机输出电压（-1000~1000）"""
        cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x26, [voltage], id_addr=id_addr)
        return self._send_cmd(cmd)

    def clear_fault(self, id_addr=None):
        """清除故障"""
        with self.lock:
            for i in range(1, 7):
                cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x18, [1], id_addr=i)
                self._send_cmd(cmd)

    def pause_motion(self, id_addr=None):
        """暂停运动"""
        with self.lock:
            cmd = self._build_cmd(self.CMD_WR_REGISTER, 0x1A, [1], id_addr=id_addr)
            return self._send_cmd(cmd)
    def send_data_to_get_status(self, id_addr, retries=3):
        for _ in range(retries):
            cmd = self._build_cmd(self.CMD_RD_STATUS, id_addr=id_addr)
            resp = self._send_cmd(cmd)
            if resp:
                return resp
            time.sleep(0.01)
        return None

    def get_positions(self):
        positions = []
        for id_addr in range(1, 7):
            
            resp = self.send_data_to_get_status(id_addr=id_addr)
            status = self._parse_status_frame(resp)
            if status:
                self.positions[id_addr] = status['current_position']
                self.info[id_addr] = status
                positions.append(status['current_position'])
            else:
                self.positions[id_addr] = None
                self.info[id_addr] = None
                positions.append(None)
        return positions
    def reset_grasp(self):
        for i in range(1, 5):
            self.set_pos_with_vel(0,500, i)
        self.set_pos_with_vel(1700,500, 5)
        self.set_pos_with_vel(1998,500, 6)

if __name__ == "__main__":
    actuator = ServoActuator("/dev/ttyUSB0", 921600)
    # actuator.start_thread()
    try:
        actuator.set_pos_with_vel(0,500,1)
        # actuator.clear_fault(1)
        # x = 20
        # actuator.set_speed(x,1,1)
        # actuator.set_mode(2,1)
        # actuator.send_message(0x32,0x25,[0x02],1)#55 aa 05 01 31 2000 0000 57
        # x = actuator.send_message(0x32,0x25,[0X0002,0X0000,0X0000,0x01F4,0x0000],1)#55 aa 05 01 31 2300 4000 9a
        # print(x.hex())
        # print(actuator._parse_status_frame(x))
        
        # actuator.send_message(0x31,0x24,0x40,1)
        # while True:
        #     # actuator.set_position(1)
        #     # for i in range(1,5):
        #     #     actuator.set_position(100,i)
        #     time.sleep(0.01)
        #     print(actuator.positions)

    except KeyboardInterrupt:
        actuator.stop_thread()
    finally:
        actuator.close()
