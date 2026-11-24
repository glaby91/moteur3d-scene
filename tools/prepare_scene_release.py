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
    scene = json.loads(files[scene_path])
    if scene.get("revision") != source["revision"]:
        raise SystemExit("base scene.json revision does not match source-archive.json")
    if release["revision"] in ("V17.606", "V17.607", "V17.608", "V17.609", "V17.610", "V17.611", "V17.612", "V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_plaza_lighting_patch import apply_patch as apply_v606
        apply_v606(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.607", "V17.608", "V17.609", "V17.610", "V17.611", "V17.612", "V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_607 import apply_patch as apply_v607
        apply_v607(files, scene_path, "V17.607")
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.608", "V17.609", "V17.610", "V17.611", "V17.612", "V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_608 import apply_patch as apply_v608
        apply_v608(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.609", "V17.610", "V17.611", "V17.612", "V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_609 import apply_patch as apply_v609
        apply_v609(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.610", "V17.611", "V17.612", "V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_610 import apply_patch as apply_v610
        apply_v610(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.611", "V17.612", "V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_611 import apply_patch as apply_v611
        apply_v611(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.613", "V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_613 import apply_patch as apply_v613
        apply_v613(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.614", "V17.615", "V17.616", "V17.617", "V17.618", "V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_614 import apply_patch as apply_v614
        apply_v614(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.618", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_618 import apply_patch as apply_v618
        apply_v618(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])
    if release["revision"] in ("V17.619", "V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_619 import apply_patch as apply_v619
        apply_v619(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])

    if release["revision"] in ("V17.620", "V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_620 import apply_patch as apply_v620
        apply_v620(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])

    if release["revision"] in ("V17.621", "V17.622", "V17.623"):
        from apply_scene_v17_621 import apply_patch as apply_v621
        apply_v621(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])

    if release["revision"] == "V17.622":
        from apply_scene_v17_622 import apply_patch as apply_v622
        apply_v622(files, scene_path, release["revision"])
        scene = json.loads(files[scene_path])

    if release["revision"] == "V17.623":
        from apply_scene_v17_623 import apply_patch as apply_v623
        apply_v623(files, scene_path, release["revision"])
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
