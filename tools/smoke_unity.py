"""Exercise the actual player receiver using explicit synthetic controls, without a camera."""
import json
import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capture_lab.retarget import LocalSender


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion-check',action='store_true',help='Also check actual bone rotation paths with synthetic trajectories')
    parser.add_argument('--expression-mode',choices=['existing','auto-custom'],default='existing')
    parser.add_argument('--mouth-corner-gamma',type=float)
    parser.add_argument('--mouth-open-smile-suppression',type=float)
    parser.add_argument('--mouth-corner-emphasis',type=float)
    parser.add_argument('--obs',action='store_true',help='Check RGBA output and live Spout sender registration')
    parser.add_argument('--gaze-bones',action='store_true',help='Compare original eye-bone gaze rendering')
    parser.add_argument('--no-face-distance',action='store_true',help='Disable relative avatar depth')
    parser.add_argument('--face-distance-translate',action='store_true',help='Use previous whole-avatar translation')
    parser.add_argument('--gaze-gain',type=float,default=4.,help='Gaze display gain, 1 restores the previous sensitivity')
    parser.add_argument('--replay-file',type=Path,help='Numeric packet JSONL for actual-bone audit after snapshot')
    parser.add_argument('--packet-file',type=Path,help='Hold one recorded/reprocessed packet to verify bone transfer, not capture accuracy')
    parser.add_argument('--output',type=Path,help='Explicit snapshot output for automated comparisons')
    parser.add_argument('--output-width',type=int)
    parser.add_argument('--output-height',type=int)
    parser.add_argument('--no-preview',action='store_true')
    parser.add_argument('--legacy-preview',action='store_true')
    args=parser.parse_args()
    if args.motion_check and args.replay_file:
        parser.error('Run motion-check and replay-file separately: they must not share modified joint history')
    if args.motion_check and args.packet_file:
        parser.error('Run motion-check and packet-file separately: recorded facial state affects synthetic assertions')
    fixture=json.loads(args.packet_file.read_text(encoding='utf-8')) if args.packet_file else None
    output = args.output or ROOT / 'results' / 'unity' / 'transport.png'
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        output = output.with_name(f'transport-{time.time_ns()}.png')
    player = ROOT / 'builds' / 'lab' / 'TanakaCap.exe'
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
        probe.bind(('127.0.0.1',0))
        test_port=probe.getsockname()[1]
    render_args=['--expression-mode',args.expression_mode]
    for key in ('mouth_corner_gamma','mouth_open_smile_suppression','mouth_corner_emphasis'):
        value=getattr(args,key)
        if value is not None:render_args+=['--'+key.replace('_','-'),str(value)]
    for key in ('output_width','output_height'):
        value=getattr(args,key)
        if value is not None:
            if not 64<=value<=4096:parser.error('Output dimensions must be 64..4096')
            render_args+=['--'+key.replace('_','-'),str(value)]
    if args.no_preview:render_args+=['--no-preview']
    if args.legacy_preview:render_args+=['--legacy-preview']
    process = subprocess.Popen([str(player)]+render_args+([] if args.obs else ['-batchmode'])+['--snapshot',str(output),
                                '--port',str(test_port),'--gaze-gain',str(args.gaze_gain),
                                '-logFile',str(output.with_suffix('.log'))]+(['--face-distance-translate'] if args.face_distance_translate else [])+(['--no-face-distance'] if args.no_face_distance else [])+(['--gaze-bones'] if args.gaze_bones else [])+(['--obs'] if args.obs else [])+(['--motion-check'] if args.motion_check else [])+(['--replay-file',str(args.replay_file.resolve())] if args.replay_file else []),cwd=ROOT,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    sender = LocalSender(test_port)
    start = time.monotonic()
    sequence = 0
    try:
        while process.poll() is None and time.monotonic()-start < 45:
            controls=dict(version=1,sequence=sequence,tracked=True,faceTracked=True,
                             headPitch=0,headYaw=25,headRoll=10,mouth=.75,mouthWidth=.5,leftBlink=1,rightBlink=0,
                             body3d=True,torsoTracked=True,torsoYaw=-25,torsoPitch=15,
                             torsoRoll=5,leftArmTracked=True,rightArmTracked=False,
                             leftHandTracked=True,leftHandForward=dict(x=0,y=1,z=0),leftHandNormal=dict(x=0,y=0,z=-1),
                             leftElbow=dict(x=-.5,y=-.2,z=.3),leftWrist=dict(x=-.3,y=.3,z=1.))
            if fixture is not None:
                controls=dict(fixture,sequence=sequence)
            if fixture is None:
                controls.update(leftFingerTracked=[True]*5,rightFingerTracked=[True]*5,
                                leftFingerFlex=[0,25,30]+[35,65,45]*4,rightFingerFlex=[0,20,25]+[20,40,30]*4)
            assert len(json.dumps(controls).encode()) <= 4096
            sender.send(controls)
            sequence += 1
            time.sleep(1/30)
        if process.poll() is None:
            process.terminate()
            raise RuntimeError('Player snapshot timed out')
        if process.returncode != 0:
            raise RuntimeError(f'Player failed: {process.returncode}')
        received = json.loads(Path(str(output)+'.tracking.json').read_text(encoding='utf-8-sig'))
        actual=json.loads(Path(str(output)+'.bones.json').read_text(encoding='utf-8-sig'))
        if fixture is None:
            assert received['tracked'] and received['headYaw'] == 25 and received['leftBlink'] == 1
            assert actual['torsoRotationError']<1,actual
            assert received['body3d'] and received['torsoYaw'] == -25 and received['leftWrist']['z'] == 1
            assert received['leftHandTracked'] and received['leftHandNormal']['z'] == -1
            assert actual['leftWristSwing']<=91 and actual['leftWristTwist']<=41, actual
        else:
            import numpy as np
            checked=0
            for side in ('left','right'):
                if not fixture.get(side+'HandTracked'):
                    continue
                assert received[side+'HandTracked']
                for suffix in ('HandForward','HandNormal'):
                    key=side+suffix
                    wanted=np.array([fixture[key][axis] for axis in 'xyz'])
                    got=np.array([actual[key][axis] for axis in 'xyz'])
                    assert np.isfinite(got).all() and abs(np.linalg.norm(got)-1)<.01
                assert actual[side+'WristSwing']<=91 and actual[side+'WristTwist']<=41, actual
                assert abs(actual[side+'ForearmTwist'])<=160.1
                checked+=1
            assert checked or fixture.get('faceTracked') or fixture.get('headTracked'), 'Fixture must contain a valid palm, face or head'
            if fixture.get('faceTracked') or fixture.get('headTracked'):
                assert abs(actual['headPitchApplied']-float(np.clip(fixture.get('headPitch',0),-40,40)))<.2,actual
            if fixture.get('gazeTracked') and fixture.get('faceTracked'):
                for field,limit in [('Yaw',20),('Pitch',12)]:
                    expected=float(np.clip(fixture['gaze'+field]*args.gaze_gain,-limit,limit))
                    assert abs(actual['gaze'+field+'Applied']-expected)<.2,actual
            if fixture.get('faceDistanceTracked') and fixture.get('faceTracked'):
                bounds=(.75,1.5) if args.face_distance_translate else (.34,2.86)
                expected=1. if args.no_face_distance else float(np.clip(fixture['faceDistanceRatio'],*bounds))
                assert abs(actual['faceDistanceRatioApplied']-expected)<.002,actual
        assert actual['lossHoldVerified']
        assert actual['mouthWidthVerified']
        if fixture is None: assert abs(actual['mouthWidthWeight']-50)<1,actual
        if args.motion_check:
            motion=json.loads(Path(str(output)+'.motion.json').read_text(encoding='utf-8-sig'))
            assert len(motion['paths'])==4 and motion['frontPoseVerified']
            print(json.dumps([{k:v for k,v in p.items() if k!='forearmAngles'} for p in motion['paths']],indent=2))
        if fixture is None:
            for side, expected in [('left',[0,25,30]+[35,65,45]*4),('right',[0,20,25]+[20,40,30]*4)]:
                assert all(abs(a-b)<1 for a,b in zip(actual[side+'FingerAngles'],expected)), actual
        assert output.exists() and output.stat().st_size > (1000 if args.no_preview else 10000)
        print(f'Actual Unity receiver and rendering succeeded: {output}')
    finally:
        sender.close()
        if process.poll() is None:
            process.terminate()


if __name__ == '__main__':
    main()
