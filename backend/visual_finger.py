import open3d as o3d
import numpy as np

def create_box(length=0.1, width=0.02, height=0.02, color=[0.8,0.2,0.2]):
    """创建一个矩形盒子手指关节"""
    mesh = o3d.geometry.TriangleMesh.create_box(width=width, height=height, depth=length)
    mesh.paint_uniform_color(color)
    mesh.compute_vertex_normals()
    return mesh

def rotate_joint(mesh, axis, angle, origin):
    """
    旋转关节
    mesh: open3d.geometry.TriangleMesh
    axis: 旋转轴, np.array([x,y,z])
    angle: 弧度
    origin: 旋转中心
    """
    R = mesh.get_rotation_matrix_from_axis_angle(axis * angle)
    mesh.translate(-origin)
    mesh.rotate(R, center=np.zeros(3))
    mesh.translate(origin)

# 创建两个关节
proximal = create_box(length=0.1, color=[0.8,0.2,0.2])  # 近端关节
distal = create_box(length=0.08, color=[0.2,0.8,0.2])  # 远端关节

# 设置远端关节初始位置（末端接近近端）
distal.translate([0,0,0.1])  # 沿 z 轴接到近端关节末端

# 输入角度（弧度）
theta1 = np.deg2rad(30)  # 近端关节旋转30°
theta2 = np.deg2rad(45)  # 远端关节旋转45°

# 旋转近端关节（绕 x 轴）
rotate_joint(proximal, np.array([1,0,0]), theta1, origin=np.array([0.01,0.01,0]))  # 旋转中心在近端底部

# 旋转远端关节（绕近端关节末端）
rotate_joint(distal, np.array([1,0,0]), theta2, origin=np.array([0.01,0.01,0.1]))  

# 可视化
o3d.visualization.draw_geometries([proximal, distal])
