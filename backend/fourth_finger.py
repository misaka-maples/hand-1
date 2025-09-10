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
    r = 0.001*8.459   # 曲柄长度
    s = 70.964*0.001   # 滑块水平位置
    d = 0.001*5.9821   # 垂直偏移
    K = (r**2 + s**2 + d**2 - L**2) / (2*r)
    rho = np.hypot(s,d)
    phi = np.arctan2(d,s)

    if abs(K) > rho:
        return []  # 无解

    delta = np.arccos(K / rho)
    theta1 = phi + delta
    theta2 = phi - delta
    return [theta1, theta2]
def calculate_cos_v_and_cos_m(n):
    a = 5.7183 #底边长
    b = 4.6098 #顶边长
    c = 37.00 #左向右边
    d = 37.73 #右边
    # 计算 M, N, C
    M = 2 * d * (c + a * math.cos(n))
    N = 2 * a * d * math.sin(n)
    C = a**2 + d**2 + c**2 + 2 * a * c * math.cos(n) - b**2
    
    denominator = M**2 + N**2
    if denominator == 0:
        return None, None  # 避免除以零
    
    # 计算根号内的值
    inside_sqrt = M**2 + N**2 - C**2
    if inside_sqrt < 0:
        return None, None  # 无实数解
    
    sqrt_val = math.sqrt(inside_sqrt)
    
    # 计算 cos(v) 的两个可能值
    cos_v1 = (M * C + N * sqrt_val) / denominator
    cos_v2 = (M * C - N * sqrt_val) / denominator
    
    # 计算对应的 cos(m) 值
    cos_m1 = (c - d * cos_v1 + a * math.cos(n)) / b
    cos_m2 = (c - d * cos_v2 + a * math.cos(n)) / b
    
    # 返回两个可能的解
    solutions = [
        (cos_v1, cos_m1),
        (cos_v2, cos_m2)
    ]
    return solutions

# 示例使用
if __name__ == "__main__":
    n = np.deg2rad(48.13)  # 45度转换为弧度
    L = 64.5*0.001+0.001*1.7029

    thetas = crank_angle_from_link(L)
    n = np.deg2rad(np.degrees(thetas[0]) - 40.15 + 48.13)
    solutions = calculate_cos_v_and_cos_m(n)
    if solutions is None:
        print("No real solutions")
    else:
        for i, (cos_v, cos_m) in enumerate(solutions):
            print(f"Solution {i+1}: cos_v = {cos_v}, cos_m = {cos_m}")
            print(f"v angle = {math.degrees(math.acos(cos_v))} degrees")
            print(f"m angle = {math.degrees(math.acos(cos_m))-47.80155097480674} degrees")