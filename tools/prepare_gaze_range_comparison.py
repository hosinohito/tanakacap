"""Compare calibration only, using the identical recorded iris observations."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capture_lab.gaze_range import GazeRange
from capture_lab.motion_gate import DirectionGate


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def main():
    source=ROOT/'results/gaze-range'
    diagnostics=read(source/'diagnostics.jsonl')
    saved=read(source/'replay.jsonl')
    times=read(ROOT/'results/comparisons/head-follow-input/source/frames.jsonl')
    gates={name:DirectionGate(.35,float('inf'),3,1) for name in ('range-off','range-on')}
    calibration=GazeRange()
    streams={name:[] for name in gates}
    for d,row,time in zip(diagnostics,saved,times,strict=True):
        assert d['frame']==time['frame']
        values=[v['offset'] for v in d['eyes'].values() if v['offset'] is not None]
        for name,gate in gates.items():
            packet=dict(row['packet'])
            packet.update(gazeTracked=False,gazeYaw=0.,gazePitch=0.)
            if d['valid_eyes']:
                assert len(values)==d['valid_eyes']
                value=np.mean(values,axis=0)
                if name=='range-on':
                    value=calibration.update(value,time['time'],learn=len(values)==2)
                accepted=gate.update(np.clip(value*[-80,60],[-20,-12],[20,12]),time['time'])
                if accepted is not None:
                    packet.update(gazeTracked=True,gazeYaw=float(accepted[0]),gazePitch=float(accepted[1]))
            else:
                gate.reset()
            if name=='range-on':
                assert packet==row['packet'], 'Calibrated replay must exactly reproduce the inference run'
            streams[name].append(dict(packet=packet,dt=row['dt']))
    output=ROOT/'results/comparisons/gaze-range'
    output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name,rows in streams.items():
        folder=output/name;folder.mkdir()
        (folder/'replay.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
        variants[name]=dict(frames=len(rows),player_args=[
            '--avatar',str(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap'),
            '--use-demo-shape-keys'])
    report=dict(status='complete',variants=variants,calibrated_reproduction='exact',
        scope='Same 853 recorded iris observations with PnP validity gates, same head/body/expressions/timestamps. Left range-off; right supported range midpoint calibration. Both use current soft gaze response and maximum-exaggeration demo. Calibration starts empty. Offline playback, no raw imagery, not a latency measurement.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('853 packets: calibrated reconstruction exact; only gaze fields differ')


if __name__=='__main__':main()
