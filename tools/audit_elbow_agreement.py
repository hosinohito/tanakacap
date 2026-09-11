"""Compare existing 2D and 3D elbow observations; no image or ground truth."""
import json
import sys
from pathlib import Path
from collections import Counter
import numpy as np

def audit(source):
    rows=[json.loads(line) for line in Path(source).read_text(encoding='utf-8').splitlines()]
    errors=[]
    for row in rows:
        if row.get('body_xy') is None:continue
        a=np.asarray(row['points_xy'],float);b=np.asarray(row['body_xy'],float)
        sa=np.asarray(row['scores']);sb=np.asarray(row['body_scores'])
        if min(sa[[5,6,7,8]].min(),sb[[5,6,7,8]].min())<.3:continue
        span=np.linalg.norm(b[6]-b[5])
        if span<30:continue
        delta=(a[[7,8]]-a[[5,6]])-(b[[7,8]]-b[[5,6]])
        errors.append(np.linalg.norm(delta,axis=1)/span)
    e=np.asarray(errors)
    return dict(source=str(source),frames=len(rows),compared=len(e),
        normalized_error_percentiles=np.percentile(e,[50,90,95,99],axis=0).tolist(),
        disagreement_over_quarter_shoulder_span=(e>.25).sum(axis=0).tolist(),
        torso_reasons=dict(Counter(r.get('body_diagnostics',{}).get('torso') for r in rows)),
        active={k:sum(r['sent_packet'].get(k,False) for r in rows) for k in ['torsoTracked','leftArmTracked','rightArmTracked']},
        limitation='Model disagreement, not identification of sleeves or measurement of accuracy.')

if __name__=='__main__':
    print(json.dumps([audit(p) for p in sys.argv[1:]],indent=2))
