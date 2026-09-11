import json
from pathlib import Path
from collections import Counter
import numpy as np

source=Path('results/20260911T184303-770361Z-rtmw-l-384/frames.jsonl')
rows=[json.loads(s) for s in source.read_text().splitlines()]
out={'frames':len(rows),'mouth_reference_count':sum(r.get('mouth_corner_reference') is not None for r in rows)}
for key in ('mouthLeftCorner','mouthRightCorner','mouth','torsoYaw'):
    out[key]=np.percentile([r['sent_packet'].get(key,0) for r in rows],[5,50,95]).tolist()
out['width_reference']=np.percentile([r['body_diagnostics']['shoulder_reference_width'] for r in rows if r['body_diagnostics'].get('shoulder_reference_width') is not None],[0,50,100]).tolist()
out['yaw_sources']=dict(Counter(r['body_diagnostics'].get('torso_yaw_magnitude_source') for r in rows))
out['mouth_negative_frames']={side:sum(r['sent_packet'].get('mouth'+side+'Corner',0)<-.1 for r in rows) for side in ('Left','Right')}
dest=Path('results/yaw-palm-mouth');dest.mkdir(exist_ok=True)
(dest/'recording-summary.json').write_text(json.dumps(out,indent=2))
# Whole-body audit consumes numeric packets, not video.
(dest/'input.jsonl').write_text(''.join(json.dumps({'packet':r['sent_packet'],'dt':(r.get('result_interval_ms') or 33.33)/1000})+'\n' for r in rows))
print(json.dumps(out,indent=2))
