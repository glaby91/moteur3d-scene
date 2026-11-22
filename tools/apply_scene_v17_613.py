"""Move the capsule lift into the existing west stairwell opening."""
from __future__ import annotations

import json
import math


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    instances_path = prefix + "instances/v442-corrections.json"
    data = json.loads(files[instances_path])
    items = data.get("instances", [])

    # V17.612 used the displaced plant as its anchor. The architectural opening
    # is the former west stairwell: 3.1 m wide, centered at x=-40, z=-34.
    wrong_ids = ("v611_landing_slab_", "v612_", "v611_left_balcony_walkway")
    items = [item for item in items if not item.get("id", "").startswith(wrong_ids)
             and not item.get("id", "").startswith("v601_indoor_plant_4_")
             and item.get("id") != "v439_floor_deck_3"]

    # Restore the uncut east lobby floor; its cutout was tied to the mistaken
    # plant anchor and must not remain after relocating the shaft.
    items.append({
        "id": "v439_floor_deck_3", "parent": "Interieur/Galeries/Sols des niveaux",
        "geometry": "unit_box", "material": "v439_gallery_warm",
        "position": [0.0, 9.164, -9.45], "size": [56.92, 0.025, 8.42], "rotationY": 0,
    })

    # The former stairwell is nearly 20 m long. Close its unused ends at level
    # two while leaving only the lift footprint open; this creates continuous
    # floor links to both side galleries instead of an exposed slit beside it.
    for ident, z, depth in (
        ("v613_landing_link_north", -39.61, 8.66),
        ("v613_landing_link_south", -28.39, 8.66),
    ):
        items.append({
            "id": ident, "parent": "Interieur/Galeries/Palier continu autour de la trémie ascenseur",
            "geometry": "unit_box", "material": "v439_gallery_warm",
            "position": [-40.0, 9.164, z], "size": [3.1, 0.025, depth], "rotationY": 0,
        })

    # Reintroduce the plant that was removed only because of the bad anchor.
    # It remains at its original place behind the glazed facade.
    plant_parts = [
        ("snakeplant_03_snakeplant_leave_0_0", "shapespark_snakeplant_03_0", "shapespark_plant_mat_2"),
        ("snakeplant_03_soil_0_0", "shapespark_snakeplant_03_1", "shapespark_plant_mat_1"),
        ("snakeplant_03_pot_03_0_0", "shapespark_snakeplant_03_2", "shapespark_plant_mat_6"),
    ]
    for suffix, geometry, material in plant_parts:
        items.append({
            "id": "v601_indoor_plant_4_" + suffix,
            "parent": "Architecture/Interieur/Plantes GLB Shapespark derrière la baie vitrée",
            "geometry": geometry, "material": material,
            "position": [13.0, 0.56, -8.0], "size": [2.45, 2.45, 2.45], "rotationY": 116,
        })

    # Keep the third-floor stair opening closed as requested. Remove any
    # second-floor bridge that would cover the lift's actual shaft opening.
    items = [item for item in items if item.get("id") != "v611_left_balcony_walkway"]

    lift_x, lift_z = -40.0, -34.0
    base_y, top_y = 0.15, 11.35
    shaft_h = top_y - base_y
    shaft_mid = (base_y + top_y) / 2.0
    rx, rz, facets = 1.30, 1.28, 12  # fits inside the 3.1 m gallery slot
    aluminum, glass, accent = "v439_gallery_warm", "prp_window_glass", "prp_roof_metal"
    parent = "Interieur/Galeries/Ascenseur capsule alu et verre dans trémie ouest"

    def add(ident: str, material: str, pos: list[float], size: list[float], yaw: float = 0.0) -> None:
        items.append({"id": ident, "parent": parent, "geometry": "unit_box", "material": material,
                      "position": pos, "size": size, "rotationY": yaw})

    def point(i: int, r_x: float = rx, r_z: float = rz) -> tuple[float, float]:
        angle = math.tau * i / facets
        return lift_x + r_x * math.cos(angle), lift_z + r_z * math.sin(angle)

    def ring(tag: str, y: float, height: float, material: str, r_x: float = rx, r_z: float = rz) -> None:
        for i in range(facets):
            if i in open_facets:
                continue
            x0, z0 = point(i, r_x, r_z)
            x1, z1 = point((i + 1) % facets, r_x, r_z)
            dx, dz = x1 - x0, z1 - z0
            add(f"v613_{tag}_{i:02d}", material,
                [(x0 + x1) / 2, y, (z0 + z1) / 2], [math.hypot(dx, dz) + .03, height, .12],
                math.degrees(math.atan2(-dz, dx)))

    # The two doors face opposite gallery sides (+X/-X). Leave those facets
    # open and glaze the rest, so the shaft visibly sits inside the floor void.
    open_facets = {0, 5, 6, 11}
    for i in range(facets):
        if i in (0, 6):
            continue
        x, z = point(i)
        add(f"v613_shaft_post_{i:02d}", aluminum, [x, shaft_mid, z], [.11, shaft_h - .16, .11])
    for i in range(facets):
        if i in open_facets:
            continue
        x0, z0 = point(i)
        x1, z1 = point((i + 1) % facets)
        dx, dz = x1 - x0, z1 - z0
        add(f"v613_shaft_glass_{i:02d}", glass,
            [(x0 + x1) / 2, shaft_mid, (z0 + z1) / 2],
            [math.hypot(dx, dz) - .10, shaft_h - .32, .045], math.degrees(math.atan2(-dz, dx)))
    ring("shaft_sill", base_y + .08, .16, aluminum)
    ring("shaft_crown", top_y - .09, .18, aluminum)
    ring("shaft_mid_band", 5.8, .06, accent)

    # Twin opposing landing portals at ground and level two, aligned with both
    # gallery edges. Their lower edges meet the floor surfaces.
    floors = (("ground", 1.20, .05), ("second", 10.24, 9.164))
    for level, y, floor_y in floors:
        for side in (-1, 1):
            x = lift_x + side * (rx + .035)
            for leaf, dz in (("a", -.34), ("b", .34)):
                add(f"v613_landing_door_{level}_{side}_{leaf}", glass,
                    [x, y, lift_z + dz], [.045, 2.08, .66])
            for dz in (-.78, .78):
                add(f"v613_landing_jamb_{level}_{side}_{dz}", aluminum,
                    [x, y, lift_z + dz], [.10, 2.24, .075])
            add(f"v613_landing_header_{level}_{side}", aluminum,
                [x, y + 1.13, lift_z], [.10, .08, 1.65])
            add(f"v613_landing_sill_{level}_{side}", accent,
                [x, y - 1.05, lift_z], [.16, .045, 1.65])
            # Short flush bridges span the 0.25 m reveal between shaft and
            # existing side gallery floors, at both served levels.
            bridge_x = lift_x + side * 1.48
            add(f"v613_bridge_{level}_{side}", aluminum,
            [bridge_x, floor_y + .0125, lift_z], [.42, .025, 1.52])

    # Compact glass car held at ground level for the static scene preview.
    # Renderer-independent geometry leaves the opposing portals unobstructed.
    car_rx, car_rz, car_bottom, car_top = 1.02, .98, .18, 2.42
    car_mid, car_h = (car_bottom + car_top) / 2, car_top - car_bottom
    for i in range(facets):
        if i in (0, 6):
            continue
        x, z = point(i, car_rx, car_rz)
        add(f"v613_car_post_{i:02d}", aluminum, [x, car_mid, z], [.07, car_h - .08, .07])
    for i in range(facets):
        if i in open_facets:
            continue
        x0, z0 = point(i, car_rx, car_rz)
        x1, z1 = point((i + 1) % facets, car_rx, car_rz)
        dx, dz = x1 - x0, z1 - z0
        add(f"v613_car_glass_{i:02d}", glass,
            [(x0 + x1) / 2, car_mid, (z0 + z1) / 2],
            [math.hypot(dx, dz) - .08, car_h - .16, .035], math.degrees(math.atan2(-dz, dx)))
    ring("car_base", .28, .10, aluminum, car_rx, car_rz)
    ring("car_crown", car_top - .08, .14, aluminum, car_rx, car_rz)
    for side in (-1, 1):
        x = lift_x + side * (car_rx + .02)
        for leaf, dz in (("a", -.29), ("b", .29)):
            add(f"v613_car_door_{side}_{leaf}", glass, [x, 1.22, lift_z + dz], [.035, 2.02, .56])

    data["instances"] = items
    files[instances_path] = _dump(data)
    report = {
        "revision": revision,
        "anchor": "existing west stairwell opening, measured from split level-2 gallery decks",
        "liftCenterXZ": [lift_x, lift_z], "openingWidth": 3.1,
        "doors": "opposed on both gallery sides (+X and -X)",
        "servedLandingsY": [0.05, 9.164], "shaftTopY": top_y,
        "eastLobbyFloor": "restored; previous plant-based cutout removed",
        "thirdFloorOpening": "closed by V17.612 closure panel",
        "secondFloorOpening": "kept clear around the lift shaft",
    }
    files[prefix + "reports/interior-lift-v613.json"] = _dump(report)
    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
