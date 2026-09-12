"""Recorded-input fidelity audit for trial K; reports differences, never calls a camera."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capture_lab.inference import SimCCModel,preprocess,provider_summary

out=ROOT/'results/gpu-preprocess-audit';out.mkdir(exist_ok=True)
base=SimCCModel('rtmw3d-x-384',None,execution_mode='graph',preprocess_mode='crop')
trial=SimCCModel('rtmw3d-x-384',out,execution_mode='graph',preprocess_mode='crop',gpu_preprocess=True)
cap=cv2.VideoCapture(str(ROOT/'results/comparison-takes/20260911T235327-031115Z/camera.avi'))
rows=[]
for i in range(80):
    cap.set(cv2.CAP_PROP_POS_FRAMES,i*60);ok,frame=cap.read()
    if not ok:break
    roi=[(0,0,1280,720),(320,20,640,680),(-20,-10,1300,730),(300.25,12.5,690.5,700)][i%4]
    p,s,_=base.predict(frame,roi);q,t,_=trial.predict(frame,roi)
    old,_,_=preprocess(frame,roi,(288,384),'RGB')
    new=trial.preprocessor.output.numpy()
    confident=(s>.3)&(t>.3)
    delta=np.linalg.norm(p-q,axis=1)
    rows.append(dict(frame=i*60,input_max=float(np.max(np.abs(old-new))),
        input_changed_fraction=float(np.mean(old!=new)),
        xy_max=float(np.nanmax(delta)),xy_confident_max=float(np.nanmax(delta[confident])) if confident.any() else 0.,
        z_max=float(np.nanmax(np.abs(base.depth-trial.depth))),
        z_confident_max=float(np.nanmax(np.abs(base.depth-trial.depth)[confident])) if confident.any() else 0.,
        score_max=float(np.max(np.abs(s-t)))))
cap.release()
profile=trial.finish()
prep_path=Path(trial.preprocessor.session.end_profiling())
result={'frames':len(rows),'maxima':{k:max(r[k] for r in rows) for k in rows[0] if k!='frame'},
        'model_profile':profile,'preprocess_profile':provider_summary(prep_path),'rows':rows}
(out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
