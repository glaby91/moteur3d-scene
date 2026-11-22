"""Improve night lighting on the plaza monument and pool building sign."""
from __future__ import annotations

import json


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # Letter faces used colored reflective paint, so they looked dark at night
    # even when the surrounding neon tubes were visible. The engine's existing
    # lamp material provides the night-controlled emissive response.
    letters = [item for item in items
               if item.get("parent", "").startswith("Architecture/Complexe sportif/Enseigne toiture")
               and "/Face_neon_lettre_" in item.get("parent", "")]
    if len(letters) != 8:
        raise ValueError(f"V17.609 expected 8 roof-sign letter faces, found {len(letters)}")
    for letter in letters:
        letter["material"] = "lamp"

    # Add concealed, night-only uplight sources in the planted bed around the
    # monument. This keeps the approved low floor globes in place and lights the
    # sculpture directly instead of trying to stretch their short-range pools.
    lights_path = prefix + "lighting/plaza-luminaires-v17-606.json"
    light_data = json.loads(files[lights_path])
    lights = light_data.get("lights", [])
    lights = [light for light in lights if not light.get("id", "").startswith("v609_monument_uplight_")]
    # Broaden the floor-light overlap and reduce each source proportionally so
    # the four visible pools blend into a more even paving surface.
    for light in lights:
        if light.get("group") == "exterior":
            light["radius"] = 20.0
            light["intensity"] = 4.5
    for index, (x, z) in enumerate(((-4.5, 0), (4.5, 0), (0, -4.5), (0, 4.5)), 1):
        lights.append({
            "id": f"v609_monument_uplight_{index:02d}",
            "position": [x, 2.4, round(72.0 + z, 3)],
            "radius": 18.0,
            "intensity": 10.0,
            "color": [255, 222, 178],
            "group": "exterior",
        })
    light_data["lights"] = lights
    files[lights_path] = _json(light_data)
    files[instances_path] = _json(data)

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)
