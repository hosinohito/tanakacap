"""Exercise experimental UI settings through the real process controller on recorded input."""
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.control_panel import DEFAULT, Session, recorded_test_settings


def main():
    output=ROOT/'results/ui-experiments';output.mkdir(exist_ok=True)
    results={}
    variants={
        'hinge-90':dict(arm_rotation='hinge-90'),
        'legacy-wrist':dict(arm_rotation='legacy',hand_head_contact='wrist',cross_body='off',wrist_front='off',outward_elbow='off'),
        'integer-no-head':dict(body_peaks='integer',head_clearance='off',head_pitch_gain=2.2,brow_gain=1.5,mouth_lip_depth_scale=1.),
    }
    for name,options in variants.items():
        config=dict(recorded_test_settings(DEFAULT),expression='auto-custom',**options)
        session=Session();samples=[];messages=[]
        try:
            session.start(config,frames=120)
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                status=session.poll()
                if status:samples.append(status)
                while not session.messages.empty():messages.append(session.messages.get_nowait())
                if session.player.poll() is not None:raise RuntimeError('Player exited: '+name)
                if session.infer.poll() is not None:break
                time.sleep(.1)
            if session.infer.poll()!=0:raise RuntimeError(str(messages[-10:]))
            if not any(s.get('player') for s in samples):raise RuntimeError('No Player telemetry')
            if not any(s.get('inference') for s in samples):raise RuntimeError('No inference telemetry')
            results[name]=dict(config=config,samples=samples,messages=messages)
            (output/'report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
            print(name,'passed',flush=True)
        finally:
            session.stop()
            deadline=time.monotonic()+20
            while session.stopping and time.monotonic()<deadline:time.sleep(.1)
            if session.stopping:raise RuntimeError('Session failed to stop')
            session.sock.close()


if __name__=='__main__':main()
