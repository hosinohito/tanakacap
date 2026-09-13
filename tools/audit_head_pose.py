"""Replay numeric landmarks to audit new geometry; no ground-truth pose labels."""
import sys,json,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tanakacap.head_pose import HeadPose
from tanakacap.retarget import packet_from_landmarks,FaceFilter
source=Path(sys.argv[1]);output=Path(sys.argv[2]);output.parent.mkdir(parents=True,exist_ok=True)
tracker=HeadPose();filter=FaceFilter(3,1);legacy_filter=FaceFilter(3,1);rows=[];now=0.
for i,line in enumerate(source.read_text().splitlines()):
    old=json.loads(line);points=old['points_xy'];scores=old['scores']
    p=packet_from_landmarks(points,scores,i)
    before={k:p.get(k) for k in ('headPitch','mouthLeftCorner','mouthRightCorner')}
    now+=(old.get('result_interval_ms') or 63)/1000
    legacy=p.copy();legacy_filter.update(legacy,now)
    start=time.perf_counter();d=tracker.update(points,scores,p,old['image_size']);elapsed=(time.perf_counter()-start)*1000
    filter.update(p,now)
    rows.append(dict(frame=old['frame'],pose=d,before=before,legacy_packet=legacy,packet=p,geometry_ms=elapsed))
valid=[r for r in rows if r['pose']['tracked']]
report=dict(source=str(source),frames=len(rows),valid=len(valid),scope='Approximate geometry, not measured subject accuracy',
            pitch_percentiles=np.percentile([r['pose']['pitch'] for r in valid],[0,5,50,95,100]).tolist() if valid else [],
            error_percentiles=np.percentile([r['pose']['normalized_reprojection_error'] for r in valid],[5,50,95]).tolist() if valid else [],
            geometry_ms=np.percentile([r['geometry_ms'] for r in rows],[50,95]).tolist())
report['corner_near_upper_limit']={k:{mode:sum(r[mode].get(k,0)>.95 for r in rows) for mode in ('legacy_packet','packet')} for k in ('mouthLeftCorner','mouthRightCorner')}
output.write_text(json.dumps(report,indent=2))
output.with_suffix('.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows))
print(json.dumps(report,indent=2))
