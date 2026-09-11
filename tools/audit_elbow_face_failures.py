import json
from pathlib import Path
from collections import Counter
import numpy as np

sources=['20260911T185608-545920Z-rtmw-l-384','20260911T191301-012493Z-rtmw-l-384']
out=[]
for name in sources:
    rows=[json.loads(s) for s in (Path('results')/name/'frames.jsonl').read_text().splitlines()]
    report={'source':name,'frames':len(rows)}
    for key in ['mouthLeftCorner','mouthRightCorner','mouth','headPitch']:
        report[key]=np.percentile([r['sent_packet'].get(key,0) for r in rows],[5,50,95]).tolist()
    refs=[r.get('mouth_corner_reference') for r in rows if r.get('mouth_corner_reference') is not None]
    report['mouth_reference']=refs[0] if refs else None
    for side in ['left','right']:
        active=[r for r in rows if r.get('body_xy') is not None]
        report[side]={
            'reasons':dict(Counter(r['body_diagnostics'].get(side) for r in rows)),
            'finger_valid_counts':np.sum([r['sent_packet'].get(side+'FingerTracked',[False]*5) for r in rows],axis=0).tolist(),
            'flex_p50_p95':np.percentile([r['sent_packet'].get(side+'FingerFlex',[0]*15) for r in rows],[50,95],axis=0).tolist(),
            'palm_observed':sum(r['body_diagnostics'].get('palm_observation',{}).get(side,False) for r in rows),
            'upper_forced':sum(r['sent_packet'].get(side+'UpperInFront',False) for r in rows)}
    out.append(report)
dest=Path('results/elbow-face-research');dest.mkdir(exist_ok=True)
(dest/'baseline.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
