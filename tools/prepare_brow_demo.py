"""Reprocess face XY with PnP and brow gain; audit blinks numerically, without changing them."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tanakacap.head_pose import HeadPose
from tanakacap.retarget import FaceFilter,packet_from_landmarks
from tanakacap.comparison import line,dump

def main():
    source=ROOT/'results/comparisons/head-follow-input/source/frames.jsonl'
    output=ROOT/'results/brow-demo';output.mkdir(parents=True,exist_ok=False)
    pose=HeadPose();filter=FaceFilter(3,1,brow_gain=2)
    values=[];raw=[];brows=[];previous=None
    with source.open() as stream,(output/'replay.jsonl').open('w') as replay:
        for row in map(json.loads,stream):
            p=packet_from_landmarks(row['xy'],row['scores'],row['frame'])
            raw.append([p['leftBlink'],p['rightBlink']])
            pose.update(row['xy'],row['scores'],p,(1280,720));filter.update(p,row['time'])
            packet=row['sent_packet'].copy()
            for key,value in p.items():
                if key.startswith(('head','mouth','brow')) or key in ('faceTracked','leftBlink','rightBlink'):packet[key]=value
            values.append([packet['leftBlink'],packet['rightBlink']])
            if packet.get('browTracked'):brows.append([packet[k] for k in ('browLeftInner','browLeftOuter','browRightInner','browRightOuter')])
            line(replay,dict(packet=packet,dt=1/30 if previous is None else row['time']-previous))
            previous=row['time']
    a=np.asarray(values);b=np.asarray(raw)
    report=dict(frames=len(a),brow_active=len(brows),brow_max=np.max(brows,axis=0).tolist(),
                raw_blink_max=b.max(0).tolist(),filtered_blink_max=a.max(0).tolist(),
                raw_blink_over_09=(b>.9).sum(0).tolist(),filtered_blink_over_09=(a>.9).sum(0).tolist(),
                note='Left/right order. No ground truth eye labels. Blink code unchanged; raw eye ratios from saved XY. Brow gain 2, PnP face. Rendering uses frozen demo avatar with current Player.')
    dump(output/'report.json',report);print(report)

if __name__=='__main__':main()
