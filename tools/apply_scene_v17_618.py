"""Correct the lift datum/entry and remove the suspended east gallery slab."""
from __future__ import annotations

import json


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # The wide, shallow east-gallery floor was the remaining hanging panel in
    # the submitted view. Remove its thin duplicate overlay as well.
    removed = {"v17_000029", "v439_floor_deck_3"}
    items = [item for item in items if item.get("id") not in removed]

    lift_x, lift_z = -40.0, -34.0
    ground_y = 0.55  # top of the actual ground-floor foundation/deck
    raised_prefixes = (
        "v613_car_", "v614_lift_marble_annulus", "v614_lift_brass_inlay",
        "v614_lift_car_floor", "v614_car_track_", "v614_car_guide_roller_",
        "v614_landing_track_ground_", "v614_landing_operator_ground_",
    )
    shaft_x = ("v613_shaft_post_", "v613_shaft_glass_")

    for item in items:
        ident = item.get("id", "")
        pos, size = item.get("position"), item.get("size")
        if not isinstance(pos, list) or len(pos) != 3 or not isinstance(size, list) or len(size) != 3:
            continue
        if ident.startswith(raised_prefixes):
            pos[1] += .50

        # Lower shaft sill to the floor datum while preserving the crown at
        # its existing height; shorten the posts/glazing to match.
        if ident.startswith("v613_shaft_post_"):
            pos[1] += .20
            size[1] -= .40
        elif ident.startswith("v613_shaft_glass_"):
            pos[1] += .20
            size[1] -= .40
        elif ident.startswith("v613_shaft_sill_"):
            pos[1] += .40
        elif ident.startswith("v613_shaft_mid_band_"):
            pos[1] += .15

        if ident.startswith(("v613_landing_door_ground_", "v613_landing_jamb_ground_",
                             "v613_landing_header_ground_", "v613_landing_sill_ground_",
                             "v613_bridge_ground_")):
            pos[1] += .50

        # Widen the paired sliding leaves to a 1.56 m clear entrance on both
        # served landings. The jambs and tracks move outward with the opening.
        if ident.startswith("v613_landing_door_"):
            leaf = ident.rsplit("_", 1)[-1]
            sign = -1 if leaf == "a" else 1
            # Keep the static preview passable: the panels are modeled at
            # their fully-open slide positions until the engine animates them.
            pos[2] = lift_z + sign * 1.17
            size[2] = .78
        elif ident.startswith("v613_landing_jamb_"):
            sign = -1 if "_-0.78" in ident else 1
            pos[2] = lift_z + sign * .90
        elif ident.startswith(("v613_landing_header_", "v613_landing_sill_")):
            size[2] = 1.90
        elif ident.startswith("v613_bridge_"):
            size[2] = 1.80

        if ident.startswith("v614_landing_track_"):
            size[2] = 3.12
        if ident.startswith("v613_car_door_"):
            leaf = ident.rsplit("_", 1)[-1]
            sign = -1 if leaf == "a" else 1
            pos[2] = lift_z + sign * .80
            size[2] = .40
        if ident.startswith("v614_car_track_"):
            size[2] = 2.00
        if ident.startswith("v614_lift_guide_rail_"):
            pos[1] = 5.95
            size[1] = 10.80

    data["instances"] = items
    files[instances_path] = _dump(data)

    # Update the earlier report so the scene carries the correct physical
    # floor datum, plus a concise V17.618 correction record.
    old_report_path = prefix + "reports/interior-lift-v614.json"
    if old_report_path in files:
        old_report = json.loads(files[old_report_path])
        old_report["car"]["closedFloorTopY"] = ground_y
        old_report["car"]["upperLandingY"] = 9.164
        old_report["car"]["travelMeters"] = 8.614
        old_report["car"]["floorBottomY"] = .42
        old_report["notes"] = [
            "Cabin floor top is flush with the ground landing at y=0.55 m.",
            "The ground landing is aligned to the foundation top; the marble ring is flush with the hall floor.",
            "Sliding entry leaves were widened; their movement remains future engine animation metadata only.",
        ]
        files[old_report_path] = _dump(old_report)
    files[prefix + "reports/interior-lift-v618.json"] = _dump({
        "revision": revision,
        "groundLandingY": ground_y,
        "cabinFloorTopY": ground_y,
        "upperLandingY": 9.164,
        "cabinTravelMeters": 8.614,
        "landingOpeningClearWidthMeters": 1.56,
        "carDoorOpeningClearWidthMeters": 1.20,
        "doorPreviewState": "open; static pose until the engine adds animation",
        "removedInstances": sorted(removed),
        "notes": [
            "Lift base, doors, and circular marble medallion now share the actual ground-floor datum.",
            "Lift and cabin door leaves are parked open so exploration can enter the car.",
            "The east gallery slab and its overlay were removed from above the hall viewpoint.",
        ],
    })

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
