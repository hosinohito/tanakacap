"""Collect exact upstream runtime artifacts; no installation or camera access."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-license-evidence'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def fetch(url, path, expected=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or (expected and sha(path) != expected):
        temporary = path.with_suffix(path.suffix + '.part')
        with urllib.request.urlopen(url, timeout=60) as src, temporary.open('wb') as dst:
            while data := src.read(4 * 1024 * 1024):
                dst.write(data)
        if expected and sha(temporary) != expected:
            raise ValueError('Upstream archive checksum mismatch: ' + url)
        temporary.replace(path)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for product, version, keys in [('cuda', '13.4.1', ['libnvjitlink']),
                                    ('cudnn', '9.26.0', ['cudnn'])]:
        base = f'https://developer.download.nvidia.com/compute/{product}/redist/'
        manifest_url = base + f'redistrib_{version}.json'
        manifest_path = fetch(manifest_url, OUT / (product + '.json'))
        manifest = json.loads(manifest_path.read_bytes())
        for key in keys:
            entry = manifest[key]
            target = entry['windows-x86_64']
            if key == 'cudnn':
                target = target['cuda13']
            url = base + target['relative_path']
            print('Fetching official archive:', key, target['size'], flush=True)
            archive = fetch(url, OUT / Path(target['relative_path']).name, target['sha256'])
            matches = []
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    name = Path(info.filename).name
                    if name.lower() in ('license', 'license.txt'):
                        fetch_path = OUT / (key + '-archive-LICENSE.txt')
                        fetch_path.write_bytes(z.read(info))
                    if name.lower().endswith('.dll'):
                        local = list((ROOT / '.venv/Lib/site-packages/nvidia').rglob(name))
                        if not local:
                            continue
                        with z.open(info) as stream:
                            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                        for path in local:
                            assert sha(path) == digest, name
                            matches.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=digest))
            records.append(dict(component=key, version=entry['version'], manifest=manifest_url,
                                archive=url, archive_sha256=target['sha256'], matches=matches))
            print(key, 'matched DLLs:', len(matches), flush=True)
    (OUT / 'nvidia-identity.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
