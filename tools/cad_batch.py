# -*- coding: utf-8 -*-
"""批量把导出的 CAD 转成网页用的 glb，并把结果写进 assets/models/manifest.json。

用法
----
    # 把导出件丢进一个文件夹（STEP / STL / 3MF / URDF 包都可以混放）
    python tools/cad_batch.py "C:/path/to/导出" --season 2026

    # 只转不写清单
    python tools/cad_batch.py "C:/path/to/导出" --no-manifest

    # 转换后自动按目标面数抽稀
    python tools/cad_batch.py "C:/path/to/导出" --target-tris 150000

命名建议：`r26-r1.step`、`r26-r2.step`、`r25-r1.stl` ……
文件名里的 `rNN` 会被识别成赛季，`R1`/`R2` 会被识别成车型，
识别不出也不影响转换，只是清单里的显示名要手工改。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
MODELS = os.path.join(SITE, "assets", "models")
MANIFEST = os.path.join(MODELS, "manifest.json")

SUPPORTED = (".step", ".stp", ".stl", ".3mf", ".obj", ".ply", ".urdf")


def slugify(name):
    s = os.path.splitext(name)[0].lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", s).strip("-")
    return s or "model"


def guess_meta(filename, season_hint=None):
    stem = os.path.splitext(os.path.basename(filename))[0]
    low = stem.lower()
    season = season_hint
    m = re.search(r"r(2\d)", low)
    if m and not season:
        season = "20" + m.group(1)
    kind = None
    for k in ("r1", "r2"):
        if k in low:
            kind = k.upper()
            break
    if season and kind:
        name = f"{season} 赛季 {kind} 整机"
    elif season:
        name = f"{season} 赛季模型"
    else:
        name = stem
    return {"season": season or "", "kind": kind, "name": name}


def iter_inputs(root):
    """遍历输入。URDF 包按「一个整体」处理：只产出 package 目录，跳过它自己的 meshes/。"""
    if os.path.isfile(root):
        if root.lower().endswith(".urdf"):
            yield _package_root(root)
        else:
            yield root
        return

    packages = []
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".urdf"):
                pkg = _package_root(os.path.join(dirpath, f))
                if pkg not in packages:
                    packages.append(pkg)

    for pkg in packages:
        yield pkg

    def inside_pkg(path):
        p = os.path.abspath(path).lower()
        return any(p.startswith(pk.lower() + os.sep) or p == pk.lower() for pk in packages)

    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            low = f.lower()
            if low.startswith(".") or not low.endswith(SUPPORTED) or low.endswith(".urdf"):
                continue
            if inside_pkg(full):
                continue
            yield full


def _package_root(urdf_path):
    """urdf/xxx.urdf → 包根；直接放在根目录的 urdf → 其所在目录。"""
    d = os.path.dirname(os.path.abspath(urdf_path))
    if os.path.basename(d).lower() == "urdf":
        return os.path.dirname(d)
    return d


def convert(src, out_glb, target_tris):
    cmd = [sys.executable, os.path.join(HERE, "cad_to_glb.py"), src, "-o", out_glb]
    if target_tris:
        cmd += ["--target-tris", str(target_tris)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    tri = None
    size = None
    m = re.search(r"三角面 ([\d,]+)", out)
    if m:
        tri = int(m.group(1).replace(",", ""))
    m2 = re.search(r"尺寸 \[([^\]]+)\]", out)
    if m2:
        size = [float(v) for v in m2.group(1).split(",")]
    return proc.returncode, tri, size, out


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            return json.load(fh)
    return {"updated": "", "models": [], "planned": []}


def main():
    ap = argparse.ArgumentParser(description="批量 CAD → glb")
    ap.add_argument("input", help="导出件所在目录或单个文件")
    ap.add_argument("--season", default="", help="赛季提示，如 2026")
    ap.add_argument("--target-tris", type=int, default=0, help="抽稀到目标面数")
    ap.add_argument("--no-manifest", action="store_true", help="只转不写清单")
    args = ap.parse_args()

    os.makedirs(MODELS, exist_ok=True)
    srcs = list(iter_inputs(args.input))
    if not srcs:
        raise SystemExit(f"{args.input} 里没有可转换的文件（支持 {'/'.join(SUPPORTED)}）")

    manifest = load_manifest()
    by_file = {m["file"]: m for m in manifest.get("models", [])}
    added, updated, failed = 0, 0, 0

    for src in srcs:
        base = os.path.basename(src.rstrip("/\\"))
        slug = slugify(base)
        glb_name = slug + ".glb"
        out_glb = os.path.join(MODELS, glb_name)
        print(f"\n==> {src}")
        code, tri, size, log = convert(src, out_glb, args.target_tris)
        if code != 0 or not os.path.exists(out_glb):
            failed += 1
            print("    失败：")
            for line in log.strip().splitlines()[-4:]:
                print("      " + line)
            continue

        mb = os.path.getsize(out_glb) / 1024 / 1024
        print(f"    -> {glb_name}  {mb:.2f} MB  {tri or '?'} 面")
        print("", end="")

        if args.no_manifest:
            continue

        meta = guess_meta(src, args.season or None)
        entry = {
            "id": slug,
            "name": meta["name"],
            "season": meta["season"],
            "badge": (meta["kind"] or "") + " · 整机" if meta["kind"] else "模型",
            "file": glb_name,
            "triangles": tri or 0,
            "size": [round(v, 4) for v in (size or [0, 0, 0])],
            "note": "由 SolidWorks 总装导出后转换，保留装配位置，仅可视化几何。",
            "source": os.path.basename(src),
        }
        if glb_name in by_file:
            by_file[glb_name].update(entry)
            updated += 1
        else:
            manifest["models"].append(entry)
            by_file[glb_name] = entry
            added += 1

    if not args.no_manifest:
        manifest["updated"] = __import__("datetime").date.today().isoformat()
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\n清单已更新：新增 {added}，更新 {updated}，失败 {failed}")
        print(f"  {MANIFEST}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
