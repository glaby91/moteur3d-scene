"""Prepare and verify the experimental Reflect scene without altering the stable publisher."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def dump(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def require(ok, message):
    if not ok: raise ValueError(message)
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f, "sha256").hexdigest()

def prepare(work, source_commit, engine_commit):
    cfg=load(ROOT/"reflect-release.json")
    require(cfg["engineCommit"]==engine_commit, "Unexpected engine compiler commit")
    base=work/"base"
    subprocess.run([sys.executable, str(ROOT/"tools/prepare_scene_release.py"), "--output", str(base),
                    "--source-commit", source_commit, "--repository", "glaby91/moteur3d-scene"], check=True)
    require(load(base/"SCENE_VERSION.json")["revision"]==cfg["baseRevision"], "Wrong stable scene base")
    stage=work/"stage"
    require(not stage.exists(), "Stage must be fresh")
    stage.mkdir(parents=True)
    with zipfile.ZipFile(base/"V17-scene.zip") as z:
        require(z.testzip() is None, "Bad base ZIP")
        z.extractall(stage)
    scene=stage/"benchmark-civic/scene.json"
    doc=load(scene)
    require(doc["revision"]==cfg["baseRevision"], "Wrong scene revision")
    if cfg["revision"] in ("V17.632","V17.633"):
        from apply_scene_v17_632 import apply_patch
        apply_patch(scene)
        doc=load(scene)
    if cfg["revision"]=="V17.633":
        from apply_scene_v17_633 import apply_patch
        apply_patch(scene)
        doc=load(scene)
    policy=load(ROOT/cfg["policy"])
    require(policy["sceneRevision"]==cfg["revision"] and policy["sceneTag"]==cfg["tag"], "Policy release mismatch")
    doc["revision"]=doc["sceneVersion"]=cfg["revision"]
    doc["zReflectAuthorPolicy"]=policy
    dump(scene,doc)
    pre=scene.parent/"precomputed"
    pre.mkdir(exist_ok=True)
    # Discard stale inherited files, then generate both caches from final geometry.
    for name in ("csp001-bvh.bin","zreflect-candidates.json","zreflect-index.json","manifest.json"):
        (pre/name).unlink(missing_ok=True)
    dump(pre/"zreflect-policy.json",policy)
    dump(pre/"reflection-probes.json",{"schema":1,"sceneRevision":cfg["revision"],"probes":policy["sharedProbes"]})
    manifest={"schema":1,"revision":cfg["revision"],"scene":"benchmark-civic/scene.json",
              "sourceCommit":source_commit,"repository":"glaby91/moteur3d-scene",
              "engineCommit":engine_commit,"channel":"reflect","tag":cfg["tag"]}
    dump(stage/"SCENE_VERSION.json",manifest)
    dump(scene.parent/"SCENE_VERSION.json",manifest)
    print("Reflect source prepared:",scene)

def package(work, output):
    stage=work/"stage"
    cfg=load(ROOT/"reflect-release.json")
    meta=load(stage/"SCENE_VERSION.json")
    scene=stage/meta["scene"]
    pre=scene.parent/"precomputed"
    require(meta["engineCommit"]==cfg["engineCommit"] and meta["revision"]==cfg["revision"], "Wrong final metadata")
    require(load(scene)["zReflectAuthorPolicy"]==load(pre/"zreflect-policy.json"),"Policy mismatch")
    catalogue=load(pre/"zreflect-candidates.json")
    require(catalogue["revision"]==cfg["revision"] and catalogue["catalogRevision"]==4, "Bad catalogue revision")
    require(catalogue["counts"]["eligibleObjects"]==121 and catalogue["counts"]["planes"]==5, "Unexpected scene optical counts")
    require(all(o["authorized"] and o["material"]!="v614_lift_blue_glass" for o in catalogue["objects"]), "Wrong author selection")
    require(len(catalogue["cameraSimulation"])==29 and all(v["indexParity"] and v["selectedUncapped"]<=2 for v in catalogue["cameraSimulation"]), "Camera regression")
    runtime=load(pre/"zreflect-index.json")["payload"]
    require(runtime["schema"]==2 and len(runtime["planes"])==5 and runtime["nodes"] and len(runtime["order"])==5,"Invalid runtime glass index")
    files={}
    for name in ("csp001-bvh.bin","zreflect-candidates.json","zreflect-index.json","zreflect-policy.json","reflection-probes.json"):
        path=pre/name
        require(path.is_file() and path.stat().st_size>0, "Missing "+name)
        files[name]={"sizeBytes":path.stat().st_size,"sha256":sha(path)}
    dump(pre/"manifest.json",{"schema":1,"sceneRevision":meta["revision"],"engineCommit":meta["engineCommit"],"files":files,
         "sharedProbeRendering":"not-implemented","runtimeOpticalIndex":"validated-native-roundtrip"})
    output.mkdir(parents=True,exist_ok=True)
    dump(output/"SCENE_VERSION.json",meta)
    archive=output/"V17-scene.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(stage.rglob("*")):
            if path.is_file(): z.write(path,path.relative_to(stage).as_posix())
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None, "Final ZIP CRC failed")
        for name in files:
            h=hashlib.sha256()
            with z.open("benchmark-civic/precomputed/"+name) as f:
                for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
            require(h.hexdigest()==files[name]["sha256"], "ZIP sidecar hash mismatch")
    print("Published archive bytes:",archive.stat().st_size,"SHA256:",sha(archive))
    print("Validated annexes:",json.dumps(files,indent=2))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["prepare","package"])
    p.add_argument("--work",required=True,type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--source-commit")
    p.add_argument("--engine-commit")
    a=p.parse_args()
    if a.mode=="prepare": prepare(a.work,a.source_commit,a.engine_commit)
    else: package(a.work,a.output)
if __name__=="__main__": main()
