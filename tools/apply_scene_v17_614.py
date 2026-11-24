"""Correct the west lift landing, glazing, floor medallion, and pool numbers."""
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _annulus_mesh(mesh_id: str, outer: float, inner: float, thickness: float,
                  segments: int = 48) -> dict:
    vertices: list[list[float]] = []
    uv: list[list[float]] = []
    for y in (0.0, thickness):
        for radius in (outer, inner):
            for i in range(segments):
                a = math.tau * i / segments
                x, z = radius * math.cos(a), radius * math.sin(a)
                vertices.append([x, y, z])
                uv.append([x / (outer * 2) + .5, z / (outer * 2) + .5])

    def idx(layer: int, ring: int, i: int) -> int:
        return layer * 2 * segments + ring * segments + (i % segments)

    faces: list[list[int]] = []
    for i in range(segments):
        j = (i + 1) % segments
        # Top and bottom annulus faces, with double-sided winding.
        top = [idx(1, 0, i), idx(1, 1, i), idx(1, 0, j), idx(1, 1, j)]
        bottom = [idx(0, 0, i), idx(0, 0, j), idx(0, 1, i), idx(0, 1, j)]
        for a, b, c in ((top[0], top[1], top[3]), (top[0], top[3], top[2]),
                        (bottom[0], bottom[2], bottom[3]), (bottom[0], bottom[3], bottom[1])):
            faces.extend(([a, b, c], [c, b, a]))
        # Outer and inner side walls.
        for a, b, c, d in (
            (idx(0, 0, i), idx(0, 0, j), idx(1, 0, j), idx(1, 0, i)),
            (idx(0, 1, j), idx(0, 1, i), idx(1, 1, i), idx(1, 1, j)),
        ):
            faces.extend(([a, b, c], [a, c, d], [c, b, a], [d, c, a]))
    return {"id": mesh_id, "type": "triangle_mesh", "vertices": vertices,
            "faces": faces, "uv": uv}


def _disc_mesh(mesh_id: str, radius: float, thickness: float, segments: int = 12) -> dict:
    vertices: list[list[float]] = [[0, 0, 0], [0, thickness, 0]]
    uv: list[list[float]] = [[.5, .5], [.5, .5]]
    for y in (0.0, thickness):
        for i in range(segments):
            a = math.tau * i / segments
            x, z = radius * math.cos(a), radius * math.sin(a)
            vertices.append([x, y, z])
            uv.append([x / (radius * 2) + .5, z / (radius * 2) + .5])
    faces: list[list[int]] = []
    for i in range(segments):
        j = (i + 1) % segments
        bi, bj, ti, tj = 2 + i, 2 + j, 2 + segments + i, 2 + segments + j
        faces.extend(([1, tj, ti], [1, ti, tj], [0, bi, bj], [0, bj, bi]))
        faces.extend(([bi, bj, tj], [bi, tj, ti], [tj, bj, bi], [ti, tj, bi]))
    return {"id": mesh_id, "type": "triangle_mesh", "vertices": vertices,
            "faces": faces, "uv": uv}


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # Remove the hanging closure panel above the lift and the three benches
    # that were placed directly across its approaches.
    removed_ids = {"v611_close_third_floor_stairwell", "v17_001802", "v17_001803", "v17_001804"}
    items = [item for item in items if item.get("id") not in removed_ids]

    # The ten lane labels are on the west-facing plane; flip U so they read
    # normally from the pool / spectator side.
    geometry_path = prefix + "geometry/v8-nine-anomalies.json"
    geometry = json.loads(files[geometry_path])
    flipped_numbers = 0
    for mesh in geometry.get("meshes", []):
        if mesh.get("id", "").startswith("v8_start_plot_number_"):
            uv = mesh.get("uv", [])
            if uv:
                mesh["uv"] = [[1.0 - float(pair[0]), float(pair[1])] for pair in uv]
                flipped_numbers += 1
    if flipped_numbers != 10:
        raise ValueError(f"V17.614 expected 10 start-plot number meshes, found {flipped_numbers}")
    files[geometry_path] = _dump(geometry)

    # Install a pale, gold-veined marble annulus and a slim champagne inlay.
    detail_path = prefix + "geometry/v614-lift-details.json"
    files[detail_path] = _dump({
        "format": "m3d-geometry-v1", "units": "meters",
        "meshes": [
            _annulus_mesh("geo_v614_lift_marble_annulus", 2.42, 1.39, .035),
            _annulus_mesh("geo_v614_lift_brass_inlay", 2.455, 2.425, .018),
            _disc_mesh("geo_v614_lift_car_floor", 1.00, .13),
        ],
    })
    items.extend([
        {"id": "v614_lift_marble_annulus", "parent": "Interieur/Galeries/Médaillon circulaire en marbre autour ascenseur",
         "geometry": "geo_v614_lift_marble_annulus", "material": "v614_lift_marble",
         "position": [-40.0, .015, -34.0], "size": [1.0, 1.0, 1.0], "rotationY": 0},
        {"id": "v614_lift_brass_inlay", "parent": "Interieur/Galeries/Médaillon circulaire en marbre autour ascenseur",
         "geometry": "geo_v614_lift_brass_inlay", "material": "v614_lift_brass",
         "position": [-40.0, .032, -34.0], "size": [1.0, 1.0, 1.0], "rotationY": 0},
        {"id": "v614_lift_car_floor", "parent": "Interieur/Galeries/Ascenseur capsule alu et verre dans trémie ouest/Cabine mobile",
         "geometry": "geo_v614_lift_car_floor", "material": "prp_terrazzo_floor",
         "position": [-40.0, -.08, -34.0], "size": [1.0, 1.0, 1.0], "rotationY": 0},
    ])

    # Replace the neutral shaft/cabin panes by a restrained blue-tinted glass.
    blue_ids = ("v613_shaft_glass_", "v613_car_glass_", "v613_landing_door_", "v613_car_door_")
    blue_count = 0
    for item in items:
        if item.get("id", "").startswith(blue_ids):
            item["material"] = "v614_lift_blue_glass"
            blue_count += 1

    # Lower the cabin shell until its floor, door leaves, and lower glazing
    # meet the ground landing datum instead of hovering above it.
    for item in items:
        ident = item.get("id", "")
        if ident.startswith("v613_car_post_"):
            item["position"][1] -= .13
        elif ident.startswith("v613_car_glass_"):
            item["position"][1] -= .13
            item["size"][1] += .13
        elif ident.startswith("v613_car_door_"):
            item["position"][1] -= .16
        elif ident.startswith("v613_car_base_"):
            item["position"][1] -= .18
        elif ident.startswith("v613_car_crown_"):
            item["position"][1] -= .13
        elif ident.startswith("v613_landing_door_ground_"):
            item["position"][1] -= .11
        elif ident.startswith("v613_landing_jamb_ground_"):
            item["position"][1] -= .03
        elif ident.startswith("v613_landing_sill_ground_"):
            item["position"][1] -= .10

    # Add visible sliding-door tracks, operator boxes, lift guide rails, and
    # a compact head drive. These are static geometry plus a future motion map.
    lift_x, lift_z = -40.0, -34.0
    parent = "Interieur/Galeries/Ascenseur capsule alu et verre dans trémie ouest/Mécanismes"
    def add_box(ident: str, material: str, pos: list[float], size: list[float]) -> None:
        items.append({"id": ident, "parent": parent, "geometry": "unit_box", "material": material,
                      "position": pos, "size": size, "rotationY": 0})

    for level, floor_y, head_y in (("ground", .05, 2.36), ("second", 9.164, 10.28)):
        for side in (-1, 1):
            x = lift_x + side * 1.335
            add_box(f"v614_landing_track_{level}_{side}_top", "v614_lift_brass",
                    [x, head_y, lift_z], [.075, .055, 1.55])
            add_box(f"v614_landing_track_{level}_{side}_bottom", "v439_gallery_warm",
                    [x, floor_y + .0225, lift_z], [.075, .045, 1.55])
            add_box(f"v614_landing_operator_{level}_{side}", "v439_gallery_warm",
                    [x, head_y + .12, lift_z + side * .55], [.16, .18, .38])
    for side in (-1, 1):
        x = lift_x + side * 1.04
        add_box(f"v614_car_track_top_{side}", "v614_lift_brass", [x, 2.11, lift_z], [.06, .05, 1.34])
        add_box(f"v614_car_track_bottom_{side}", "v439_gallery_warm", [x, .09, lift_z], [.06, .04, 1.34])
        for y in (1.0, 2.0):
            add_box(f"v614_car_guide_roller_{side}_{int(y)}", "v614_lift_brass",
                    [lift_x + side * .72, y, lift_z + .94], [.18, .12, .12])
        add_box(f"v614_lift_guide_rail_{side}", "v614_lift_brass",
                [lift_x + side * .70, 5.65, lift_z + 1.10], [.055, 11.0, .055])
    add_box("v614_lift_head_drive", "v439_gallery_warm", [lift_x, 11.02, lift_z + .62], [1.20, .38, .62])
    add_box("v614_lift_head_drive_accent", "v614_lift_brass", [lift_x, 10.81, lift_z + .62], [.94, .055, .64])

    # Register the new materials and image-backed texture set.
    materials_path = prefix + "materials/v442-corrections.json"
    materials = json.loads(files[materials_path])
    existing_materials = {m.get("id") for m in materials.get("materials", [])}
    if "v614_lift_marble" not in existing_materials:
        materials["materials"].append({
            "id": "v614_lift_marble", "baseColor": [0.92, 0.89, 0.82],
            "roughness": 0.23, "metallic": 0.02, "transmission": 0, "ior": 1.5,
            "textureSet": "tex_v614_lift_marble", "origin": "Calacatta marble reference approved for lift landing",
        })
        materials["materials"].append({
            "id": "v614_lift_brass", "baseColor": [0.68, 0.52, 0.29],
            "roughness": 0.28, "metallic": 0.68, "transmission": 0, "ior": 1.5,
            "textureSet": "tex_v614_lift_brass", "origin": "Champagne-aluminum edge inlay on lift medallion",
        })
        materials["materials"].append({
            "id": "v614_lift_blue_glass", "baseColor": [0.34, 0.59, 0.72],
            "roughness": 0.14, "metallic": 0.0, "transmission": 0.58, "ior": 1.5,
            "textureSet": "tex_v614_lift_blue_glass", "origin": "Blue-tinted lift glazing",
        })
    files[materials_path] = _dump(materials)

    pbr_path = prefix + "pbr/v440-audit.json"
    pbr = json.loads(files[pbr_path])
    sets = pbr.get("sets", [])
    set_ids = {entry.get("id") for entry in sets}
    if "tex_v614_lift_marble" not in set_ids:
        sets.append({"id": "tex_v614_lift_marble", "material": "v614_lift_marble",
                     "pattern": "image", "resolution": 1024, "channels": ["albedo"],
                     "imageFile": "textures/v614_lift_marble.png",
                     "textureDetail": {"mode": "preserve", "minResolution": 1024},
                     "status": "Seamless base-color texture generated from approved marble reference"})
    for material_id, color, rough in (
        ("v614_lift_brass", [0.68, 0.52, 0.29], 0.28),
        ("v614_lift_blue_glass", [0.34, 0.59, 0.72], 0.14),
    ):
        texture_id = "tex_" + material_id
        if texture_id not in set_ids:
            sets.append({"id": texture_id, "material": material_id, "pattern": "solid",
                         "resolution": 64, "channels": ["albedo"], "baseColor": color,
                         "roughness": rough, "status": "V17.614 generated material fallback"})
    files[pbr_path] = _dump(pbr)

    # The patch asset is stored beside the release tooling, then embedded into
    # the standalone package at the canonical scene texture path.
    marble_path = ROOT / "assets" / "v614_lift_marble.png"
    if not marble_path.is_file():
        raise FileNotFoundError(marble_path)
    files[prefix + "textures/v614_lift_marble.png"] = marble_path.read_bytes()
    files[instances_path] = _dump({**data, "instances": items})

    motion = {
        "revision": revision,
        "animationReadyOnly": True,
        "engineAnimation": "not implemented; static scene geometry only",
        "car": {"groupPrefix": "v613_car_", "floorInstance": "v614_lift_car_floor",
                "axis": "Y", "closedFloorTopY": 0.05, "upperLandingY": 9.164,
                "travelMeters": 9.114, "floorBottomY": -0.08},
        "slidingDoors": {"axis": "Z", "closed": True,
                         "panels": [
                             {"prefix": "v613_landing_door_ground_", "travelMeters": 0.70},
                             {"prefix": "v613_landing_door_second_", "travelMeters": 0.70},
                             {"prefix": "v613_car_door_", "travelMeters": 0.60},
                         ],
                         "visualMechanisms": "header operators, upper/lower tracks, guide rails"},
        "removed": sorted(removed_ids),
        "blueGlazingInstances": blue_count,
        "poolLaneNumbersUvFlipped": flipped_numbers,
        "notes": [
            "Elevator cabin floor top is flush with the ground landing at y=0.05 m.",
            "The overhanging third-floor closure panel was removed; surrounding levels remain unchanged.",
            "Sliding doors and cabin have transforms recorded for future engine animation.",
        ],
    }
    files[prefix + "reports/interior-lift-v614.json"] = _dump(motion)
    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
