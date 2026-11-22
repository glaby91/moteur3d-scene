#!/usr/bin/env python3
"""Reassemble the chunked scene archive and create the immutable release asset."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSPECTION_TERMS = (
    "bench", "banc", "tree", "arbre", "light", "lamp", "lum", "mosaic",
    "mosai", "facade", "façade", "beam", "poutre", "garden", "jardin",
    "planter", "bac", "root", "racine",
)


def print_scene_inspection(files: dict[str, bytes], output: Path) -> None:
    """Write a compact inspection of objects involved in the reported anomalies."""
    wanted = ("banc ovale béton/assise", "banc ovale béton/piétement",
              "banc ovale béton/v4b dossier continu")
    report: dict[str, object] = {"facade": [], "bench": [], "trees": [],
                                  "groundLights": [], "scene": {},
                                  "treeReports": {}, "lightingFiles": {},
                                  "mosaicMaterials": []}
    for name, raw in files.items():
        lower = name.lower()
        if not lower.endswith(".json"):
            continue
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            continue
        if name == "benchmark-civic/scene.json":
            report["scene"] = {"revision": data.get("revision"),
                               "sceneVersion": data.get("sceneVersion"),
                               "sectors": data.get("sectors")}
        if name.endswith(("trees-v600-plaza.json", "trees-v601-plaza.json")):
            report["treeReports"][name] = data
        if name.startswith("benchmark-civic/lighting/"):
            report["lightingFiles"][name] = data
        if name.startswith("benchmark-civic/materials/"):
            mats = data.get("materials", []) if isinstance(data, dict) else []
            report["mosaicMaterials"].extend(
                {"file": name, **m} for m in mats
                if "mosaic" in str(m.get("id", "")).lower()
                or "mosai" in str(m.get("id", "")).lower()
                or str(m.get("id", "")).startswith("v604")
            )
        if "/instances/" not in lower or not isinstance(data, dict):
            continue
        for item in data.get("instances", []):
            if not isinstance(item, dict):
                continue
            ident = str(item.get("id", ""))
            parent = str(item.get("parent", ""))
            geom = str(item.get("geometry", ""))
            rec = {"file": name, "id": ident, "parent": parent,
                   "geometry": geom, "material": item.get("material"),
                   "position": item.get("position"), "size": item.get("size"),
                   "rotationY": item.get("rotationY")}
            if ident.startswith("v604_facade_mosaic") or "Piliers mosaique de facade" in parent:
                report["facade"].append(rec)
            elif any(parent.lower().endswith(t) for t in wanted):
                report["bench"].append(rec)
            elif ident.startswith("v600_garden_tree_"):
                report["trees"].append(rec)
            elif ident.startswith("v600_garden_floor_light_"):
                report["groundLights"].append(rec)
    references = []
    for name, raw in files.items():
        for token in (b"v604_mosaic_panel_mesh", b"v604_mosaic_panel", b"v604_sunrise_mosaic"):
            at = raw.find(token)
            if at >= 0:
                snippet = raw[max(0, at - 240):at + 500].decode("utf-8", errors="replace")
                references.append({"file": name, "token": token.decode(), "snippet": snippet})
    report["references"] = references
    summary = {
        "facade": report["facade"], "mosaicMaterials": report["mosaicMaterials"],
        "trees": report["trees"], "treeReports": report["treeReports"],
        "groundLights": report["groundLights"], "lightingFiles": report["lightingFiles"],
        "references": report["references"],
        "benchCounts": {key: sum(1 for x in report["bench"] if x["parent"].endswith("/" + key))
                        for key in ("Assise", "Piétement", "V4b Dossier continu")},
        "benchSamples": report["bench"][:4],
    }
    print("SCENE_INSPECTION_SUMMARY=" + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    output.mkdir(parents=True, exist_ok=True)
    (output / "scene-inspection.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()

    source = json.loads((ROOT / "source-archive.json").read_text(encoding="utf-8"))
    release = json.loads((ROOT / "scene-release.json").read_text(encoding="utf-8"))
    if source.get("schema") != 1 or release.get("schema") != 1:
        raise SystemExit("Unsupported scene package manifest schema")
    if source.get("revision") != release.get("baseRevision", source.get("revision")):
        raise SystemExit("Source archive revision does not match release baseRevision")
    if release.get("scene") != "benchmark-civic/scene.json":
        raise SystemExit("Unexpected scene entry point")

    archive_bytes = b"".join((ROOT / "payload" / name).read_bytes() for name in source["parts"])
    if len(archive_bytes) != source.get("sizeBytes"):
        raise SystemExit("Reassembled archive size does not match source-archive.json")
    if hashlib.sha256(archive_bytes).hexdigest() != source.get("sha256"):
        raise SystemExit("Reassembled archive SHA-256 does not match source-archive.json")

    src_zip = zipfile.ZipFile(BytesIO(archive_bytes))
    bad_file = src_zip.testzip()
    if bad_file:
        raise SystemExit(f"Corrupt file inside source archive: {bad_file}")
    scene_path = release["scene"]
    if scene_path not in src_zip.namelist():
        raise SystemExit(f"Missing scene entry point in archive: {scene_path}")
    files = {name: src_zip.read(name) for name in src_zip.namelist()}
    print_scene_inspection(files, args.output)
    scene = json.loads(files[scene_path])
    if scene.get("revision") != source["revision"]:
        raise SystemExit("base scene.json revision does not match source-archive.json")
    if release["revision"] == "V17.606":
        from apply_plaza_lighting_patch import apply_patch
        apply_patch(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if scene.get("revision") != release["revision"]:
        raise SystemExit("Final scene.json revision does not match scene-release.json")

    version = {
        "schema": 1,
        "revision": release["revision"],
        "scene": scene_path,
        "sourceCommit": args.source_commit,
        "repository": args.repository,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    version_path = args.output / "SCENE_VERSION.json"
    version_path.write_text(json.dumps(version, indent=2) + "\n", encoding="utf-8")
    out_archive = args.output / "V17-scene.zip"
    with zipfile.ZipFile(out_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        for name, content in files.items():
            if name == "SCENE_VERSION.json":
                continue
            dst.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        dst.writestr("SCENE_VERSION.json", version_path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(out_archive) as result:
        bad_file = result.testzip()
        if bad_file or scene_path not in result.namelist():
            raise SystemExit(f"Invalid final scene release archive: {bad_file or scene_path}")
    print(f"Verified scene release: {release['revision']} (base {source['revision']}, {source['sizeBytes']} bytes)")


if __name__ == "__main__":
    main()
