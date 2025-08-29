import serial
import time
import serial.tools.list_ports
import logging
from typing import List, Optional, Dict, Any
import threading
from collections import deque
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SensorCommunication:
    """传感器通信类，封装与力传感器设备的串口通信功能"""
    
    def __init__(self, port: str = None, baudrate: int = 460800, timeout: float = 0.2):
        """
        初始化传感器通信类
        
        参数:
            port: 串口号，如'COM8'
            baudrate: 波特率
            timeout: 串口超时时间
        """
        logger.setLevel(logging.WARNING)  # 只显示 WARNING 及以上级别
        self.force_history = {i: deque(maxlen=3) for i in range(1, 8)}  # 1~7端口，每个保存10帧
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connected = False
        self.current_port = None
        self.error_code = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None,7:None}
        self.force_data = {}
        self._running = threading.Event()  # 正确的运行标志
        self._thread = None
        self.lock = threading.RLock()
        self.force_history = {i: deque(maxlen=1) for i in range(1, 5)}
        if port is not None:
            self.connect_port(port)
            self.init_box()
        else:
            self.connect_port(self.find_acm_ports())
    def run(self):
        while self._running.is_set():
            start = time.time()
            self.get_all_force()
            end = time.time()
            # print(self.force_data,end-start)

            time.sleep(0.01)
    def check_connection(self) -> bool:
        """
        检查当前串口连接是否正常
        """
        if self.ser is None:
            return False
        if not self.ser.is_open:
            return False
        return True
    def find_acm_ports(self):
        """扫描系统中所有包含 ACM 的串口"""
        ports = serial.tools.list_ports.comports()
        # print([p.device for p in ports if "ACM" in p.device])
        return [p.device for p in ports if "ACM" in p.device]

    def reconnect(self, retries: int = 3, delay: float = 2.0) -> bool:
        """
        尝试重新连接串口
        """
        logger.warning("检测到串口断开，开始尝试重连...")
        self.stop_thread()
        if self.ser:
            try:
                self.disconnect()
                print("已断开串口连接")

            except Exception:
                pass
            self.ser = None
        time.sleep(1)
        acm_ports = self.find_acm_ports()
        if acm_ports == []:
            logger.error("未检测到任何 ACM 串口")
            return self.reconnect()
        for port in acm_ports:
            for attempt in range(1, retries + 1):
                try:
                    logger.warning(f"第 {attempt} 次重连 {port}...")
                    if self.connect(port):
                        if self.init_box():
                            logger.warning("串口重连成功")
                            self.start_thread()
                            return True
                except Exception as e:
                    logger.error(f"重连失败: {e}")
                time.sleep(delay)

            logger.error("重连失败，已放弃")
            return False

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

    def list_available_ports(self) -> List[Dict[str, str]]:
        """获取所有可用串口信息"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
            logger.info(f"检测到可用串口: {port.device} - {port.description}")
        return ports
    def connect_port(self,port):
        if isinstance(port,list):
            for i in port:
                self.connect(i)
        elif isinstance(port,str):
            self.connect(port)
    def connect(self, port: str = None) -> bool:
        """
        连接到指定串口
        
        参数:
            port: 串口号，若为None则使用初始化时的port
            
        返回:
            连接是否成功
        """
        try:
            if port:
                self.port = port
                
            if not self.port:
                logger.error("未指定串口号")
                return False
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            if self.ser.is_open:
                self.connected = True
                logger.info(f"成功连接到串口: {self.port}")
                return True
            else:
                logger.error(f"无法打开串口: {self.port}")
                return False
        except serial.SerialException as e:
            logger.error(f"串口连接异常: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"连接过程中发生未知错误: {str(e)}")
            return False
    
    def disconnect(self):
        """断开串口连接"""
        if self.connected and self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            self.current_port = None
            logger.info("已断开串口连接")
    
    def send_hex_data(self, hex_data: str) -> bool:
        """
        发送16进制数据到串口
        
        参数:
            hex_data: 16进制字符串，如"55 AA 7B 7B"
            
        返回:
            发送是否成功
        """
        if not self.connected:
            logger.error("未连接到串口，无法发送数据")
            return False
        with self.lock:
            try:
                # 移除空格并转换为字节
                clean_hex = hex_data.replace(' ', '').upper()
                data_bytes = bytes.fromhex(clean_hex)
                self.ser.write(data_bytes)
                logger.debug(f"已发送16进制数据: {hex_data}")
                return True
            except Exception as e:
                logger.error(f"发送数据时出错: {str(e)}")
                self.reconnect()
                if self.check_connection():
                    self.ser.write(data_bytes)
                    return True
                return False
    
    def read_serial_response(self, timeout: float = 0.02) -> Optional[bytes]:
        """
        从串口读取回复数据
        
        参数:
            timeout: 读取超时时间
            
        返回:
            读取到的数据字节，若无数据则返回None
        """
        if not self.connected:
            logger.error("未连接到串口，无法读取数据")
            return None
        with self.lock:
            try:
                # 等待数据到达
                time.sleep(timeout)
                response = self.ser.read_all()
                if response:
                    logger.debug(f"收到回复数据: {response.hex(' ')}")
                    return response
                return None
            except Exception as e:
                logger.error(f"读取数据时出错: {str(e)}")
                return None
    
    @staticmethod
    def calculate_lrc(data: bytes) -> int:
        """
        计算LRC校验码
        
        参数:
            data: 要计算校验码的数据字节
            
        返回:
            LRC校验码
        """
        lrc = 0
        for byte in data:
            lrc = (lrc + byte) & 0xFF  # 累加并确保8位无符号整数
        lrc = ((~lrc) + 1) & 0xFF  # 取反加一
        logger.debug(f"LRC校验码计算结果: {lrc:02X}")
        return lrc
    
    def select_port(self, port_id: int) -> bool:
        """
        选择指定的物理端口
        
        参数:
            port_id: 端口ID，1或2
            
        返回:
            端口选择是否成功
        """
        if not self.connected:
            logger.error("未连接到串口，无法选择端口")
            return False
            

            
        # 如果已经选择了该端口，则无需重复选择
        if self.current_port == port_id:
            logger.info(f"已选择端口{port_id}，无需重复选择")
            return True
            
        # 选择端口的命令配置
        port_commands = {
            1: {
                #CN1
                "command": "choose_port1",
                "body": "0E 00 70 B1 0A 01 00 00",
                "sleep": 1
            },
            2: {
                #CN2
                "command": "choose_port2",
                "body": "0E 00 70 B1 0A 01 00 03",
                "sleep": 1
            },
            3: {
                #CN1
                "command": "choose_port3",
                "body": "0E 00 70 B1 0A 01 00 06",
                "sleep": 1
            },
            4: {
                #CN2
                "command": "choose_port4",
                "body": "0E 00 70 B1 0A 01 00 09",
                "sleep": 1
            },
            5: {
                #CN1
                "command": "choose_port5",
                "body": "0E 00 70 B1 0A 01 00 0D",
                "sleep": 1
            },
            6: {
                #CN2
                "command": "choose_port6",
                "body": "0E 00 70 B1 0A 01 00 10",
                "sleep": 1
            },
            7:{
                "command": "choose_port7",
                "body": "0E 00 70 B1 0A 01 00 12",
                "sleep": 1
            },
            8:{
                "command": "choose_port8",
                "body": "0E 00 70 B1 0A 01 00 15",
                "sleep": 1
            },
            9:{
                "command": "choose_port9",
                "body": "0E 00 70 B1 0A 01 00 18",
                "sleep": 1
            },
            10:{
                "command": "choose_port10",
                "body": "0E 00 70 B1 0A 01 00 1B",
                "sleep": 1
            }
        }
        
        cmd = port_commands[port_id]
        head = "55 AA 7B 7B"
        body = cmd["body"]
        sleep_time = cmd["sleep"]
        
        # 计算LRC校验码
        data_bytes = bytes.fromhex(body.replace(' ', ''))
        lrc = self.calculate_lrc(data_bytes)
        tail = "55 AA 7D 7D"
        
        # 构建完整发送数据
        full_hex_data = f"{head} {body} {lrc:02X} {tail}"
        logger.info(f"选择端口{port_id}: {full_hex_data}")
        
        # 发送选择端口命令
        if not self.send_hex_data(full_hex_data):
            return False
            
        # 等待命令执行完成
        # time.sleep(sleep_time)
        
        # 读取响应（可选）
        response = self.read_serial_response()
        if response:
            # 简单验证是否成功
            if len(response) >= 16 and response[9] == 0x00:
                self.current_port = port_id
                logger.info(f"成功选择端口{port_id}")
                return True
            else:
                logger.warning(f"选择端口{port_id}可能失败，响应: {response.hex(' ')}")
        
        # 即使没有响应，也假设命令已发送
        self.current_port = port_id
        logger.info(f"已发送端口{port_id}选择命令，等待确认")
        return True
    
    def get_ser_response(self, fun: str, length: int = 0) -> Optional[str]:
        """
        向传感器发送命令并获取响应
        
        参数:
            fun: 命令功能标识，如"get_version"
            length: 数据长度，用于get_data等需要指定长度的命令
            
        返回:
            解析后的数据字符串，若失败则返回None
        """
        if not self.connected:
            logger.error("未连接到串口，无法执行命令")
            return None
            
        # 命令配置字典，避免大量if-else
        commands = {
            "get_version": {
                "body": "0E 00 60 A0 01 00 00",
                "sleep": 1,
                "parse": "ascii",
                "description": "获取版本号"
            },
            "recalibration": {
                "body": "0E 00 70 B0 02 02 00 03 01",
                "sleep": 1,
                "parse": "text",
                "description": "重新校准"
            },
            "set_mode": {
                "body": "0E 00 70 C0 0C 01 00 05",
                "sleep": 1,
                "parse": "",
                "description": "设置模式"
            },
            "get_mode": {
                "body": "0E 00 70 C0 0D 00 00 B5",
                "sleep": 1,
                "parse": "text",
                "description": "获取模式"
            },
            "get_data": {
                "body": "0E 00 70 C0 06 05 00 7B 0E 04",    #分布力
                "sleep": 0.05,
                "parse": "hex",
                "description": "获取CN1数据"
            },
            "get_force": {
                "body": "0E 00 70 C0 06 05 00 7B F0 03",    #合力
                "sleep": 0.05,
                "parse": "hex",
                "description": "获取合力数据"
            }
        }
        
        if fun not in commands:
            logger.error(f"不支持的命令: {fun}")
            return None
            
        cmd = commands[fun]
        head = "55 AA 7B 7B"
        body = cmd["body"]
        sleep_time = cmd["sleep"]
        parse_type = cmd["parse"]
        logger.info(f"执行命令: {fun} - {cmd['description']}")
        
        # 处理需要长度参数的命令
        if fun in ["get_data", "get_force"] and length > 0:
            # 将长度转为小端字节序并添加到body
            length_bytes = length.to_bytes(2, byteorder='little')
            body = f"{body} {length_bytes.hex()}"
            logger.debug(f"添加长度参数: {length} 字节, 十六进制: {length_bytes.hex()}")
        
        # 计算LRC校验码
        data_bytes = bytes.fromhex(body.replace(' ', ''))
        lrc = self.calculate_lrc(data_bytes)
        tail = "55 AA 7D 7D"
        
        # 构建完整发送数据
        full_hex_data = f"{head} {body} {lrc:02X} {tail}"
        logger.debug(f"完整发送数据: {full_hex_data}")
        
        # 发送数据
        if not self.send_hex_data(full_hex_data):
            return None
            
        # 等待响应
        # time.sleep(sleep_time)
        
        # 读取响应
        response = self.read_serial_response()
        if not response:
            logger.warning("未收到设备响应")
            return None
            
        # 解析响应
        try:
            if len(response) >= 16:
                # 检查头和尾
                if response[0:4] == bytes.fromhex(head.replace(' ', '')) and response[-4:] == bytes.fromhex(tail.replace(' ', '')):
                    # 解析Error域
                    error = response[9]
                    if error == 0x00:
                        # 解析Length域（小端字节序）
                        length_bytes = response[10:12]
                        data_length = int.from_bytes(length_bytes, byteorder='little')
                        
                        # 提取Data域
                        data = response[12:12+data_length]
                        
                        # 按类型解析数据
                        if parse_type == "ascii":
                            result = data.decode('ascii', errors='replace')
                            logger.info(f"{fun}: {result}")
                            return result
                        elif parse_type == "text":
                            result = data.hex()
                            logger.debug(f"{fun}: {result}")
                            return result
                        elif parse_type == "hex":
                            result = data.hex()
                            logger.info(f"0x7b 获取数据: {result}")
                            return result
                        else:
                            logger.info(f"{fun}: 执行成功")
                            return "success"
                    else:
                        logger.error(f"命令 {fun} 执行失败，错误码: {error} (0x{error:02X})，原始响应: {response.hex(' ')}")
                        # logger.error(f"命令执行错误，错误码: {error:02X}")
                        return {"error": error}
                else:
                    logger.error("响应数据格式错误，头或尾不匹配")
                    return None
            else:
                logger.warning(f"响应数据长度不足，无法解析，实际长度: {len(response)}")
                return None
        except Exception as e:
            logger.error(f"解析响应数据时出错: {str(e)}")
            return None
    
    def init_box(self) -> bool:
        """初始化控制盒，执行必要的启动命令"""
        if not self.connected:
            logger.error("未连接到控制盒，无法初始化")
            return False
            
        try:
            # 获取控制盒版本号
            version = self.get_ser_response("get_version")
            if not version:
                logger.error("获取版本号失败")
                return False
                
            # 设置模式
            if self.get_ser_response("set_mode") != "success":
                logger.error("设置模式失败")
                return False
                
            logger.info("控制盒初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化过程中出错: {str(e)}")
            return False
    
    def get_port_data(self, port_id: int, request_length: int, command: str = 'get_force') -> Optional[List[int]]:
        """
        从指定端口获取传感器数据

        参数:
            port_id: 端口ID，1或2
            request_length: 请求的数据长度（字节）
            command: 命令标识，比如 'get_force'

        返回:
            解析后的数据列表，若失败则返回None
        """
        if not self.connected:
            logger.error("未连接到传感器，无法获取数据")
            return None

        # 选择端口
        if not self.select_port(port_id):
            logger.error(f"选择端口{port_id}失败")
            return None

        logger.info(f"从端口{port_id}获取{request_length}字节数据")
        # 获取原始数据
        data = self.get_ser_response(command, request_length)
        if isinstance(data, dict) and "error" in data:
            self.error_code[port_id] = data["error"]
            return None
        else:
            self.error_code[port_id] = None
        if not data:
            logger.error(f"从端口{port_id}获取原始数据失败")
            return None

        # 检查长度
        if len(data) < 12 :
            logger.error(f"端口{port_id}数据长度不足，无法裁切，实际长度: {len(data)}")
            return None

        # 跳过前12个字符
        valid_data = data[12:]
        logger.debug(f"端口{port_id}裁切后数据: {valid_data}")

        # 解析为字节数组
        try:
            if isinstance(valid_data, list):
                valid_data = ''.join(valid_data)  # 把 ['0a','1b'] 转为 "0a1b"
            byte_values = list(bytes.fromhex(valid_data))
            logger.info(f"成功从端口{port_id}解析{len(byte_values)}个单字节值")
            return byte_values
        except ValueError as e:
            logger.error(f"端口{port_id}十六进制数据解析失败: {str(e)}, 数据: {valid_data}")
            return None

    def convert_hex_to_sensor_data(self, valid_data, axis_types: List[str]) -> Optional[List[int]]:
        """
        将16进制数据按轴类型转换为传感器数值（支持有符号/无符号转换）
        
        参数:
            valid_data: 裁切后的16进制数据，可以是 str / list[int] / list[str] / bytes
            axis_types: 轴类型列表，每个元素为 "signed"（有符号）或 "unsigned"（无符号）
            
        返回:
            转换后的数值列表，失败时返回None
        """
        try:
            if isinstance(valid_data, bytes):
                valid_data = valid_data.hex()
            elif isinstance(valid_data, list) and all(isinstance(x, int) for x in valid_data):
                valid_data = ''.join(f"{x:02x}" for x in valid_data)
            elif isinstance(valid_data, list) and all(isinstance(x, str) for x in valid_data):
                valid_data = ''.join(valid_data)

            if not isinstance(valid_data, str):
                logger.error(f"不支持的 valid_data 类型: {type(valid_data)}")
                return None

            bytes_data = bytes.fromhex(valid_data)
            if len(bytes_data) < len(axis_types):
                logger.error(f"数据长度不足，实际{len(bytes_data)}，期望至少{len(axis_types)}")
                return None

            result = []
            for byte, axis_type in zip(bytes_data[:len(axis_types)], axis_types):
                if axis_type == "signed":
                    value = byte if byte < 128 else byte - 256
                elif axis_type == "unsigned":
                    value = byte
                else:
                    logger.warning(f"未知轴类型: {axis_type}，使用默认有符号转换")
                    value = byte if byte < 128 else byte - 256
                result.append(value)
            return result

        except Exception as e:
            logger.error(f"数据转换异常: {e}")
            return None
    def get_force(self, index, axis=None):
        data = self.get_port_data(index, 3, 'get_force')
        if data:
            axis_types = ["signed", "signed", "unsigned"]
            parsed_force = self.convert_hex_to_sensor_data(data, axis_types)
            if parsed_force:
                parsed_force = [0 if f == -1 else f for f in parsed_force]
            else:
                logger.warning(f"CN1合力数据解析失败，原始数据: {data}")
            if axis is None:
                # print("get force",index, parsed_force)
                return parsed_force
            else:
                if axis == "fx":
                    return parsed_force[0]
                elif axis == "fy":
                    return parsed_force[1]
                elif axis == "fz":
                    return parsed_force[2]
                else:
                    logger.warning(f"未知轴: {axis}")
                    # return None
        else:
            return None
            # parsed_force = self.get_force(index)
            # return parsed_force
    def get_all_force(self):
        forces = {}
        force_map = {
            1:1,
            2:4,
            3:7,
            4:10
        }
        for i in range(1, 5):
            force = self.get_force(force_map[i])
            if force:
                # 存入历史队列（超出长度会自动丢弃旧值）
                self.force_history[i].append(force)

            if self.force_history[i]:
                # 计算三轴平均
                summed = [0, 0, 0]
                for f in self.force_history[i]:
                    for j in range(3):
                        summed[j] += f[j]
                averaged = [round(s / len(self.force_history[i]), 2) for s in summed]
                forces[i] = averaged
            else:
                forces[i] = None

            self.force_data[i] = forces[i]

        return forces

if __name__ == "__main__":
    sensor = SensorCommunication()
    time.sleep(1)
    sensor.start_thread()
    try:
        while True:
            # start = time.time()
            # sensor.get_force(10)
            # end = time.time()
            # print("Time taken:", end - start)
            # # time.sleep(1)
            # sensor.get_force(1)
            # sensor.get_force(7)
            # sensor.get_all_force()
            print(sensor.force_data)
            time.sleep(0.5)
    except KeyboardInterrupt:
        sensor.stop_thread()

    finally:
        sensor.disconnect()
    # main()

    # sensor = SensorCommunication("/dev/ttyACM0")
    # data = sensor.get_all_force()
    # print(data)
    # # 选择串口
    # chosen_port = '/dev/ttyACM0'
    # sensor.connect(chosen_port)
    # sensor.init_box()
    # sensor.get_force(2)