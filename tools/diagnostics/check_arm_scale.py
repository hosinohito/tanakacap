"""Compare arm scale handling on saved landmarks, without images or a camera."""
import argparse
import copy
import json
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
    parser.add_argument('--baseline',default='d0b6598')
    args=parser.parse_args()
    code=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',
                                  'show',f'{args.baseline}:tanakacap/body3d.py'],cwd=ROOT).decode('utf-8')
    baseline=types.ModuleType('tanakacap._baseline_body3d')
    baseline.__package__='tanakacap'
    exec(compile(code,'baseline_body3d.py','exec'),baseline.__dict__)
    trackers={name:cls(3,1,arm_depth_mode='front_projection',shoulder_yaw_mode='face_ratio')
              for name,cls in [('before',baseline.BodyRetarget),('after',BodyRetarget)]}
    report={name:dict(updated=0,held_scale_updates=0,expired=0) for name in trackers}
    output=ROOT/'results/arm-scale';output.mkdir(parents=True,exist_ok=True)
    count=0
    with args.source.open(encoding='utf-8') as source,(output/'frames.jsonl').open('w',encoding='utf-8') as log:
        for row in map(json.loads,source):
            inputs=[None if row.get(k) is None else np.asarray(row[k],float)
                    for k in ('body_xy','body_scores','body_depth','body_depth_scores')]
            result={}
            for name,tracker in trackers.items():
                p=tracker.update(copy.deepcopy(row['sent_packet']),*inputs,now=row['time'],image_size=row['image_size'])
                active=sum(bool(p[side+'ArmTracked'] and not p[side+'ArmHeld']) for side in ('left','right'))
                report[name]['updated']+=active
                held=tracker.diagnostics.get('arm_scale_source')=='held_face'
                report[name]['held_scale_updates']+=active if held else 0
                if held:
                    assert not tracker.diagnostics['arm_length_learning']
                if tracker.diagnostics.get('arm_scale_source')=='unavailable':
                    report[name]['expired']+=1
                result[name]=dict(active=active,diagnostics=tracker.diagnostics,packet=p)
            log.write(json.dumps(dict(frame=row['frame'],result=result),default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v)+'\n')
            count+=1
    summary=dict(source=str(args.source),baseline=args.baseline,frames=count,counts=report,
                 scope='Recorded numeric observations; updated counts are not accuracy scores')
    (output/'report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
