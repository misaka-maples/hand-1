import serial
import struct
import time

# ====== 协议工具函数 ======
def calc_lrc(data: bytes) -> int:
    """计算 LRC 校验，8位累加取反加一"""
    s = sum(data) & 0xFF
    return ((~s + 1) & 0xFF)

def build_frame(fix_id, index, main_cmd, sub_cmd, data_bytes=b''):
    """构造主机发送帧"""
    head = b'\x55\xAA\x7B\x7B'
    tail = b'\x55\xAA\x7D\x7D'
    length = struct.pack('<H', len(data_bytes))  # 小端
    # LRC 范围: FIX ID, Index, Main Cmd, Sub Cmd, Length, Data
    lrc_data = bytes([fix_id, index, main_cmd, sub_cmd]) + length + data_bytes
    lrc = bytes([calc_lrc(lrc_data)])
    return head + lrc_data + lrc + tail

# ====== 串口初始化 ======
ser = serial.Serial(
    port='/dev/ttyACM0',  # 修改为实际端口
    baudrate=460800,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

# ====== 示例：选择端口 0 模组 ======
# 协议内容参考文档 "选择指定端口的模组"
fix_id = 0x0E
index = 0x00
main_cmd = 0x70
sub_cmd = 0xB1
data = bytes([0x00])  # 端口号 0
frame = build_frame(fix_id, index, main_cmd, sub_cmd, data)

print("发送帧:", frame.hex(' ').upper())
ser.write(frame)

# ====== 接收返回 ======
time.sleep(0.05)
if ser.in_waiting:
    resp = ser.read(ser.in_waiting)
    print("接收帧:", resp.hex(' ').upper())

ser.close()
