"""Prepare actual-player replay and summarize new controls (not motion accuracy)."""
import json
from pathlib import Path
import numpy as np
root=Path('results/crossbody-mouth')
rows=[json.loads(l) for l in (root/'reprocessed/packets.jsonl').read_text().splitlines()]
last=0.;stream=[]
for r in rows:
    now=r['time_seconds'];stream.append(json.dumps(dict(packet=r['packet'],dt=max(.001,min(.2,now-last)))))
    last=now
(root/'unity-input.jsonl').write_text('\n'.join(stream),encoding='utf-8')
report={'frames':len(rows),'limitation':'Control activation, not observed pose accuracy; fresh calibration.'}
for side in ('left','right'):
    values=[r['packet'].get(side+'CrossBody',0) for r in rows if r['packet'].get(side+'ArmTracked')]
    report[side]={'crossing_frames':sum(v>0 for v in values),'fully_crossing_frames':sum(v>.99 for v in values)}
shift=[r['packet'].get('mouthShift',0) for r in rows if r['packet'].get('mouthContourTracked')]
report['mouth_shift_p05_p50_p95']=np.percentile(shift,[5,50,95]).tolist()
(root/'controls.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
