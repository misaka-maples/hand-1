import math

def calculate_cos_v_and_cos_m(a, b, c, d, n):
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
    a = 20
    b = 40.0
    c = 100.0
    d = 100.0
    n = math.pi / 2  # 45度转换为弧度
    
    solutions = calculate_cos_v_and_cos_m(a, b, c, d, n)
    if solutions is None:
        print("No real solutions")
    else:
        for i, (cos_v, cos_m) in enumerate(solutions):
            print(f"Solution {i+1}: cos_v = {cos_v}, cos_m = {cos_m}")
            print(f"v angle = {math.degrees(math.acos(cos_v))} degrees")
            print(f"m angle = {math.degrees(math.acos(cos_m))} degrees")