"""Summarize actual-player numeric audits; packet agreement is not human accuracy."""
import argparse
import json
from pathlib import Path
import numpy as np


def summarize(path):
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]
    out={'frames':len(rows)}
    for side in ('left','right'):
        valid=[r for r in rows if r[side+'HandTracked']]
        out[side]={
            'tracked':len(valid),
            'palm_error_p50_p95':np.percentile([r[side+'PalmError'] for r in valid],[50,95]).tolist(),
            'requested_roll_min_max': [min(r[side+'RequestedRoll'] for r in valid),max(r[side+'RequestedRoll'] for r in valid)],
            'roll_outside_limit':sum(abs(r[side+'RequestedRoll'])>160 for r in valid)}
    valid=[r for r in rows if r['torsoTracked']]
    for key in ('actualYaw','shoulderYaw'):
        out[key+'_error_p50_p95']=np.percentile([abs((r[key]-r['requestedYaw']+180)%360-180) for r in valid],[50,95]).tolist()
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before',type=Path)
    parser.add_argument('after',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    report={'limitation':'Same recorded packet input and smoke startup pose required. No human ground truth; limit violations are requested values, not actual bones.',
            'before':summarize(args.before),'after':summarize(args.after)}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
