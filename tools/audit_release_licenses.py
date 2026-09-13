"""Audit an actual staged release; mechanical checks do not grant legal permission."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def audit(stage):
    sources = json.loads((ROOT / 'release/notices/sources.json').read_text(encoding='utf-8'))
    errors = []
    for item in sources:
        p = stage / 'ライセンス/notices' / item['file']
        if not p.is_file() or sha(p) != item['sha256']:
            errors.append('Missing or changed notice: ' + item['file'])
    for required in ('ライセンス/README.md', 'ライセンス/第三者部品の利用条件.md', 'ライセンス/TanakaCap.txt', 'ライセンス/face_template.LICENSE'):
        if not (stage / required).is_file():
            errors.append('Missing: ' + required)
    site = stage / 'runtime/Lib/site-packages'
    evidence = json.loads((ROOT / 'release/runtime-license-evidence.json').read_text(encoding='utf-8'))
    for item in evidence['unity_runtime']:
        p = stage / item['path']
        if not p.is_file() or sha(p) != item['sha256']:
            errors.append('Unity runtime differs from audited version: ' + item['path'])
    nvidia_lock = {r['path']: r['sha256'] for r in evidence['nvidia_runtime']}
    bundle = stage / 'ライセンス/sources/opencv-ffmpeg-sources.zip'
    if not bundle.is_file() or sha(bundle) != evidence['ffmpeg_source_bundle_sha256']:
        errors.append('Missing or changed corresponding FFmpeg source bundle')
    source_lock = json.loads((ROOT / 'release/ffmpeg-source-lock.json').read_text(encoding='utf-8'))
    ffmpeg = site / 'cv2/opencv_videoio_ffmpeg500_64.dll'
    if not ffmpeg.is_file() or sha(ffmpeg) != source_lock['dll_sha256']:
        errors.append('FFmpeg binary no longer matches audited source')
    libraries = []
    for p in sorted((site / 'nvidia').rglob('*')):
        if not p.is_file():
            continue
        if p.suffix.lower() != '.dll':
            errors.append('Non-runtime NVIDIA file: ' + str(p.relative_to(stage)))
            continue
        family = re.sub(r'(64)?_[0-9_]+(?=\.dll$)', '', p.name)
        if nvidia_lock.get(p.relative_to(site).as_posix()) != sha(p):
            errors.append('NVIDIA runtime differs from audited version: ' + p.name)
        status = 'Redistributable runtime under official matching-version SDK agreement; notices required'
        libraries.append(dict(path=p.relative_to(stage).as_posix(), family=family, sha256=sha(p), assessment=status))
    for relative in nvidia_lock:
        if not (site / relative).is_file():
            errors.append('Missing audited NVIDIA DLL: ' + relative)
    models = []
    for relative, expected in json.loads((ROOT / 'release/models.lock.json').read_text(encoding='utf-8')).items():
        p = stage / relative
        actual = sha(p) if p.is_file() else None
        if actual != expected:
            errors.append('Model lock mismatch: ' + relative)
        models.append(dict(path=relative, sha256=actual))
    binaries = [dict(path=p.relative_to(stage).as_posix(), sha256=sha(p))
                for p in sorted(stage.rglob('*')) if p.is_file() and p.suffix.lower() in ('.dll', '.pyd', '.exe')]
    config = json.loads((ROOT / 'release/config.json').read_text(encoding='utf-8'))
    return dict(mechanical_errors=errors, publication_approved=config['publication_approved'],
                unresolved=config['open_license_items'], notices=len(sources), nvidia=libraries,
                models=models, binaries=binaries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.stage.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(errors=report['mechanical_errors'], notices=report['notices'],
                          nvidia_dlls=len(report['nvidia']), binaries=len(report['binaries']),
                          publication_approved=report['publication_approved']), ensure_ascii=True))
    raise SystemExit(bool(report['mechanical_errors']))
