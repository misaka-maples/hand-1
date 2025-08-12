import serial
import struct
import time

# 计算 LRC 校验
def calc_lrc(data: bytes) -> int:
    s = sum(data) & 0xFF
    return ((~s + 1) & 0xFF)

# 构造协议帧
def build_frame(fix_id, index, main_cmd, sub_cmd1, sub_cmd2, data_bytes=b''):
    head = b'\x55\xAA\x7B\x7B'
    tail = b'\x55\xAA\x7D\x7D'
    length = struct.pack('<H', len(data_bytes))  # 小端
    lrc_data = bytes([fix_id, index, main_cmd, sub_cmd1, sub_cmd2]) + length + data_bytes
    lrc = bytes([calc_lrc(lrc_data)])
    return head + lrc_data + lrc + tail

# 发送命令并接收应答
def send_cmd(ser, frame):
    ser.write(frame)
    time.sleep(0.05)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print("收到应答:", resp.hex(' ').upper())
        return resp
    return None

if __name__ == "__main__":
    ser = serial.Serial('/dev/ttyACM0', 460800, timeout=1)

    # FIX_ID = 0x0E  # 控制盒 ID
    # INDEX = 0x00   # 序号
    # PORT = 0x01
    # MODE = 0X15
    data1 = bytes.fromhex('55 AA 7B 7B 0E 00 70 C0 0C 01 00 01 B4 55 AA 7D 7D')
    data2 = bytes.fromhex('55 AA 7B 7B 0E 00 70 B1 0A 01 00 01 C5 55 AA 7D 7D')
    data3 = bytes.fromhex('55 AA 7B 7B 0E 00 70 C0 06 00 24 00 09 7B 04 1E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 E4 55 AA 7D 7D')
    send_cmd(ser, data1)
    print("\n")
    send_cmd(ser, data2)
    print("\n")

    send_cmd(ser, data3)
    # # 1. 选择 CAN1 端口（协议端口ID=0x0A表示CAN1）
    # select_can1 = build_frame(FIX_ID, INDEX, 0x70, 0xB1, 0x0A, bytes([PORT]))
    # print(f"选择指定端口{PORT}的模组:", select_can1.hex(' ').upper())
    # send_cmd(ser, select_can1)

    # # 2. 设置 Gen2 工作模式（模式值0x15，协议给的）
    # set_mode = build_frame(FIX_ID, INDEX, 0x70, 0xC0, 0x0C, bytes([MODE]))
    # print(f"设置{MODE}工作模式:", set_mode.hex(' ').upper())
    # send_cmd(ser, set_mode)

    # # 3. 从地址 0x040E (1038) 读取 30 字节
    # # SPI 读命令格式: [功能码0x7B][地址(2B小端)][长度(2B小端)]
    # start_addr = struct.pack('<H', 0x03F0)  # 小端
    # read_len = struct.pack('<H', 3)        # 30 字节
    # spi_read_data = bytes([0x7B]) + start_addr + read_len

    # get_data_frame = build_frame(FIX_ID, INDEX, 0x70, 0xC0, 0x06, spi_read_data)
    # print("读取地址 0x040E 开始的 30 字节:", get_data_frame.hex(' ').upper())
    # resp = send_cmd(ser, get_data_frame)

    # # 4. 解析 FX/FY/FZ
    # if resp and len(resp) >= 13:
    #     try:
    #         data_len = struct.unpack('<H', resp[8:10])[0]
    #         data = resp[10:10+data_len]
    #         if len(data) >= 3:
    #             fx, fy, fz = struct.unpack('bbb', data[:3])
    #             # print(f"合力值: FX={fx}, FY={fy}, FZ={fz}")
    #         else:
    #             print("数据区长度不足，无法解析 FX/FY/FZ")
    #     except Exception as e:
    #         print("解析失败:", e)

    # ser.close()
