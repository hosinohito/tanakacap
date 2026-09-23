"""Measure pre-clamp signed finger angles from a historical tracker and cached observations."""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records', type=Path, required=True)
    p.add_argument('--reference-report', type=Path, required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    source = subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'show', f'{a.revision}:tanakacap/fingers.py'], text=True)
    captures = []
    replacements = {
        "                if finger==0:\n": "                if finger!=0: capture(side, finger, flex)\n                if finger==0:\n",
        "                    axis/=np.linalg.norm(axis)\n": "                    axis/=np.linalg.norm(axis)\n                    capture(side, finger, [0.]+[float(np.degrees(np.arctan2(axis@np.cross(a,b),a@b))) for a,b in zip(segments[1:3],segments[2:4])])\n",
    }
    for before, after in replacements.items():
        assert source.count(before) == 1, 'Historical implementation changed; inspect instrumentation'
        source = source.replace(before, after)
    ns = dict(__name__='tanakacap.finger_audit', __package__='tanakacap', capture=lambda side, finger, flex: captures.append((side, finger, np.asarray(flex).copy())))
    exec(compile(source, 'instrumented_fingers.py', 'exec'), ns)
    settings = json.loads(a.reference_report.read_text(encoding='utf-8'))['settings']
    tracker = ns['FingerTracker'](settings['observation_block'], settings['observation_stride'])
    samples = []
    count = 0
    for line in a.records.read_text(encoding='utf-8').splitlines():
        row = json.loads(line); captures.clear()
        if 'xy' in row:
            xy = np.asarray(row['xy']); xyz = np.zeros((133, 3)); scores = np.zeros(133); depth = np.zeros(133)
            xyz[91:] = np.column_stack((-xy[:, 0]*row['scale'], -xy[:, 1]*row['scale'], -np.asarray(row['z'])))
            scores[91:] = row['scores']; depth[91:] = row['depth_scores']
            packet = dict(row['packet'])
            tracker.update(packet, xyz, scores, depth, row['time'])
            assert packet == row['packet'], f'Baseline mismatch at {row["frame"]}'
            for side, finger, flex in captures:
                samples.append(dict(frame=row['frame'], time=row['time'], side=side, finger=finger, angles=flex.tolist()))
        count += 1
    report = dict(revision=a.revision, records=str(a.records), frames=count, baseline_exact=True,
                  scope='Raw signed angles after geometry validity checks, before temporal gate/deadband/clamp; not ground-truth error rates.', fingers={})
    for side in ('left', 'right'):
        report['fingers'][side] = {}
        for finger, name in enumerate(('thumb', 'index', 'middle', 'ring', 'little')):
            values = np.asarray([s['angles'] for s in samples if s['side']==side and s['finger']==finger])
            if not len(values):
                report['fingers'][side][name] = {'status': 'no_valid_observations', 'n': 0}
                continue
            joints = {}
            for j, joint in enumerate(('CMC', 'MCP', 'IP') if finger==0 else ('MCP', 'PIP', 'DIP')):
                if finger==0 and j==0: continue
                v = values[:, j]; band = 5 if finger==0 else 7
                joints[joint] = dict(n=len(v), negative_percent=round(float(np.mean(v < -band)*100), 1), positive_percent=round(float(np.mean(v > band)*100), 1), median_degrees=round(float(np.median(v)), 1), p05_degrees=round(float(np.percentile(v, 5)), 1), p95_degrees=round(float(np.percentile(v, 95)), 1))
            report['fingers'][side][name] = joints
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (a.output/'angles.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples), encoding='utf-8')
    print(json.dumps(report, indent=2))
if __name__ == '__main__': main()