"""Sequential all-model comparisons; no renderer or OBS unless tested separately."""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('B','C','D','face'),default='B')
    parser.add_argument('--frames',type=int,default=900)
    parser.add_argument('--landmarks',action='store_true')
    args=parser.parse_args()
    out=ROOT/'results'/('full-optimization-'+args.stage+'-'+str(time.time_ns()));out.mkdir()
    modes={'B':{'run':['--inference-mode','run'],'binding':['--inference-mode','binding'],
                'graph':['--inference-mode','graph']},
           'C':{'every-frame':['--inference-mode','graph','--detector-interval','1'],
                'interval3':['--inference-mode','graph','--detector-interval','3']},
           'D':{'medium':['--inference-mode','graph','--detector-interval','3'],
                'tiny':['--inference-mode','graph','--detector-interval','3','--detector-model','yolox-tiny-human']},
           'face':{'separate':['--inference-mode','graph','--detector-interval','3','--face-source','separate'],
                   'body3d':['--inference-mode','graph','--detector-interval','3','--face-source','body3d']}}[args.stage]
    reports={}
    for name,extra in modes.items():
        command=[sys.executable,'-m','capture_lab','benchmark','--source','video','--video',
            str(ROOT/'results/comparison-takes/20260911T235327-031115Z/camera.avi'),
            '--frames',str(args.frames),'--warmup','30','--body3d','--gaze','--unity-port','39549',
            '--no-ort-profile','--arm-depth-mode','front_projection','--shoulder-yaw-mode','face_ratio',*extra]
        if args.landmarks: command+=['--landmarks']
        with (out/(name+'.log')).open('wb') as log:
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
        text=(out/(name+'.log')).read_text(encoding='utf-8',errors='replace').replace('\0','')
        folder=Path(re.search(r'Results: ([^\r\n]+)',text)[1])
        r=json.loads((folder/'report.json').read_text())
        reports[name]=dict(report=str(folder.relative_to(ROOT)/'report.json'),
                          pose_frames=r['pose_frames'],timings=r['timings'],coverage=r['coverage'])
        (out/'summary.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
        print(name,{k:round(v['p50'],3) for k,v in r['timings'].items() if v and k in
            ('iteration_ms','face_model_ms','body3d_ms','gaze_ms','detector_ms')},flush=True)
    print(out)


if __name__=='__main__':main()
