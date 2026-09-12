"""Swap only hand geometry through the unchanged finger controller offline."""
import argparse,copy,json,sys
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.fingers import FingerTracker
from capture_lab.visibility import screen_visibility
from capture_lab.comparison import dump,line

def run(root,candidate,output):
 report=json.loads((root/'report.json').read_text());other=json.loads((candidate/'report.json').read_text())
 if other['status']!='complete' or other['video_sha256']!=report['source_video_sha256'] or other['controls_sha256']!=report['controls']['sha256'] or other['stride']!=1 or other['start_frame']!=0:raise ValueError('Complete, aligned, consecutive candidate required')
 settings=report['controls']['settings'];trackers=[FingerTracker(settings['observation_block'],settings['observation_stride']) for _ in range(2)]
 output.mkdir(parents=True,exist_ok=False);counts=defaultdict(Counter);mismatch=0;total=0;last=None
 with (root/'baseline/frames.jsonl').open() as a,(candidate/'raw.jsonl').open() as b,(output/'replay.jsonl').open('w') as replay,(output/'frames.jsonl').open('w') as details:
  for a_line in a:
   raw_line=next(b,None)
   if raw_line is None:raise ValueError('Short candidate')
   r=json.loads(a_line);h=json.loads(raw_line)
   if r['frame']!=h['frame'] or r['time']!=h['time']:raise ValueError('Frame alignment mismatch')
   total+=1;d=r['body_diagnostics'];packet=r['sent_packet'];result=copy.deepcopy(packet);stage=r['stage']
   if 'geometry' in d:
    xy=np.asarray(r['body_xy'],float);scores,_=screen_visibility(xy,r['body_scores'],r['image_size']);zs=np.asarray(r['body_depth_scores'],float)
    xyz=np.column_stack((-xy[:,0]*d['geometry']['model_scale'],-xy[:,1]*d['geometry']['model_scale'],-np.asarray(r['body_depth'],float)))
    check={};trackers[0].update(check,xyz,scores,zs,r['time'])
    for side in ['left','right']:
     if check[side+'FingerTracked']!=packet[side+'FingerTracked'] or not np.allclose(check[side+'FingerFlex'],packet[side+'FingerFlex'],atol=.002,rtol=0):mismatch+=1
    candidate_xyz=xyz.copy();candidate_scores=scores.copy();preds={v['side']:v for v in h['predictions']}
    for side,offset in [('left',91),('right',112)]:
     if side not in preds:candidate_scores[offset:offset+21]=0;continue
     # Official HaMeR is OpenPose 21 joints, meters, camera x right/y down/z away.
     # Left reflection is already applied by raw worker. Retarget uses all axes negated.
     hand=-np.asarray(preds[side]['hand_xyz_camera_axes'],float)
     candidate_xyz[offset:offset+21]=hand-hand[0]+xyz[offset]
    trackers[1].update(result,candidate_xyz,candidate_scores,zs,r['time'])
    for name,t in zip(['baseline','hamer'],trackers):
     for side,reasons in t.diagnostics.items():counts[stage+':'+name+':'+side].update(reasons)
   elif r['body_xy'] is None or r['body_depth'] is None:
    trackers=[FingerTracker(settings['observation_block'],settings['observation_stride']) for _ in range(2)]
   # Everything except finger validity and angles must stay byte-equivalent.
   fingerkeys={side+suffix for side in ['left','right'] for suffix in ['FingerTracked','FingerFlex']}
   assert all(result[k]==v for k,v in packet.items() if k not in fingerkeys)
   line(replay,{'packet':result,'dt':.033 if last is None else r['time']-last});last=r['time']
   line(details,{'frame':r['frame'],'time':r['time'],'stage':stage,'finger_fields':{k:result[k] for k in fingerkeys}})
  if next(b,None) is not None:raise ValueError('Extra candidate frames')
 if mismatch:raise AssertionError(f'Baseline finger reproduction failed: {mismatch}')
 dump(output/'summary.json',{'status':'complete','frames':total,'baseline_reproduction_mismatches':mismatch,'reasons':dict(counts),'scope':'Only 3D finger geometry swapped. All original RTMW3D confidence/boundary gates and finger corrections retained; these are NOT HaMeR confidence scores. Arms/palms/face unchanged. No accuracy ground truth.'})
 print('finger comparison',total,'baseline mismatches',mismatch)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--common',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.common,a.candidate,a.output)
