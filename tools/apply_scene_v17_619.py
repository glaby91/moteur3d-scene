"""Expand the lift's marble floor area to three times its previous coverage."""
from __future__ import annotations

import json
import math


def _dump(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _set_annulus_radii(mesh: dict, outer: float, inner: float, texture_span: float) -> None:
    vertices = mesh.get("vertices", [])
    uvs = mesh.get("uv", [])
    segments = 48
    if len(vertices) != segments * 4 or len(uvs) != len(vertices):
        raise ValueError(f"Unexpected V17.619 annulus mesh layout: {mesh.get('id')}")
    for i in range(len(vertices)):
        layer = i // (2 * segments)
        ring = (i % (2 * segments)) // segments
        step = i % segments
        radius = outer if ring == 0 else inner
        angle = math.tau * step / segments
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        vertices[i] = [x, float(vertices[i][1]), z]
        # Keep marble veining at roughly the same physical scale as before.
        uvs[i] = [x / texture_span + .5, z / texture_span + .5]


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    geometry_path = prefix + "geometry/v614-lift-details.json"
    geometry = json.loads(files[geometry_path])
    meshes = {mesh.get("id"): mesh for mesh in geometry.get("meshes", [])}
    if "geo_v614_lift_marble_annulus" not in meshes or "geo_v614_lift_brass_inlay" not in meshes:
        raise ValueError("V17.619 requires the registered V17.614 lift detail meshes")

    # Old annulus area: pi * (2.42^2 - 1.39^2). Keep its inner edge fixed and
    # solve for the outer radius that gives exactly three times that area.
    inner = 1.39
    old_outer = 2.42
    new_outer = math.sqrt(inner * inner + 3.0 * (old_outer * old_outer - inner * inner))
    _set_annulus_radii(meshes["geo_v614_lift_marble_annulus"], new_outer, inner, 2 * old_outer)

    # Widen the slim champagne border in place at the new outside edge.
    _set_annulus_radii(meshes["geo_v614_lift_brass_inlay"], new_outer + .033, new_outer + .003, 2 * old_outer)
    files[geometry_path] = _dump(geometry)

    report_path = prefix + "reports/interior-lift-v618.json"
    if report_path in files:
        report = json.loads(files[report_path])
        report["marbleInnerRadiusMeters"] = inner
        report["marbleOuterRadiusMeters"] = round(new_outer, 4)
        report["marbleSurfaceAreaMultiplier"] = 3.0
        report["marbleSurfaceAreaSquareMeters"] = round(math.pi * (new_outer ** 2 - inner ** 2), 3)
        files[report_path] = _dump(report)
    files[prefix + "reports/lift-marble-v619.json"] = _dump({
        "revision": revision,
        "areaMultiplier": 3.0,
        "innerRadiusMeters": inner,
        "outerRadiusMeters": round(new_outer, 4),
        "brassInlay": "moved to the new outer edge",
        "geometry": "annular marble paving remains flush with the ground-floor datum",
    })

    scene = json.loads(files[scene_path])
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)
