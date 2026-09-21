"""Add eyebrows to saved FP16 controls, then share the exact packet clock across renderers."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.brows import BrowFilter,KEYS
from tanakacap.head_pose import HeadPose
from tanakacap.retarget import packet_from_landmarks
from tanakacap.comparison import dump,line
from tanakacap.models import sha256
import numpy as np


def main():
    source=ROOT/'results/comparisons/cuda-precision/CUDA-FP16/frames.jsonl'
    output=ROOT/'results/comparisons/expression-mapping'
    output.mkdir(parents=True,exist_ok=False)
    settings=json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    pose=HeadPose(settings['head_pitch_gain'],settings['mouth_lip_depth_scale'])
    brows=BrowFilter(settings['observation_block'],settings['observation_stride'])
    count=active=0;previous=None;values=[]
    with source.open(encoding='utf-8') as inputs,(output/'replay.jsonl').open('w',encoding='utf-8') as replay:
        for row in map(json.loads,inputs):
            xy=np.asarray(row['xy'],float);scores=np.asarray(row['scores'],float)
            p=packet_from_landmarks(xy,scores,row['frame'])
            pose.update(xy,scores,p,(1280,720));brows.update(p,row['time'])
            packet=row['sent_packet'].copy()
            packet['browTracked']=bool(packet.get('faceTracked') and p.get('browTracked'))
            for key in KEYS:packet[key]=float(p.get(key,0)) if packet['browTracked'] else 0.
            if packet['browTracked']:active+=1;values.append([packet[k] for k in KEYS])
            line(replay,dict(packet=packet,dt=1/30 if previous is None else row['time']-previous))
            previous=row['time'];count+=1
    variants={'existing':{},'auto-custom':dict(player_args=['--expression-mode','auto-custom'])}
    for name in variants:
        folder=output/name;folder.mkdir()
        (folder/'replay.jsonl').write_bytes((output/'replay.jsonl').read_bytes())
        variants[name]['frames']=count
    dump(output/'report.json',dict(status='complete',scope='Same saved FP16 observations and controls; only brow channels added once. Identical packets/timing for existing morphs and experimental auto-generated morphs. Renderer mapping comparison, not brow comparison or inference latency.',
        source_sha256=sha256(source),variants=variants,brow_active=active,observations=count,
        brow_range=np.ptp(values,axis=0) if values else []))
    print(count,active,flush=True)


if __name__=='__main__':main()
