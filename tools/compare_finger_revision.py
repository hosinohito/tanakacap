"""Identical-landmark comparison; face proximity is a numeric proxy, not labels."""
import json,sys,zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tanakacap.fingers import FingerTracker
from tanakacap.retarget import FaceFilter,packet_from_landmarks

with zipfile.ZipFile('results/checkpoints/before-elbow-face-research-20260912.zip') as z:
    source=z.read('tanakacap/fingers.py').decode('utf-8-sig')
scope={'__name__':'tanakacap.baseline_fingers','__package__':'tanakacap'}
exec(compile(source,'baseline_fingers.py','exec'),scope)
reports=[]
for name in ('20260911T185608-545920Z-rtmw-l-384','20260911T191301-012493Z-rtmw-l-384'):
    trackers=[scope['FingerTracker'](3,1),FingerTracker(3,1)]
    rows=[json.loads(l) for l in (Path('results')/name/'frames.jsonl').read_text().splitlines()]
    samples={side:[[],[]] for side in ('left','right')};bows=[[],[]];face=FaceFilter(3,1)
    for i,row in enumerate(rows):
        if row.get('points_xy') is not None:
            p=packet_from_landmarks(row['points_xy'],row['scores'],i)
            if p.get('mouthContourTracked'):
                bows[0].append(p['mouthBow'])
                bows[1].append(face.update(p,i/30)['mouthBow'])
        if row.get('body_xy') is None:continue
        xy=np.array(row['body_xy']);s=np.array(row['body_scores'])
        scale=row['body_diagnostics'].get('geometry',{}).get('model_scale')
        if scale is None:continue
        xyz=np.column_stack((-xy*scale,-np.array(row['body_depth'])))
        packets=[{},{}]
        for tracker,p in zip(trackers,packets):tracker.update(p,xyz,s,row['body_depth_scores'],i/30)
        face_xy=xy[23:91];lo=face_xy.min(axis=0);hi=face_xy.max(axis=0)
        center=(lo+hi)/2;extent=np.maximum(hi-lo,1)
        for side,offset in [('left',91),('right',112)]:
            near=bool((abs(xy[offset+9]-center)<extent*.85).all() and s[offset+9]>=.3)
            if not near:continue
            for k,p in enumerate(packets):
                samples[side][k].append([p[side+'FingerTracked'],p[side+'FingerFlex']])
    result={'source':name,'near_face_proxy':'middle MCP within expanded face landmark bounding box; no manual ground truth'}
    for side,versions in samples.items():
        result[side]=[]
        for values in versions:
            flags=np.array([v[0] for v in values]);angles=np.array([v[1] for v in values])
            result[side].append(dict(frames=len(values),valid_counts=flags.sum(axis=0).tolist(),
                flex_p95=np.percentile(angles,95,axis=0).tolist()) if values else {})
    result['bow_raw_then_neutral_p50_p95']=[np.percentile(v,[50,95]).tolist() for v in bows]
    reports.append(result)
out=Path('results/elbow-face-research/finger-comparison.json')
out.write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(out.read_text())
