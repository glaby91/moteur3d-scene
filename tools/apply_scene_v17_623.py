"""Replace the west locker-room L partition with translucent glass mosaic."""
from __future__ import annotations

import json
import math


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _box(vertices: list, faces: list, uv: list, center: tuple[float, float, float],
         size: tuple[float, float, float]) -> None:
    x, y, z = center
    sx, sy, sz = (v * 0.5 for v in size)
    base = len(vertices)
    vertices.extend([
        [x - sx, y - sy, z - sz], [x + sx, y - sy, z - sz],
        [x + sx, y + sy, z - sz], [x - sx, y + sy, z - sz],
        [x - sx, y - sy, z + sz], [x + sx, y - sy, z + sz],
        [x + sx, y + sy, z + sz], [x - sx, y + sy, z + sz],
    ])
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for a, b, c, d in quads:
        faces.extend([[base + a, base + b, base + c],
                      [base + a, base + c, base + d]])
    uv.extend([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
               [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])


def _palette(y: float, u: float) -> str:
    wave = 2.15 + 0.57 * math.sin(math.tau * u / 15.0)
    if abs(y - (wave + 0.34)) < 0.14:
        return "v623_mosaic_gold"
    if abs(y - wave) < 0.29:
        return "v623_mosaic_deep_teal"
    if abs(y - (wave - 0.40)) < 0.16:
        return "v623_mosaic_turquoise"
    return "v623_mosaic_aqua"


def _add_panel_tiles(groups: dict[str, tuple[list, list, list]],
                     center: tuple[float, float, float], size: tuple[float, float, float],
                     along_x: bool, u_origin: float) -> int:
    pitch_u, pitch_y = 0.36, 0.29
    tile_u, tile_y, tile_depth = 0.337, 0.267, 0.012
    span_u = size[0] if along_x else size[2]
    cols = int(span_u / pitch_u)
    rows = int(size[1] / pitch_y)
    x0, y0, z0 = center
    x_start = x0 - span_u * 0.5 + (span_u - cols * pitch_u) * 0.5 + pitch_u * 0.5
    y_start = y0 - size[1] * 0.5 + (size[1] - rows * pitch_y) * 0.5 + pitch_y * 0.5
    faces_z = (z0 - size[2] * 0.5 - tile_depth * 0.55,
               z0 + size[2] * 0.5 + tile_depth * 0.55)
    faces_x = (x0 - size[0] * 0.5 - tile_depth * 0.55,
               x0 + size[0] * 0.5 + tile_depth * 0.55)
    count = 0
    for col in range(cols):
        u = u_origin + col * pitch_u + pitch_u * 0.5
        for row in range(rows):
            y = y_start + row * pitch_y
            material = _palette(y, u)
            for face in (0, 1):
                if along_x:
                    pos = (x_start + col * pitch_u, y, faces_z[face])
                    extent = (tile_u, tile_y, tile_depth)
                else:
                    pos = (faces_x[face], y, z0 - size[2] * 0.5 +
                           (span_u - cols * pitch_u) * 0.5 + pitch_u * 0.5 + col * pitch_u)
                    extent = (tile_depth, tile_y, tile_u)
                _box(*groups[material], pos, extent)
                count += 1
    return count


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    materials_path = prefix + "materials/v442-corrections.json"
    pbr_path = prefix + "pbr/v440-audit.json"
    scene = json.loads(files[scene_path])
    instances_data = json.loads(files[instances_path])
    instances = instances_data.get("instances", [])
    by_id = {item.get("id"): item for item in instances}
    wall_ids = ("v17_001771", "v17_001773")
    if any(ident not in by_id for ident in wall_ids):
        raise ValueError("Expected the two approved vestiaire L-partition walls")
    for ident in wall_ids:
        by_id[ident]["material"] = "v614_lift_blue_glass"

    palette = {
        "v623_mosaic_aqua": ([0.43, 0.79, 0.81], 0.23, 0.28),
        "v623_mosaic_turquoise": ([0.14, 0.60, 0.65], 0.19, 0.24),
        "v623_mosaic_deep_teal": ([0.045, 0.30, 0.40], 0.18, 0.22),
        "v623_mosaic_gold": ([0.77, 0.58, 0.32], 0.24, 0.08),
    }
    materials = json.loads(files[materials_path])
    known_materials = {entry.get("id") for entry in materials.get("materials", [])}
    for ident, (color, roughness, transmission) in palette.items():
        if ident not in known_materials:
            materials["materials"].append({
                "id": ident, "baseColor": color, "roughness": roughness,
                "metallic": 0.0, "transmission": transmission, "ior": 1.5,
                "textureSet": "tex_" + ident,
                "origin": "V17.623 translucent aquatic glass mosaic tesserae",
            })
    files[materials_path] = _dump(materials)

    pbr = json.loads(files[pbr_path])
    sets = pbr.setdefault("sets", [])
    known_sets = {entry.get("id") for entry in sets}
    for ident, (color, roughness, _) in palette.items():
        texture_id = "tex_" + ident
        if texture_id not in known_sets:
            sets.append({"id": texture_id, "material": ident, "pattern": "solid",
                         "resolution": 64, "channels": ["albedo"], "baseColor": color,
                         "roughness": roughness,
                         "status": "V17.623 glass mosaic tile palette"})
    files[pbr_path] = _dump(pbr)

    groups = {ident: ([], [], []) for ident in palette}
    tile_count = 0
    x_wall, z_wall = by_id[wall_ids[0]], by_id[wall_ids[1]]
    tile_count += _add_panel_tiles(groups, tuple(x_wall["position"]), tuple(x_wall["size"]), True, 0.0)
    tile_count += _add_panel_tiles(groups, tuple(z_wall["position"]), tuple(z_wall["size"]), False, 17.0)
    geometry = {"format": "m3d-geometry-v1", "units": "m", "meshes": []}
    for ident, (vertices, faces, uv) in groups.items():
        if not faces:
            continue
        geometry["meshes"].append({"id": "geo_" + ident, "type": "triangle_mesh",
                                   "vertices": vertices, "faces": faces, "uv": uv})
        by_id[ident] = {"id": ident, "parent": "Interieur/Vestiaires et douches ouest/Mosaique de verre",
                        "geometry": "geo_" + ident, "material": ident,
                        "position": [0.0, 0.0, 0.0], "size": [1.0, 1.0, 1.0], "rotationY": 0}
    files[prefix + "geometry/v623-glass-mosaic.json"] = _dump(geometry)

    # The two former lift-side ceiling bars become three restrained wall-wash
    # fittings on the left structural pilasters, following the L at right angle.
    old_light_a, old_light_b = "v17_001815", "v17_001816"
    if old_light_a not in by_id or old_light_b not in by_id:
        raise ValueError("Expected the two lift-side ceiling light bars")
    del by_id[old_light_a]
    del by_id[old_light_b]
    lights = [
        ("v623_l_wallwash_01", [-48.87, 3.62, -48.0], [0.10, 0.09, 1.35], 0),
        ("v623_l_wallwash_02", [-48.87, 3.62, -30.0], [0.10, 0.09, 1.35], 0),
        ("v623_l_wallwash_03", [-47.58, 3.62, -36.0], [1.35, 0.09, 0.10], 0),
    ]
    for ident, position, size, rotation in lights:
        by_id[ident] = {"id": ident, "parent": "Interieur/Vestiaires et douches ouest/Luminaires sur poutres",
                        "geometry": "unit_box", "material": "cse_pool_strip",
                        "position": position, "size": size, "rotationY": rotation}
    instances_data["instances"] = list(by_id.values())
    files[instances_path] = _dump(instances_data)

    scene["revision"] = revision
    scene["sceneVersion"] = revision
    for sector in scene.get("sectors", []):
        geometry_files = sector.setdefault("geometry", [])
        path = "geometry/v623-glass-mosaic.json"
        if path not in geometry_files:
            geometry_files.append(path)
    files[scene_path] = _dump(scene)

    files[prefix + "reports/glass-mosaic-v623.json"] = _dump({
        "revision": revision,
        "wallsReplaced": list(wall_ids),
        "wallBoundsPreserved": True,
        "mosaic": "translucent aqua, turquoise and deep-teal tesserae with restrained champagne-gold wave accents",
        "tileCount": tile_count,
        "glassBackingMaterial": "v614_lift_blue_glass",
        "formerLiftLightsRemoved": [old_light_a, old_light_b],
        "newWallWashLights": [entry[0] for entry in lights],
        "notes": [
            "The two vestiaire partition legs remain at their original ground datum and dimensions.",
            "The wave motif continues around the L corner; each tile band is grouped into four meshes to limit draw calls.",
            "Three compact wall-wash bars replace the two strips around the lift, spaced along the left-side L beams.",
        ],
    })
