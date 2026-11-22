"""Rework the west stairwell and add the retrofuturist glass lift."""
from __future__ import annotations

import json


def _json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # The three visible flights and their rails made the west gallery crowded.
    # The lift becomes the vertical connection; the left gallery remains a
    # continuous walkable route at level two.
    stair_prefixes = ("v8_stair_0", "v8_stair_1", "v8_stair_2", "inst_v8_stair_")
    void_ids = ("v8_floor_void_rail_", "v8_void_post_")
    removed_stairs = [item for item in items if item.get("id", "").startswith(stair_prefixes + void_ids)]
    items = [item for item in items if item not in removed_stairs]

    # Clear the small returns and the west locker bank in the stair view.
    remove_ids = {"v439_stair_wall_return_0", "v439_stair_wall_return_1"}
    removed_walls = [item for item in items if item.get("id") in remove_ids]
    items = [item for item in items if item.get("id") not in remove_ids]
    removed_lockers = []
    for item in items:
        parent = item.get("parent", "").lower()
        pos = item.get("position", [0, 0, 0])
        if "casier" in parent and len(pos) == 3 and pos[0] < -45.0 and -45.5 < pos[2] < -30.0:
            removed_lockers.append(item)
    items = [item for item in items if item not in removed_lockers]

    # Remove the three roof beams previously identified as ending in open space.
    floating_beams = {"v17_000891", "v17_000894", "v17_000896"}
    found_beams = {item.get("id") for item in items if item.get("id") in floating_beams}
    if found_beams != floating_beams:
        raise ValueError(f"V17.611 expected the three reported beams; found {sorted(found_beams)}")
    items = [item for item in items if item.get("id") not in floating_beams]

    # Replace the old potted plant in the selected glazed bay with the lift.
    lift_x, lift_z = 13.0, -10.0
    plants = [item for item in items
              if item.get("id", "").startswith("v601_indoor_plant_4_")]
    if len(plants) < 3:
        raise ValueError(f"V17.611 expected the plant group in the lift bay; found {len(plants)} parts")
    items = [item for item in items if item not in plants]

    # Replace the floating upper landing slab with four pieces around a 3.6 x
    # 3.4 m shaft opening. Its inner-side doors face into the building.
    old_landing = [item for item in items if item.get("id") == "v439_floor_deck_3"]
    if len(old_landing) != 1:
        raise ValueError(f"V17.611 expected one hall slab for the lift opening; found {len(old_landing)}")
    items = [item for item in items if item.get("id") != "v439_floor_deck_3"]
    slab_material = old_landing[0].get("material", "v439_gallery_warm")
    slab_parent = "Interieur/Galeries/Plancher niveau 2 autour ascenseur"
    for ident, pos, size in (
        ("v611_landing_slab_left", [-8.63, 9.164, -9.45], [39.66, 0.045, 8.42]),
        ("v611_landing_slab_right", [21.63, 9.164, -9.45], [13.66, 0.045, 8.42]),
        ("v611_landing_slab_inner", [13.0, 9.164, -12.68], [3.60, 0.045, 1.96]),
        ("v611_landing_slab_facade", [13.0, 9.164, -6.77], [3.60, 0.045, 3.06]),
    ):
        items.append({"id": ident, "parent": slab_parent, "geometry": "unit_box",
                      "material": slab_material, "position": pos, "size": size, "rotationY": 0})

    # Close the third-floor stair opening and bridge the narrow gap on the
    # second-floor left balcony route.
    items.extend([
        {"id": "v611_left_balcony_walkway", "parent": "Interieur/Galeries/Acces balcon gauche",
         "geometry": "unit_box", "material": "v439_gallery_warm",
         "position": [-40.0, 9.164, -30.0], "size": [3.18, 0.045, 48.9], "rotationY": 0},
        {"id": "v611_close_third_floor_stairwell", "parent": "Interieur/Galeries/Fermeture trémie niveau 3",
         "geometry": "unit_box", "material": "v439_waxed_concrete",
         "position": [-35.0, 13.664, -30.0], "size": [3.18, 0.045, 48.9], "rotationY": 0},
    ])

    # Space-Age capsule: brushed-aluminum uprights and rounded ring details,
    # translucent glazing, and split inner-facing doors. The shaft stops at
    # level two; no opening is retained above it.
    base_y, top_y = 0.60, 11.20
    shaft_h = top_y - base_y
    half_x, half_z = 1.78, 1.63
    metal, glass = "prp_roof_metal", "prp_window_glass"
    lift_parent = "Interieur/Hall/Ascenseur capsule alu et verre années 60"
    def box(ident: str, material: str, pos: list[float], size: list[float], parent: str = lift_parent) -> None:
        items.append({"id": ident, "parent": parent, "geometry": "unit_box", "material": material,
                      "position": pos, "size": size, "rotationY": 0})

    # Shaft frame and glazed sides. The inner side is deliberately left open
    # except for two retracted glass door leaves at each landing.
    for ix, dx in enumerate((-half_x, half_x)):
        for iz, dz in enumerate((-half_z, half_z)):
            box(f"v611_shaft_post_{ix}_{iz}", metal,
                [lift_x + dx, (base_y + top_y) / 2, lift_z + dz], [0.16, shaft_h, 0.16])
    for y, tag in ((base_y + 0.12, "sill"), (top_y - 0.12, "crown")):
        box(f"v611_shaft_ring_x0_{tag}", metal, [lift_x, y, lift_z - half_z], [3.56, 0.18, 0.16])
        box(f"v611_shaft_ring_x1_{tag}", metal, [lift_x, y, lift_z + half_z], [3.56, 0.18, 0.16])
        box(f"v611_shaft_ring_z0_{tag}", metal, [lift_x - half_x, y, lift_z], [0.16, 0.18, 3.26])
        box(f"v611_shaft_ring_z1_{tag}", metal, [lift_x + half_x, y, lift_z], [0.16, 0.18, 3.26])
    box("v611_shaft_glass_front", glass, [lift_x, (base_y + top_y) / 2, lift_z + half_z],
        [3.36, shaft_h - 0.35, 0.055])
    for side, x in (("left", lift_x - half_x), ("right", lift_x + half_x)):
        box(f"v611_shaft_glass_{side}", glass, [x, (base_y + top_y) / 2, lift_z],
            [0.055, shaft_h - 0.35, 3.06])
    # Inner-facing glazed door leaves are held aside, leaving a clear opening.
    for level, y in (("ground", 1.75), ("second", 10.10)):
        for side, dx in (("left", -1.15), ("right", 1.15)):
            box(f"v611_landing_door_{level}_{side}", glass, [lift_x + dx, y, lift_z - half_z],
                [0.86, 2.15, 0.045])
            box(f"v611_landing_door_trim_{level}_{side}", metal,
                [lift_x + dx, y, lift_z - half_z - 0.035], [0.045, 2.15, 0.045])

    # Ground-floor capsule cab, with rounded, polished-metal edge beads.
    cab_y, cab_h, cab_w, cab_d = 1.82, 2.42, 2.08, 2.18
    items.append({"id": "v611_cab_floor", "parent": lift_parent, "geometry": "unit_sphere",
                  "material": metal, "position": [lift_x, 0.70, lift_z],
                  "size": [2.24, 0.15, 2.36], "rotationY": 0})
    box("v611_cab_glass_front", glass, [lift_x, cab_y, lift_z + cab_d / 2],
        [cab_w - 0.18, cab_h, 0.045])
    for side, x in (("left", lift_x - cab_w / 2), ("right", lift_x + cab_w / 2)):
        box(f"v611_cab_glass_{side}", glass, [x, cab_y, lift_z], [0.045, cab_h, cab_d - 0.18])
        box(f"v611_cab_post_{side}", metal, [x, cab_y, lift_z - cab_d / 2], [0.08, cab_h + 0.14, 0.08])
    items.append({"id": "v611_cab_midband", "parent": lift_parent, "geometry": "unit_sphere",
                  "material": metal, "position": [lift_x, 2.82, lift_z],
                  "size": [2.30, 0.08, 2.40], "rotationY": 0})
    items.append({"id": "v611_cab_crown", "parent": lift_parent, "geometry": "unit_sphere",
                  "material": metal, "position": [lift_x, 3.12, lift_z],
                  "size": [2.20, 0.22, 2.30], "rotationY": 0})
    # A low amber interior light gives the aluminum/glass capsule a restrained
    # 1960s instrument-panel accent without adding another emissive mesh type.
    for i, dx in enumerate((-0.60, 0.60), 1):
        box(f"v611_cab_light_{i}", "lamp", [lift_x + dx, 2.94, lift_z - 0.72], [0.10, 0.05, 0.06])

    data["instances"] = items
    files[instances_path] = _json(data)

    report = {
        "revision": revision,
        "stairsRemoved": len(removed_stairs),
        "wallReturnsRemoved": len(removed_walls),
        "westLockerPartsRemoved": len(removed_lockers),
        "floatingRoofBeamsRemoved": sorted(found_beams),
        "indoorPlantPartsReplaced": len(plants),
        "liftCenter": [lift_x, lift_z],
        "liftStops": [0.60, 9.0],
        "liftLandingDoorsFace": "building interior (-Z)",
        "secondFloorLeftRoute": "continuous at y=9.164 m",
        "thirdFloorOpening": "closed at y=13.664 m",
    }
    files[prefix + "reports/interior-lift-v611.json"] = _json(report)

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)
