"""Prepare the matching LGPL source bundle for the pinned OpenCV FFmpeg DLL."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REF = '664c0098dcb47b361f20c1d6a518653c23f5f2b5'
DLL_SHA = '7aabff029d1fa47cf56ede4dbbe05dc62da3208f07cd16471d4c966a33f9aa31'
OUT = ROOT / 'results/runtime-license-evidence/ffmpeg-sources'
BUNDLE = ROOT / 'assets-source/licenses/opencv-ffmpeg-sources.zip'


def main():
    dll = ROOT / '.venv/Lib/site-packages/cv2/opencv_videoio_ffmpeg500_64.dll'
    assert hashlib.sha256(dll.read_bytes()).hexdigest() == DLL_SHA, 'Reaudit changed FFmpeg DLL'
    url = f'https://api.github.com/repos/opencv/opencv_3rdparty/git/trees/{REF}?recursive=1'
    tree = json.load(urllib.request.urlopen(url, timeout=30))
    assert not tree.get('truncated')
    records = []
    OUT.mkdir(parents=True, exist_ok=True)
    for entry in tree['tree']:
        name = entry['path']
        if entry['type'] != 'blob' or name.endswith('.dll'):
            continue
        source = f'https://raw.githubusercontent.com/opencv/opencv_3rdparty/{REF}/{name}'
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes() if path.exists() else urllib.request.urlopen(source, timeout=60).read()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert blob == entry['sha'], source
        path.write_bytes(data)
        records.append(dict(path=name, url=source, sha256=hashlib.sha256(data).hexdigest()))
    # The upstream source branch has an empty OpenH264 header archive, and its
    # OpenCV tar includes only wrapper headers. Include the exact source refs
    # required by its actual CMake build, not a nearby release's source tree.
    for repo, ref, name in [
        ('opencv/opencv', 'a0a660fcb1e58a295e6caa6aee64ed4d369b0181', 'opencv-full.tar.gz'),
        ('cisco/openh264', '8c7008aeb6335e7d36ab0d9a023a63f82a8eaac0', 'openh264-full.tar.gz'),
    ]:
        source = f'https://codeload.github.com/{repo}/tar.gz/{ref}'
        path = OUT / name
        if not path.exists():
            with urllib.request.urlopen(source, timeout=60) as response:
                path.write_bytes(response.read())
        records.append(dict(path=name, url=source, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (OUT / 'BUILDING.txt').write_text('''Corresponding source for opencv_videoio_ffmpeg500_64.dll

Upstream scripts and compressed source archives are preserved unchanged.
TanakaCap does not modify this DLL. Ubuntu/Docker cross-compilation is the
upstream build environment (ffmpeg/docker/Dockerfile lists build dependencies).

In a NEW empty working directory, extract this bundle. Then:
  mkdir -p build/ffmpeg build/libvpx build/aom build/openh264 opencv
  tar -xJf sources/build/ffmpeg/ffmpeg-src-n7.1.tar.xz -C build/ffmpeg
  tar -xJf sources/build/libvpx/libvpx-src-v1.16.0.tar.xz -C build/libvpx
  tar -xJf sources/build/aom/aom-src-v3.14.1.tar.xz -C build/aom
  tar -xzf openh264-full.tar.gz --strip-components=1 -C build/openh264
  tar -xzf opencv-full.tar.gz --strip-components=1 -C opencv
  chmod +x ffmpeg/*.sh ffmpeg/docker/entry.sh
  BUILD_SKIP_DOWNLOAD_SOURCES=1 bash ffmpeg/build_via_docker.sh

The empty upstream OpenH264 header archive is superseded by the full v2.5.0
source above; only its public headers and dynamic loader wrapper are compiled.
The Cisco OpenH264 codec binary itself is NOT included in TanakaCap.
Output: ffmpeg/opencv_videoio_ffmpeg_64.dll. Close TanakaCap and replace
runtime/Lib/site-packages/cv2/opencv_videoio_ffmpeg500_64.dll with your build
(rename the result). Keep a backup. LGPL permits modification/replacement
and reverse engineering for debugging those modifications.

Source and build flags were inspected; rebuilding bit-identical binaries was
not tested. Docker image/package revisions can affect reproducibility.
''', encoding='utf-8')
    metadata = dict(source_commit=REF, dll_sha256=DLL_SHA, files=records)
    lock_path = ROOT / 'release/ffmpeg-source-lock.json'
    if lock_path.exists():
        lock = json.loads(lock_path.read_text(encoding='utf-8'))
        assert metadata == lock, 'Source archive changed: reaudit before updating the lock'
    (OUT / 'SOURCE-MANIFEST.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted([r['path'] for r in records] + ['BUILDING.txt', 'SOURCE-MANIFEST.json']):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (OUT / name).read_bytes())
    with zipfile.ZipFile(BUNDLE) as archive:
        assert archive.testzip() is None
    print(json.dumps(dict(bundle=str(BUNDLE), bytes=BUNDLE.stat().st_size,
                          sha256=hashlib.sha256(BUNDLE.read_bytes()).hexdigest(), files=len(records))))


if __name__ == '__main__':
    main()
