"""Read-only audit of shortened image projections left near the camera plane."""
import json
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def run():
    common=ROOT/'results/comparisons/first-take/common.jsonl'
    control=ROOT/'results/comparisons/body-three-models/current/frames.jsonl'
    counts=Counter();examples=[]
    with common.open() as ca,control.open() as co:
        for a,b in zip(ca,co,strict=True):
            raw,row=json.loads(a),json.loads(b)
            if raw['frame']!=row['frame']:raise ValueError('Frame mismatch')
            if row['stage']!='arm_depth' or raw['body_xy'] is None:continue
            diag=row['body_diagnostics'];scale=diag.get('geometry',{}).get('model_scale')
            if scale is None:continue
            xy=np.asarray(raw['body_xy'],float);z=np.asarray(raw['body_depth'],float)
            scores=np.asarray(raw['body_scores'],float)
            for side,ids in [('left',[5,7,9]),('right',[6,8,10])]:
                lengths=np.asarray(diag.get(side+'_automatic_lengths',[0,0]),float)
                if diag.get(side)!='ok' or not np.isfinite(xy[ids]).all() or not np.isfinite(z[ids]).all() or not (scores[ids]>=.3).all():continue
                projected=np.linalg.norm(np.diff(xy[ids],axis=0),axis=1)*scale
                depths=-np.diff(z[ids]);p=row['sent_packet']
                elbow=np.array([p[side+'Elbow'][k] for k in 'xyz'])*.36
                wrist=np.array([p[side+'Wrist'][k] for k in 'xyz'])*.36
                sent=np.stack([elbow,wrist-elbow])
                for i,part in enumerate(['upper','forearm']):
                    if lengths[i]<=.07:continue
                    counts['eligible_segments']+=1
                    if projected[i]>=.75*lengths[i] or abs(depths[i])>=.035:continue
                    counts['short_projection_near_zero_model_z']+=1
                    counts['mode:'+diag.get(side+'_depth_mode','missing')]+=1
                    sent_length=float(np.linalg.norm(sent[i]))
                    examples.append(dict(frame=row['frame'],time=row['time'],side=side,part=part,
                        projected_m=float(projected[i]),supported_length_m=float(lengths[i]),model_relative_z_m=float(depths[i]),
                        sent_length_m=sent_length,sent_relative_z_m=float(sent[i,2]),
                        supported_over_sent=float(lengths[i]/max(sent_length,1e-8)),
                        front=bool(diag.get(side+'_inward_front')),mode=diag.get(side+'_depth_mode')))
    result=dict(scope='Recorded arm_depth guide interval only; thresholds are diagnostic selection, not ground truth or proof of the reported pose. Supported length is a learned projection lower bound, not actual anatomy. Unity normalizes directions to avatar bone lengths; supported_over_sent is NOT measured avatar scaling.',counts=dict(counts),examples=sorted(examples,key=lambda x:x['supported_over_sent'],reverse=True))
    out=ROOT/'results/comparisons/body-three-models/foreshortening-audit.json'
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(counts=result['counts'],examples=result['examples'][:5])))

if __name__=='__main__':run()
