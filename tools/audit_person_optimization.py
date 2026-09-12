"""Compare ROI changes on six continuous excerpts spanning the user's recording.

Identical detailed models, precision and decoding. Differences are not ground-truth accuracy.
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture_lab.inference import PersonDetector, SimCCModel
from capture_lab.person_region import PersonRegionTracker


def summary(values):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return None if not len(a) else dict(count=len(a), mean=float(a.mean()), p50=float(np.median(a)), p95=float(np.percentile(a, 95)))


def main():
    out = ROOT/'results'/('person-optimization-audit-'+str(time.time_ns()))
    out.mkdir()
    models = [SimCCModel(n, None, 'graph') for n in ('rtmw-l-384', 'rtmw3d-x-384')]
    detectors = {n: PersonDetector(None, 'graph', n) for n in ('yolox-m-human', 'yolox-tiny-human')}
    configs = {'baseline': ('yolox-m-human', 1), 'C': ('yolox-m-human', 3), 'D': ('yolox-tiny-human', 3)}
    records = {key: [] for key in configs}
    cap = cv2.VideoCapture(str(ROOT/'results/comparison-takes/20260911T235327-031115Z/camera.avi'))
    for start in (0, 900, 1800, 2700, 3600, 4500):
        trackers = {key: PersonRegionTracker(detectors[name], interval) for key, (name, interval) in configs.items()}
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        for frame in range(start, start+150):
            ok, image = cap.read()
            if not ok:
                raise RuntimeError(f'Missing frame {frame}')
            for key, tracker in trackers.items():
                roi, _, _ = tracker.update(image, frame/30)
                row = {'frame': frame, 'valid': roi is not None, 'region': tracker.diagnostics}
                if roi is not None:
                    for label, model in zip(('face', 'body'), models):
                        points, scores, _ = model.predict(image, roi)
                        row[label+'_xy'] = points.tolist()
                        row[label+'_scores'] = scores.tolist()
                        if label == 'face': tracker.observe(points, scores)
                        else: row['depth'] = model.depth.tolist()
                records[key].append(row)
        print('completed excerpt', start, flush=True)
    cap.release()
    report = {'scope': 'Six 150-frame excerpts; same FP32 detail models/decoding; no ground-truth accuracy or renderer judgment', 'modes': {}}
    for key, rows in records.items():
        (out/(key+'.json')).write_text(json.dumps(rows), encoding='utf-8')
        valid = [r for r in rows if r['valid']]
        stats = dict(frames=len(rows), valid=len(valid), reasons=dict(Counter(r['region']['reason'] for r in rows)))
        body_xy, depth = [], []
        ids = [5, 6, 7, 8, 9, 10]
        for a, b in zip(records['baseline'], rows):
            if not (a['valid'] and b['valid']): continue
            body_xy.extend(np.linalg.norm(np.array(a['body_xy'])[ids]-np.array(b['body_xy'])[ids], axis=1))
            depth.extend(abs(np.array(a['depth'])[ids]-np.array(b['depth'])[ids]))
        stats['body_joint_delta_px'] = summary(body_xy)
        stats['body_depth_delta_m'] = summary(depth)
        for part, ids in {'face': range(23,91), 'left_hand': range(91,112), 'right_hand': range(112,133), 'upper_body': range(5,11)}.items():
            scores = np.array([r['face_scores'] for r in valid])[:, list(ids)]
            stats[part+'_coverage'] = float((scores >= .3).mean())
            differences = []
            for a,b in zip(records['baseline'], rows):
                if not (a['valid'] and b['valid']): continue
                pa,pb = np.array(a['face_xy'])[list(ids)], np.array(b['face_xy'])[list(ids)]
                good = (np.array(a['face_scores'])[list(ids)] >= .3) & (np.array(b['face_scores'])[list(ids)] >= .3)
                differences.extend(np.linalg.norm(pa[good]-pb[good],axis=1))
            stats[part+'_delta_px'] = summary(differences)
        report['modes'][key] = stats
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(out, flush=True)
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__': main()
