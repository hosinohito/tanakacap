"""Explicit model downloads and reproducible local model identity."""
import hashlib
import json
import shutil
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def catalog():
    return json.loads((ROOT / 'models/catalog.json').read_text(encoding='utf-8'))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def model_path(name):
    if name not in catalog():
        raise ValueError(f'Unknown model: {name}')
    return ROOT / 'models' / name / 'model.onnx'


def fetch(name):
    info = catalog()[name]
    target = model_path(name)
    receipt = target.with_suffix('.receipt.json')
    if target.exists() and receipt.exists():
        stored = json.loads(receipt.read_text(encoding='utf-8'))
        if sha256(target) != stored['onnx_sha256']:
            raise RuntimeError(f'Model checksum differs from local receipt: {target}')
        return stored
    target.parent.mkdir(parents=True, exist_ok=True)
    archive = target.parent / 'download.zip.partial'
    request = urllib.request.Request(info['url'], headers={'User-Agent': 'tanakacap-capture-lab/0.1'})
    with urllib.request.urlopen(request, timeout=60) as source, archive.open('wb') as dest:
        shutil.copyfileobj(source, dest)
    if info.get('format') == 'onnx':
        shutil.copyfile(archive, target.with_suffix('.onnx.partial'))
        target.with_suffix('.onnx.partial').replace(target)
        member = None
    else:
        with zipfile.ZipFile(archive) as bundle:
            members = [m for m in bundle.infolist() if m.filename.endswith('.onnx')]
            if len(members) != 1:
                raise RuntimeError(f'Expected one ONNX file, found {len(members)}')
            # Never extract archive paths. Copy just the selected model to a known path.
            partial = target.with_suffix('.onnx.partial')
            with bundle.open(members[0]) as source, partial.open('wb') as dest:
                shutil.copyfileobj(source, dest)
            partial.replace(target)
            member = members[0].filename
    stored = {**info, 'model_id': name, 'downloaded_utc': datetime.now(timezone.utc).isoformat(),
              'archive_sha256': sha256(archive), 'onnx_sha256': sha256(target),
              'archive_member': member,
              'integrity_note': 'Locally recorded hash, not an upstream signed checksum.'}
    receipt.write_text(json.dumps(stored, indent=2), encoding='utf-8')
    archive.unlink()
    return stored
