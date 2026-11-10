# -*- coding: utf-8 -*-
"""CAD → GLB：把 SolidWorks 导出的模型转成网页可直接加载的 glTF 二进制（.glb）。

支持的输入
----------
1. URDF 包（SolidWorks → URDF Exporter 的导出，含 meshes/*.STL + 关节位姿）
   —— 会按关节把零件摆到正确位置，并按材质上色，得到完整的装配体。
2. 单个网格文件：.stl / .3mf / .obj / .ply
   —— 直接居中、定向、按目标面数抽稀。
3. .step / .stp（需要 cadquery/OCP，未安装时给出提示并跳过）

用法
----
    python tools/cad_to_glb.py <输入路径> -o ../assets/models/xxx.glb
    python tools/cad_to_glb.py 底盘/R2025.SLDASM -o out/r2025.glb --name "2025 R1 底盘"
    python tools/cad_to_glb.py model.STL -o out/m.glb --target-tris 200000

约定
----
- CAD 普遍是 Z 轴向上，glTF/three.js 是 Y 轴向上：默认把 Z-up 转成 Y-up。
- 单位按米处理；SolidWorks 的 URDF 导出与 STL 导出通常已经是米。
- 输出统一把包围盒底面贴到 y=0、水平居中，方便网页里套用同一个相机参数。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import trimesh


# ---------------------------------------------------------------- 工具函数


def _rpy_to_matrix(rpy):
    r, p, y = (float(v) for v in rpy)
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return np.array(
        [
            [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr],
        ]
    )


def _transform(xyz, rpy):
    m = np.eye(4)
    m[:3, :3] = _rpy_to_matrix(rpy)
    m[:3, 3] = [float(v) for v in xyz]
    return m


def _z_up_to_y_up():
    """绕 X 轴 -90°：把 CAD 的 Z-up 转到 glTF 的 Y-up。"""
    m = np.eye(4)
    m[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)
    return m


def _parse_vec(text, default):
    if not text:
        return list(default)
    return [float(v) for v in text.split()]


# ---------------------------------------------------------------- URDF 装配


def load_urdf(urdf_path):
    """返回 [(link_name, mesh_path, world_matrix, (r,g,b,a))]，已经算好世界变换。"""
    root = ET.parse(urdf_path).getroot()
    base_dir = os.path.dirname(os.path.abspath(urdf_path))
    pkg_root = os.path.dirname(base_dir)  # urdf/ 的上一层，即包根

    # link -> visual 信息
    links = {}
    for link in root.findall("link"):
        name = link.get("name")
        visual = link.find("visual")
        if visual is None:
            continue
        mesh = visual.find("geometry/mesh")
        if mesh is None:
            continue
        filename = mesh.get("filename", "")
        if filename.startswith("package://"):
            filename = filename[len("package://"):]
            pkg, _, rest = filename.partition("/")
            path = os.path.join(pkg_root, rest.replace("/", os.sep))
        else:
            path = os.path.join(base_dir, filename.replace("/", os.sep))
        if not os.path.exists(path):
            print(f"  ! 缺少网格文件：{path}")
            continue
        origin = visual.find("origin")
        xyz = _parse_vec(origin.get("xyz") if origin is not None else None, (0, 0, 0))
        rpy = _parse_vec(origin.get("rpy") if origin is not None else None, (0, 0, 0))
        color = (0.75, 0.76, 0.78, 1.0)
        mat = visual.find("material/color")
        if mat is not None:
            rgba = _parse_vec(mat.get("rgba"), (0.75, 0.76, 0.78, 1.0))
            if len(rgba) == 4:
                color = tuple(rgba)
        links[name] = {"path": path, "origin": _transform(xyz, rpy), "color": color}

    # 关节：child -> (parent, 相对变换)
    parent_of = {}
    joint_tf = {}
    for joint in root.findall("joint"):
        child = joint.find("child").get("link")
        parent = joint.find("parent").get("link")
        origin = joint.find("origin")
        xyz = _parse_vec(origin.get("xyz") if origin is not None else None, (0, 0, 0))
        rpy = _parse_vec(origin.get("rpy") if origin is not None else None, (0, 0, 0))
        parent_of[child] = parent
        joint_tf[child] = _transform(xyz, rpy)

    def world_of(link):
        m = np.eye(4)
        cur = link
        chain = []
        while cur in parent_of:
            chain.append(joint_tf[cur])
            cur = parent_of[cur]
        for t in reversed(chain):
            m = m @ t
        return m

    out = []
    for name, info in links.items():
        out.append((name, info["path"], world_of(name) @ info["origin"], info["color"]))
    return out


def build_scene_from_urdf(urdf_path, target_tris=None):
    parts = load_urdf(urdf_path)
    if not parts:
        raise SystemExit("URDF 里没有可用的带网格的 link")

    scene = trimesh.Scene()
    total = 0
    for name, path, world, color in parts:
        mesh = trimesh.load(path, force="mesh")
        mesh.apply_transform(world)
        total += len(mesh.faces)
        scene.add_geometry(
            mesh,
            geom_name=name,
            node_name=name,
            transform=np.eye(4),
            metadata={"name": name},
        )
        scene.geometry[name].visual = trimesh.visual.TextureVisuals(
            material=trimesh.visual.material.PBRMaterial(
                baseColorFactor=[color[0], color[1], color[2], color[3]],
                metallicFactor=0.15,
                roughnessFactor=0.65,
                doubleSided=True,
                name=name,
            )
        )
    print(f"  零件 {len(parts)} 个，共 {total:,} 个三角面")
    return scene, total


# ---------------------------------------------------------------- 单文件网格


def build_scene_from_mesh(path, target_tris=None):
    mesh = trimesh.load(path, force="mesh")
    if target_tris and len(mesh.faces) > target_tris:
        try:
            import fast_simplification  # noqa: F401

            mesh = mesh.simplify_quadric_decimation(face_count=target_tris)
            print(f"  抽稀到 {len(mesh.faces):,} 面")
        except Exception:
            print("  ! 未安装 fast-simplification，跳过抽稀（pip install fast-simplification）")
    scene = trimesh.Scene()
    scene.add_geometry(mesh, geom_name="mesh", node_name="mesh")
    scene.geometry["mesh"].visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=[0.72, 0.74, 0.77, 1.0],
            metallicFactor=0.2,
            roughnessFactor=0.6,
            doubleSided=True,
        )
    )
    print(f"  共 {len(mesh.faces):,} 个三角面")
    return scene, len(mesh.faces)


def build_scene_from_step(path, target_tris=None):
    try:
        from OCP.STEPControl import STEPControl_Reader
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_FACE
        from OCP.BRep import BRep_Tool
        from OCP.TopoDS import TopoDS
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "读取 STEP 需要 cadquery / OCP，当前未安装：\n"
            "    pip install cadquery\n"
            f"（原始错误：{exc}）\n"
            "替代方案：在 SolidWorks 里直接把装配体另存为 STL/3MF，再喂给本脚本。"
        )

    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"STEP 读取失败：{path}")
    reader.TransferRoots()
    shape = reader.OneShape()

    BRepMesh_IncrementalMesh(shape, 0.15, False, 0.5, True)

    verts = []
    faces = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = face.Location()
        triangulation = BRep_Tool.Triangulation_s(face, loc)
        if triangulation is not None:
            offset = len(verts)
            for i in range(1, triangulation.NbNodes() + 1):
                p = triangulation.Node(i)
                verts.append((p.X(), p.Y(), p.Z()))
            for i in range(1, triangulation.NbTriangles() + 1):
                tri = triangulation.Triangle(i)
                a, b, c = tri.Get()
                faces.append((offset + a - 1, offset + b - 1, offset + c - 1))
        exp.Next()

    if not faces:
        raise SystemExit("STEP 里没提取到三角面")
    mesh = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=True)
    print(f"  共 {len(mesh.faces):,} 个三角面")
    scene = trimesh.Scene()
    scene.add_geometry(mesh, geom_name="step", node_name="step")
    scene.geometry["step"].visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=[0.72, 0.74, 0.77, 1.0],
            metallicFactor=0.2,
            roughnessFactor=0.6,
            doubleSided=True,
        )
    )
    return scene, len(mesh.faces)


# ---------------------------------------------------------------- 收尾与导出


def normalize(scene):
    """转 Y-up、按尺寸猜单位、水平居中、底部贴地，并记录尺寸。"""
    scene.apply_transform(_z_up_to_y_up())

    # 单位猜测：SolidWorks 的 STEP / STL 默认毫米，URDF 导出一般是米。
    # 机器人尺度在 0.2–3 m；若最大尺寸 > 20，几乎可以断定是毫米。
    extents = scene.extents
    max_dim = float(max(extents))
    unit = "m"
    if max_dim > 20.0:
        scene.apply_scale(0.001)
        unit = "mm→m"
        extents = scene.extents

    bounds = scene.bounds
    center = (bounds[0] + bounds[1]) / 2.0
    shift = np.array([-center[0], -bounds[0][1], -center[2]])
    scene.apply_translation(shift)
    size = scene.extents
    return {"size": [round(float(v), 4) for v in size], "unit": unit}


def main():
    ap = argparse.ArgumentParser(description="CAD → GLB 转换")
    ap.add_argument("input", help="URDF 文件 / URDF 包目录 / 网格文件 / STEP 文件")
    ap.add_argument("-o", "--output", required=True, help="输出 .glb 路径")
    ap.add_argument("--name", default="", help="写入 manifest 的显示名")
    ap.add_argument("--target-tris", type=int, default=0, help="抽稀到目标面数（单网格输入）")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    if not os.path.exists(src):
        raise SystemExit(f"找不到输入：{src}")

    lower = src.lower()
    print(f"==> {src}")

    if os.path.isdir(src):
        urdfs = []
        for root_dir, _dirs, files in os.walk(src):
            urdfs += [os.path.join(root_dir, f) for f in files if f.lower().endswith(".urdf")]
        if not urdfs:
            raise SystemExit("目录里没有 .urdf")
        urdfs.sort(key=len)
        scene, tris = build_scene_from_urdf(urdfs[0], args.target_tris)
    elif lower.endswith(".urdf"):
        scene, tris = build_scene_from_urdf(src, args.target_tris)
    elif lower.endswith((".stl", ".3mf", ".obj", ".ply")):
        scene, tris = build_scene_from_mesh(src, args.target_tris)
    elif lower.endswith((".step", ".stp")):
        scene, tris = build_scene_from_step(src, args.target_tris)
    else:
        raise SystemExit(f"不支持的格式：{os.path.splitext(src)[1]}")

    meta = normalize(scene)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    scene.export(args.output)
    size_mb = os.path.getsize(args.output) / 1024 / 1024
    print(f"==> 写出 {args.output}  {size_mb:.2f} MB  三角面 {tris:,}  尺寸 {meta['size']} m  单位 {meta['unit']}")
    if args.name:
        print(json.dumps({"name": args.name, "file": os.path.basename(args.output),
                          "triangles": tris, "size": meta["size"], "unit": meta["unit"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
