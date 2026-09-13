"""Collect redistribution notices with provenance; never grants publication approval."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'release/notices'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []

    def save(name, data, source):
        (OUT / name).write_bytes(data)
        records.append(dict(file=name, source=source, sha256=hashlib.sha256(data).hexdigest()))

    def local(name, relative):
        save(name, (ROOT / relative).read_bytes(), relative)

    for name, relative in [
        ('YuNet-MIT.txt', 'docs/YUNET_LICENSE.txt'),
        ('HeadPose-MIT.txt', 'docs/HEAD_MODEL_LICENSE.txt'),
        ('Iris-Apache-2.0.txt', 'models/iris-landmark.LICENSE'),
        ('lilToon-MIT.txt', 'unity/TanakaCap/Packages/jp.lilxyzw.liltoon/LICENSE'),
        ('VRC-Light-Volumes-MIT.txt', 'unity/TanakaCap/Packages/jp.lilxyzw.liltoon/Shader/Includes/VRC Light Volumes/license.txt'),
        ('KlakSpout-Unlicense.txt', 'unity/TanakaCap/Packages/jp.keijiro.klak.spout/LICENSE'),
    ]:
        local(name, relative)
    unity = Path('C:/Program Files/Unity/Hub/Editor/2022.3.22f1/Editor/Data')
    for name, relative in [('Unity-2022.3.22f1-ThirdPartyNotices.txt', 'Resources/legal.txt'),
                           ('Unity-NativePlugin-License.md', 'PluginAPI/LICENSE.md')]:
        save(name, (unity / relative).read_bytes(), 'Unity 2022.3.22f1 Editor/Data/' + relative)
    url = 'https://unity.com/legal/licenses/unity-companion-license'
    with urllib.request.urlopen(url, timeout=30) as response:
        save('Unity-Companion-License.html', response.read(), url)

    # Pin GitHub sources to actual commits before downloading. No model downloads.
    repos = [('open-mmlab/mmpose', 'main', 'LICENSE', 'MMPose-Apache-2.0.txt'),
             ('Megvii-BaseDetection/YOLOX', 'main', 'LICENSE', 'YOLOX-Apache-2.0.txt'),
             ('keijiro/KlakSpout', '2.0.6', None, None)]
    for repo, ref, path, name in repos:
        with urllib.request.urlopen(f'https://api.github.com/repos/{repo}/commits/{ref}', timeout=30) as response:
            commit = json.load(response)['sha']
        def fetch(path):
            url = f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'
            with urllib.request.urlopen(url, timeout=30) as response:
                return url, response.read()
        if path:
            url, data = fetch(path)
            save(name, data, url)
        else:
            # Preserve copyright/license blocks from the exact vendored Spout version.
            for path in ('SpoutSenderNames.cpp', 'SpoutSharedMemory.cpp', 'SpoutUtils.cpp'):
                url, data = fetch('Plugin/Spout/' + path)
                comment = data.decode('utf-8').split('*/', 1)[0] + '*/\n'
                assert 'Redistribution' in comment and 'Copyright' in comment
                save('KlakSpout-' + path + '-NOTICE.txt', comment.encode('utf-8'), url)
    (OUT / 'sources.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Collected {len(records)} notices')


if __name__ == '__main__':
    main()
