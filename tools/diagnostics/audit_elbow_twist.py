"""Summarize actual avatar joint rotations from an offline video report."""
import argparse
import json
from pathlib import Path
import numpy as np


def summarize(path):
    report=json.loads(path.read_text(encoding='utf-8'))
    rows=report['armPoses'];result={}
    for side in ('left','right'):
        details={}
        for suffix in ('Twist','RequestedTwist','ElbowTwist'):
            values=np.array([row[side+suffix] for row in rows])
            index=int(np.argmax(np.abs(values)))
            details[suffix]=dict(min=float(values.min()),max=float(values.max()),
                abs_p95=float(np.percentile(abs(values),95)),peak_seconds=index/report['fps'],
                frames_over_120=int((abs(values)>120).sum()))
        for suffix in ('UpperRotation','LowerRotation'):
            values=np.array([[row[side+suffix][key] for key in 'xyzw'] for row in rows])
            dots=np.sum(values[1:]*values[:-1],axis=1)
            changes=np.degrees(2*np.arccos(np.clip(abs(dots),0,1)))
            index=int(np.argmax(changes))
            details[suffix]=dict(max_step_degrees=float(changes[index]),
                p95_step_degrees=float(np.percentile(changes,95)),peak_seconds=(index+1)/report['fps'])
        result[side]=details
    return dict(source=str(path),frames=len(rows),fps=report['fps'],
        hand_contact={key:report[key] for key in ('wristHeadOnly','handHeadCorrections','maximumHandHeadShift','maximumHandHeadResidual')},
        joints=result,scope='Authored-rest-relative swing/twist decomposition and local quaternion changes. Not an anatomical measurement or mesh-quality verdict.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports',type=Path,nargs='+');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=[summarize(path) for path in args.reports]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
