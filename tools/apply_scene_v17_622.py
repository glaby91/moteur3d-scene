"""Remove the user-approved obsolete stairwell closure only."""
from __future__ import annotations

import json


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])
    by_id = {item.get("id"): item for item in items}

    # V17.621 removed the wrong side-gallery slab. Restore both of its layers;
    # the approved removal below is the separate obsolete stairwell closure.
    restore = {
        "v8_side_gallery_floor_90_3": {
            "id": "v8_side_gallery_floor_90_3",
            "parent": "Interieur/Galeries/Escaliers lateraux/Planchers decoupes",
            "geometry": "unit_box", "material": "prp_concrete_raw",
            "position": [-40.0, 9.0, -14.8], "size": [3.1, 0.3, 18.6], "rotationY": 0,
        },
        "v439_floor_deck_12": {
            "id": "v439_floor_deck_12",
            "parent": "Interieur/Galeries/Sols des niveaux",
            "geometry": "unit_box", "material": "v439_gallery_warm",
            "position": [-40.0, 9.164, -14.8], "size": [3.02, 0.025, 18.52], "rotationY": 0,
        },
    }
    by_id.update(restore)

    target = "v7_close_obsolete_hall_stairwell"
    matches = [item for item in by_id.values() if item.get("id") == target]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one approved slab {target}; found {len(matches)}")
    by_id.pop(target)
    data["instances"] = list(by_id.values())
    files[instances_path] = _dump(data)

    files[prefix + "reports/gallery-slab-v622.json"] = _dump({
        "revision": revision,
        "approvedRemoval": target,
        "position": matches[0]["position"],
        "size": matches[0]["size"],
        "restoredUnrelatedInstances": sorted(restore),
        "notes": [
            "Removed only the obsolete hall-stairwell closure confirmed by the user.",
            "Restored the unrelated side-gallery slab and finish layer from V17.621.",
        ],
    })

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
