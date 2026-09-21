"""Make one-at-a-time avatar-only arm-correction videos from a completed replay."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from tanakacap.models import sha256
from render_comparison_videos import run as render


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True,help='Completed compare_precision output')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=json.loads((args.source/'report.json').read_text(encoding='utf-8'))
    assert report['status']=='complete'
    source=args.source/'recorded/replay.jsonl'
    rows=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    active={side:[r['packet'] for r in rows if r['packet'].get(side+'ArmTracked') and not r['packet'].get(side+'ArmHeld')]
            for side in ('left','right')}
    # Current automatic front_projection bypasses the legacy model branch.
    # Do not activate an unrelated algorithm to manufacture a visible difference.
    for side,packets in active.items():
        assert packets and all(p[side+'WristInFront'] and not p[side+'UpperInFront'] for p in packets)
    variants=[('00-base','none','0 Base - projection only'),
              ('01-head','head','1 Base + nearest head surface'),
              ('02-cross-body','cross-body','2 Base + cross-body clearance'),
              ('03-wrist-front','wrist-front','3 Base + wrist front clamp'),
              ('04-legacy-front','legacy-front','4 Legacy front - inactive in this path'),
              ('05-outward-elbow','outward-elbow','5 Base + posterior elbow selection')]
    controls=args.output.with_name(args.output.name+'-controls');controls.mkdir(exist_ok=False)
    descriptions={}
    for name,policy,label in variants:
        folder=controls/name;folder.mkdir();shutil.copyfile(source,folder/'replay.jsonl')
        descriptions[name]=dict(label=label,player_args=['--expression-mode','auto-custom',
            '--diagnostic-arm-correction',policy],expected_log=['TANAKACAP_ARM_CORRECTION_TRIAL '+policy])
    info=dict(status='complete',variants=descriptions,layout_columns=3,
        source_video_sha256=report['source_video_sha256'],source_replay_sha256=sha256(source),
        source_frames=len(rows),active_arm_observations={s:len(p) for s,p in active.items()},
        scope='One correction enabled at a time on identical recorded controls and auto-custom avatar. '
              'FrontProjection remains active including its shoulder-front endpoint branch. Manual calibration prior remains implemented but is not exercised by this automatic capture. '
              'Legacy inward/front model branch is bypassed by FrontProjection and is identical to base. '
              'Posterior elbow selection is an additional displayed-pose correction also disabled in base. '
              'No raw camera images. No ground truth or live latency claim.')
    (controls/'report.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    render(args.output,controls)
    rendered=json.loads((args.output/'report.json').read_text())
    for name,policy,_ in variants:
        value=rendered[name];assert value['armCorrection']==policy
        for key,expected in [('headCorrections','head'),('crossBodyCues','cross-body'),
                             ('wristFrontClamps','wrist-front'),('outwardElbowCues','outward-elbow')]:
            if policy!=expected:assert value[key]==0,(name,key,value[key])
    ff=ROOT/'tools/bin/ffmpeg.exe'
    # Animated shaders/secondary motion may differ at process startup. Compare
    # actual arm bones, not whole-frame pixels, to establish correction isolation.
    def poses(name):
        return np.array([[[p[key][axis] for axis in 'xyz'] for key in ('leftElbow','leftWrist','rightElbow','rightWrist')]
                         for p in rendered[name]['armPoses']])
    base=poses('00-base');assert len(base)==rendered['00-base']['frames']
    pose_errors={name:float(np.max(np.abs(poses(name)-base))) for name,_,_ in variants}
    assert pose_errors['04-legacy-front']<1e-5,'Inactive legacy changed arm bones'
    rendered['max_arm_bone_difference_metres']=pose_errors
    for name,policy,label in variants[1:]:
        output=args.output/('compare-'+name+'.mp4')
        font='C\\:/Windows/Fonts/arial.ttf'
        filters=[]
        for i,text in enumerate(['Base - projection only',label]):
            filters.append(f"[{i}:v]pad=iw:ih+48:0:48:color=0x161c26,drawtext=fontfile='{font}':text='{text}':fontcolor=white:fontsize=25:x=20:y=10[v{i}]")
        subprocess.run([str(ff),'-v','error','-n','-i',str(args.output/'00-base.mp4'),'-i',str(args.output/(name+'.mp4')),
            '-filter_complex',';'.join(filters)+';[v0][v1]hstack=inputs=2[out]','-map','[out]','-an',
            '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],
            check=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run([str(ff),'-v','error','-xerror','-i',str(output),'-f','null','-'],check=True,timeout=300,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        rendered['videos'][output.name]=dict(sha256=sha256(output),bytes=output.stat().st_size)
    (args.output/'report.json').write_text(json.dumps(rendered,indent=2),encoding='utf-8')
    print(args.output,flush=True)


if __name__=='__main__':main()
