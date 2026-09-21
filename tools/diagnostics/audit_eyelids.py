"""Measure recorded eyelid controls before/after filtering; never open a camera."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap import __main__ as app
from tanakacap.control_panel import load_settings, commands


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video',type=Path)
    parser.add_argument('--frames',type=int,default=900)
    args=parser.parse_args()
    config=load_settings()
    video=args.video or Path(config['video'])
    if not video.is_file():raise ValueError('A saved video is required')
    config.update(source='video',video=str(video),mode='full',body=True)
    _,command=commands(config,39549,39548,0)
    argv=['tanakacap',*command[3:]]
    for option in ('--parent-pid','--status-port'):
        index=argv.index(option);del argv[index:index+2]
    argv.remove('--loop-video')
    argv[argv.index('--frames')+1]=str(args.frames)
    rows=[]
    original=app.FaceFilter.update
    def observe(self,pose,now):
        row=dict(frame=pose['sequence'],rawValid=bool(pose.get('faceTracked')),
                 rawLeft=float(pose['leftBlink']),rawRight=float(pose['rightBlink']))
        result=original(self,pose,now)
        row.update(filteredValid=bool(pose['faceTracked']),filteredLeft=float(pose['leftBlink']),filteredRight=float(pose['rightBlink']))
        rows.append(row)
        return result
    class Sink:
        def __init__(self,port):pass
        def send(self,pose,parts=None,**kwargs):pass
        def close(self):pass
    output=ROOT/'results/eyelid-audit';output.mkdir(parents=True,exist_ok=True)
    with (output/'inference.log').open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log),patch.object(sys,'argv',argv),patch.object(app,'LocalSender',Sink),patch.object(app.FaceFilter,'update',observe),patch.dict(os.environ,{'TANAKACAP_UI_PRECISION':config['precision']}):
        app.main()
    summary=dict(video=str(video),frames=len(rows),scope='Recorded numeric predictions; no visual ground truth or camera activation',controls={})
    for stage in ('raw','filtered'):
        valid=[r for r in rows if r[stage+'Valid']]
        for side in ('Left','Right'):
            values=np.array([r[stage+side] for r in valid])
            summary['controls'][stage+side]=dict(valid=len(valid),maximum=float(values.max()) if len(values) else None,
                above_01=int((values>.1).sum()),above_05=int((values>.5).sum()),above_09=int((values>.9).sum()))
    (output/'frames.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n',encoding='utf-8')
    (output/'report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
