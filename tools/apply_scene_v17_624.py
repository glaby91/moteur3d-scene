#!/usr/bin/env python3
"""Add the user-supplied ice-cream truck to the V17.623 civic scene."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ_PATH = ROOT / "assets" / "camion_icecream.obj"
MTL_PATH = ROOT / "assets" / "camion_icecream.mtl"


def _dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _materials():
    materials = {}
    current = None
    for line in MTL_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "newmtl":
            current = parts[1]
            materials[current] = {}
        elif current and parts[0] in ("Kd", "Ks", "Ke") and len(parts) >= 4:
            materials[current][parts[0]] = [float(x) for x in parts[1:4]]
        elif current and parts[0] == "Ns" and len(parts) >= 2:
            materials[current]["Ns"] = float(parts[1])
    return materials


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    source_mtl = _materials()
    positions = []
    uvs = []
    groups: dict[str, list] = {}
    material = None

    def obj_index(token: str, count: int) -> int:
        index = int(token)
        return index - 1 if index > 0 else count + index

    for line in OBJ_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "v" and len(parts) >= 4:
            positions.append(tuple(float(x) for x in parts[1:4]))
        elif parts[0] == "vt" and len(parts) >= 3:
            uvs.append(tuple(float(x) for x in parts[1:3]))
        elif parts[0] == "usemtl" and len(parts) >= 2:
            material = parts[1]
        elif parts[0] == "f" and len(parts) >= 4:
            if material not in source_mtl:
                raise ValueError(f"OBJ references missing MTL material: {material}")
            refs = []
            for token in parts[1:]:
                fields = token.split("/")
                vi = obj_index(fields[0], len(positions))
                ti = obj_index(fields[1], len(uvs)) if len(fields) > 1 and fields[1] else None
                if vi < 0 or vi >= len(positions) or (ti is not None and (ti < 0 or ti >= len(uvs))):
                    raise ValueError(f"Bad OBJ index: {token}")
                refs.append((vi, ti))
            for corner in range(1, len(refs) - 1):
                tri = [refs[0], refs[corner], refs[corner + 1]]
                a, b, c = (positions[item[0]] for item in tri)
                ab = [b[i] - a[i] for i in range(3)]
                ac = [c[i] - a[i] for i in range(3)]
                cross = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
                if sum(value * value for value in cross) < 1e-18:
                    continue
                groups.setdefault(material, []).append(tri)

    if not positions or not groups:
        raise ValueError("The ice-cream-truck OBJ contains no indexed mesh")
    min_x, max_x = min(v[0] for v in positions), max(v[0] for v in positions)
    min_y = min(v[1] for v in positions)
    min_z, max_z = min(v[2] for v in positions), max(v[2] for v in positions)
    center_x, center_z = (min_x + max_x) / 2, (min_z + max_z) / 2

    names = {"Material.003":"blue_enamel", "Material.005":"headlamp_glass",
             "Material.006":"signal_red", "caisse":"cream_paint",
             "jante":"wheel_metal", "noir":"rubber_black"}
    patterns = {"Material.003":"metal", "Material.005":"glass", "Material.006":"solid",
                "caisse":"metal", "jante":"metal", "noir":"solid"}
    roughness = {"Material.003":.62, "Material.005":.38, "Material.006":.42,
                 "caisse":.72, "jante":.38, "noir":.92}
    metallic = {"Material.003":.18, "Material.005":.05, "Material.006":.08,
                "caisse":.08, "jante":.68, "noir":0.0}
    meshes, instances, materials, sets = [], [], [], []
    triangle_count = 0
    for source_name in ("caisse", "Material.003", "jante", "noir", "Material.005", "Material.006"):
        triangles = groups.get(source_name, [])
        if not triangles:
            continue
        short = names[source_name]
        material_id = "cse_icecream_" + short
        mesh_id = "geo_icecream_" + short
        indices, vertices, texcoords, faces = {}, [], [], []
        for tri in triangles:
            face = []
            for vi, ti in tri:
                key = (vi, ti)
                if key not in indices:
                    indices[key] = len(vertices)
                    p = positions[vi]
                    vertices.append([round(p[0]-center_x,6), round(p[1],6), round(p[2]-center_z,6)])
                    texcoords.append([round(uvs[ti][0],6), round(uvs[ti][1],6)] if ti is not None else [0.0,0.0])
                face.append(indices[key])
            faces.append(face)
        meshes.append({"id":mesh_id,"type":"triangle_mesh","vertices":vertices,"faces":faces,"uv":texcoords,
                       "source":"assets/camion_icecream.obj; source material "+source_name})
        triangle_count += len(faces)
        texture_id = "tex_" + material_id
        materials.append({"id":material_id,"baseColor":source_mtl[source_name].get("Kd",[.7,.7,.7]),
                          "roughness":roughness[source_name],"metallic":metallic[source_name],
                          "transmission":0.0,"ior":1.5,"textureSet":texture_id,
                          "origin":"User-supplied camion_icecream.mtl; diffuse color preserved; no source image textures"})
        sets.append({"id":texture_id,"material":material_id,"pattern":patterns[source_name],"resolution":128,
                     "channels":["albedo","normal","roughness"],
                     "status":"V17.624 procedural PBR fallback; MTL supplies flat Kd color only"})
        instances.append({"id":"v624_icecream_"+short,
                          "parent":"Place/Service et restauration rapide/Stand mobile de glaces",
                          "geometry":mesh_id,"material":material_id,
                          "position":[43.8,0.129549,98.55],"size":[1.0,1.0,1.0],"rotationY":90.0})

    geometry_path = "benchmark-civic/geometry/camion-icecream-v17-624.json"
    instance_path = "benchmark-civic/instances/camion-icecream-v17-624.json"
    material_path = "benchmark-civic/materials/camion-icecream-v17-624.json"
    pbr_path = "benchmark-civic/pbr/camion-icecream-v17-624.json"
    files[geometry_path] = _dump({"format":"m3d-geometry-v1","units":"m","meshes":meshes})
    files[instance_path] = _dump({"format":"m3d-instances-v1","instances":instances})
    files[material_path] = _dump({"format":"m3d-materials-v1","materials":materials})
    files[pbr_path] = _dump({"format":"m3d-pbr-v1","library":"CSE WARP V17 procedural materials",
                            "textureResolutionTarget":128,"channels":["albedo","normal","roughness"],"sets":sets})
    scene = json.loads(files[scene_path])
    sector = scene["sectors"][0]
    for kind, rel in (("geometry",geometry_path),("instances",instance_path),
                      ("materials",material_path),("pbr",pbr_path)):
        short_path = rel.split("benchmark-civic/",1)[1]
        if short_path not in sector[kind]:
            sector[kind].append(short_path)
    scene["name"] = "CSE WARP V17.624 — Complexe aquatique et place avec camion de glaces"
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
    files["benchmark-civic/source-assets/camion_icecream.obj"] = OBJ_PATH.read_bytes()
    files["benchmark-civic/source-assets/camion_icecream.mtl"] = MTL_PATH.read_bytes()
    floor_top = .118 + .075 / 2
    wheel_world_y = .129549 + min_y
    report = {"sceneRevision":revision,"baseSceneRevision":"V17.623",
              "asset":"camion_icecream.obj + camion_icecream.mtl","assetMaterials":list(groups),
              "nativeMeshCount":len(meshes),"nativeTriangleCount":triangle_count,
              "sourceBoundsMeters":{"min":[min_x,min_y,min_z],"max":[max_x,max(v[1] for v in positions),max_z]},
              "placement":{"position":[43.8,.129549,98.55],"rotationYDegrees":90,
                          "frontDirection":"toward plaza / negative Z","pavingTileCenter":[43.8,.118,98.55],
                          "pavingTileSize":[3.65,.075,3.65],"pavingTopY":floor_top,
                          "lowestWheelVertexSourceY":min_y,"lowestWheelWorldY":wheel_world_y,
                          "wheelGroundClearanceMeters":round(wheel_world_y-floor_top,9),
                          "wheelContactVerified":abs(wheel_world_y-floor_top)<1e-5},
              "notes":["Truck footprint fits within the existing 3.65 m paving tile.",
                       "The front faces the central plaza and the hill.",
                       "The supplied MTL has flat diffuse colors and no image maps; the scene uses procedural PBR fallback.",
                       "Original OBJ/MTL files are included under source-assets/."]}
    files["benchmark-civic/reports/camion-icecream-v624.json"] = _dump(report)
    files["benchmark-civic/README-CAMION-GLACES-V17.624.txt"] = (
        "CAMION DE GLACES — SCÈNE V17.624\n\n"
        "Le modèle est intégré sur le dallage existant près du massif et des arbres.\n"
        "Son avant regarde vers la place. Le point le plus bas des roues touche exactement\n"
        "la dalle. Les sources OBJ et MTL d’origine sont conservées dans source-assets/.\n"
        "Le MTL ne contient pas de texture image ; ses couleurs sont reprises par des\n"
        "matériaux PBR procéduraux.\n"
        f"Triangles importés : {triangle_count}. Révision de base : V17.623.\n"
    ).encode("utf-8")
    if abs(wheel_world_y - floor_top) >= 1e-5:
        raise ValueError("Truck wheels do not touch the paving surface")
