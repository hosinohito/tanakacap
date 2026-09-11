import json
from pathlib import Path
from collections import Counter
import numpy as np
p=Path('results/20260911T182939-789455Z-rtmw-l-384/frames.jsonl')
rows=[json.loads(s) for s in p.read_text().splitlines()]
print('frames',len(rows))
for key in ('torsoYaw','mouthLeftCorner','mouthRightCorner'):
    print(key,np.percentile([r['sent_packet'].get(key,0) for r in rows],[5,50,95]).tolist())
for side in ('left','right'):
    print(side,Counter(r['body_diagnostics'].get(side) for r in rows))
    print('arm hand',sum(r['sent_packet'].get(side+'ArmTracked',False) for r in rows),sum(r['sent_packet'].get(side+'HandTracked',False) for r in rows))
print('mouth',sum(r['sent_packet'].get('mouthContourTracked',False) for r in rows))
