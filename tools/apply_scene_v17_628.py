#!/usr/bin/env python3
"""Fix the V17.627 truck glazing material-to-PBR reference."""
from __future__ import annotations

import json


def _dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def apply_patch(files: dict[str, bytes], scene_path: str, revision: str) -> None:
    path = scene_path.rsplit("/", 1)[0] + "/materials/camion-icecream-v17-627.json"
    if path not in files:
        raise ValueError("V17.627 truck material library is missing")
    library = json.loads(files[path])
    material = next(
        (item for item in library.get("materials", [])
         if item.get("id") == "cse_icecream_window_glass"),
        None,
    )
    if material is None:
        raise ValueError("V17.627 truck window-glass material is missing")
    material["textureSet"] = "tex_cse_icecream_window_glass"
    files[path] = _dump(library)

    scene = json.loads(files[scene_path])
    scene["name"] = "CSE WARP V17.628 — Référence PBR des vitres corrigée"
    scene["revision"] = revision
    scene["sceneVersion"] = revision
    files[scene_path] = _dump(scene)

    report_path = scene_path.rsplit("/", 1)[0] + "/reports/camion-icecream-v625.json"
    report = json.loads(files[report_path])
    report["sceneRevision"] = revision
    report["windowGlassTextureSet"] = "tex_cse_icecream_window_glass"
    report["windowGlassTextureSetValidated"] = True
    files[report_path] = _dump(report)

    files[scene_path.rsplit("/", 1)[0] + "/README-CAMION-GLACES-V17.628.txt"] = (
        "CAMION DE GLACES — SCÈNE V17.628\n\n"
        "Correctif de la référence PBR du matériau des vitres : après le renommage du jeu de "
        "textures en tex_cse_icecream_window_glass, le matériau utilise maintenant ce même identifiant.\n"
        "Le générateur de package valide désormais chaque référence textureSet de chaque matériau "
        "contre les bibliothèques PBR complètes avant de produire l'archive.\n"
        "Les autres corrections du camion de la V17.627 sont conservées.\n"
    ).encode("utf-8")
