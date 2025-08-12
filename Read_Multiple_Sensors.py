import serial
import time
import serial.tools.list_ports
import logging
from typing import List, Optional, Dict, Any

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
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connected = False
        self.current_port = None
        
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
            
        try:
            # 移除空格并转换为字节
            clean_hex = hex_data.replace(' ', '').upper()
            data_bytes = bytes.fromhex(clean_hex)
            self.ser.write(data_bytes)
            logger.debug(f"已发送16进制数据: {hex_data}")
            return True
        except Exception as e:
            logger.error(f"发送数据时出错: {str(e)}")
            return False
    
    def read_serial_response(self, timeout: float = 0.3) -> Optional[bytes]:
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
            
        if port_id not in [1, 2]:
            logger.error(f"无效的端口ID: {port_id}，支持1或2")
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
        time.sleep(sleep_time)
        
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
                "sleep": 2,
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
            "get_data2": {
                "body": "0E 00 70 C0 06 05 00 7B F0 03",    #合力
                "sleep": 0.05,
                "parse": "hex",
                "description": "获取CN2数据"
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
        if fun in ["get_data", "get_data2"] and length > 0:
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
        time.sleep(sleep_time)
        
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
                        logger.error(f"命令执行错误，错误码: {error:02X}")
                        return None
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
    
    def get_port_data(self, port_id: int, request_length: int, parse_type: str = 'byte') -> Optional[List[int]]:
        """
        从指定端口获取传感器数据
        
        参数:
            port_id: 端口ID，1或2
            request_length: 请求的数据长度（字节）
            parse_type: 解析类型，支持 'int16' 等
            
        返回:
            解析后的数据列表，若失败则返回None
        """
        if not self.connected:
            logger.error("未连接到传感器，无法获取数据")
            return None
            
        # 选择指定端口
        if not self.select_port(port_id):
            logger.error(f"选择端口{port_id}失败")
            return None
            
        # 根据端口ID选择合适的命令
        command = "get_data" if port_id == 1 else "get_data2"
        logger.info(f"从端口{port_id}获取{request_length}字节数据")
        
        # 调用接口
        data = self.get_ser_response(command, request_length)
        if not data:
            logger.error(f"从端口{port_id}获取原始数据失败")
            return None
    
        # 数据验证
        if len(data) < 12:
            logger.error(f"端口{port_id}数据长度不足，无法裁切，实际长度: {len(data)}")
            return None
            
        # 提取真正的数据部分（跳过头部12个字符）
        valid_data = data[12:]
        logger.debug(f"端口{port_id}裁切后数据: {valid_data}")

        # 解析为单字节数组
        try:
            byte_values = list(bytes.fromhex(valid_data))
            logger.info(f"成功从端口{port_id}解析{len(byte_values)}个单字节值")
            return byte_values
        except ValueError as e:
            logger.error(f"端口{port_id}十六进制数据解析失败: {str(e)}, 数据: {valid_data}")
            return None      
    
def main():
    """主函数，程序入口"""
    logger.info("力传感器数据采集程序启动")
    
    # 创建通信实例
    sensor = SensorCommunication()
    
    try:
        # 列出可用串口
        ports = sensor.list_available_ports()
        if not ports:
            logger.error("未检测到可用串口，请检查设备连接")
            return
            
        # 选择第一个可用串口（也可修改为用户选择）
        chosen_port = ports[0]['device']
        logger.info(f"选择串口: {chosen_port}")
        
        # 连接串口
        if not sensor.connect(chosen_port):
            logger.error("串口连接失败，程序退出")
            return
            
        # 初始化控制盒
        if not sensor.init_box():
            logger.error("传感器初始化失败，程序退出")
            return
            
        # 主循环
        try:
            while True:
                # 获取CN1数据
                # logger.info("读取CN1数据...")
                # data1 = sensor.get_port_data(1, 27, 'byte')
                # if data1:
                #     # data1 = data1[6:]
                #     logger.info(f"CN1数据: {data1}...")  # 只显示前10个数据
                
                # time.sleep(1)
                
                # 获取CN2数据
                logger.info("读取CN2数据...")
                data2 = sensor.get_port_data(2, 3, 'byte')
                if data2:
                # if data2 and len(data2) >= 3:
                    # data2 = data2[-3:]
                    logger.info(f"CN2数据: {data2}...")
                    # 保留最后3字节
                    # last_three_bytes = data2[-3:] if len(data2) >= 3 else data2
                    # logger.info(f"CN2数据（最后3字节）: {last_three_bytes}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("用户中断程序")
        except Exception as e:
            logger.error(f"主循环出错: {str(e)}")
            
    finally:
        # 断开连接
        sensor.disconnect()
        logger.info("程序结束")

if __name__ == "__main__":
    main()