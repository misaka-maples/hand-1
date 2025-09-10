import math
import numpy as np

def crank_angle_from_link(L):
    """
    输入：
        r: 曲柄长度
        L: 连杆长度
        s,d: 滑块铰点坐标
    返回：
        theta_list: 所有可能解（弧度）
    """
    r = 0.001*29   # 曲柄长度
    s = 58*0.001   # 滑块水平位置
    d = 0.001*29.6   # 垂直偏移
    K = (r**2 + s**2 + d**2 - L**2) / (2*r)
    rho = np.hypot(s,d)
    phi = np.arctan2(d,s)

    if abs(K) > rho:
        return []  # 无解

    delta = np.arccos(K / rho)
    theta1 = phi + delta
    theta2 = phi - delta
    return [theta1, theta2]
print(90-np.rad2deg(crank_angle_from_link(0.001*43.1211))[0]) 