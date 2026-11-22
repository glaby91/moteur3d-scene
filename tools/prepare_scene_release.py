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


def print_scene_inspection(files: dict[str, bytes]) -> None:
    """Emit scene object transforms relevant to the reported V17.606 anomalies."""
    report: dict[str, object] = {"matchingFiles": [], "matchingInstances": []}
    for name, raw in files.items():
        lower_name = name.lower()
        if any(term in lower_name for term in INSPECTION_TERMS):
            report["matchingFiles"].append(name)
        if not lower_name.endswith(".json") or "/instances/" not in lower_name:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            continue
        instances = data.get("instances", []) if isinstance(data, dict) else []
        for item in instances:
            if not isinstance(item, dict):
                continue
            searchable = " ".join(str(item.get(k, "")) for k in
                                  ("id", "parent", "geometry", "material", "model")).lower()
            if any(term in searchable for term in INSPECTION_TERMS):
                report["matchingInstances"].append({
                    "file": name,
                    "id": item.get("id"),
                    "parent": item.get("parent"),
                    "geometry": item.get("geometry"),
                    "material": item.get("material"),
                    "position": item.get("position"),
                    "size": item.get("size"),
                    "scale": item.get("scale"),
                    "rotation": item.get("rotation"),
                    "rotationY": item.get("rotationY"),
                })
    report["sceneJson"] = json.loads(files["benchmark-civic/scene.json"])
    report["supportingJson"] = {}
    for name, raw in files.items():
        if not name.endswith(".json") or name == "benchmark-civic/scene.json":
            continue
        if (name.endswith("trees-v600-plaza.json")
                or name.endswith("trees-v601-plaza.json")
                or name.endswith("scene-fix-v17.603.json")
                or name.startswith("benchmark-civic/lighting/")):
            try:
                report["supportingJson"][name] = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                pass
        if name.startswith("benchmark-civic/geometry/"):
            try:
                data = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                continue
            encoded = json.dumps(data, ensure_ascii=False).lower()
            if "v604_mosaic_panel_mesh" in encoded or "v604_facade" in encoded:
                report["supportingJson"][name] = data
        print("SCENE_INSPECTION_JSON=" + json.dumps(report, ensure_ascii=False, separators=(",", ":")))


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
    print_scene_inspection(files)
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
