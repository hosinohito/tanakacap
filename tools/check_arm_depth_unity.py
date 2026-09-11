"""Isolate actual Unity depth retargeting from uncertain camera/model depth."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    output=ROOT/'results'/'unity'/f'arm-depth-{time.time_ns()}'
    output.mkdir()
    results={}
    for label,depth in [('plane',0.),('forward',1.)]:
        packet=dict(version=1,sequence=0,tracked=True,faceTracked=True,body3d=True,
                    torsoTracked=True,torsoYaw=0,torsoPitch=0,torsoRoll=0,
                    leftArmTracked=True,rightArmTracked=False,leftHandTracked=True,
                    leftElbow=dict(x=-.5,y=-.3,z=depth*.5),
                    leftWrist=dict(x=-.7,y=-.1,z=depth),
                    leftHandForward=dict(x=0,y=1,z=0),leftHandNormal=dict(x=0,y=0,z=1))
        fixture=output/(label+'.json')
        fixture.write_text(json.dumps(packet),encoding='utf-8')
        snapshot=output/(label+'.png')
        subprocess.run([sys.executable,str(ROOT/'tools/smoke_unity.py'),
                        '--packet-file',str(fixture),'--output',str(snapshot)],check=True,cwd=ROOT)
        results[label]=json.loads(Path(str(snapshot)+'.bones.json').read_text(encoding='utf-8-sig'))
    delta=results['forward']['leftWristRelative']['z']-results['plane']['leftWristRelative']['z']
    assert abs(results['plane']['leftWristRelative']['z'])<.03, results
    assert delta>.15, results
    (output/'report.json').write_text(json.dumps(dict(scope='Synthetic static packets -> actual Unity wrist positions; not camera accuracy',
                                                    forward_depth_increase=delta,bones=results),indent=2),encoding='utf-8')
    print(f'Actual arm depth transfer passed: {output} (delta Z={delta:.3f})')


if __name__=='__main__': main()
