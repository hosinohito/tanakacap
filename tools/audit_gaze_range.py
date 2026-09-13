"""Rerun iris tracking on saved frames without displaying any source image."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from tanakacap.gaze import IrisGaze

ROOT=Path(__file__).resolve().parents[1]

def main():
    output=ROOT/'results/gaze-range'
    output.mkdir(parents=True,exist_ok=False)
    rows=[json.loads(s) for s in (ROOT/'results/comparisons/head-follow-input/source/frames.jsonl').read_text().splitlines()]
    replay=[json.loads(s) for s in (ROOT/'results/brow-demo/replay.jsonl').read_text().splitlines()]
    video=cv2.VideoCapture(str(ROOT/'results/comparison-takes/20260912T230559-718866Z/camera.avi'))
    model=IrisGaze(output,3,1,execution_mode='graph-fp16',batch_eyes=True)
    learned=tracked=0
    try:
        with (output/'diagnostics.jsonl').open('w',encoding='utf-8') as diagnostics, (output/'replay.jsonl').open('w',encoding='utf-8') as stream:
            for row,saved in zip(rows,replay,strict=True):
                ok,frame=video.read()
                if not ok:raise RuntimeError('Recording ended early')
                packet=dict(saved['packet'])
                d=model.update(frame,np.asarray(row['xy']),np.asarray(row['scores']),packet,row['time'])
                stream.write(json.dumps(dict(packet=packet,dt=saved['dt']))+'\n')
                diagnostics.write(json.dumps(dict(frame=row['frame'],**d))+'\n')
                learned+=int(d['range_calibration']['ready'])
                tracked+=int(packet['gazeTracked'])
        report=dict(status='complete',frames=len(rows),tracked=tracked,execution=model.finish(),
                    final_range=model.range_calibration.report(),ready_frames=learned,
                    scope='Saved frames with saved PnP head gates, iris CUDA FP16 rerun. No source display or gaze ground truth.')
        (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(dict(final_range=report['final_range'],ready_frames=learned,tracked=tracked)))
    finally:
        video.release()

if __name__=='__main__':main()
