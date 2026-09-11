import json
from pathlib import Path
from collections import Counter
import numpy as np

source=Path('results/20260911T181106-027282Z-rtmw-l-384/frames.jsonl')
rows=[json.loads(s) for s in source.read_text().splitlines()]
out={'frames':len(rows)}
for side in ('left','right'):
    values=[r.get('arm_image_width',{}).get(side,{}) for r in rows]
    widths=[v['distance_normalized_width'] for v in values if v.get('distance_normalized_width') is not None]
    runs=[];run=0
    for v in values:
        if v.get('distance_normalized_width') is not None:run+=1
        else:runs.append(run);run=0
    runs.append(run)
    out[side]={'status':dict(Counter(v.get('status','absent') for v in values)),
               'normalized_count':len(widths),'longest_run':max(runs),
               'normalized_p5_p50_p95':np.percentile(widths,[5,50,95]).tolist() if widths else []}
dest=Path('results/shoulder-width-yaw');dest.mkdir(exist_ok=True)
(dest/'width-audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
