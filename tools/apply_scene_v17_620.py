"""Restore the gallery floor and remove only the isolated suspended landing."""
from __future__ import annotations

import json


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # V17.618 removed an entire gallery floor while the isolated upper-level
    # segment remained. Restore both floor layers and remove only that segment.
    restore = {
        "v17_000029": {
            "id": "v17_000029", "parent": "Interieur/Galeries",
            "geometry": "unit_box", "material": "prp_concrete_raw",
            "position": [0, 9, -9.45], "size": [57, 0.3, 8.5], "rotationY": 0,
        },
        "v439_floor_deck_3": {
            "id": "v439_floor_deck_3", "parent": "Interieur/Galeries/Sols des niveaux",
            "geometry": "unit_box", "material": "v439_gallery_warm",
            "position": [0.0, 9.164, -9.45], "size": [56.92, 0.025, 8.42], "rotationY": 0,
        },
    }
    items = [item for item in items if item.get("id") not in restore]
    items.extend(restore.values())
    target = "v8_side_gallery_floor_135_3"
    matches = [item for item in items if item.get("id") == target]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one suspended landing {target}; found {len(matches)}")
    items = [item for item in items if item.get("id") != target]
    data["instances"] = items
    files[instances_path] = _dump(data)

    report_path = prefix + "reports/gallery-slab-v620.json"
    files[report_path] = _dump({
        "revision": revision,
        "restoredInstances": ["v17_000029", "v439_floor_deck_3"],
        "removedInstances": [target],
        "removedInstancePosition": matches[0]["position"],
        "removedInstanceSize": matches[0]["size"],
        "notes": [
            "Restored the full level-2 gallery slab and its thin finish layer.",
            "Removed only the isolated upper-level slab identified in the suspended-slab view.",
        ],
    })

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
