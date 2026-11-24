"""Remove the isolated second-level slab beside the lift without deleting the gallery floor."""
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

    # V17.620 removed the wrong, higher segment. Put it back exactly as authored.
    restore_upper = {
        "id": "v8_side_gallery_floor_135_3",
        "parent": "Interieur/Galeries/Escaliers lateraux/Planchers decoupes",
        "geometry": "unit_box", "material": "prp_concrete_raw",
        "position": [-35.0, 13.5, -14.8], "size": [3.1, 0.3, 18.6], "rotationY": 0,
    }
    by_id[restore_upper["id"]] = restore_upper

    # This paired slab and finish strip form only the isolated overhang seen in
    # the supplied view; the long continuous gallery floor remains in place.
    targets = {"v8_side_gallery_floor_90_3", "v439_floor_deck_12"}
    target_records = {item.get("id"): item for item in items if item.get("id") in targets}
    if target_records.keys() != targets:
        raise ValueError(f"Expected both isolated slab layers; found {sorted(target_records)}")
    by_id = {key: item for key, item in by_id.items() if key not in targets}
    data["instances"] = list(by_id.values())
    files[instances_path] = _dump(data)

    report_path = prefix + "reports/gallery-slab-v621.json"
    files[report_path] = _dump({
        "revision": revision,
        "cameraReferenceXZ": [-26.0, -16.2],
        "removedInstances": sorted(targets),
        "removedInstancesPosition": {key: target_records[key]["position"] for key in sorted(targets)},
        "restoredInstance": restore_upper["id"],
        "continuousGalleryFloor": "v17_000029 and v439_floor_deck_3 retained",
        "notes": [
            "Removed only the isolated second-level slab and its thin finish layer at x=-40, z=-14.8.",
            "Restored the unrelated upper-level side-gallery segment removed by V17.620.",
            "Kept the continuous level-2 gallery floor and finish layer intact.",
        ],
    })

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
