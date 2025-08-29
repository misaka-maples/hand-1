import open3d as o3d

def main():
    # 创建一个立方体
    cube = o3d.geometry.TriangleMesh.create_box(width=1.0, height=1.0, depth=1.0)
    cube.compute_vertex_normals()  # 计算法线，方便渲染
    cube.paint_uniform_color([0.1, 0.7, 0.3])  # 给立方体上色 (绿色)

    # 可视化
    o3d.visualization.draw_geometries([cube])

if __name__ == "__main__":
    main()
