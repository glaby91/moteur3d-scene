#!/usr/bin/env python3
"""Repair the ice-cream truck livery, glazing and body normals for V17.627."""
from __future__ import annotations

import json
import math


def _dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _cross(a, b, c):
    ab = [b[i] - a[i] for i in range(3)]
    ac = [c[i] - a[i] for i in range(3)]
    return [
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    ]


def _unit(value):
    length = math.sqrt(sum(component * component for component in value))
    return [component / length for component in value] if length > 1e-12 else [0.0, 0.0, 1.0]


def _clip(poly, axis, bound, keep_greater):
    if not poly:
        return []
    out = []
    for index, a in enumerate(poly):
        b = poly[(index + 1) % len(poly)]
        da, db = a[axis] - bound, b[axis] - bound
        inside_a = da >= -1e-10 if keep_greater else da <= 1e-10
        inside_b = db >= -1e-10 if keep_greater else db <= 1e-10
        if inside_a:
            out.append(a)
        if inside_a != inside_b:
            t = da / (da - db)
            out.append([a[i] + (b[i] - a[i]) * t for i in range(3)])
    return out


def _clip_rect(points, rect):
    x0, x1, y0, y1 = rect
    for axis, bound, greater in (
        (0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)
    ):
        points = _clip(points, axis, bound, greater)
    return points


def _mesh_faces(mesh):
    vertices = mesh.get("vertices", [])
    for face in mesh.get("faces", []):
        if len(face) != 3:
            continue
        yield [vertices[index] for index in face]


def _side_records(mesh, side, rect):
    x0, x1, y0, y1 = rect
    records = []
    for points in _mesh_faces(mesh):
        normal_raw = _cross(*points)
        normal = _unit(normal_raw)
        center = [sum(point[i] for point in points) / 3.0 for i in range(3)]
        if side * normal[2] < 0.50 or side * center[2] < 0.20:
            continue
        if center[0] < x0 - 0.15 or center[0] > x1 + 0.15:
            continue
        if center[1] < y0 - 0.15 or center[1] > y1 + 0.15:
            continue
        records.append((points, normal, center))
    return records


def _exterior_surface(records, record, side):
    center = record[2]
    nearby = [
        other[2][2] * side
        for other in records
        if abs(other[2][0] - center[0]) <= 0.14
        and abs(other[2][1] - center[1]) <= 0.10
    ]
    return not nearby or max(nearby) - center[2] * side <= 0.055


def _make_patch(mesh_id, source_mesh, rect, side, rotate_texture=False):
    outv, outuv, outnormals, faces = [], [], [], []
    records = _side_records(source_mesh, side, rect)
    for record in records:
        points, normal, _center = record
        if not _exterior_surface(records, record, side):
            continue
        clipped = _clip_rect([point[:] for point in points], rect)
        if len(clipped) < 3:
            continue
        for corner in range(1, len(clipped) - 1):
            triangle = [clipped[0], clipped[corner], clipped[corner + 1]]
            face = []
            for point in triangle:
                # Offset by less than 1 mm after scene scaling to prevent z-fighting.
                point = [point[0] + normal[0] * 0.00035,
                         point[1] + normal[1] * 0.00035,
                         point[2] + normal[2] * 0.00035]
                u = (point[0] - rect[0]) / (rect[1] - rect[0])
                v = 1.0 - (point[1] - rect[2]) / (rect[3] - rect[2])
                if rotate_texture:
                    u, v = 1.0 - u, 1.0 - v
                face.append(len(outv))
                outv.append([round(component, 7) for component in point])
                outuv.append([round(u, 7), round(v, 7)])
                outnormals.append([round(component, 7) for component in normal])
            faces.append(face)
    if not faces:
        raise ValueError(f"No exterior truck surface found for {mesh_id}")
    return {
        "id": mesh_id,
        "type": "triangle_mesh",
        "vertices": outv,
        "faces": faces,
        "uv": outuv,
        "normals": outnormals,
        "source": "V17.627 decal clipped to and offset from the original exterior body triangles",
    }


def _smooth_body_normals(meshes):
    # Rebuild these triangles with per-corner normals. Adjacent faces are averaged
    # only within a 50-degree crease, so rounded panels smooth while sharp edges remain.
    faces_by_mesh = []
    adjacency = {}
    for mesh in meshes:
        triangles = []
        for points in _mesh_faces(mesh):
            raw = _cross(*points)
            area2 = math.sqrt(sum(value * value for value in raw))
            if area2 < 1e-12:
                continue
            normal = [value / area2 for value in raw]
            triangles.append((points, normal, area2 * 0.5))
            for point in points:
                key = tuple(round(value, 5) for value in point)
                adjacency.setdefault(key, []).append((normal, area2 * 0.5))
        faces_by_mesh.append((mesh, triangles))

    for mesh, triangles in faces_by_mesh:
        vertices, uvs, normals, faces = [], [], [], []
        old_uv = mesh.get("uv", [])
        old_faces = mesh.get("faces", [])
        old_vertices = mesh.get("vertices", [])
        for old_face, (points, face_normal, _area) in zip(old_faces, triangles):
            new_face = []
            for corner, point in enumerate(points):
                key = tuple(round(value, 5) for value in point)
                weighted = [0.0, 0.0, 0.0]
                total = 0.0
                for neighbor, area in adjacency.get(key, []):
                    if sum(face_normal[i] * neighbor[i] for i in range(3)) < 0.643:
                        continue
                    for axis in range(3):
                        weighted[axis] += neighbor[axis] * area
                    total += area
                smooth = _unit(weighted) if total else face_normal
                old_index = old_face[corner]
                new_face.append(len(vertices))
                vertices.append(old_vertices[old_index])
                uvs.append(old_uv[old_index] if old_index < len(old_uv) else [0.0, 0.0])
                normals.append([round(value, 7) for value in smooth])
            faces.append(new_face)
        mesh["vertices"], mesh["faces"], mesh["uv"], mesh["normals"] = vertices, faces, uvs, normals
        mesh["source"] = "V17.627: body triangles retain corrected winding and use area-weighted corner normals"


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    old_stem = "camion-icecream-v17-625.json"
    new_stem = "camion-icecream-v17-627.json"
    paths = {
        "geometry": prefix + "geometry/" + old_stem,
        "instances": prefix + "instances/" + old_stem,
        "materials": prefix + "materials/" + old_stem,
        "pbr": prefix + "pbr/" + old_stem,
    }
    if any(path not in files for path in paths.values()):
        raise ValueError("V17.626 truck package is incomplete")

    data = {kind: json.loads(files[path]) for kind, path in paths.items()}
    geometry, instances = data["geometry"], data["instances"]
    materials, pbr = data["materials"], data["pbr"]

    # Material.003 is assigned to the windshield and cab glazing in the source OBJ.
    for mesh in geometry.get("meshes", []):
        if mesh.get("id") == "geo_icecream_trim_metal":
            mesh["id"] = "geo_icecream_window_glass"
    for instance in instances.get("instances", []):
        if instance.get("geometry") == "geo_icecream_trim_metal":
            instance["geometry"] = "geo_icecream_window_glass"
        if instance.get("material") == "cse_icecream_trim_metal":
            instance["material"] = "cse_icecream_window_glass"

    for material in materials.get("materials", []):
        if material.get("id") == "cse_icecream_trim_metal":
            material.update({
                "id": "cse_icecream_window_glass",
                "baseColor": [0.58, 0.76, 0.84],
                "roughness": 0.14,
                "metallic": 0.0,
                "transmission": 0.78,
                "ior": 1.45,
                "origin": "V17.627 glazing identified from Material.003 in the source OBJ",
            })
        elif material.get("id") == "cse_icecream_headlamp_glass":
            material.update({"transmission": 0.32, "roughness": 0.16, "ior": 1.45})
        elif material.get("id") == "cse_icecream_signal_red":
            material.update({"transmission": 0.24, "roughness": 0.20, "ior": 1.45})

    for texture in pbr.get("sets", []):
        if texture.get("id") == "tex_cse_icecream_trim_metal":
            texture.update({
                "id": "tex_cse_icecream_window_glass",
                "material": "cse_icecream_window_glass",
                "pattern": "glass",
                "resolution": 128,
                "status": "V17.627: source Material.003 surfaces identified as truck glazing",
            })
        elif texture.get("id") == "tex_cse_icecream_headlamp_glass":
            texture.update({"pattern": "glass", "status": "V17.627: headlamp lens identified from phare_Plane.002"})
        elif texture.get("id") == "tex_cse_icecream_signal_red":
            texture.update({"pattern": "glass", "status": "V17.627: red lamp lenses use tinted glass"})
    pbr["textureResolutionTarget"] = 1024

    # Replace the free-standing flat decals with patches clipped to the actual side mesh.
    geometry["meshes"] = [
        mesh for mesh in geometry.get("meshes", [])
        if not mesh.get("id", "").startswith(("geo_icecream_sign_", "geo_icecream_stripe_"))
    ]
    instances["instances"] = [
        instance for instance in instances.get("instances", [])
        if not instance.get("id", "").startswith(("v625_icecream_sign_", "v625_icecream_stripe_"))
    ]

    report_path = prefix + "reports/camion-icecream-v625.json"
    report = json.loads(files[report_path])
    bounds = report["sourceBoundsMeters"]
    min_x, max_x = bounds["min"][0], bounds["max"][0]
    center_x = (min_x + max_x) * 0.5
    # Keep the plaque centered on the rear side panel, but reduce its footprint by 30%.
    old_x0, old_x1 = min_x + 0.28, max_x - 1.08
    old_width = old_x1 - old_x0
    sign_x0 = (old_x0 + old_x1) * 0.5 - old_width * 0.35 - center_x
    sign_x1 = (old_x0 + old_x1) * 0.5 + old_width * 0.35 - center_x
    sign_y0, sign_y1 = 0.8225, 1.0775
    stripe_x0, stripe_x1 = min_x + 0.20 - center_x, max_x - 0.12 - center_x
    sign_counts, stripe_counts = {}, {}
    body_meshes = [
        mesh for mesh in geometry.get("meshes", [])
        if mesh.get("id") in ("geo_icecream_cream_paint", "geo_icecream_turquoise_enamel")
    ]
    if len(body_meshes) != 2:
        raise ValueError("Could not identify both original painted body meshes")

    for side, label in ((1, "near"), (-1, "far")):
        sign_mesh = _make_patch(
            "geo_icecream_sign_" + label,
            next(mesh for mesh in body_meshes if mesh["id"] == "geo_icecream_cream_paint"),
            [sign_x0, sign_x1, sign_y0, sign_y1],
            side,
            rotate_texture=(side < 0),
        )
        stripe_mesh = _make_patch(
            "geo_icecream_stripe_" + label,
            next(mesh for mesh in body_meshes if mesh["id"] == "geo_icecream_turquoise_enamel"),
            [stripe_x0, stripe_x1, 0.61, 0.635],
            side,
        )
        geometry["meshes"].extend((sign_mesh, stripe_mesh))
        sign_counts[label] = len(sign_mesh["faces"])
        stripe_counts[label] = len(stripe_mesh["faces"])
        base_instance = next(
            item for item in instances["instances"]
            if item.get("id") == "v625_icecream_cream_paint"
        )
        for mesh_id, mat_id, ident in (
            (sign_mesh["id"], "cse_icecream_side_sign", "v627_icecream_sign_" + label),
            (stripe_mesh["id"], "cse_icecream_accent_stripe", "v627_icecream_stripe_" + label),
        ):
            decal_instance = dict(base_instance)
            decal_instance.update({
                "id": ident,
                "geometry": mesh_id,
                "material": mat_id,
            })
            instances["instances"].append(decal_instance)

    _smooth_body_normals(body_meshes)

    for kind, document in data.items():
        new_path = prefix + kind + "/" + new_stem
        files[new_path] = _dump(document)
    scene = json.loads(files[scene_path])
    sector = scene["sectors"][0]
    for kind, old_path in paths.items():
        old_short = old_path.split("benchmark-civic/", 1)[1]
        new_short = old_short.replace(old_stem, new_stem)
        sector[kind] = [item for item in sector.get(kind, []) if item != old_short and old_stem not in item]
        sector[kind].append(new_short)

    scene["name"] = "CSE WARP V17.627 — Camion corrigé, vitrages et livrée plaquée"
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)

    report["sceneRevision"] = revision
    report["livery"] = {
        "sideSignWidthScale": 0.70,
        "signPatchesFollowBodyTriangles": True,
        "stripePatchesFollowBodyTriangles": True,
        "stripeSkipsMissingOrRecessedSideSurface": True,
        "signTriangleCountBySide": sign_counts,
        "stripeTriangleCountBySide": stripe_counts,
        "farSideArtworkRotationDegrees": 180,
    }
    report["glassMaterialIdentification"] = {
        "Material.003": "windshield and cab glazing; mapped to transmissive window glass",
        "Material.005": "lens on source object phare_Plane.002; mapped to headlamp glass",
        "Material.006": "red lamp lenses on source phare objects; mapped to tinted transmissive glass",
    }
    report["mesh"]["bodyNormals"] = "area-weighted per-corner normals, smoothed across shared positions with a 50-degree crease"
    files[report_path] = _dump(report)

    files[prefix + "README-CAMION-GLACES-V17.627.txt"] = (
        "CAMION DE GLACES — SCÈNE V17.627\n\n"
        "L'enseigne est réduite de 30 %, orientée pour rester lisible sur chaque face et découpée "
        "sur les triangles réels de la carrosserie. Le filet rouge suit les triangles extérieurs "
        "du panneau turquoise ; il ne traverse ni ouverture ni retrait de porte.\n"
        "Les vitrages Material.003 sont identifiés séparément des lentilles de phares Material.005 "
        "et des lentilles rouges Material.006. Les matériaux portent une transmission optique.\n"
        "Les panneaux peints reçoivent des normales de coin pondérées par l'aire pour lisser les "
        "facettes tout en conservant les arêtes franches.\n"
    ).encode("utf-8")


__all__ = ["apply_patch"]
