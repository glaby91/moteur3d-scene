"""Apply the V17.607 scene corrections requested from the V17.606 screenshots."""
from __future__ import annotations

import json
import math


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    instances_data = json.loads(files[instances_path])
    items = instances_data.get("instances", [])

    # The facade mosaic mesh was wound toward the inside and sat behind the
    # front beam. Face it toward the plaza and bring the corner piers forward.
    for item in items:
        if item.get("id") in ("v604_facade_mosaic_left", "v604_facade_mosaic_right"):
            item["position"][0] = -49.0 if item["id"].endswith("_left") else 49.0
            item["position"][2] = -4.20
            item["size"] = [1.55, 1.0, 1.0]

    geometry_path = prefix + "geometry/v7-corrections.json"
    geometry = json.loads(files[geometry_path])
    geometry_changed = False
    for node in _walk(geometry):
        if node.get("id") == "v604_mosaic_panel_mesh":
            # Reverse both triangle windings so the exterior face is visible.
            node["faces"] = [[0, 1, 2], [0, 2, 3]]
            geometry_changed = True
    if not geometry_changed:
        raise ValueError("V17.607: v604 facade mosaic mesh was not found")
    files[geometry_path] = _json(geometry)

    # Close the two exposed end bays between the outermost canopy beams.
    # Their coordinates match the existing beam pairs at x=-48/-42 and 42/48.
    items = [item for item in items if item.get("id") not in (
        "v607_facade_beam_infill_left", "v607_facade_beam_infill_right")]
    for side, x in (("left", -45.0), ("right", 45.0)):
        items.append({
            "id": f"v607_facade_beam_infill_{side}",
            "parent": "Architecture/Complexe aquatique/Façade/Remplissage entre poutres",
            "geometry": "unit_box", "material": "prp_concrete_panel",
            "position": [x, 15.0, -4.47], "size": [5.45, 0.72, 0.12],
            "rotationY": 0,
        })

    # Reduce the seat overhang relative to its concrete feet while preserving
    # the existing open entrances between bench arcs.
    seats = []
    for item in items:
        parent = item.get("parent", "")
        if parent == "Place/Banc ovale béton/Assise":
            item["size"][2] = 1.0
            seats.append(item)
        elif parent == "Place/Banc ovale béton/Piétement":
            item["size"][2] = 0.90

    if not seats:
        raise ValueError("V17.607: no oval bench seats found")
    min_x = min(item["position"][0] for item in seats)
    max_x = max(item["position"][0] for item in seats)
    min_z = min(item["position"][2] for item in seats)
    max_z = max(item["position"][2] for item in seats)
    center_x, center_z = (min_x + max_x) / 2, (min_z + max_z) / 2
    radius_x = (max_x - min_x) / 2 + 3.6
    radius_z = (max_z - min_z) / 2 + 3.6

    # The exported tree origins are already below grade. Sink the plaza trees
    # another 20 cm to cover the roots that remain exposed in the planted beds.
    for item in items:
        if item.get("id", "").startswith("v600_garden_tree_"):
            item["position"][1] = round(item["position"][1] - 0.20, 3)

    # Remove the V17.606 centerline pucks and the old scattered generic pucks.
    items = [item for item in items if not (
        item.get("id", "").startswith("v600_garden_floor_light_")
        or item.get("id", "").startswith("plaza_luminaire_")
    )]

    # Keep the low-profile X-globe fixture, but place it on paving outside the
    # oval bench, with larger overlapping light pools and no fixture in the mound.
    luminaire_instances = []
    light_sources = []
    for index in range(12):
        angle = math.radians(15.0 + 30.0 * index)
        x = center_x + radius_x * math.cos(angle)
        z = center_z + radius_z * math.sin(angle)
        x, z = round(x, 3), round(z, 3)
        parent = f"Place/Banc ovale/Éclairage extérieur {index + 1:02d}"
        luminaire_instances.extend([
            {"id": f"plaza_luminaire_{index + 1:02d}_bezel",
             "parent": parent + "/Collerette acier", "geometry": "unit_sphere",
             "material": "plaza_luminaire_bezel", "position": [x, 0.167, z],
             "size": [0.34, 0.022, 0.34], "rotationY": 0},
            {"id": f"plaza_luminaire_{index + 1:02d}_globe",
             "parent": parent + "/Globe diffusant bas", "geometry": "unit_sphere",
             "material": "plaza_luminaire_globe", "position": [x, 0.178, z],
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
            direction = ((-1, 0), (0, -1), (1, 0), (0, 1))[led_index - 1]
            light_sources.append({
                "position": [round(x + direction[0] * 0.10, 3), 0.28,
                             round(z + direction[1] * 0.10, 3)],
                "radius": 5.0, "intensity": 1.2,
                "color": [255, 194, 137], "group": "exterior",
            })
    items.extend(luminaire_instances)
    instances_data["instances"] = items
    files[instances_path] = _json(instances_data)

    custom_instances_path = prefix + "instances/plaza-luminaires-v17-606.json"
    files[custom_instances_path] = _json({
        "format": "m3d-instances-v1", "instances": luminaire_instances})
    custom_lighting_path = prefix + "lighting/plaza-luminaires-v17-606.json"
    files[custom_lighting_path] = _json({
        "format": "m3d-lighting-v1", "hour": 14.75, "lights": light_sources})

    # Remove the weak legacy sources at the old scattered floor-puck locations.
    legacy_lighting_path = prefix + "lighting/v8-nine-anomalies.json"
    legacy_lighting = json.loads(files[legacy_lighting_path])
    old_points = {(0, 31), (-38, 64), (38, 64), (-38, 80), (38, 80), (0, 108)}
    legacy_lighting["lights"] = [
        light for light in legacy_lighting.get("lights", [])
        if not (round(light.get("position", [0, 0, 0])[0]),
                round(light.get("position", [0, 0, 0])[2])) in old_points
        or light.get("position", [0, 0, 0])[1] > 0.5
    ]
    files[legacy_lighting_path] = _json(legacy_lighting)

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)
