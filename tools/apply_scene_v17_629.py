#!/usr/bin/env python3
"""Remove the two obsolete opaque shower partitions; keep the approved glass mosaic."""
from __future__ import annotations

import json


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    instances = data.get("instances", [])
    obsolete = {
        "v17_001776": "Interieur/Vestiaires et douches ouest/Douches/Cloisons",
        "v17_001777": "Interieur/Vestiaires et douches ouest/Douches/Cloisons",
    }
    by_id = {item.get("id"): item for item in instances}
    for ident, expected_parent in obsolete.items():
        item = by_id.get(ident)
        if item is None:
            raise ValueError(f"Expected obsolete shower partition {ident}")
        if item.get("parent") != expected_parent or item.get("material") != "prp_tile_ceramic":
            raise ValueError(f"Refusing to remove unexpected instance {ident}: {item}")

    data["instances"] = [item for item in instances if item.get("id") not in obsolete]
    files[instances_path] = _dump(data)

    files[prefix + "reports/shower-panels-v629.json"] = _dump({
        "revision": revision,
        "removedInstances": sorted(obsolete),
        "removedParent": "Interieur/Vestiaires et douches ouest/Douches/Cloisons",
        "removedMaterial": "prp_tile_ceramic",
        "notes": [
            "Removed only the two obsolete opaque shower partitions identified by the user.",
            "Kept the approved translucent glass mosaic on vestiaire L-partition walls v17_001771 and v17_001773.",
            "Did not alter other glazing, shower fixtures, or the pool scene geometry.",
        ],
    })

    scene = json.loads(files[scene_path])
    scene["name"] = "CSE WARP V17.629 — Cloisons de douche retirées, mosaïque translucide conservée"
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
