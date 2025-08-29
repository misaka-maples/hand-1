import numpy as np
from scipy.optimize import fsolve
# 或者 from scipy.optimize import root

def solve_for_cosv(a,b,c,d,n, x0=0.5, y0=0.5, v0=0.5):
    """
    输入：标量 a,b,c,d,n（n 单位为弧度）
    可选初值 x0,y0,v0（v 单位为弧度）
    返回：字典 { 'x':..., 'y':..., 'v':..., 'cosv':... }
    """
    def fun(vars):
        x,y,v = vars
        cv = np.cos(v)
        cnv = np.cos(n - v)
        f1 = x*x + y*y - 2*x*y*cv - a*a             # eq1 = 0
        f2 = (d - x)**2 + (c - y)**2 - 2*(d-x)*(c-y)*cv - b*b  # eq2 = 0
        f3 = y*y - (a*a + x*x - 2*a*x*cnv)          # eq3 = 0
        return np.array([f1,f2,f3])

    # 推荐使用 root 或 fsolve；fsolve 用法如下
    sol = fsolve(fun, np.array([x0,y0,v0]), maxfev=20000)
    x_sol, y_sol, v_sol = sol
    cosv = (x_sol**2 + y_sol**2 - a*a) / (2*x_sol*y_sol)
    return {'x':float(x_sol), 'y':float(y_sol), 'v':float(v_sol), 'cosv':float(cosv)}

# 示例（注意：n 以弧度输入）
a,b,c,d,n = 20, 40, 100, 100, np.pi/2
res = solve_for_cosv(a,b,c,d,n, x0=40, y0=40, v0=np.pi/1.5)
print(np.rad2deg(res['v']))
