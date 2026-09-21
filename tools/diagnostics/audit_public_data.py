"""Check Git history and release ZIPs for private captures, avatars and user settings."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[2]
PRIVATE_SUFFIXES={'.avi','.mp4','.mov','.mkv','.webm','.wmv','.mpg','.mpeg','.tcap','.fbx','.blend','.vrm','.obj','.unity','.prefab'}


def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),*args],cwd=ROOT)


def audit_history(ref):
    failures=[];count=0;media=[]
    for line in git('rev-list','--objects',ref).decode('utf-8').splitlines():
        if ' ' not in line:continue
        oid,name=line.split(' ',1);p=Path(name);count+=1
        if (p.suffix.lower() in PRIVATE_SUFFIXES or name.startswith(('results/','builds/')) or
            p.name in ('ui-settings.json','memo.txt','token.dpapi')):
            failures.append(dict(object=oid,path=name))
        if p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.gif'):
            media.append(dict(object=oid,path=name))
    return dict(ref=ref,objects_with_paths=count,forbidden=failures,images_to_review=media)


def audit_zip(path):
    failures=[];images=[];runtime_images=[]
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            p=Path(name);rel='/'.join(p.parts[1:])
            # .obj files in compiler packages are not distributed by this build.
            if p.suffix.lower() in PRIVATE_SUFFIXES or rel.startswith(('results/','logs/','avatars/')):
                failures.append(name)
            if p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.gif'):
                original=Path(sys.base_prefix)/rel.removeprefix('runtime/')
                if (rel.startswith('runtime/tcl/') and original.is_file() and
                    hashlib.sha256(z.read(name)).digest()==hashlib.sha256(original.read_bytes()).digest()):
                    runtime_images.append(name)
                else:images.append(name)
            if p.name=='ui-settings.json':
                data=json.loads(z.read(name))
                if data!={'avatar':'avatars/avatar.tcap','camera':0}:failures.append(name+': non-default settings')
            if p.suffix=='.unitypackage':
                with tarfile.open(fileobj=io.BytesIO(z.read(name)),mode='r:gz') as package:
                    for member in package:
                        if member.name.endswith('/pathname'):
                            asset=package.extractfile(member).read().decode('utf-8')
                            if Path(asset).suffix not in ('.cs','.txt'):
                                failures.append(name+': '+asset)
        bad=z.testzip()
        if bad:failures.append('CRC '+bad)
    return dict(path=str(path),forbidden=failures,images_to_review=images,
                python_tcl_images_matching_installed_original=runtime_images)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ref',default='HEAD');p.add_argument('--release',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=dict(history=audit_history(a.ref),archives=[])
    if a.release:
        release=json.loads((a.release/'release-report.json').read_text(encoding='utf-8'))
        report['archives']=[audit_zip(a.release/v['name']) for v in release['assets']]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    bad=report['history']['forbidden']+report['history']['images_to_review']
    for archive in report['archives']:bad+=archive['forbidden']+archive['images_to_review']
    print(json.dumps(dict(status='review-required' if bad else 'passed',items=len(bad),report=str(a.output))))
    if bad:raise SystemExit(1)


if __name__=='__main__':main()
