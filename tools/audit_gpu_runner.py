"""B: verify CUDA buffer/graph execution against unchanged FP32 output tensors."""
import json
import sys
import time
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.inference import SimCCModel, PersonDetector, preprocess
from tanakacap.gaze import IrisGaze


def main():
    output=ROOT/'results'/('gpu-runner-audit-'+str(time.time_ns()));output.mkdir()
    cap=cv2.VideoCapture(str(ROOT/'results/comparison-takes/20260911T235327-031115Z/camera.avi'))
    frames=[]
    for index in (0,200,500,800):
        cap.set(cv2.CAP_PROP_POS_FRAMES,index)
        ok,image=cap.read();assert ok;frames.append(image)
    cap.release()
    frames.extend([np.zeros_like(frames[0]),frames[0]])
    reports={}
    for name in ('rtmw-l-384','rtmw3d-x-384','yolox-m-human','yolox-tiny-human','iris'):
        baseline=IrisGaze(None) if name=='iris' else SimCCModel(name,None)
        candidate=IrisGaze(output,execution_mode='graph') if name=='iris' else SimCCModel(name,output,execution_mode='graph')
        differences=[]
        for frame in frames:
            if name=='iris':
                # Two different image crops ensure successive eye buffers cannot be stale.
                tensor=np.ascontiguousarray(cv2.resize(frame[270:310,650:735],(64,64))[:,:,::-1].transpose(2,0,1)[None],dtype=np.float32)/255
                key='input_1';names=['output_iris','output_eyes_contours_and_brows']
            elif name.startswith('yolox-'):
                iw,ih=baseline.info['input_wh'];rh=int(frame.shape[0]*iw/frame.shape[1])
                resized=cv2.resize(frame,(iw,rh));canvas=np.full((ih,iw,3),114,np.uint8);canvas[:rh]=resized
                tensor=np.ascontiguousarray(canvas.transpose(2,0,1)[None],dtype=np.float32)
                key=baseline.input_name;names=None
            else:
                source=frame[:,:,::-1] if name=='rtmw3d-x-384' else frame
                tensor,_,_=preprocess(source,[320,70,700,650],baseline.info['input_wh'])
                key=baseline.input_name;names=None
            a=baseline.runner.run(tensor,key,names)
            b=candidate.runner.run(tensor,key,names)
            for x,y in zip(a,b):
                np.testing.assert_allclose(x,y,rtol=1e-5,atol=1e-5)
                differences.append(float(np.max(np.abs(x-y))) if x.size else 0.)
        candidate.calls=len(frames)
        execution=candidate.finish()
        reports[name]=dict(max_absolute_difference=max(differences),effective_mode=candidate.runner.mode,execution=execution)
        del candidate,baseline
    (output/'report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(output)
    print(json.dumps({k:v['max_absolute_difference'] for k,v in reports.items()}))


if __name__=='__main__':main()
