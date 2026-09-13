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
    libraries = []
    for p in sorted((site / 'nvidia').rglob('*')):
        if not p.is_file():
            continue
        if p.suffix.lower() != '.dll':
            errors.append('Non-runtime NVIDIA file: ' + str(p.relative_to(stage)))
            continue
        family = re.sub(r'(64)?_[0-9_]+(?=\.dll$)', '', p.name)
        if p.name.startswith('cudnn'):
            status = 'blocked: wheel supplement names cudnn64_7.dll, not shipped cuDNN9 DLLs'
        elif p.name.lower().startswith('nvjitlink'):
            status = 'blocked: wheel attachment does not list nvJitLink'
        else:
            status = 'CUDA attachment family match; exact-version license reconciliation required'
        libraries.append(dict(path=p.relative_to(stage).as_posix(), family=family, sha256=sha(p), assessment=status))
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
