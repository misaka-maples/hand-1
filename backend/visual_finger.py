import open3d as o3d
import numpy as np
import faulthandler
faulthandler.enable()

def create_box(length=0.1, width=0.02, height=0.02, color=[0.8,0.2,0.2]):
    """创建长方体指骨"""
    mesh = o3d.geometry.TriangleMesh.create_box(width=width, height=height, depth=length)
    mesh.paint_uniform_color(color)
    mesh.compute_vertex_normals()
    return mesh

def rotate_joint(mesh, R, origin):
    """绕 origin 点应用旋转矩阵 R"""
    mesh.translate(-origin)
    mesh.rotate(R, center=np.zeros(3))
    mesh.translate(origin)

def create_finger(lengths, angles, colors=None):
    """
    创建一根手指
    lengths: [l1, l2, ...]
    angles : [θ1, θ2, ...]  每节相对上一节的转角
    return: (meshes, final_dir)
    """
    if colors is None:
        colors = [[0.8,0.2,0.2],[0.2,0.8,0.2],[0.2,0.2,0.8]]

    meshes = []
    pivot = np.array([0,0,0])   # 根部
    axis  = np.array([1,0,0])   # 绕 X 轴
    R_total = np.eye(3)         # 累积旋转矩阵

    for i, (length, theta) in enumerate(zip(lengths, angles)):
        # Step1: 创建骨段
        bone = create_box(length=length, color=colors[i % len(colors)])
        bone.translate(pivot)

        # Step2: 当前关节旋转矩阵（在局部坐标系里）
        R_local = o3d.geometry.get_rotation_matrix_from_axis_angle(axis * theta)

        # Step3: 累积旋转（关键修改：右乘，表示在前一节的坐标系下旋转）
        R_total = R_total @ R_local

        # Step4: 应用旋转到骨段
        rotate_joint(bone, R_total, origin=pivot)

        # Step5: 更新 pivot（末端）
        local_tip = np.array([0,0,length])
        global_tip = (R_total @ local_tip.reshape(3,1)).flatten()
        pivot = pivot + global_tip

        meshes.append(bone)

    # 最终远端方向
    final_dir = R_total @ np.array([0,0,1])

    return meshes, final_dir,pivot

if __name__ == "__main__":
    lengths = [0.04700,0.0434822]   # 两节手指
    angles  = [np.deg2rad(0), np.deg2rad(11.795026563914718)]  # 第二节相对于第一节
    finger, final_dir, pivot = create_finger(lengths, angles)

    # === 地面 ===
    ground = o3d.geometry.TriangleMesh.create_box(width=0.5, height=0.5, depth=0.01)
    ground.paint_uniform_color([0.7,0.7,0.7])
    ground.translate([-0.25, -0.25, -0.01])

    # === 可视化 ===
    o3d.visualization.draw_geometries([ground] + finger)

    # === 计算远端相对垂直方向的角度 ===
    z_axis = np.array([0,0,1])
    cos_angle = np.dot(final_dir, z_axis) / (np.linalg.norm(final_dir) * np.linalg.norm(z_axis))
    angle_with_vertical = np.arccos(np.clip(cos_angle, -1.0, 1.0))

    print("远端相对垂直地面的角度(度)：", np.degrees(angle_with_vertical))
    print("远端指尖位置：", pivot)