"""Balance the plaza lighting and light the pool sign at night."""
from __future__ import annotations

import json


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # Keep the renderer-recognized night-emission material on the actual letter
    # faces; the engine's "lamp" material is time-controlled by its dusk curve.
    letters = [item for item in items
               if item.get("parent", "").startswith("Architecture/Complexe sportif/Enseigne toiture")
               and "/Face_neon_lettre_" in item.get("parent", "")]
    if len(letters) != 8:
        raise ValueError(f"V17.610 expected 8 roof-sign letter faces, found {len(letters)}")
    for letter in letters:
        letter["material"] = "lamp"

    # A previous patch made four nearby point sources per globe, producing
    # separated, square-looking pools on the paving. Use one centered source
    # per visible four-LED globe, with a broad, softer footprint instead.
    luminaire_path = prefix + "instances/plaza-luminaires-v17-606.json"
    luminaire_data = json.loads(files[luminaire_path])
    globe_instances = [item for item in luminaire_data.get("instances", [])
                       if item.get("id", "").startswith("plaza_luminaire_")
                       and item.get("id", "").endswith("_globe")]
    if len(globe_instances) != 12:
        raise ValueError(f"V17.610 expected 12 plaza globes, found {len(globe_instances)}")
    lights = []
    for index, globe in enumerate(globe_instances, 1):
        x, _, z = globe["position"]
        lights.append({
            "id": f"v610_globe_pool_{index:02d}",
            "position": [x, 0.48, z], "radius": 18.0, "intensity": 4.0,
            "color": [255, 190, 135], "group": "exterior",
        })

    # Moderate, concealed uplights illuminate the monument's silhouette rather
    # than concentrating the whole plaza's brightness in one central pool.
    for index, (x, z) in enumerate(((-4.5, 0), (4.5, 0), (0, -4.5), (0, 4.5)), 1):
        lights.append({
            "id": f"v610_monument_uplight_{index:02d}",
            "position": [x, 2.2, round(72.0 + z, 3)],
            "radius": 14.0, "intensity": 4.2,
            "color": [255, 222, 185], "group": "exterior",
        })

    # Low-power fill along the tree rows and the otherwise dark approach from
    # the building to the plaza. All sources share the exterior hysteresis.
    for side in (-1, 1):
        for index, z in enumerate((48.0, 72.0, 96.0), 1):
            lights.append({
                "id": f"v610_tree_fill_{'L' if side < 0 else 'R'}_{index:02d}",
                "position": [side * 51.5, 2.6, z],
                "radius": 15.0, "intensity": 2.6,
                "color": [220, 224, 232], "group": "exterior",
            })
        for index, z in enumerate((12.0, 31.0), 1):
            lights.append({
                "id": f"v610_approach_fill_{'L' if side < 0 else 'R'}_{index:02d}",
                "position": [side * 12.0, 2.4, z],
                "radius": 12.0, "intensity": 2.0,
                "color": [255, 218, 175], "group": "exterior",
            })

    # Add a restrained wall-wash in front of the roof lettering. The letters
    # themselves remain emissive; these sources make their relief legible too.
    for index, x in enumerate((-4.0, 0.0, 4.0), 1):
        lights.append({
            "id": f"v610_sign_wash_{index:02d}",
            "position": [x, 22.4, -4.25],
            "radius": 7.0, "intensity": 2.0,
            "color": [255, 210, 155], "group": "exterior",
        })

    light_path = prefix + "lighting/plaza-luminaires-v17-606.json"
    light_data = json.loads(files[light_path])
    light_data["lights"] = lights
    files[light_path] = _json(light_data)
    files[instances_path] = _json(data)

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)
