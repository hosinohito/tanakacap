"""Numeric checks only: motion is not labeled as true movement or jitter."""
import json
import sys
import time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.arm_width import measure_arm_widths

def main():
    source=ROOT/'results/20260911T180020-133848Z-rtmw-l-384/frames.jsonl'
    rows=[json.loads(s) for s in source.read_text().splitlines()]
    yaw=np.array([r['sent_packet']['torsoYaw'] for r in rows])
    raw=np.array([r['body_diagnostics'].get('torso_raw_angles',[0,0,0])[1] for r in rows])
    image=np.zeros((720,1280,3),np.uint8);image[50:600,380:420]=[90,150,210]
    xy=np.zeros((133,2));s=np.zeros(133);xy[[7,9]]=[[400,100],[400,550]];s[[7,9]]=1
    elapsed=[]
    for _ in range(500):
        start=time.perf_counter();width=measure_arm_widths(image,xy,s,.002);elapsed.append((time.perf_counter()-start)*1000)
    gpu=json.loads((ROOT/'results/20260911T180755-607527Z-rtmw-l-384/report.json').read_text())
    summary={'source':str(source),'frames':len(rows),
        'raw_yaw_step_abs_p50_p95_max':np.percentile(abs(np.diff(raw)),[50,95,100]).tolist(),
        'sent_yaw_step_abs_p50_p95_max':np.percentile(abs(np.diff(yaw)),[50,95,100]).tolist(),
        'depth_bin_model_units':2.1744869/288,
        'one_bin_yaw_near_zero_degrees':float(np.degrees(np.arctan2(2.1744869/288,.36))),
        'image_width_synthetic':width,'image_width_ms_p50_p95':np.percentile(elapsed,[50,95]).tolist(),
        'gpu_body_execution':gpu['body_execution'],'gpu_synthetic_pipeline_ms':gpu.get('pipeline_ms'),
        'limitations':'No source images or raw SimCC distributions in old recording: cannot reproduce new decoder or measure true jitter reduction. Synthetic width contrast is not real sleeve accuracy.'}
    out=ROOT/'results/width-subbin';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
