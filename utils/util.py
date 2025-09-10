import pybullet as p
import pybullet_data
import trimesh
import os

p.connect(p.DIRECT)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# 加载机器人 URDF
robot_id = p.loadURDF("/home/wfx/A-wfx-project/一代靈巧手/linker-bot linkerhand-urdf main l20/left/linkerhand_l20_left.urdf")
meshes = []
for link_index in range(-1, p.getNumJoints(robot_id)):
    visual_shapes = p.getVisualShapeData(robot_id, link_index)
    for vs in visual_shapes:
        filename = vs[4]
        if filename:
            # bytes 转 str
            if isinstance(filename, bytes):
                filename = filename.decode('utf-8')
            # 拼接路径
            mesh_path = os.path.join(pybullet_data.getDataPath(), filename)
            if os.path.exists(mesh_path):
                mesh = trimesh.load(mesh_path)
                meshes.append(mesh)

if len(meshes) == 0:
    print("没有加载到任何 mesh，检查 mesh 文件路径是否正确")
else:
    print(f"加载到 {len(meshes)} 个 mesh，正在导出为 robot.glb ...")
    scene = trimesh.Scene(meshes)
    scene.export("robot.glb")
    print("导出成功: robot.glb")
