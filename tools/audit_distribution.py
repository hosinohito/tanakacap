"""Inventory installed package licenses; never treat metadata as release approval."""
import argparse
import hashlib
import importlib.metadata as metadata
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    packages = []
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
        name = dist.metadata['Name']
        licenses = []
        for entry in dist.files or []:
            if not any(word in entry.name.lower() for word in ('license', 'licence', 'notice', 'copying')):
                continue
            source = Path(dist.locate_file(entry)).resolve()
            if not source.is_file():
                continue
            target = output/'notices'/name/(digest(source)[:12]+'-'+source.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            licenses.append(dict(installed_path=str(entry), sha256=digest(source), saved=str(target.relative_to(output))))
        packages.append(dict(name=name, version=dist.version,
                             declared_license=dist.metadata.get('License-Expression') or dist.metadata.get('License'),
                             license_files=licenses))
    assets = []
    for source in sorted((ROOT/'models').rglob('*.onnx')):
        assets.append(dict(path=str(source.relative_to(ROOT)), sha256=digest(source)))
    report = dict(status='inventory-only-not-release-approval', created_utc=datetime.now(timezone.utc).isoformat(),
                  python=sys.version, packages=packages, local_models=assets,
                  exclusions='Does not clear model training-data rights, Unity/native transitive components, avatars, or SDK redistribution. See docs/DISTRIBUTION_LICENSES.md.')
    (output/'inventory.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(packages=len(packages), license_files=sum(len(p['license_files']) for p in packages),
                          local_models=len(assets), output=str(output)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output.resolve())
