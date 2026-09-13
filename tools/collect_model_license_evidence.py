"""Read public license declarations and LFS pointers; never download/run models.

Stores source snapshots under results and verifies their relationship to local
models. A passing identity check does not itself decide licensing or publication.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/model-license-evidence'
RTM_REF = 'cd4d7095f5cfc9cfc4f46289bee91ea4a1e1d9fd'
RTM = f'https://huggingface.co/Tau-J/RTMPose/raw/{RTM_REF}/'
HEAD_REF = '4c7ed723a20deb7ff154b1ba7d6e73747d954016'
HEAD = f'https://huggingface.co/yakhyo/uniface-weights/raw/{HEAD_REF}/'
SOURCES = {
    'rtmpose-card': RTM + 'README.md',
    'rtmw-l-pointer': RTM + 'rtmw/onnx_sdk/rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip',
    'yolox-m-pointer': RTM + 'rtmposev1/onnx_sdk/yolox_m_8xb8-300e_humanart-c2c7a14a.zip',
    'head-card': HEAD + 'README.md',
    'head-pointer': HEAD + 'headpose_mobilenetv3_small.onnx',
    'humanart-issue': 'https://api.github.com/repos/open-mmlab/mmpose/issues/3271',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'sources': {}, 'identity': []}
    payloads = {}
    for name, url in SOURCES.items():
        error = None
        for _ in range(3):
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'TanakaCap-license-audit/0.1'})
                with urllib.request.urlopen(request, timeout=15) as response:
                    # /raw/ returns tiny LFS pointer text, not /resolve/ binaries.
                    data = response.read(1024 * 1024 + 1)
                    if len(data) > 1024 * 1024:
                        raise ValueError('Expected metadata under 1 MiB')
                    headers = {k: response.headers[k] for k in ('etag', 'x-repo-commit') if k in response.headers}
                payloads[name] = data.decode('utf-8')
                (OUT / f'{name}.txt').write_bytes(data)
                report['sources'][name] = {'url': url, 'sha256': hashlib.sha256(data).hexdigest(), **headers}
                print(f'{name}: {len(data)} bytes', flush=True)
                error = None
                break
            except (urllib.error.URLError, OSError, ValueError) as exc:
                error = str(exc)
        if error:
            report['sources'][name] = {'url': url, 'error': error}
            print(f'{name}: FAILED {error}', flush=True)

    lock = json.loads((ROOT / 'release/models.lock.json').read_text(encoding='utf-8'))
    for name, relative in [('rtmw-l-pointer', 'models/rtmw-l-384/model.onnx'),
                           ('yolox-m-pointer', 'models/yolox-m-human/model.onnx'),
                           ('head-pointer', 'models/head-mobilenetv3-small.onnx')]:
        match = re.search(r'^oid sha256:([0-9a-f]{64})$', payloads.get(name, ''), re.M)
        local = ROOT / relative
        with local.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        receipt_path = local.with_suffix('.receipt.json')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else None
        expected = receipt['archive_sha256'] if receipt else digest
        passed = bool(match and match[1] == expected and digest == lock[relative]
                      and (not receipt or receipt['onnx_sha256'] == digest))
        report['identity'].append({'model': relative, 'onnx_sha256': digest,
                                   'upstream_sha256': match[1] if match else None,
                                   'receipt_archive_sha256': expected if receipt else None,
                                   'archive_member': receipt['archive_member'] if receipt else None,
                                   'matches': passed})
    report['identity_complete'] = all(row['matches'] for row in report['identity'])
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['identity'], indent=2))
    raise SystemExit(0 if report['identity_complete'] and all('error' not in row for row in report['sources'].values()) else 1)


if __name__ == '__main__':
    main()
