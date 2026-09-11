import json
from pathlib import Path
import numpy as np
rows=[json.loads(l) for l in Path('results/20260911T200402-785025Z-rtmw-l-384/frames.jsonl').read_text().splitlines()]
out={'frames':len(rows)}
for side,ids in [('left',(5,7,9,6)),('right',(6,8,10,5))]:
    values=[]
    for r in rows:
        p=r['sent_packet'];xy=r.get('body_xy');z=r.get('body_depth')
        if xy is None or not p.get(side+'ArmTracked') or p.get(side+'ArmHeld'):continue
        shoulder,elbow,wrist,other=ids
        fraction=(xy[wrist][0]-xy[shoulder][0])/(xy[other][0]-xy[shoulder][0])
        if fraction>=0:continue
        values.append([z[shoulder]-z[elbow],p[side+'Elbow']['z']*.36,p.get(side+'CrossBody',0)])
    a=np.array(values)
    out[side]={'outward':len(a),'raw_front':int(sum(a[:,0]>0)), 'processed_front':int(sum(a[:,1]>0)),
        'raw_back_processed_front':int(sum((a[:,0]<-.035)&(a[:,1]>.035))), 'cross':int(sum(a[:,2]>0))}
out['yaw_percentiles']=np.percentile([r['sent_packet'].get('torsoYaw',0) for r in rows],[5,50,95]).tolist()
out['reference_updates']=sum(r['body_diagnostics'].get('shoulder_frontal_reference_updated',False) for r in rows)
dest=Path('results/mouth-isolation');dest.mkdir(exist_ok=True)
(dest/'baseline.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(out)
replay=dest/'reprocessed/packets.jsonl'
if replay.exists():
    fresh=[json.loads(l) for l in replay.read_text().splitlines()]
    summary={'width_without_depth_rejected':sum(r['body_diagnostics'].get('torso_yaw_evidence_consistent') is False for r in fresh),
             'yaw_percentiles':np.percentile([r['packet'].get('torsoYaw',0) for r in fresh],[5,50,95]).tolist()}
    (dest/'comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(summary)
    stream=[];previous=0.
    for r in fresh:
        now=r['time_seconds'];stream.append(json.dumps(dict(packet=r['packet'],dt=max(.001,min(.2,now-previous)))));previous=now
    (dest/'unity-input.jsonl').write_text('\n'.join(stream),encoding='utf-8')
