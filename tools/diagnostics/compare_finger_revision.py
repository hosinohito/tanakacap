"""Replay saved hand observations before/after a finger implementation revision."""
import argparse, copy, json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.fingers import FingerTracker
from tanakacap.models import sha256

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records',type=Path,required=True)
    p.add_argument('--reference-report',type=Path,required=True)
    p.add_argument('--before-revision',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    source=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','show',f'{a.before_revision}:tanakacap/fingers.py'],cwd=ROOT,text=True)
    namespace={'__name__':'tanakacap.fingers_before','__package__':'tanakacap'}
    exec(compile(source,'fingers_before.py','exec'),namespace)
    ref=json.loads(a.reference_report.read_text(encoding='utf-8'))
    settings=ref['settings'];block=settings['observation_block'];stride=settings['observation_stride']
    trackers={'before':namespace['FingerTracker'](block,stride),'left-sign-reversed':FingerTracker(block,stride)}
    a.output.mkdir(parents=True,exist_ok=False)
    streams={}
    for name in trackers:
        folder=a.output/name;folder.mkdir();streams[name]=(folder/'replay.jsonl').open('w',encoding='utf-8')
    previous=None;changed=0;count=0
    try:
        for line in a.records.read_text(encoding='utf-8').splitlines():
            row=json.loads(line);now=row['time'];packets={}
            for name,tracker in trackers.items():
                packet=copy.deepcopy(row['packet'])
                if 'xy' in row:
                    xy=np.array(row['xy']);z=np.array(row['z']);scale=row['scale']
                    xyz=np.zeros((133,3));scores=np.zeros(133);ds=np.zeros(133)
                    xyz[91:]=np.column_stack((-xy[:,0]*scale,-xy[:,1]*scale,-z))
                    scores[91:]=row['scores'];ds[91:]=row['depth_scores']
                    tracker.update(packet,xyz,scores,ds,now)
                packets[name]=packet
                streams[name].write(json.dumps(dict(packet=packet,dt=1/30 if previous is None else now-previous))+'\n')
            before=packets['before'];after=packets['left-sign-reversed']
            assert before==row['packet'],f'Baseline reproduction differs at {row["frame"]}'
            for key,value in before.items():
                if key!='leftFingerFlex':assert after[key]==value,(row['frame'],key)
            changed+=before['leftFingerFlex']!=after['leftFingerFlex'];count+=1;previous=now
    finally:
        for stream in streams.values():stream.close()
    args=ref['variants']['original']['player_args']
    report=dict(status='complete',variants={n:dict(label=('Before' if n=='before' else 'Left finger sign reversed'),player_args=args) for n in trackers},
        scope='Same cached original FP16 recording observations and timestamps. Only left signed finger flexion differs; no raw video displayed. Avatar quality unverified.',
        source=str(a.records),source_sha256=sha256(a.records),before_revision=a.before_revision,frames=count,changed_frames=changed,baseline_exact=True,other_channels_exact=True)
    (a.output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
