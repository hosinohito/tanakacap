import copy,json,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tanakacap.body3d import BodyRetarget
old={};exec(subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'show','5dcce24:tanakacap/front_projection.py'],text=True),old)
class BeforeProjection(old['FrontProjection']):
 def solve(self,bones,lengths,now,**kwargs):return super().solve(bones,lengths,now)
base=ROOT/'results/arm-release-fix'
for take in (sys.argv[1:] or ['20260911T235327-031115Z']):
 source=Path((base/take/'source.txt').read_text().strip());rows=[json.loads(l) for l in (source/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
 for variant in ('before-matched','depth-fixed'):
  tracker=BodyRetarget(3,1,'front_projection','face_ratio')
  if variant=='before-matched':tracker.projector={side:BeforeProjection() for side in ('left','right')}
  output=base/take/(variant+'.jsonl');stats=[]
  with output.open('w') as f:
   for i,r in enumerate(rows):
    p=copy.deepcopy(r['sent_packet']);result=tracker.update(p,np.array(r['body_xy']) if 'body_xy' in r else None,np.array(r['body_scores']) if 'body_scores' in r else None,np.array(r['body_depth']) if 'body_depth' in r else None,np.array(r['body_depth_scores']) if 'body_depth_scores' in r else None,now=i/30,image_size=tuple(r['image_size']),reference_xy=np.array(r['points_xy']),reference_scores=np.array(r['scores']))
    # Only arm geometry is the comparison variable; retain head/torso/hand/finger signals.
    packet=copy.deepcopy(r['sent_packet'])
    for side in ('left','right'):
     for name in ('Elbow','Wrist','ArmTracked','ArmHeld','WristInFront','UpperInFront','CrossBody','OutOfView'):
      key=side+name
      if key in result:packet[key]=result[key]
    f.write(json.dumps({'dt':1/30,'packet':packet})+'\n');stats.append(copy.deepcopy(tracker.diagnostics))
  (base/take/(variant+'-diagnostics.json')).write_text(json.dumps(stats),encoding='utf-8')
 print(take,flush=True)


