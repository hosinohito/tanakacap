"""Prepare an isolated Unity Editor comparison; SDK and avatar stay in ignored results."""
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"results/physbone-reference"
PROJECT=BASE/"project"
PACKAGES={
 "com.vrchat.base":"fbfb3e7a38778dcb55d7a860286819e6f0726d10d5039f61474bd1b9c629029e",
 "com.vrchat.avatars":"03bdea0c24257070f0e7a73c9033742a1ce0f67463b12a6c2ad29608b1f33a77"}
def main():
    BASE.mkdir(parents=True,exist_ok=True)
    for name,digest in PACKAGES.items():
        archive=BASE/(name+".zip")
        if not archive.exists():
            urllib.request.urlretrieve(f"https://github.com/vrchat/packages/releases/download/3.10.5/{name}-3.10.5.zip",archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:
            raise RuntimeError("SDK archive SHA256 mismatch: "+name)
        target=PROJECT/"Packages"/name
        target.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                if not (target/item.filename).resolve().is_relative_to(target.resolve()):
                    raise RuntimeError("Unsafe archive path")
            z.extractall(target)
    assets=PROJECT/"Assets/Comparison"
    (assets/"Editor").mkdir(parents=True,exist_ok=True)
    (PROJECT/"ProjectSettings").mkdir(exist_ok=True)
    source=ROOT/"unity/TanakaCap"
    shutil.copy2(source/"ProjectSettings/ProjectVersion.txt",PROJECT/"ProjectSettings/ProjectVersion.txt")
    shutil.copytree(source/"Assets/HAOLAN",PROJECT/"Assets/HAOLAN",dirs_exist_ok=True)
    shutil.copy2(source/"Assets/HAOLAN.meta",PROJECT/"Assets/HAOLAN.meta")
    shutil.copytree(source/"Packages/jp.lilxyzw.liltoon",PROJECT/"Packages/jp.lilxyzw.liltoon",dirs_exist_ok=True)
    for name in ("AvatarPackage.cs","SecondaryMotion.cs","Editor/SecondaryMotionExporter.cs"):
        shutil.copy2(source/"Assets/TanakaCap"/name,assets/name)
    for script in (ROOT/"tools/physbone-reference").glob("*.cs"):
        shutil.copy2(script,assets/("Editor" if script.name=="PhysReferenceSetup.cs" else "")/script.name)
    manifest=json.loads((source/"Packages/manifest.json").read_text(encoding="utf-8"))
    manifest["dependencies"].update({name:"file:"+name for name in PACKAGES})
    manifest["dependencies"]["com.unity.test-framework"]="1.1.33"
    for module in ("audio","ui","uielements","unitywebrequest","unitywebrequesttexture","unitywebrequestaudio",
                   "unitywebrequestassetbundle","xr","video","director","particlesystem","terrain",
                   "physics2d","androidjni","cloth","vehicles","terrainphysics","wind","subsystems"):
        manifest["dependencies"]["com.unity.modules."+module]="1.0.0"
    (PROJECT/"Packages/manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(PROJECT)
if __name__=="__main__": main()
