"""Summarize numeric replay and benchmark relative-face-scale arithmetic only."""
import json
import sys
import time
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capture_lab.face_scale import FaceScale


def main():
    target=ROOT/'results/wrist-distance-review'
    rows=[json.loads(x) for x in (target/'reprocessed-release/packets.jsonl').read_text().splitlines()]
    source=ROOT/'results/20260911T160326-607733Z-rtmw-l-384/frames.jsonl'
    original=[json.loads(x) for x in source.read_text().splitlines()]
    inputs=[(np.asarray(r['body_xy']),np.asarray(r['body_scores'])) for r in original]
    tracker=FaceScale(); elapsed=[]
    for xy,scores in inputs:
        start=time.perf_counter()
        tracker.update(xy,scores,.002)
        elapsed.append((time.perf_counter()-start)*1000)
    report=dict(source=str(source),frames=len(rows),
        distance_sources=dict(Counter(r['body_diagnostics'].get('distance_source') for r in rows)),
        face_scale_cpu_ms_p50_p95=np.percentile(elapsed,[50,95]).tolist(),
        max_udp_bytes=max(len(json.dumps(r['packet'],separators=(',',':')).encode()) for r in rows),
        limitation='No image inference timed; no human ground truth. Finger populations differ.',
        finger_valid={side:{'before':sum(sum(r['sent_packet'].get(side+'FingerTracked',[])) for r in original),
                           'after':sum(sum(r['packet'].get(side+'FingerTracked',[])) for r in rows)} for side in ('left','right')})
    (target/'distance-summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
