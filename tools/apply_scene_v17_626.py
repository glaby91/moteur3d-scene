#!/usr/bin/env python3
"""Fix the non-power-of-two PBR mip resolution in the V17.625 truck sign."""
from __future__ import annotations
import json


def _dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    prefix = scene_path.rsplit("/", 1)[0] + "/"
    pbr_path = prefix + "pbr/camion-icecream-v17-625.json"
    if pbr_path not in files:
        raise ValueError("V17.625 truck PBR material file is missing")
    pbr = json.loads(files[pbr_path])
    sign = next((entry for entry in pbr.get("sets", []) if entry.get("id") == "tex_cse_icecream_side_sign"), None)
    if sign is None:
        raise ValueError("V17.625 truck side-sign PBR set is missing")
    sign["resolution"] = 1024
    stripe = next((entry for entry in pbr.get("sets", []) if entry.get("id") == "tex_cse_icecream_accent_stripe"), None)
    if stripe is None:
        raise ValueError("V17.625 truck accent-stripe PBR set is missing")
    stripe["resolution"] = 64
    pbr["textureResolutionTarget"] = 1024
    sign["status"] = "V17.626 corrected power-of-two mip resolution; artwork is resampled by the engine"
    files[pbr_path] = _dump(pbr)

    scene = json.loads(files[scene_path])
    scene["name"] = "CSE WARP V17.626 — Complexe aquatique et place avec camion de glaces"
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)

    report_path = prefix + "reports/camion-icecream-v625.json"
    report = json.loads(files[report_path])
    report["sceneRevision"] = revision
    report["liveryMipResolution"] = 1024
    report["mipResolutionValidation"] = "power of two, accepted by the renderer"
    files[report_path] = _dump(report)
    files[prefix + "README-CAMION-GLACES-V17.626.txt"] = (
        "CAMION DE GLACES — SCÈNE V17.626\n\n"
        "Correctif de la résolution de mipmaps du panneau latéral : la valeur est maintenant 1024,\n"
        "une puissance de deux acceptée par le moteur. L’image originale est rééchantillonnée\n"
        "par le moteur pour construire la texture. Les dimensions, le placement et la livrée\n"
        "du camion restent ceux de V17.625.\n"
    ).encode("utf-8")
