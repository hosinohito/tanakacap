"""Compare original/compact GPU outputs on recorded frames; no camera or visual review."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capture_lab.inference import SimCCModel

out=ROOT/'results/compact-simcc-audit'
out.mkdir(exist_ok=True)
base=SimCCModel('rtmw3d-x-384',None,execution_mode='graph',preprocess_mode='crop')
trial=SimCCModel('rtmw3d-x-384',out,execution_mode='graph',preprocess_mode='crop',gpu_decode=True)
cap=cv2.VideoCapture(str(ROOT/'results/comparison-takes/20260911T235327-031115Z/camera.avi'))
maximum={'xy':0.,'score':0.,'z':0.,'z_score':0.}
count=0
for i in range(80):
    cap.set(cv2.CAP_PROP_POS_FRAMES,i*60)
    ok,frame=cap.read()
    if not ok:break
    roi=[(0,0,1280,720),(320,20,640,680),(-20,-10,1300,730),(300.25,12.5,690.5,700)][i%4]
    p,s,_=base.predict(frame,roi);q,t,_=trial.predict(frame,roi)
    for key,a,b in [('xy',p,q),('score',s,t),('z',base.depth,trial.depth),('z_score',base.depth_scores,trial.depth_scores)]:
        assert np.array_equal(np.isnan(a),np.isnan(b)),key
        maximum[key]=max(maximum[key],float(np.nanmax(np.abs(a-b))))
    assert base.decode_diagnostics==trial.decode_diagnostics
    count+=1
cap.release()
profile=trial.finish()
result={'frames':count,'maximum_absolute_difference':maximum,'profile':profile,
        'output_bytes_before':133*(576+768+576)*4,'output_bytes_after':3*133*5*4}
(out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
assert count==80 and all(v==0 for v in maximum.values())
