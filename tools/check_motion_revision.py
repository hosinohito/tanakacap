"""Compare recorded controls, revised front constraints, and block gate timing."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.motion_gate import DirectionGate
from tanakacap.body_geometry import visible_in_front_of_torso


def main():
    name='20260911T140701-321003Z-rtmw-l-384'
    rows=[json.loads(line) for line in (ROOT/'results'/name/'frames.jsonl').read_text().splitlines()]
    report={'source':name,'frames':len(rows),'limitation':'Landmark replay and synthetic timing, not ground-truth pose accuracy or camera-to-display latency.'}
    for size in (1,3):
        packets=[json.loads(line)['packet'] for line in (ROOT/'results'/f'average{size}-final-20260911T140701'/'packets.jsonl').read_text().splitlines()]
        metric={'max_udp_bytes':max(len(json.dumps(p,separators=(',',':'),allow_nan=False).encode()) for p in packets)}
        for side in ('left','right'):
            active=[p for p in packets if p.get(side+'ArmTracked') and p.get(side+'WristInFront')]
            violation=sum(p[side+'Wrist']['z']<0 for p in active)
            assert violation==0
            old=sum(bool(row.get('body_xy') is not None and
                         visible_in_front_of_torso(row['body_xy'],row['body_scores'],side) and
                         row['sent_packet'].get(side+'ArmTracked') and row['sent_packet'][side+'Wrist']['z']<0) for row in rows)
            metric[side]={'new_front_active_frames':len(active),'new_negative_wrist_frames':violation,
                          'recorded_negative_wrist_with_current_overlap_cue':old}
        assert metric['max_udp_bytes']<=4096
        report[f'block{size}']=metric
    report['synthetic_step_timing']=[]
    for fps in (10,20,30):
        for size in (1,3):
            gate=DirectionGate(.01,float('inf'),size)
            for i in range(6): gate.update([0],i/fps)
            for i in range(12):
                v=gate.update([1],(6+i)/fps)
                if v is not None and v[0]>=.9:
                    report['synthetic_step_timing'].append(dict(fps=fps,block_size=size,
                        changed_frames=i+1,delay_from_first_changed_observation_ms=round(i/fps*1000,3)))
                    break
    intervals=[row['result_interval_ms'] for row in rows if row.get('result_interval_ms') is not None]
    report['recorded_median_observation_interval_ms']=float(np.median(intervals))
    out=ROOT/'results'/'motion-revision-report.json'
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
