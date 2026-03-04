#!/usr/bin/env python3
"""Batch simplify STL meshes using Blender's Decimate modifier.

Usage:
  blender --background --python simplify_meshes_blender.py -- <input_dir> <output_dir> [ratio]
"""

import glob
import os
import sys

import bpy


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []

    if len(argv) < 2:
        raise SystemExit(
            "Usage: blender --background --python simplify_meshes_blender.py -- "
            "<input_dir> <output_dir> [ratio]"
        )

    input_dir = argv[0]
    output_dir = argv[1]
    ratio = float(argv[2]) if len(argv) >= 3 else 0.01

    if not (0.0 < ratio <= 1.0):
        raise SystemExit("ratio must be in (0, 1]")

    return input_dir, output_dir, ratio


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def simplify_file(src_path: str, dst_path: str, ratio: float):
    bpy.ops.import_mesh.stl(filepath=src_path)
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj

    tris_before = len(obj.data.polygons)

    mod = obj.modifiers.new(name="Decimate", type="DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)

    tris_after = len(obj.data.polygons)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    bpy.ops.export_mesh.stl(filepath=dst_path, use_selection=True, ascii=False)

    mesh_data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh_data.users == 0:
        bpy.data.meshes.remove(mesh_data)

    return tris_before, tris_after


def main():
    input_dir, output_dir, ratio = parse_args()

    stl_files = sorted(glob.glob(os.path.join(input_dir, "*.STL")))
    if not stl_files:
        raise SystemExit(f"No STL files found in: {input_dir}")

    clear_scene()

    print(f"[simplify] files={len(stl_files)} ratio={ratio}")

    total_before = 0
    total_after = 0

    for src in stl_files:
        name = os.path.basename(src)
        dst = os.path.join(output_dir, name)
        before, after = simplify_file(src, dst, ratio)
        total_before += before
        total_after += after
        print(f"[simplify] {name}: {before} -> {after} triangles")

    reduction = 100.0 * (1.0 - (total_after / total_before)) if total_before else 0.0
    print(
        f"[simplify] total: {total_before} -> {total_after} triangles "
        f"({reduction:.2f}% reduced)"
    )


if __name__ == "__main__":
    main()
