#!/usr/bin/env python3
"""Scale, repaint and repair the supplied ice-cream truck in V17.625."""
from __future__ import annotations
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBJ_PATH = ROOT / "assets" / "camion_icecream.obj"
MTL_PATH = ROOT / "assets" / "camion_icecream.mtl"
DECAL_PATH = ROOT / "assets" / "camion-glaces-side-v625.jpg"


def _dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _mtl():
    out, current = {}, None
    for line in MTL_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        part = line.strip().split()
        if not part or part[0].startswith("#"):
            continue
        if part[0] == "newmtl":
            current = part[1]; out[current] = {}
        elif current and part[0] in ("Kd", "Ks", "Ke") and len(part) >= 4:
            out[current][part[0]] = [float(x) for x in part[1:4]]
        elif current and part[0] == "Ns" and len(part) >= 2:
            out[current][part[0]] = float(part[1])
    return out


def _cross(a, b, c):
    ab = [b[i] - a[i] for i in range(3)]
    ac = [c[i] - a[i] for i in range(3)]
    return (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    source_mtl = _mtl()
    vertices, uvs, normals = [], [], []
    groups: dict[str, list] = {}
    material = None
    flipped = 0

    def idx(token, count):
        n = int(token)
        return n - 1 if n > 0 else count + n

    for line in OBJ_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        part = line.strip().split()
        if not part or part[0].startswith("#"):
            continue
        if part[0] == "v" and len(part) >= 4:
            vertices.append(tuple(float(x) for x in part[1:4]))
        elif part[0] == "vt" and len(part) >= 3:
            uvs.append(tuple(float(x) for x in part[1:3]))
        elif part[0] == "vn" and len(part) >= 4:
            normals.append(tuple(float(x) for x in part[1:4]))
        elif part[0] == "usemtl" and len(part) >= 2:
            material = part[1]
        elif part[0] == "f" and len(part) >= 4:
            if material not in source_mtl:
                raise ValueError(f"OBJ references missing MTL material: {material}")
            refs = []
            for token in part[1:]:
                fields = token.split("/")
                vi = idx(fields[0], len(vertices))
                ti = idx(fields[1], len(uvs)) if len(fields) > 1 and fields[1] else None
                ni = idx(fields[2], len(normals)) if len(fields) > 2 and fields[2] else None
                if vi < 0 or vi >= len(vertices) or (ti is not None and not 0 <= ti < len(uvs)) or (ni is not None and not 0 <= ni < len(normals)):
                    raise ValueError(f"Bad OBJ index: {token}")
                refs.append((vi, ti, ni))
            for corner in range(1, len(refs) - 1):
                tri = [refs[0], refs[corner], refs[corner + 1]]
                a, b, c = (vertices[item[0]] for item in tri)
                geometric = _cross(a, b, c)
                if sum(x*x for x in geometric) < 1e-18:
                    continue
                ns = [normals[item[2]] for item in tri if item[2] is not None]
                if ns and sum(geometric[i] * sum(n[i] for n in ns) for i in range(3)) < 0:
                    tri[1], tri[2] = tri[2], tri[1]
                    flipped += 1
                if material == "caisse":
                    center_y = sum(vertices[item[0]][1] for item in tri) / 3
                    bucket = "cream_paint" if center_y >= 0.72 else "turquoise_enamel"
                else:
                    bucket = {"Material.003":"trim_metal", "Material.005":"headlamp_glass",
                              "Material.006":"signal_red", "jante":"wheel_metal", "noir":"rubber_black"}.get(material, material)
                groups.setdefault(bucket, []).append(tri)

    if not vertices or not groups:
        raise ValueError("The supplied OBJ has no indexed faces")
    min_x, max_x = min(v[0] for v in vertices), max(v[0] for v in vertices)
    min_y, max_y = min(v[1] for v in vertices), max(v[1] for v in vertices)
    min_z, max_z = min(v[2] for v in vertices), max(v[2] for v in vertices)
    cx, cz = (min_x + max_x) / 2, (min_z + max_z) / 2
    target = (4.30, 2.20, 2.05)  # length, height, width, in metres
    scale = (target[0] / (max_x-min_x), target[1] / (max_y-min_y), target[2] / (max_z-min_z))
    tile_top = 0.118 + 0.075 / 2
    origin_y = tile_top - min_y * scale[1]
    position = [43.8, round(origin_y, 9), 98.55]

    short_names = ["cream_paint", "turquoise_enamel", "trim_metal", "wheel_metal", "rubber_black", "headlamp_glass", "signal_red"]
    palette = {
        "cream_paint": ([0.88, 0.82, 0.66], .48, .02, "metal"),
        "turquoise_enamel": ([0.055, 0.31, 0.34], .31, .16, "metal"),
        "trim_metal": ([0.26, 0.31, 0.29], .38, .48, "metal"),
        "wheel_metal": ([0.33, 0.34, 0.31], .42, .58, "metal"),
        "rubber_black": ([0.035, 0.039, 0.038], .88, 0.0, "solid"),
        "headlamp_glass": ([0.78, 0.77, 0.62], .21, .04, "glass"),
        "signal_red": ([0.62, 0.105, 0.065], .32, .04, "solid"),
        "side_sign": ([1.0, 1.0, 1.0], .55, 0.0, "image"),
        "accent_stripe": ([0.67, 0.11, 0.06], .32, .02, "solid"),
    }
    meshes, instances, materials, sets = [], [], [], []

    def add_mesh(mesh_id, source_tris):
        indices, outv, outuv, faces = {}, [], [], []
        for tri in source_tris:
            face = []
            for vi, ti, _ni in tri:
                key = (vi, ti)
                if key not in indices:
                    indices[key] = len(outv)
                    p = vertices[vi]
                    outv.append([round(p[0]-cx, 6), round(p[1], 6), round(p[2]-cz, 6)])
                    outuv.append([round(uvs[ti][0], 6), round(uvs[ti][1], 6)] if ti is not None else [0.0, 0.0])
                face.append(indices[key])
            faces.append(face)
        meshes.append({"id":mesh_id,"type":"triangle_mesh","vertices":outv,"faces":faces,"uv":outuv,
                       "source":"User supplied camion_icecream.obj; winding checked against OBJ vertex normals"})
        return len(faces)

    total_triangles = 0
    for short in short_names:
        tris = groups.get(short, [])
        if not tris:
            continue
        geo = "geo_icecream_" + short
        total_triangles += add_mesh(geo, tris)
        mat = "cse_icecream_" + short
        color, roughness, metallic, pattern = palette[short]
        materials.append({"id":mat,"baseColor":color,"roughness":roughness,"metallic":metallic,
                          "transmission":0.0,"ior":1.5,"textureSet":"tex_"+mat,
                          "origin":"V17.625 restrained vintage ice-cream truck paint palette"})
        sets.append({"id":"tex_"+mat,"material":mat,"pattern":pattern,"resolution":128,
                     "channels":["albedo"],"baseColor":color,"roughness":roughness,
                     "status":"V17.625 scene material; source diffuse colors intentionally replaced by coordinated livery"})
        instances.append({"id":"v625_icecream_"+short,"parent":"Place/Service et restauration rapide/Stand mobile de glaces",
                          "geometry":geo,"material":mat,"position":position,"size":list(scale),"rotationY":90.0})

    # Printed enamel side plaques sit on the original body panels. The real OBJ silhouette is untouched.
    x0, x1 = min_x + 0.28 - cx, max_x - 1.08 - cx
    y0, y1 = 0.78, 1.12
    for side, z, flip in (("near", max_z-cz+0.002, False), ("far", min_z-cz-0.002, True)):
        geo = "geo_icecream_sign_" + side
        verts = [[x0,y0,z],[x1,y0,z],[x1,y1,z],[x0,y1,z]]
        faces = [[0,2,1],[0,3,2]] if flip else [[0,1,2],[0,2,3]]
        meshes.append({"id":geo,"type":"triangle_mesh","vertices":verts,"faces":faces,
                       "uv":[[0,1],[1,1],[1,0],[0,0]],"source":"V17.625 enamel sign texture on original truck side"})
        ident = "v625_icecream_sign_" + side
        instances.append({"id":ident,"parent":"Place/Service et restauration rapide/Stand mobile de glaces",
                          "geometry":geo,"material":"cse_icecream_side_sign","position":position,
                          "size":list(scale),"rotationY":90.0})
    # A thin red pinstripe runs along both original side panels; it is a decal plane, not a new body part.
    sx0, sx1, sy0, sy1 = min_x+.20-cx, max_x-.12-cx, .61, .635
    for side,z,flip in (("near",max_z-cz+.003,False),("far",min_z-cz-.003,True)):
        geo="geo_icecream_stripe_"+side
        verts=[[sx0,sy0,z],[sx1,sy0,z],[sx1,sy1,z],[sx0,sy1,z]]
        faces=[[0,2,1],[0,3,2]] if flip else [[0,1,2],[0,2,3]]
        meshes.append({"id":geo,"type":"triangle_mesh","vertices":verts,"faces":faces,"uv":[[0,1],[1,1],[1,0],[0,0]]})
        instances.append({"id":"v625_icecream_stripe_"+side,"parent":"Place/Service et restauration rapide/Stand mobile de glaces",
                          "geometry":geo,"material":"cse_icecream_accent_stripe","position":position,"size":list(scale),"rotationY":90.0})

    for short in ("side_sign", "accent_stripe"):
        color, roughness, metallic, pattern = palette[short]
        mat="cse_icecream_"+short
        materials.append({"id":mat,"baseColor":color,"roughness":roughness,"metallic":metallic,
                          "transmission":0.0,"ior":1.5,"textureSet":"tex_"+mat,
                          "origin":"V17.625 printed enamel livery and accent stripe"})
        entry={"id":"tex_"+mat,"material":mat,"pattern":pattern,"resolution":1200 if short=="side_sign" else 64,
               "channels":["albedo"],"status":"V17.625 custom retro Soviet-style ice-cream livery"}
        if short=="side_sign": entry["imageFile"]="textures/camion-glaces-side-v625.jpg"
        else: entry.update({"baseColor":color,"roughness":roughness})
        sets.append(entry)

    prefix="benchmark-civic/"
    geometry_path=prefix+"geometry/camion-icecream-v17-625.json"
    instance_path=prefix+"instances/camion-icecream-v17-625.json"
    material_path=prefix+"materials/camion-icecream-v17-625.json"
    pbr_path=prefix+"pbr/camion-icecream-v17-625.json"
    files[geometry_path]=_dump({"format":"m3d-geometry-v1","units":"m","meshes":meshes})
    files[instance_path]=_dump({"format":"m3d-instances-v1","instances":instances})
    files[material_path]=_dump({"format":"m3d-materials-v1","materials":materials})
    files[pbr_path]=_dump({"format":"m3d-pbr-v1","library":"CSE WARP V17 procedural materials",
                           "textureResolutionTarget":1200,"channels":["albedo"],"sets":sets})
    files[prefix+"textures/camion-glaces-side-v625.jpg"]=DECAL_PATH.read_bytes()

    scene=json.loads(files[scene_path]); sector=scene["sectors"][0]
    for kind, rel in (("geometry",geometry_path),("instances",instance_path),("materials",material_path),("pbr",pbr_path)):
        short=rel.split("benchmark-civic/",1)[1]
        # Supersede V17.624 truck data in each package list.
        sector[kind]=[p for p in sector.get(kind,[]) if "camion-icecream-v17-624.json" not in p]
        if short not in sector[kind]: sector[kind].append(short)
    # Enlarge the paving tile just enough to contain the 4.3 m vehicle footprint.
    tile_found=False
    for rel in sector.get("instances",[]):
        path=prefix+rel
        if path not in files: continue
        data=json.loads(files[path]); changed=False
        for inst in data.get("instances",[]):
            if inst.get("id")=="v4_006247":
                inst["size"]=[4.55,.075,4.55]; tile_found=True; changed=True
        if changed: files[path]=_dump(data)
    if not tile_found:
        raise ValueError("Could not find the paving tile under the truck")
    scene["name"]="CSE WARP V17.625 — Complexe aquatique et place avec camion de glaces"
    scene["revision"]=revision; scene["sceneVersion"]=revision
    files[scene_path]=_dump(scene)
    files[prefix+"source-assets/camion_icecream.obj"]=OBJ_PATH.read_bytes()
    files[prefix+"source-assets/camion_icecream.mtl"]=MTL_PATH.read_bytes()
    wheel_y=position[1]+min_y*scale[1]
    report={"sceneRevision":revision,"baseSceneRevision":"V17.624","asset":"camion_icecream.obj + camion_icecream.mtl",
            "sourceBoundsMeters":{"min":[min_x,min_y,min_z],"max":[max_x,max_y,max_z]},
            "vehicleDimensionsMeters":{"length":round((max_x-min_x)*scale[0],3),"height":round((max_y-min_y)*scale[1],3),"width":round((max_z-min_z)*scale[2],3)},
            "placement":{"position":position,"rotationYDegrees":90,"frontDirection":"toward plaza / negative Z",
                         "pavingTileCenter":[43.8,.118,98.55],"pavingTileSizeMeters":[4.55,.075,4.55],"pavingTopY":tile_top,
                         "lowestWheelWorldY":round(wheel_y,9),"wheelGroundClearanceMeters":round(wheel_y-tile_top,9),
                         "wheelContactVerified":abs(wheel_y-tile_top)<1e-5},
            "mesh":{"triangleCount":total_triangles,"sourceWindingCorrections":flipped,"sourceNormalComparison":"OBJ vertex normals"},
            "livery":"ivory upper body, dark turquoise lower enamel, thin red side pinstripe, printed Cyrillic МОРОЖЕНОЕ plaques on both sides",
            "notes":["Original truck silhouette and wheels retained; no serving hatch or fabricated body parts added.",
                     "Vehicle scaled to 4.30 m long × 2.20 m high × 2.05 m wide.",
                     "Paving tile widened to keep the larger truck fully supported.",
                     "Source OBJ and MTL retained in source-assets; custom sign texture is under textures/."]}
    files[prefix+"reports/camion-icecream-v625.json"]=_dump(report)
    files[prefix+"README-CAMION-GLACES-V17.625.txt"]=(
        "CAMION DE GLACES — SCÈNE V17.625\n\n"
        "Le camion reprend la géométrie OBJ fournie, sans ajout de vitrine ou de pièces de carrosserie inventées.\n"
        "Dimensions visées : 4,30 m de long, 2,20 m de haut et 2,05 m de large.\n"
        "Les roues touchent le dallage ; celui-ci est élargi pour porter entièrement le véhicule.\n"
        "La livrée associe ivoire, émail turquoise, un filet rouge et un panneau latéral imprimé en cyrillique.\n"
        f"Triangles importés : {total_triangles} ; faces remises dans le bon sens : {flipped}.\n"
    ).encode("utf-8")
    if abs(wheel_y-tile_top)>=1e-5:
        raise ValueError("Scaled truck wheels do not touch the paving surface")
    if flipped != 8:
        raise ValueError(f"Expected 8 reversed source faces to be corrected, got {flipped}")
