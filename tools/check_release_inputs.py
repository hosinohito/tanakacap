"""Check release originals without a camera or network access."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    def require(relative, expected=None):
        p = ROOT / relative
        if not p.is_file():
            errors.append('Missing: ' + relative)
        elif expected:
            with p.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != expected:
                errors.append('Hash mismatch: ' + relative)
    for relative in (
        'unity/TanakaCap/Assets/TanakaCap/Editor/BuildRelease.cs',
        'unity/TanakaCap/ProjectSettings/ProjectVersion.txt',
        'unity/TanakaCap/Packages/jp.keijiro.klak.spout/Editor/SpoutResources.asset',
        'unity/TanakaCap/Packages/jp.keijiro.klak.spout/Plugin/KlakSpout.dll',
        'unity/TanakaCap/Packages/jp.lilxyzw.liltoon/package.json',
        'tanakacap/control_panel.py', 'tracking-settings.json', 'ui-settings.example.json',
        'models/catalog.json', 'docs/ui-part-costs.json', 'docs/USER_GUIDE.md',
        'LICENSE', 'release/THIRD_PARTY.md', 'release/THIRD_PARTY_TERMS.md',
    ):
        require(relative)
    for relative, digest in json.loads((ROOT / 'release/models.lock.json').read_bytes()).items():
        require(relative, digest)
    for item in json.loads((ROOT / 'release/notices/sources.json').read_bytes()):
        require('release/notices/' + item['file'], item['sha256'])
    evidence = json.loads((ROOT / 'release/runtime-license-evidence.json').read_bytes())
    require('assets-source/licenses/opencv-ffmpeg-sources.zip', evidence['ffmpeg_source_bundle_sha256'])
    for item in evidence['nvidia_runtime']:
        require('.venv/Lib/site-packages/' + item['path'], item['sha256'])
    normalize = lambda s: re.sub(r'[-_.]+', '-', s).lower()
    installed = {normalize(d.metadata['Name']): d.version for d in metadata.distributions()}
    for line in (ROOT / 'requirements.lock.txt').read_text(encoding='utf-8-sig').splitlines():
        if '==' in line:
            name, version = line.strip().split('==', 1)
            if installed.get(normalize(name)) != version:
                errors.append('Dependency missing or different: ' + line)
    for error in errors:
        print(error)
    print('Release input check:', 'FAILED' if errors else 'OK')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(check())
