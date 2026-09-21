"""Allowlisted portable distribution, manifests, notices and size-bounded ZIPs."""
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from audit_release_licenses import audit

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def run(version,publishable=False):
    if not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z._-]{0,60}',version):raise ValueError('Invalid version')
    config=json.loads((ROOT/'release/config.json').read_text(encoding='utf-8'))
    model_lock=json.loads((ROOT/'release/models.lock.json').read_text(encoding='utf-8'))
    for relative,expected in model_lock.items():
        if sha(ROOT/relative)!=expected:raise RuntimeError('Model differs from release lock: '+relative)
    if publishable and (not config['publication_approved'] or config['open_license_items']):
        raise RuntimeError('Final release review pending. Open license items: '+str(config['open_license_items']))
    output=ROOT/'builds/releases'/version
    output.mkdir(parents=True,exist_ok=False)
    stage=output/'TanakaCap';stage.mkdir()
    def copy(source,destination):
        target=stage/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    def tree(source,destination,excluded=()):
        for p in sorted(source.rglob('*')):
            relative=p.relative_to(source)
            if p.is_file() and not any(part in excluded for part in relative.parts) and p.suffix not in ('.pyc','.pdb'):
                copy(p,Path(destination)/relative)
    player=ROOT/'builds/release-player'
    for name in ('TanakaCap.exe','UnityPlayer.dll','UnityCrashHandler64.exe'):copy(player/name,Path('app')/name)
    for name in ('TanakaCap_Data','MonoBleedingEdge'):tree(player/name,Path('app')/name)
    copy(player/'TanakaCapExporter.unitypackage','プラグイン/TanakaCapExporter.unitypackage')
    tree(ROOT/'tanakacap','tanakacap',('__pycache__',))
    for name in ('tracking-settings.json','models/catalog.json','docs/ui-part-costs.json'):copy(ROOT/name,name)
    copy(ROOT/'docs/user_guide.txt','使い方.txt')
    copy(ROOT/'release/THIRD_PARTY.md','ライセンス/README.md')
    copy(ROOT/'release/THIRD_PARTY_TERMS.md','ライセンス/第三者部品の利用条件.md')
    tree(ROOT/'release/notices','ライセンス/notices')
    source_bundle=ROOT/'assets-source/licenses/opencv-ffmpeg-sources.zip'
    if not source_bundle.is_file():
        raise RuntimeError('Run tools/prepare_ffmpeg_sources.py before building')
    copy(source_bundle,'ライセンス/sources/opencv-ffmpeg-sources.zip')
    base=Path(sys.base_prefix)
    for name in ('python.exe','pythonw.exe','python3.dll','python311.dll','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt'):copy(base/name,Path('runtime')/name)
    for name in ('Lib','DLLs','tcl'):tree(base/name,Path('runtime')/name,('site-packages','test','tests','idlelib','ensurepip','__pycache__'))
    locked=dict(line.strip().split('==',1) for line in (ROOT/'requirements.lock.txt').read_text(encoding='utf-8-sig').splitlines() if '==' in line)
    normalize=lambda name:re.sub(r'[-_.]+','-',name).lower()
    locked={normalize(k):v for k,v in locked.items()}
    packages=[]
    for dist in sorted(metadata.distributions(),key=lambda d:d.metadata['Name'].lower()):
        name=dist.metadata['Name']
        if name.lower() in config['excluded_distributions']:continue
        if normalize(name) not in locked:raise RuntimeError('Unapproved runtime dependency: '+name)
        if dist.version!=locked[normalize(name)]:raise RuntimeError('Runtime dependency differs from lock: '+name)
        site=Path(dist.locate_file('')).resolve()
        for entry in dist.files or []:
            source=Path(dist.locate_file(entry)).resolve()
            if not source.is_relative_to(site) or not source.is_file() or source.suffix=='.pyc':continue
            # NVIDIA SDK headers/import libraries are not needed by the prebuilt runtime.
            # Retain dist-info (including original license) and the DLLs unchanged.
            relative=source.relative_to(site)
            if name.lower().startswith('nvidia-') and relative.parts[0]=='nvidia' and source.suffix.lower()!='.dll':continue
            copy(source,Path('runtime/Lib/site-packages')/source.relative_to(site))
            if any(word in source.name.lower() for word in ('license','licence','notice','copying')):
                copy(source,Path('ライセンス/packages')/name/(sha(source)[:12]+'-'+source.name))
        packages.append(dict(name=name,version=dist.version))
    for name in config['models']:
        copy(ROOT/'models'/name/'model.onnx',Path('models')/name/'model.onnx')
        for p in (ROOT/'models'/name).glob('*'):
            if p.suffix=='.json' or 'license' in p.name.lower():copy(p,Path('models')/name/p.name)
    for name in config['root_models']:copy(ROOT/'models'/name,Path('models')/name)
    for name in ('PROCEDURAL_MOTION_LICENSE.txt','THIRD_PARTY.md','HEAD_MODEL_LICENSE.txt'):
        p=ROOT/'docs'/name if (ROOT/'docs'/name).exists() else ROOT/'builds/player'/name
        if p.exists():copy(p,Path('ライセンス')/name)
    copy(base/'LICENSE.txt','ライセンス/Python.txt')
    if (ROOT/'LICENSE').exists():copy(ROOT/'LICENSE','ライセンス/TanakaCap.txt')
    for p in (ROOT/'tanakacap/data').glob('*LICENSE*'):copy(p,Path('ライセンス')/p.name)
    for name,path in [('lilToon','unity/TanakaCap/Packages/jp.lilxyzw.liltoon/LICENSE'),('KlakSpout','unity/TanakaCap/Packages/jp.keijiro.klak.spout/LICENSE')]:
        if (ROOT/path).exists():copy(ROOT/path,Path('ライセンス')/(name+'.txt'))
    (stage/'avatars').mkdir()
    ui=json.loads((ROOT/'ui-settings.example.json').read_text(encoding='utf-8'))
    (stage/'ui-settings.json').write_text(json.dumps(ui),encoding='utf-8')
    (stage/'TanakaCap.bat').write_text('@echo off\ncd /d "%~dp0"\nset PYTHONNOUSERSITE=1\nset PYTHONPATH=%~dp0\nstart "" "%~dp0runtime\\pythonw.exe" -m tanakacap.control_panel\n',encoding='ascii')
    (stage/'release-status.json').write_text(json.dumps(dict(version=version,publishable=publishable,open_license_items=config['open_license_items'],packages=packages),ensure_ascii=False,indent=2),encoding='utf-8')
    # Probe the relocated interpreter, including Tk and CUDA runtime availability, without opening a camera.
    code="import sys,tkinter,numpy,cv2,onnx,onnxruntime as o; o.preload_dlls(directory=''); print(sys.prefix); print(o.get_available_providers()); from tanakacap.control_panel import load_settings, commands; c=load_settings(); c['source']='camera'; assert commands(c,39500,39501)[1][2]=='tanakacap'"
    result=subprocess.run([str(stage/'runtime/python.exe'),'-s','-c',code],cwd=stage,text=True,capture_output=True,encoding='utf-8',errors='replace')
    (output/'runtime-check.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Portable runtime failed: '+result.stderr[-2000:])
    license_report=audit(stage)
    (output/'license-audit.json').write_text(json.dumps(license_report,ensure_ascii=False,indent=2),encoding='utf-8')
    if license_report['mechanical_errors']:raise RuntimeError('Release license packaging check failed: '+str(license_report['mechanical_errors']))
    files=[p for p in sorted(stage.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    manifest=[dict(path=p.relative_to(stage).as_posix(),size=p.stat().st_size,sha256=sha(p)) for p in files]
    m=stage/'manifest.json';m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(m)
    def archive(path,entries):
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in entries:z.write(p,Path('TanakaCap')/p.relative_to(stage))
    whole=output/f'TanakaCap-{version}-windows.zip';archive(whole,files)
    assets=[whole];limit=config['asset_limit_bytes']
    if whole.stat().st_size>=limit:
        with zipfile.ZipFile(whole) as z:sizes={i.filename:i.compress_size+len(i.filename.encode('utf-8'))*2+160 for i in z.infolist()}
        batches=[];batch=[];total=0
        for p in files:
            size=sizes[(Path('TanakaCap')/p.relative_to(stage)).as_posix()]
            if size>=limit-1048576:raise RuntimeError('An individual compressed file exceeds the release limit')
            if total+size>=limit-1048576:batches.append(batch);batch=[];total=0
            batch.append(p);total+=size
        if batch:batches.append(batch)
        assets=[]
        for i,entries in enumerate(batches,1):
            target=output/f'TanakaCap-{version}-part{i:02d}.zip';archive(target,entries);assets.append(target)
        whole.rename(output/'oversize-local-only.zip')
    for p in assets:
        if p.stat().st_size>=limit:raise RuntimeError('Release asset limit exceeded')
        with zipfile.ZipFile(p) as z:
            if z.testzip():raise RuntimeError('ZIP integrity failure')
    report=dict(version=version,status='publishable' if publishable else 'local-review-only',assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in assets],files=len(files),uncompressed_bytes=sum(p.stat().st_size for p in files))
    (output/'release-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--publishable',action='store_true');a=p.parse_args();run(a.version,a.publishable)
