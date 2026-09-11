import json
from pathlib import Path
from collections import Counter
import numpy as np
rows=[json.loads(l) for l in Path('results/20260911T195028-703037Z-rtmw-l-384/frames.jsonl').read_text().splitlines()]
report={}
for key in ('torsoYaw','leftCrossBody','rightCrossBody'):
    report[key]=np.percentile([r['sent_packet'].get(key,0) for r in rows],[0,5,50,95,100]).tolist()
report['yaw_source']=dict(Counter(r['body_diagnostics'].get('torso_yaw_source') for r in rows))
report['agreement']=dict(Counter(r['body_diagnostics'].get('elbow_agreement',{}).get('status') for r in rows))
report['width_ratio']=np.percentile([r['body_diagnostics']['shoulder_face_relative_ratio'] for r in rows if r['body_diagnostics'].get('shoulder_face_relative_ratio') is not None],[0,5,50,95,100]).tolist()
for side,wrist,shoulder,other in [('left',9,5,6),('right',10,6,5)]:
    outside=[]
    for r in rows:
        xy=r.get('body_xy');p=r['sent_packet']
        if xy is None or not p.get(side+'ArmTracked'):continue
        fraction=(xy[wrist][0]-xy[shoulder][0])/(xy[other][0]-xy[shoulder][0])
        if fraction<0:outside.append([p.get(side+'CrossBody',0),p[side+'Elbow']['z']])
    report[side+'_outside']={'frames':len(outside),'cross_active':sum(v[0]>0 for v in outside),'elbow_positive':sum(v[1]>0 for v in outside)}
print(json.dumps(report,indent=2))
for begin in range(0,len(rows),200):
    chunk=rows[begin:begin+200];data=[]
    for r in chunk:
        d=r['body_diagnostics']
        if not d.get('geometry') or d.get('torso_elbow_depths') is None or d.get('shoulder_face_relative_ratio') is None:continue
        data.append([d['geometry']['shoulder_depth_difference'],d['torso_elbow_depths'][0]-d['torso_elbow_depths'][1],d.get('shoulder_face_relative_ratio',1),r['sent_packet'].get('torsoYaw',0)])
    if data:print(begin,np.median(data,axis=0).tolist())
dest=Path('results/face-clearance');dest.mkdir(exist_ok=True)
(dest/'baseline.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
replay=dest/'reprocessed-final/packets.jsonl'
if replay.exists():
    new=[json.loads(l) for l in replay.read_text().splitlines()]
    summary={'frontal_reference_updates':sum(r['body_diagnostics'].get('shoulder_frontal_reference_updated',False) for r in new),
             'yaw_p05_p50_p95':np.percentile([r['packet'].get('torsoYaw',0) for r in new],[5,50,95]).tolist()}
    for side,wrist,shoulder,other in [('left',9,5,6),('right',10,6,5)]:
        outside=[]
        for old,r in zip(rows,new):
            p=r['packet'];xy=old.get('body_xy')
            if xy is None or not p.get(side+'ArmTracked') or p.get(side+'ArmHeld'):continue
            if (xy[wrist][0]-xy[shoulder][0])/(xy[other][0]-xy[shoulder][0])<0:outside.append(p.get(side+'CrossBody',0))
        summary[side+'_outside_cross_active']=sum(v>0 for v in outside)
    (dest/'comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(summary)
    stream=[];previous=0.
    for r in new:
        now=r['time_seconds'];stream.append(json.dumps({'packet':r['packet'],'dt':max(.001,min(.2,now-previous))}));previous=now
    (dest/'unity-input.jsonl').write_text('\n'.join(stream),encoding='utf-8')
