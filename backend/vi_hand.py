import open3d as o3d
import numpy as np
import faulthandler
faulthandler.enable()

def create_box(length=0.1, width=0.02, height=0.02, color=[0.8,0.2,0.2]):
    mesh = o3d.geometry.TriangleMesh.create_box(width=width, height=height, depth=length)
    mesh.paint_uniform_color(color)
    mesh.compute_vertex_normals()
    return mesh

def rotate_joint(mesh, R, origin):
    mesh.translate(-origin)
    mesh.rotate(R, center=np.zeros(3))
    mesh.translate(origin)

def create_marker(radius=0.005, color=[1,0,0]):
    sphere = o3d.geometry.TriangleMesh.create_sphere(radius=radius)
    sphere.paint_uniform_color(color)
    sphere.compute_vertex_normals()
    return sphere

def create_finger(lengths, angles, colors=None, width=0.015, height=0.015):
    meshes = []
    pivot = np.array([0,0,0])
    axis  = np.array([1,0,0])
    R_total = np.eye(3)

    for i, (length, theta) in enumerate(zip(lengths, angles)):
        color = colors[i % len(colors)] if colors else [0.8,0.2,0.2]
        bone = create_box(length=length, width=width, height=height, color=color)
        bone.translate(pivot)
        R_local = o3d.geometry.get_rotation_matrix_from_axis_angle(axis * theta)
        R_total = R_total @ R_local
        rotate_joint(bone, R_total, origin=pivot)
        local_tip = np.array([0,0,length])
        pivot = pivot + (R_total @ local_tip.reshape(3,1)).flatten()
        meshes.append(bone)

    final_dir = R_total @ np.array([0,0,1])
    return meshes, final_dir, pivot

def create_hand():
    finger_lengths = [0.047, 0.0435]
    finger_angles = [np.deg2rad(0), np.deg2rad(12)]
    total_finger_length = sum(finger_lengths)

    # 手掌尺寸
    palm_width = 0.08 * 1.2
    palm_height = 0.05 * 1.0
    palm_depth = total_finger_length * 0.5

    # -------------------------
    # 三指在手掌顶面一排
    z_top = palm_depth
    num_fingers = 3
    x_start = -palm_width/4
    x_end   = palm_width/4
    x_positions = np.linspace(x_start, x_end, num_fingers)
    y_top = palm_height/2  
    finger_bases = [[x, y_top, z_top] for x in x_positions]

    # 大拇指在右侧
    thumb_x = palm_width / 2
    thumb_y = 0
    thumb_z = palm_depth / 2
    finger_bases.append([thumb_x, thumb_y, thumb_z])

    # -------------------------
    colors = [
        [[0.8,0.2,0.2],[0.8,0.5,0.5]],  # index
        [[0.2,0.8,0.2],[0.5,0.8,0.5]],  # middle
        [[0.2,0.2,0.8],[0.5,0.5,0.8]],  # ring
        [[0.8,0.5,0.2],[0.9,0.7,0.5]]   # thumb
    ]

    all_fingers, finger_tips = [], []

    for idx, (base, color) in enumerate(zip(finger_bases, colors)):
        meshes, final_dir, tip = create_finger(finger_lengths, finger_angles, colors=color)
        if idx == 3:
            # 大拇指绕 Z 轴旋转 -45° 指向食指
            R_thumb = o3d.geometry.get_rotation_matrix_from_axis_angle(np.array([0,0,1])*np.deg2rad(-45))
            for m in meshes:
                rotate_joint(m, R_thumb, origin=np.array([0,0,0]))
        for m in meshes:
            m.translate(base)
        all_fingers.extend(meshes)

        # 指尖位置基于统一 base (手掌原点)
        finger_tips.append(tip + np.array(base))

    # -------------------------
    # 手掌 mesh
    palm = o3d.geometry.TriangleMesh.create_box(width=palm_width, height=palm_height, depth=palm_depth)
    palm.paint_uniform_color([0.5,0.5,0.5])
    palm.translate([-palm_width/2, -palm_height/2, 0])

    # 统一 base marker (放在手掌中心底部原点)
    base_marker = create_marker(color=[0,0,1])
    base_marker.translate([0,0,0])

    return all_fingers, palm, base_marker, finger_tips

if __name__ == "__main__":
    hand, palm, base_marker, finger_tips = create_hand()

    # 地面
    ground = o3d.geometry.TriangleMesh.create_box(width=0.5, height=0.5, depth=0.01)
    ground.paint_uniform_color([0.7,0.7,0.7])
    ground.translate([-0.25,-0.25,-0.01])

    # 可视化
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    for g in [ground, palm] + hand + [base_marker]:
        vis.add_geometry(g)
    
    ctr = vis.get_view_control()
    ctr.set_front([0.5, -1, -0.8])
    ctr.set_up([0,0,1])
    ctr.set_lookat([0,0,0])
    
    vis.run()
    vis.destroy_window()

    print("指尖位置 (基于统一base):")
    for idx, tip in enumerate(finger_tips):
        print(f"Finger {idx+1} tip:", tip)
