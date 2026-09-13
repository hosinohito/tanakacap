"""Deterministic filter + scalar render approximation; not camera-to-display latency."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.arm_filter import filter_arm
from tanakacap.motion_gate import DirectionGate


def old_filter(previous,target,dt):
    delta=target-previous
    distance=np.linalg.norm(delta,axis=1,keepdims=True)
    return previous+delta*np.minimum(1,8*dt/np.maximum(distance,1e-6))*(1-np.exp(-18*dt))


def run(filter_fn,render_gain,gated=False):
    state=np.zeros((2,3)); rendered=0.; samples=[]
    gate=DirectionGate(.006,float('inf'))
    for frame in range(120):
        if frame%3==0:
            target=np.zeros((2,3))
            if frame>=30: target[:,1]=1
            if gated: target=gate.update(target,frame/60)
            state=filter_fn(state,target,.05)
        rendered+=(state[1,1]-rendered)*(1-np.exp(-render_gain/60))
        samples.append(rendered)
    reach=next(i for i in range(30,120) if samples[i]>=.9)
    return dict(step_90_percent_ms=(reach-30+1)*1000/60,trajectory=samples)


if __name__=='__main__':
    report={'scope':'Synthetic unit step at 20 Hz plus scalar approximation of render easing at 60 Hz. No inference/camera/UDP/quaternion/IK latency measured.',
            'old':run(old_filter,16),'new':run(filter_arm,36,True)}
    assert report['new']['step_90_percent_ms']<report['old']['step_90_percent_ms']
    output=ROOT/'results'/'arm-response-synthetic.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:value['step_90_percent_ms'] for key,value in report.items() if isinstance(value,dict)}))
