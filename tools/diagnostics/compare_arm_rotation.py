"""Compare parent-relative elbow rotation and twist limits on identical replay."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from render_comparison_videos import run,sha
from audit_elbow_twist import summarize


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    controls=args.output.with_name(args.output.name+'-controls');controls.mkdir(parents=True,exist_ok=False)
    choices=[('legacy','Previous - independent rotations'),('hinge','Coupled - same 160 deg limit'),
             ('hinge-90','Coupled - 90 deg limit'),('hinge-unlimited','Coupled - no twist limit')]
    variants={}
    for name,label in choices:
        folder=controls/name;folder.mkdir();shutil.copyfile(args.replay,folder/'replay.jsonl')
        variants[name]=dict(label=label,player_args=['--expression-mode','auto-custom','--diagnostic-arm-rotation',name],
            expected_log=['TANAKACAP_ELBOW_AXIS left','TANAKACAP_ELBOW_AXIS right'])
    info=dict(status='complete',variants=variants,layout_columns=2,
        scope='Identical recorded controls and all retained arm corrections ON. Only arm rotation composition and diagnostic twist limits differ. Automatic custom avatar. No raw imagery.')
    (controls/'report.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    run(args.output,controls)
    audits=[summarize(args.output/(name+'.mp4.json')) for name,_ in choices]
    (args.output/'twist-audit.json').write_text(json.dumps(audits,indent=2),encoding='utf-8')
    ff=ROOT/'tools/bin/ffmpeg.exe';output=args.output/'previous-vs-coupled.mp4'
    filters=[]
    for i,label in enumerate([choices[0][1],choices[1][1]]):
        filters.append(f"[{i}:v]pad=iw:ih+48:0:48:color=0x161c26,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{label}':fontcolor=white:fontsize=25:x=20:y=10[v{i}]")
    subprocess.run([str(ff),'-v','error','-n','-i',str(args.output/'legacy.mp4'),'-i',str(args.output/'hinge.mp4'),
        '-filter_complex',';'.join(filters)+';[v0][v1]hstack=inputs=2[out]','-map','[out]','-an',
        '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],
        check=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.run([str(ff),'-v','error','-xerror','-i',str(output),'-f','null','-'],check=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
    path=args.output/'report.json';report=json.loads(path.read_text());report['videos'][output.name]=dict(sha256=sha(output),bytes=output.stat().st_size)
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(output,flush=True)


if __name__=='__main__':main()
