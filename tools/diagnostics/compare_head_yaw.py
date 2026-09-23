"""Render-ready comparison of old/new head mapping from saved numeric observations."""
import copy,json,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.head_pose import HeadPose
from tanakacap.retarget import packet_from_landmarks,FaceFilter
from tanakacap.fingers import FingerTracker

def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--records',type=Path,required=True);p.add_argument('--hand-records',type=Path,required=True)
 p.add_argument('--reference-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--before-revision',default='c8bfb61');a=p.parse_args()
 source=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','show',f'{a.before_revision}:tanakacap/head_pose.py'],text=True)
 ns=dict(__name__='tanakacap.head_before',__package__='tanakacap',__file__=str(ROOT/'tanakacap/head_pose.py'))
 exec(compile(source,'head_before.py','exec'),ns)
 ref=json.loads(a.reference_report.read_text());settings=ref['settings'];b=settings['observation_block'];stride=settings['observation_stride']
 poses={'before':ns['HeadPose'](),'after':HeadPose()};filters={n:FaceFilter(b,stride) for n in poses};fingers=FingerTracker(b,stride)
 rows=[json.loads(l) for l in a.records.read_text().splitlines()];hands=[json.loads(l) for l in a.hand_records.read_text().splitlines()]
 assert len(rows)==len(hands)
 a.output.mkdir(parents=True,exist_ok=False);streams={};stats={n:[] for n in poses};previous=None
 for n in poses:
  (a.output/n).mkdir();streams[n]=(a.output/n/'replay.jsonl').open('w')
 try:
  for row,hand in zip(rows,hands):
   assert row['frame']==hand['frame'] and row['time']==hand['time']
   base=copy.deepcopy(hand['packet']);now=row['time']
   if 'xy' in hand:
    xy=np.asarray(hand['xy']);xyz=np.zeros((133,3));scores=np.zeros(133);ds=np.zeros(133)
    xyz[91:]=np.column_stack((-xy[:,0]*hand['scale'],-xy[:,1]*hand['scale'],-np.asarray(hand['z'])))
    scores[91:]=hand['scores'];ds[91:]=hand['depth_scores'];fingers.update(base,xyz,scores,ds,now)
   packets={}
   for n,pose in poses.items():
    xy=np.asarray(row['xy'],float);scores=np.asarray(row['scores'],float)
    head=packet_from_landmarks(xy,scores,row['frame']);pose.update(xy,scores,head,row['image_size']);filters[n].update(head,now)
    packet=copy.deepcopy(base)
    for key in ('headPitch','headYaw','headRoll'):packet[key]=head[key]
    packet['headTracked']=head['faceTracked'];packets[n]=packet
    streams[n].write(json.dumps(dict(packet=packet,dt=1/30 if previous is None else now-previous))+'\n')
    stats[n].append(packet['headYaw'])
   for k,v in packets['before'].items():
    if k not in ('headPitch','headYaw','headRoll','headTracked'):assert packets['after'][k]==v,k
   previous=now
 finally:
  for f in streams.values():f.close()
 args=ref['variants']['original']['player_args']
 report=dict(status='complete',frames=len(rows),before_revision=a.before_revision,source=str(a.records),
  variants={n:dict(label='Before - ratio yaw and fixed follow' if n=='before' else 'After - circular yaw and adaptive follow',player_args=args+(['--adaptive-head-follow'] if n=='after' else [])) for n in poses},
  scope='Same saved FP16 observations and clocks; both hands use current absolute flexion. Head mapping and follow differ; all non-head packets identical. Existing Unity expression interpolation shares head follow amount. No raw images displayed. Quality unverified.',
  non_head_packets_exact=True,yaw_percentiles={n:np.percentile(v,[5,50,95]).tolist() for n,v in stats.items()})
 (a.output/'report.json').write_text(json.dumps(report,indent=2));print(a.output,flush=True)
if __name__=='__main__':main()