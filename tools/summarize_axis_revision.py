"""Numeric diagnostics; never interprets packet statistics as human accuracy."""
import json
import sys
import time
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    target=ROOT/'results/axis-contour-tongue'
    original=[json.loads(x) for x in (ROOT/'results/20260911T162517-268332Z-rtmw-l-384/frames.jsonl').read_text().splitlines()]
    rows=[json.loads(x) for x in (target/'reprocessed/packets.jsonl').read_text().splitlines()]
    report=dict(frames=len(rows),
        yaw_sources=dict(Counter(r['body_diagnostics'].get('torso_yaw_source') for r in rows)),
        pitch_sources=dict(Counter(r['body_diagnostics'].get('torso_pitch_source') for r in rows)),
        before_yaw_p5_p50_p95=np.percentile([r['sent_packet']['torsoYaw'] for r in original],[5,50,95]).tolist(),
        after_yaw_p5_p50_p95=np.percentile([r['packet']['torsoYaw'] for r in rows],[5,50,95]).tolist(),
        finger_valid={side:dict(before=sum(sum(r['sent_packet'].get(side+'FingerTracked',[])) for r in original),
                              after=sum(sum(r['packet'].get(side+'FingerTracked',[])) for r in rows)) for side in ('left','right')},
        max_udp_bytes=max(len(json.dumps(r['packet'],separators=(',',':')).encode()) for r in rows),
        limitation='Historical packet summary only; no human ground truth.')
    (target/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
