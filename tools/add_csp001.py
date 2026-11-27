#!/usr/bin/env python3
"""Optional CSP001 sidecars, generated only after the final scene patches."""
from __future__ import annotations
import hashlib
import json
import stat
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

BVH_NAME = "csp001-bvh.bin"
CATALOG_NAME = "zreflect-candidates.json"
MAX_CACHE = 128 * 1024 * 1024

def extract_scene(archive: Path, root: Path) -> None:
    with zipfile.ZipFile(archive) as src:
        names = set()
        for info in src.infolist():
            name = info.filename
            path = PurePosixPath(name)
            canonical = name.rstrip("/").casefold()
            if (path.is_absolute() or any(part in ("", ".", "..") or ":" in part for part in path.parts)
                    or "\\" in name or "\x00" in name or canonical in names
                    or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError(f"Unsafe or duplicate archive member: {name}")
            names.add(canonical)
        src.extractall(root)

def verify_sidecars(root: Path, revision: str) -> list[Path]:
    bvh = root / "precomputed" / BVH_NAME
    catalogue = root / "precomputed" / CATALOG_NAME
    if not 84 <= bvh.stat().st_size <= MAX_CACHE:
        raise ValueError("CSP001 BVH size out of range")
    raw = bvh.read_bytes()
    tag, schema, p, n, m = struct.unpack_from("<5I", raw)
    if (tag != 0x43535031 or schema != 1 or not (0 < p <= 12_000_000)
            or not (0 < m <= n <= 2*p) or len(raw) != 84+4*p+41*n+56*m
            or hashlib.sha256(raw[:-32]).digest() != raw[-32:]):
        raise ValueError("Invalid CSP001 BVH header, size or digest")
    if not 0 < catalogue.stat().st_size <= MAX_CACHE:
        raise ValueError("Invalid optical catalogue size")
    data = json.loads(catalogue.read_text(encoding="utf-8"))
    if (data.get("schema") != 1 or data.get("revision") != revision
            or data.get("status") != "diagnostic-only"
            or any(not isinstance(data.get(key), list) for key in ("objects", "planes", "lights"))):
        raise ValueError("Invalid Z-Reflect catalogue")
    return [bvh, catalogue]

def repackage(archive: Path, root: Path, files: list[Path], metadata: dict) -> None:
    tmp = archive.with_name(archive.name + ".csp.tmp")
    names = {path.relative_to(root).as_posix(): path for path in files}
    manifest = (json.dumps(metadata, indent=2) + "\n").encode("utf-8")
    try:
        with zipfile.ZipFile(archive) as src, zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as dst:
            for info in src.infolist():
                if info.filename == "SCENE_VERSION.json" or info.filename in names:
                    continue
                dst.writestr(info, src.read(info))
            for name, path in names.items():
                dst.write(path, name)
            dst.writestr("SCENE_VERSION.json", manifest)
        with zipfile.ZipFile(tmp) as check:
            if check.testzip() is not None or not set(names).issubset(check.namelist()):
                raise ValueError("CSP001 final ZIP verification failed")
        tmp.replace(archive)
    finally:
        tmp.unlink(missing_ok=True)

def add_precomputed(archive: Path, manifest_path: Path, compiler: Path, engine_commit: str) -> None:
    if not compiler.is_file():
        raise FileNotFoundError(f"CSP001 executable not found: {compiler}")
    if len(engine_commit) != 40 or any(c not in "0123456789abcdef" for c in engine_commit):
        raise ValueError("Pin the precompiler to a full lowercase engine commit SHA")
    metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    if metadata.get("scene") != "benchmark-civic/scene.json":
        raise ValueError("Unexpected scene path")
    with tempfile.TemporaryDirectory(prefix="csp001-") as temp:
        root = Path(temp)
        extract_scene(archive, root)
        scene = root / metadata["scene"]
        for name in (BVH_NAME, CATALOG_NAME):
            (scene.parent / "precomputed" / name).unlink(missing_ok=True)
        subprocess.run([str(compiler.resolve()), str(scene)], check=True, timeout=1800)
        files = verify_sidecars(scene.parent, metadata["revision"])
        metadata["precomputed"] = {
            "schema": 1, "engineCommit": engine_commit,
            "files": [{"path": path.relative_to(root).as_posix(),
                       "sizeBytes": path.stat().st_size,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in files],
        }
        repackage(archive, root, files, metadata)
    temp_manifest = manifest_path.with_suffix(".json.csp.tmp")
    temp_manifest.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    temp_manifest.replace(manifest_path)
