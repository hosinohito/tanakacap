"""Audit recorded palm rejection before retargeting; does not change controls."""
import argparse,json,sys
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.visibility import screen_visibility
from capture_lab.hand_orientation import palm_basis
from capture_lab.face_distance import FaceDistance

def reason(xyz,scores,zscores,offset):
 ids=np.array([0,5,9,17])+offset;p=xyz[ids];s=scores[ids]
 if not np.isfinite(p).all() or not np.isfinite(s).all() or not np.isfinite(zscores[ids]).all():return 'nonfinite'
 if (s<.3).any():return 'confidence_or_boundary'
 w,i,m,l=p;f=m-w;a=l-i
 if not .015<np.linalg.norm(f)<.25:return 'palm_length'
 if not .01<np.linalg.norm(a)<.2:return 'palm_width'
 n=np.cross(i-w,l-w);den=np.linalg.norm(i-w)*np.linalg.norm(l-w)
 if den<1e-6 or np.linalg.norm(n)/den<.15:
  frac=np.dot(m-i,a)/np.dot(a,a)
  if not -.2<=frac<=1.2:return 'middle_outside'
  n=np.cross(f,a)
  if np.linalg.norm(n)/(np.linalg.norm(f)*np.linalg.norm(a))<.15:return 'collapsed_plane'
 f=f/np.linalg.norm(f);n=n-f*np.dot(n,f)
 if np.linalg.norm(n)<1e-6:return 'collapsed_normal'
 return 'ok'

def distance_audit(root):
 models={name:FaceDistance(mode=name) for name in ('stable','legacy')};values=defaultdict(list);steps=defaultdict(list);previous={}
 with (root/'common.jsonl').open() as common,(root/'baseline/frames.jsonl').open() as baseline:
  for a,b in zip(common,baseline):
   r=json.loads(a);control=json.loads(b);stage=control['stage']
   assert r['frame']==control['frame']
   for name,model in models.items():
    packet=dict(r['face'])
    if r['points_xy'] is not None:model.update(np.asarray(r['points_xy'],float),np.asarray(r['scores'],float),packet,r['time'])
    key=name+':'+stage
    if packet.get('faceDistanceTracked'):
     v=packet['faceDistanceRatio'];values[key].append(v);prev=previous.get(name)
     if prev and prev[0]==r['frame']-1 and prev[1]==stage:steps[key].append(abs(v-prev[2]))
     previous[name]=(r['frame'],stage,v)
    else:previous.pop(name,None)
 return {k:{'frames':len(v),'p5_p50_p95':np.percentile(v,[5,50,95]).tolist(),'adjacent_step_p95':float(np.percentile(steps[k],95)) if steps[k] else None} for k,v in values.items()}

def run(root):
 counts=defaultdict(Counter);trans=defaultdict(list);previous={};frames=Counter()
 for line in (root/'baseline/frames.jsonl').open():
  r=json.loads(line);d=r['body_diagnostics'];stage=r['stage'];frames[stage]+=1
  if 'geometry' not in d:continue
  xy=np.asarray(r['body_xy'],float);z=np.asarray(r['body_depth'],float);zs=np.asarray(r['body_depth_scores'],float)
  scores,edge=screen_visibility(xy,np.asarray(r['body_scores'],float),r['image_size'])
  xyz=np.column_stack((-xy[:,0]*d['geometry']['model_scale'],-xy[:,1]*d['geometry']['model_scale'],-z))
  for side,offset,sh,el in [('left',91,5,7),('right',112,6,8)]:
   why=reason(xyz,scores,zs,offset)
   assert (why=='ok')==(palm_basis(xyz,scores,zs,offset) is not None),(r['frame'],side,why)
   counts[stage+':'+side][why]+=1
   packet=r['sent_packet'];raw=float(xyz[el,2]-xyz[sh,2]);pos=packet.get(side+'Elbow',{}).get('z')
   out=float(pos)*.36 if pos is not None and packet.get(side+'ArmTracked') else None
   key=(stage,side);prev=previous.get(key)
   if prev and r['frame']==prev[0]+1 and out is not None and prev[2] is not None:
    trans[stage+':'+side].append([abs(raw-prev[1]),abs(out-prev[2])])
   previous[key]=(r['frame'],raw,out)
 summary={'source':str(root),'scope':'Prompt labels are not action ground truth. All available model-coordinate observations, not a manually visible-hand denominator. Elbow steps use consecutive tracked frames only.','frames':dict(frames),'palm_rejections':dict(counts),'elbow_adjacent_step_p95_m':{k:np.percentile(v,95,axis=0).tolist() for k,v in trans.items() if v}}
 summary['distance']=distance_audit(root)
 (root/'input-audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 for stage in ['left_fingers_face','right_fingers_face','hands_chest','torso_yaw']:
  print(stage,frames[stage])
  for side in ['left','right']:print(side,dict(counts[stage+':'+side]),summary['elbow_adjacent_step_p95_m'].get(stage+':'+side))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('comparison',type=Path);run(p.parse_args().comparison)
