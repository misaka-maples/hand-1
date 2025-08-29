import math

def calculate_cos_v(a, b, c, d, n):
    """
    根据已知参数计算 cos(v) 的值
    
    参数:
    a, b, c, d: 已知常数
    n: 已知角度（弧度）
    
    返回:
    cos_v1, cos_v2: cos(v) 的两个可能值（如果有实数解）
    如果无实数解，返回 None
    """
    # 计算 L
    L_sq = a**2 + c**2 + 2*a*c*math.cos(n)
    L = math.sqrt(L_sq)
    
    # 计算 T
    T = (L_sq + d**2 - b**2) / (2*d)
    
    # 计算 A
    A = c + a * math.cos(n)
    
    # 计算判别式
    discriminant = L_sq - T**2
    
    # 检查是否有实数解
    if discriminant < 0:
        print("无实数解")
        return None, None
    
    # 计算 cos(v) 的两个可能值
    sqrt_discriminant = math.sqrt(discriminant)
    cos_v1 = (A * T + a * math.sin(n) * sqrt_discriminant) / L_sq
    cos_v2 = (A * T - a * math.sin(n) * sqrt_discriminant) / L_sq
    
    return cos_v1, cos_v2

# 示例使用
if __name__ == "__main__":
    # 设置已知参数
    a = 20
    b = 40.0
    c = 100.0
    d = 100.0
    n = math.pi / 2  # 45度转换为弧度
    
    # 计算 cos(v)
    cos_v1, cos_v2 = calculate_cos_v(a, b, c, d, n)
    
    if cos_v1 is not None:
        print(f"cos(v) 的可能值 1: {cos_v1}")
        print(f"cos(v) 的可能值 2: {cos_v2}")
        
        # 如果需要，可以进一步计算 v 的角度
        v1 = math.acos(cos_v1)
        v2 = math.acos(cos_v2)
        print(f"v 的可能角度 1: {math.degrees(v1)} 度")
        print(f"v 的可能角度 2: {math.degrees(v2)} 度")