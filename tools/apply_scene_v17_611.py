"""Rework the west stairwell and add the retrofuturist glass lift."""
from __future__ import annotations

import json
import math


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

    # Replace the selected potted plant with the lift, using the plant's
    # measured footprint as the anchor instead of a guessed world coordinate.
    plants = [item for item in items
              if item.get("id", "").startswith("v601_indoor_plant_4_")]
    if len(plants) < 3:
        raise ValueError(f"V17.612 expected the target plant group; found {len(plants)} parts")
    plant_x = sorted(float(item["position"][0]) for item in plants if len(item.get("position", [])) == 3)
    plant_z = sorted(float(item["position"][2]) for item in plants if len(item.get("position", [])) == 3)
    if len(plant_x) < 3 or len(plant_z) < 3:
        raise ValueError("V17.612 target plant has no usable spatial anchor")
    lift_x = round(plant_x[len(plant_x) // 2], 3)
    lift_z = round(plant_z[len(plant_z) // 2], 3)
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
        ("v611_landing_slab_left", [lift_x - 21.63, 9.164, lift_z + 0.55], [39.66, 0.045, 8.42]),
        ("v611_landing_slab_right", [lift_x + 8.63, 9.164, lift_z + 0.55], [13.66, 0.045, 8.42]),
        ("v611_landing_slab_inner", [lift_x, 9.164, lift_z - 2.68], [3.60, 0.045, 1.96]),
        ("v611_landing_slab_facade", [lift_x, 9.164, lift_z + 3.23], [3.60, 0.045, 3.06]),
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

    # Replace the squared cage with a rounded, faceted Space-Age capsule.
    # The shaft stays inside the floor opening and stops at level two.
    base_y, top_y = 0.64, 11.16
    shaft_h = top_y - base_y
    shaft_mid = (base_y + top_y) / 2.0
    outer_rx, outer_rz, facets = 1.72, 1.58, 12
    glass, aluminum, accent = "prp_window_glass", "v439_gallery_warm", "prp_roof_metal"
    lift_parent = "Interieur/Hall/Ascenseur capsule Space Age alu champagne et verre"

    def add_box(ident: str, material: str, pos: list[float], size: list[float], yaw: float = 0.0) -> None:
        items.append({"id": ident, "parent": lift_parent, "geometry": "unit_box",
                      "material": material, "position": pos, "size": size, "rotationY": yaw})

    def ellipse_point(i: int, count: int, rx: float, rz: float) -> tuple[float, float]:
        angle = 2.0 * math.pi * i / count
        return lift_x + rx * math.cos(angle), lift_z + rz * math.sin(angle)

    def add_ring(tag: str, y: float, rx: float, rz: float, count: int, height: float, material: str) -> None:
        for i in range(count):
            x0, z0 = ellipse_point(i, count, rx, rz)
            x1, z1 = ellipse_point((i + 1) % count, count, rx, rz)
            dx, dz = x1 - x0, z1 - z0
            yaw = math.degrees(math.atan2(-dz, dx))
            add_box(f"v612_{tag}_{i:02d}", material,
                    [(x0 + x1) / 2.0, y, (z0 + z1) / 2.0],
                    [math.hypot(dx, dz) + 0.03, height, 0.13], yaw)

    # Rounded 12-sided tower, with glass facets and narrow champagne-aluminum uprights.
    for i in range(facets):
        x, z = ellipse_point(i, facets, outer_rx, outer_rz)
        add_box(f"v612_shaft_post_{i:02d}", aluminum,
                [x, shaft_mid, z], [0.12, shaft_h - 0.18, 0.12])
    for i in range(facets):
        x0, z0 = ellipse_point(i, facets, outer_rx, outer_rz)
        x1, z1 = ellipse_point((i + 1) % facets, facets, outer_rx, outer_rz)
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        # Inner entrance faces -Z; keep that facet open for the landing doors.
        if cz < lift_z - 1.25 and abs(cx - lift_x) < 0.48:
            continue
        dx, dz = x1 - x0, z1 - z0
        yaw = math.degrees(math.atan2(-dz, dx))
        add_box(f"v612_shaft_glass_{i:02d}", glass,
                [cx, shaft_mid, cz], [math.hypot(dx, dz) - 0.12, shaft_h - 0.42, 0.045], yaw)
    add_ring("shaft_sill", base_y + 0.07, outer_rx, outer_rz, facets, 0.16, aluminum)
    add_ring("shaft_crown", top_y - 0.10, outer_rx, outer_rz, facets, 0.18, aluminum)
    add_ring("shaft_belt", 5.90, outer_rx, outer_rz, facets, 0.055, accent)

    # Paired glass doors face into the building at both served floors.
    for level, y in (("ground", 1.74), ("second", 10.10)):
        for side, dx in (("left", -0.42), ("right", 0.42)):
            add_box(f"v612_landing_door_{level}_{side}", glass,
                    [lift_x + dx, y, lift_z - outer_rz - 0.035], [0.86, 2.16, 0.045])
        for side, dx in (("left", -0.87), ("right", 0.87)):
            add_box(f"v612_landing_jamb_{level}_{side}", aluminum,
                    [lift_x + dx, y, lift_z - outer_rz - 0.08], [0.075, 2.30, 0.10])
        add_box(f"v612_landing_header_{level}", aluminum,
                [lift_x, y + 1.16, lift_z - outer_rz - 0.08], [1.82, 0.09, 0.10])
        add_box(f"v612_landing_sill_{level}", accent,
                [lift_x, y - 1.08, lift_z - outer_rz - 0.08], [1.82, 0.045, 0.10])

    # The car is a smaller oval pod at the ground stop: wraparound glazing,
    # slender metal beads and a matching split-glass entrance.
    cab_rx, cab_rz, cab_facets = 1.18, 1.08, 12
    cab_bottom, cab_top = 0.72, 3.08
    cab_y, cab_h = (cab_bottom + cab_top) / 2.0, cab_top - cab_bottom
    for i in range(cab_facets):
        x, z = ellipse_point(i, cab_facets, cab_rx, cab_rz)
        add_box(f"v612_cab_post_{i:02d}", aluminum, [x, cab_y, z], [0.075, cab_h - 0.10, 0.075])
    for i in range(cab_facets):
        x0, z0 = ellipse_point(i, cab_facets, cab_rx, cab_rz)
        x1, z1 = ellipse_point((i + 1) % cab_facets, cab_rx, cab_rz)
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        if cz < lift_z - 0.85 and abs(cx - lift_x) < 0.32:
            continue
        dx, dz = x1 - x0, z1 - z0
        yaw = math.degrees(math.atan2(-dz, dx))
        add_box(f"v612_cab_glass_{i:02d}", glass,
                [cx, cab_y, cz], [math.hypot(dx, dz) - 0.09, cab_h - 0.20, 0.04], yaw)
    add_ring("cab_base_bead", cab_bottom + 0.08, cab_rx, cab_rz, cab_facets, 0.11, aluminum)
    add_ring("cab_mid_bead", 2.62, cab_rx, cab_rz, cab_facets, 0.09, accent)
    add_ring("cab_crown_bead", cab_top - 0.09, cab_rx, cab_rz, cab_facets, 0.15, aluminum)
    for side, dx in (("left", -0.31), ("right", 0.31)):
        add_box(f"v612_cab_door_{side}", glass,
                [lift_x + dx, 1.82, lift_z - cab_rz - 0.035], [0.64, 2.08, 0.04])
    for side, dx in (("left", -0.67), ("right", 0.67)):
        add_box(f"v612_cab_door_jamb_{side}", aluminum,
                [lift_x + dx, 1.82, lift_z - cab_rz - 0.075], [0.06, 2.22, 0.08])
    add_box("v612_cab_indicator", "lamp",
            [lift_x, 2.87, lift_z - cab_rz - 0.08], [0.42, 0.035, 0.04])

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
        "liftAnchorSource": "median X/Z of the replaced indoor plant group",
        "liftStyle": "rounded 12-facet Space-Age capsule, champagne aluminum and glass",
        "liftStops": [0.60, 9.0],
        "liftLandingDoorsFace": "building interior (-Z)",
        "secondFloorLeftRoute": "continuous at y=9.164 m",
        "thirdFloorOpening": "closed at y=13.664 m",
    }
    files[prefix + "reports/interior-lift-v612.json"] = _json(report)

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _json(scene)
