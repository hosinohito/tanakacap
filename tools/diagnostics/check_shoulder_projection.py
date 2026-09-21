"""Compare shoulder policies on saved landmarks; no camera or image display."""
import argparse
import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
import sys
import types
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.body3d import BodyRetarget


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'results/comparisons/first-take/baseline/frames.jsonl')
    parser.add_argument('--baseline',default='47e85b2')
    parser.add_argument('--output',type=Path,default=ROOT/'results/shoulder-continuous')
    args=parser.parse_args()
    code=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',
        'show',f'{args.baseline}:tanakacap/shoulder_projection.py'],cwd=ROOT).decode('utf-8')
    old=types.ModuleType('baseline_shoulder_projection')
    exec(compile(code,'baseline_shoulder_projection.py','exec'),old.__dict__)
    trackers={name:BodyRetarget(3,1,'front_projection','face_ratio') for name in ('before','after')}
    trackers['before'].shoulder_projection=old.ShoulderProjection()
    statuses={name:Counter() for name in trackers}
    stages={name:defaultdict(list) for name in trackers}
    args.output.mkdir(parents=True,exist_ok=True)
    count=changed=0
    with args.source.open(encoding='utf-8') as source,(args.output/'frames.jsonl').open('w',encoding='utf-8') as log:
        for row in map(json.loads,source):
            inputs=[None if row.get(k) is None else np.asarray(row[k],float)
                    for k in ('body_xy','body_scores','body_depth','body_depth_scores')]
            result={}
            for name,tracker in trackers.items():
                packet=tracker.update(copy.deepcopy(row['sent_packet']),*inputs,now=row['time'],image_size=row['image_size'])
                assert np.isfinite(packet['torsoYaw'])
                diag=tracker.diagnostics.get('shoulder_projection',{})
                statuses[name][diag.get('status','torso_missing')]+=1
                if packet.get('torsoTracked'):stages[name][row.get('stage','all')].append(packet['torsoYaw'])
                result[name]=dict(packet=packet,projection=diag)
            before=result['before']['packet'];after=result['after']['packet']
            for key in before.keys()|after.keys():
                if key!='torsoYaw':assert before.get(key)==after.get(key),(row['frame'],key)
            changed+=int(abs(before['torsoYaw']-after['torsoYaw'])>1e-6)
            log.write(json.dumps(dict(frame=row['frame'],time=row['time'],stage=row.get('stage'),result=result),
                                 default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v)+'\n')
            count+=1
    report=dict(source=str(args.source),baseline=args.baseline,frames=count,changed_yaw_frames=changed,
                other_packet_fields_identical=True,
                scope='Recorded observations, not ground-truth angles or visual quality verification',
                variants={name:dict(statuses=dict(statuses[name]),stages={key:dict(count=len(values),
                    abs_p50_p95=np.percentile(np.abs(values),[50,95]).tolist())
                    for key,values in stages[name].items()}) for name in trackers})
    (args.output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
