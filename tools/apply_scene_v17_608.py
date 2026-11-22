"""Correct the plaza bench, exterior lights, and facade mosaic returns."""
from __future__ import annotations

import json
import math


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # V17.607 placed concrete infills in the middle bays. The two missing
    # returns are instead at the building's outer edges, beyond the last window
    # mullion. Back them at the facade plane, then overlay the mosaic on top.
    items = [item for item in items if item.get("id") not in {
        "v607_facade_beam_infill_left", "v607_facade_beam_infill_right",
        "v608_facade_return_left", "v608_facade_return_right",
    }]
    for side, x in (("left", -49.15), ("right", 49.15)):
        items.append({
            "id": f"v608_facade_return_{side}",
            "parent": "Architecture/Complexe aquatique/Façade/Retour fermé sous mosaïque",
            "geometry": "unit_box", "material": "prp_concrete_raw",
            "position": [x, 9.5, -3.865], "size": [2.30, 19.0, 0.12],
            "rotationY": 0,
        })

    # Separate adjacent seat modules slightly so they read as a designed,
    # curved assembly instead of a single overlapping block. Keep every
    # existing pedestrian opening; add one concrete backrest per seat module.
    seats = [item for item in items if item.get("parent") == "Place/Banc ovale béton/Assise"]
    if len(seats) != 80:
        raise ValueError(f"V17.608 expected 80 existing seat modules, found {len(seats)}")
    feet_by_position = {
        tuple(round(v, 3) for v in item["position"]): item
        for item in items if item.get("parent") == "Place/Banc ovale béton/Piétement"
    }
    for seat in seats:
        original_key = tuple(round(v, 3) for v in seat["position"])
        theta = math.radians(float(seat.get("rotationY", 0)))
        trim = 0.16
        seat["size"][0] = round(max(0.35, seat["size"][0] - trim), 3)
        seat["position"][0] = round(seat["position"][0] + trim * 0.5 * math.cos(theta), 3)
        seat["position"][2] = round(seat["position"][2] - trim * 0.5 * math.sin(theta), 3)
        foot = feet_by_position.get(original_key)
        if foot:
            foot["size"][0] = round(max(0.35, foot["size"][0] - trim), 3)
            foot["position"][0] = seat["position"][0]
            foot["position"][2] = seat["position"][2]

        x, _, z = seat["position"]
        nx = x / (32.9 * 32.9)
        nz = (z - 72.0) / (21.0 * 21.0)
        norm = max(1e-5, math.hypot(nx, nz))
        # Backrest follows the outside of the oval so people face the planted
        # mound. It starts just above the seat and remains low and unobtrusive.
        bx = round(x + 0.61 * nx / norm, 3)
        bz = round(z + 0.61 * nz / norm, 3)
        items.append({
            "id": f"v608_bench_backrest_{seat['id']}",
            "parent": "Place/Banc ovale béton/Dossier béton courbe",
            "geometry": "unit_box", "material": "prp_concrete_raw",
            "position": [bx, 1.30, bz],
            "size": [round(max(0.32, seat["size"][0] - 0.08), 3), 0.72, 0.18],
            "rotationY": seat.get("rotationY", 0),
        })

    # Remove the V17.607 lamps before laying out the same validated X-globe
    # design with overlapping, much wider pools. Four offset sources keep the
    # light distributed toward each side rather than concentrated at center.
    items = [item for item in items if not item.get("id", "").startswith("plaza_luminaire_")]
    seat_x = [item["position"][0] for item in seats]
    seat_z = [item["position"][2] for item in seats]
    center_x = (min(seat_x) + max(seat_x)) / 2
    center_z = (min(seat_z) + max(seat_z)) / 2
    radius_x = (max(seat_x) - min(seat_x)) / 2 + 3.6
    radius_z = (max(seat_z) - min(seat_z)) / 2 + 3.6
    luminaire_instances, lights = [], []
    for index in range(12):
        angle = math.radians(15.0 + 30.0 * index)
        x = round(center_x + radius_x * math.cos(angle), 3)
        z = round(center_z + radius_z * math.sin(angle), 3)
        parent = f"Place/Banc ovale/Éclairage extérieur {index + 1:02d}"
        luminaire_instances.extend([
            {"id": f"plaza_luminaire_{index + 1:02d}_bezel",
             "parent": parent + "/Collerette acier", "geometry": "unit_sphere",
             "material": "plaza_luminaire_bezel", "position": [x, 0.167, z],
             "size": [0.34, 0.022, 0.34], "rotationY": 0},
            {"id": f"plaza_luminaire_{index + 1:02d}_globe",
             "parent": parent + "/Globe diffusant bas", "geometry": "unit_sphere",
             # The engine's existing lamp material already fades its emission
             # with the exterior-light hysteresis in every backend.
             "material": "lamp", "position": [x, 0.178, z],
             "size": [0.18, 0.045, 0.18], "rotationY": 0},
        ])
        for led_index, (dx, dz, rotation) in enumerate((
            (-0.049, -0.049, 45), (0.049, -0.049, -45),
            (-0.049, 0.049, -45), (0.049, 0.049, 45),
        ), 1):
            luminaire_instances.append({
                "id": f"plaza_luminaire_{index + 1:02d}_led_{led_index}",
                "parent": parent + f"/LED X {led_index}", "geometry": "unit_box",
                "material": "led", "position": [round(x + dx, 3), 0.195, round(z + dz, 3)],
                "size": [0.066, 0.006, 0.012], "rotationY": rotation,
            })
        for dx, dz in ((-0.75, 0), (0, -0.75), (0.75, 0), (0, 0.75)):
            lights.append({
                "position": [round(x + dx, 3), 0.42, round(z + dz, 3)],
                "radius": 13.0, "intensity": 6.0,
                "color": [255, 190, 125], "group": "exterior",
            })

    data["instances"] = items
    files[instances_path] = _json(data)
    files[prefix + "instances/plaza-luminaires-v17-606.json"] = _json({
        "format": "m3d-instances-v1", "instances": luminaire_instances})
    files[prefix + "lighting/plaza-luminaires-v17-606.json"] = _json({
        "format": "m3d-lighting-v1", "hour": 14.75, "lights": lights})

    geometry_path = prefix + "geometry/v7-corrections.json"
    geometry = json.loads(files[geometry_path])
    mesh = next((m for m in geometry.get("meshes", [])
                 if m.get("id") == "v604_mosaic_panel_mesh"), None)
    if mesh is None:
        raise ValueError("V17.608 facade mosaic mesh was not found")
    # The old 1.1 m strip sat behind the corner pier. Widen it to cover the
    # whole side return while preserving its corrected outward face winding.
    mesh["vertices"] = [[-1.05, -9.0, 0], [1.05, -9.0, 0],
                        [1.05, 9.0, 0], [-1.05, 9.0, 0]]
    mesh["faces"] = [[0, 1, 2], [0, 2, 3]]
    files[geometry_path] = _json(geometry)
    for side, x in (("left", -49.15), ("right", 49.15)):
        panel = next((item for item in items if item.get("id") == f"v604_facade_mosaic_{side}"), None)
        if panel is None:
            raise ValueError(f"V17.608 missing {side} facade mosaic instance")
        panel["position"] = [x, 9.5, -3.72]
        panel["size"] = [1.0, 1.0, 1.0]
    files[instances_path] = _json(data)

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)
