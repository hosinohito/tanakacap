"""Reproducible local import of the BOOTH archive; never edit the source archive."""
import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'unity' / 'TanakaCap'


def destination(root, name):
    relative = PurePosixPath(name.replace('\\', '/'))
    if relative.is_absolute() or '..' in relative.parts or ':' in name:
        raise ValueError(f'Unsafe asset path: {name}')
    result = root.joinpath(*relative.parts).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(name)
    return result


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise RuntimeError(f'Refusing to overwrite changed import: {path}')
    path.write_bytes(data)


def main():
    archive = ROOT / 'assets-source' / 'HAOLAN_Ver1.6.zip'
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as z:
        package = z.read('HAOLAN_Ver1.6/HAOLAN_PC.unitypackage')
    imported = []
    with tarfile.open(fileobj=io.BytesIO(package), mode='r:gz') as tar:
        members = {m.name: m for m in tar.getmembers()}
        for name, member in members.items():
            if not name.endswith('/pathname'):
                continue
            asset_name = tar.extractfile(member).read().decode('utf-8-sig')
            if not asset_name.startswith('Assets/HAOLAN/') and asset_name != 'Assets/HAOLAN':
                raise ValueError(f'Unexpected package root: {asset_name}')
            key = name.rsplit('/', 1)[0]
            target = destination(PROJECT, asset_name)
            if key + '/asset' in members:
                put(target, tar.extractfile(members[key + '/asset']).read())
            else:
                target.mkdir(parents=True, exist_ok=True)
            if key + '/asset.meta' in members:
                put(Path(str(target) + '.meta'), tar.extractfile(members[key + '/asset.meta']).read())
            imported.append(asset_name)
    shader_zip = ROOT / 'assets-source' / 'jp.lilxyzw.liltoon-2.3.4.zip'
    shader_root = PROJECT / 'Packages' / 'jp.lilxyzw.liltoon'
    with zipfile.ZipFile(shader_zip) as z:
        for member in z.infolist():
            target = destination(shader_root, member.filename)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                put(target, z.read(member))
    receipt = {'source': 'https://booth.pm/ja/items/3818504', 'avatar_sha256': digest,
               'shader_version': '2.3.4', 'shader_sha256': hashlib.sha256(shader_zip.read_bytes()).hexdigest(),
               'assets': imported, 'note': 'Source assets copied verbatim. Runtime scene adaptations are separate.'}
    (ROOT / 'assets-source' / 'unity-import.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(f'Imported {len(imported)} avatar assets and lilToon into {PROJECT}')


if __name__ == '__main__':
    main()
