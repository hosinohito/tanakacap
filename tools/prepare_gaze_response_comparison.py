"""Audit recorded gaze numerically and prepare avatar-only response comparison."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def main():
    data = (ROOT/'results/brow-demo/replay.jsonl').read_bytes()
    packets = [json.loads(line)['packet'] for line in data.splitlines()]
    angles = np.array([[p['gazeYaw'], p['gazePitch']] for p in packets if p.get('gazeTracked')])
    output = ROOT/'results/comparisons/gaze-response'
    output.mkdir(parents=True, exist_ok=False)
    normalized = angles*6/[20,15]
    response = normalized/np.sqrt(1+normalized**2)
    variants = {}
    for name, extra in [('gaze-legacy', ['--legacy-gaze-response']), ('gaze-soft', [])]:
        folder = output/name
        folder.mkdir()
        (folder/'replay.jsonl').write_bytes(data)
        variants[name] = dict(frames=len(packets), player_args=[
            '--avatar', str(ROOT/'builds/player/avatars/haolan.tcap'),
            '--expression-mode','auto-custom', *extra])
    report = dict(status='complete', variants=variants,
        packet_sha256=hashlib.sha256(data).hexdigest(),
        tracked=len(angles), total=len(packets),
        angle_quantiles_0_10_50_90_100=np.percentile(angles,[0,10,50,90,100],axis=0).tolist(),
        old_demo_clipped_fraction=np.mean(abs(angles*6)>[20,12],axis=0).tolist(),
        new_demo_exact_clipped_fraction=np.mean(abs(response)>=1,axis=0).tolist(),
        scope='Same cached gaze packets, full exaggeration demo, only gaze response differs. Upstream gaze was recorded under size2d validity gating; demo head was subsequently recomputed with PnP. No gaze ground truth; this audits display clipping, not detection accuracy. No raw frames displayed.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='variants'},indent=2))

if __name__ == '__main__':
    main()
