"""Replay saved XY observations; change head angles only, never show raw images."""
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capture_lab.head_pose import HeadPose
from capture_lab.head_pose_size import SizeHeadPose
from capture_lab.retarget import packet_from_landmarks, FaceFilter
from capture_lab.comparison import dump, line
from capture_lab.models import sha256


def main():
    source=ROOT/'results/comparisons/cuda-precision/CUDA-FP16/frames.jsonl'
    output=ROOT/'results/comparisons/head-size2d'
    output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name, model in [('pnp',HeadPose()),('size2d',SizeHeadPose())]:
        folder=output/name;folder.mkdir()
        gate=FaceFilter(3,1);previous=None;angles=[];count=0;active=0
        held=dict(headPitch=0.,headYaw=0.,headRoll=0.)
        with source.open(encoding='utf-8') as inputs,(folder/'replay.jsonl').open('w',encoding='utf-8') as replay:
            for row in map(json.loads,inputs):
                p=packet_from_landmarks(row['xy'],row['scores'],row['frame'])
                model.update(row['xy'],row['scores'],p,(1280,720))
                gate.update(p,row['time'])
                packet=row['sent_packet'].copy()
                assert bool(p.get('faceTracked')) == bool(packet.get('faceTracked')), 'Comparison tracking masks differ'
                for key in held:packet[key]=p[key]
                # Keep every non-head channel, including tracked flags, identical.
                line(replay,dict(packet=packet,dt=1/30 if previous is None else row['time']-previous))
                previous=row['time'];count+=1
                if p.get('faceTracked'):active+=1
                if packet.get('faceTracked'):held={key:p[key] for key in held}
                angles.append(list(held.values()))
        a=np.array(angles)
        variants[name]=dict(frames=count,player_args=['--expression-mode','auto-custom'],
            active=active,angle_range=np.ptp(a,axis=0).tolist(),
            step_p95=np.percentile(np.abs(np.diff(a,axis=0)),95,axis=0).tolist(),
            step_max=np.max(np.abs(np.diff(a,axis=0)),axis=0).tolist())
    dump(output/'report.json',dict(status='complete',source_sha256=sha256(source),variants=variants,
        scope='Same saved FP16 XY observations; only head angles replaced. Identical non-head controls and clock. Whole-clip steps mix real motion and noise; not jitter accuracy or live latency.'))
    print(json.dumps(variants),flush=True)


if __name__=='__main__':main()
