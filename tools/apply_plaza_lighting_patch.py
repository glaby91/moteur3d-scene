"""Apply the approved low-profile plaza luminaire design to the civic scene."""
from __future__ import annotations

import json


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    scene = json.loads(files[scene_path])
    sector = next(s for s in scene["sectors"] if s["id"] == "benchmark-leger")
    resources = {
        "instances": "instances/plaza-luminaires-v17-606.json",
        "materials": "materials/plaza-luminaires-v17-606.json",
        "lighting": "lighting/plaza-luminaires-v17-606.json",
    }
    instances_path, materials_path, lighting_path = resources.values()
    sector["instances"].append(instances_path)
    sector["materials"].append(materials_path)
    sector["lighting"].append(lighting_path)
    prefix = scene_path.rsplit("/", 1)[0] + "/"

    # The old six generic floor pucks were scattered around the square. Remove
    # them so the approved design reads as a deliberate, safe central line.
    base_instances_path = prefix + "instances/v442-corrections.json"
    base_instances = json.loads(files[base_instances_path])
    base_instances["instances"] = [
        item for item in base_instances["instances"]
        if not item.get("id", "").startswith("v600_garden_floor_light_")
    ]
    files[base_instances_path] = _json(base_instances)

    centers = [(0.0, 36.0 + 7.0 * i) for i in range(5)]
    instances = []
    lights = []
    for index, (x, z) in enumerate(centers, 1):
        parent = f"Place/Allée centrale/Éclairage encastré {index:02d}"
        # The flange sits almost flush; only the flattened globe rises 4.5 cm.
        instances.extend([
            {"id": f"plaza_luminaire_{index:02d}_bezel", "parent": parent + "/Collerette acier",
             "geometry": "unit_sphere", "material": "plaza_luminaire_bezel",
             "position": [x, 0.167, z], "size": [0.34, 0.022, 0.34], "rotationY": 0},
            {"id": f"plaza_luminaire_{index:02d}_globe", "parent": parent + "/Globe diffusant bas",
             "geometry": "unit_sphere", "material": "plaza_luminaire_globe",
             "position": [x, 0.178, z], "size": [0.18, 0.045, 0.18], "rotationY": 0},
        ])
        # Four short luminous bars form an X on the diffuser, below the 5 cm limit.
        for led_index, (dx, dz, angle) in enumerate([
            (-0.049, -0.049, 45), (0.049, -0.049, -45),
            (-0.049, 0.049, -45), (0.049, 0.049, 45),
        ], 1):
            instances.append({
                "id": f"plaza_luminaire_{index:02d}_led_{led_index}",
                "parent": parent + f"/LED X {led_index}", "geometry": "unit_box",
                "material": "led", "position": [x + dx, 0.195, z + dz],
                "size": [0.066, 0.006, 0.012], "rotationY": angle,
            })
            # Four warm pools per fixture mimic the cross-shaped directional LEDs.
            direction = [(-1, 0), (0, -1), (1, 0), (0, 1)][led_index - 1]
            lights.append({"position": [x + direction[0] * 0.10, 0.28,
                                         z + direction[1] * 0.10],
                           "radius": 3.2, "intensity": 0.72,
                           "color": [255, 194, 137], "group": "exterior"})

    files[prefix + instances_path] = _json({"format": "m3d-instances-v1", "instances": instances})
    files[prefix + materials_path] = _json({"format": "m3d-materials-v1", "materials": [
        {"id": "plaza_luminaire_bezel", "baseColor": [0.16, 0.18, 0.17],
         "roughness": 0.48, "metallic": 0.72, "transmission": 0, "ior": 1.5,
         "textureSet": "tex_prp_steel_painted"},
        {"id": "plaza_luminaire_globe", "baseColor": [0.78, 0.64, 0.43],
         "roughness": 0.42, "metallic": 0.08, "transmission": 0, "ior": 1.5,
         "textureSet": "tex_prp_roof_metal"},
        {"id": "led", "baseColor": [1.0, 0.64, 0.31],
         "roughness": 0.28, "metallic": 0.0, "transmission": 0, "ior": 1.5,
         "textureSet": "tex_prp_roof_metal"},
    ]})
    files[prefix + lighting_path] = _json({"format": "m3d-lighting-v1", "hour": 14.75,
                                           "lights": lights})
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)

