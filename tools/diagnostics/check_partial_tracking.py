"""Exercise part telemetry with saved input and the real UI process controller."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.control_panel import DEFAULT, Session


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video',type=Path)
    parser.add_argument('--frames',type=int,default=240)
    parser.add_argument('--synthetic-only',action='store_true')
    args=parser.parse_args()
    output=ROOT/'results/partial-tracking';output.mkdir(parents=True,exist_ok=True)
    for arm in (True,False):
        fixture=dict(sequence=0,faceTracked=False,headTracked=False,body3d=True,
            leftArmTracked=arm,leftHandTracked=True,
            leftElbow=dict(x=-.5,y=-.2,z=.3),leftWrist=dict(x=-.3,y=.3,z=1.),
            leftHandForward=dict(x=0,y=1,z=0),leftHandNormal=dict(x=0,y=0,z=-1),
            leftFingerTracked=[True]*5,leftFingerFlex=[0,25,30]+[35,65,45]*4)
        name='arm-without-face' if arm else 'palm-without-arm'
        path=output/(name+'.json');path.write_text(json.dumps(fixture),encoding='utf-8')
        subprocess.run([sys.executable,str(ROOT/'tools/smoke_unity.py'),
                        '--packet-file',str(path),'--output',str(output/(name+'.png'))],check=True,cwd=ROOT)
    if args.synthetic_only:return
    video=args.video or next((ROOT/'results/comparison-takes').glob('*/camera.avi'))
    results=[]
    for mode in ('full','face_head','head_only'):
        session=Session();samples=[];messages=[];seen={};start=time.monotonic()
        config={**DEFAULT,'source':'video','video':str(video),'mode':mode,
                'expression':'auto-custom','avatar':str(ROOT/'builds/player/avatars/haolan.tcap')}
        try:
            session.start(config,frames=args.frames)
            while time.monotonic()-start<120:
                for kind,value in session.poll().items():
                    if seen.get(kind)!=session.last[kind]:
                        seen[kind]=session.last[kind];samples.append(dict(value,at=time.monotonic()-start))
                while not session.messages.empty():messages.append(session.messages.get_nowait())
                if session.infer.poll() is not None:break
                if session.player.poll() is not None:raise RuntimeError('Player exited')
                time.sleep(.03)
            assert session.infer.poll()==0,messages[-15:]
            player=[sample for sample in samples if sample['kind']=='player' and sample.get('parts')]
            assert player,'No part telemetry'
            parts=[part for sample in player for part in sample['parts']]
            assert len({part['id'] for part in parts})==13
            assert any(part['id']=='head' and part['state']=='valid' and part['intervalMs']>0 for part in parts)
            if mode=='head_only':assert all(part['state']=='disabled' for part in parts if part['id']!='head')
            inference=[sample for sample in samples if sample['kind']=='inference']
            summary=dict(mode=mode,inferenceHz=statistics.median(sample['hz'] for sample in inference),
                         busyMs=statistics.median(sample['busyMs'] for sample in inference),
                         parts={key:statistics.median(p['intervalMs'] for p in parts if p['id']==key and p['state']=='valid' and p['intervalMs']>0)
                                for key in {p['id'] for p in parts if p['state']=='valid' and p['intervalMs']>0}})
            (output/(mode+'.json')).write_text(json.dumps(dict(summary=summary,samples=samples),indent=2),encoding='utf-8')
            (output/(mode+'.log')).write_text('\n'.join(messages),encoding='utf-8')
            print(summary,flush=True);results.append(summary)
        finally:
            session.stop()
            deadline=time.monotonic()+15
            while session.stopping and time.monotonic()<deadline:time.sleep(.1)
            assert not session.running
            session.sock.close()
    (output/'report.json').write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__=='__main__':main()
