"""Compare official RTMW3D PyTorch and ONNX on identical private recording tensors.
Run prepare/compare with product Python, torch with the isolated MMPose Python.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')
def prepare(a):
    import cv2
    from tanakacap.inference import preprocess
    from compare_hand_mirror import reflect_roi
    rows=[json.loads(x) for x in a.records.read_text().splitlines()]
    ids=sorted(set(range(165,196,3))|set(range(225,244,3))|set(range(435,466,3))|set(range(555,586,3)))
    cap=cv2.VideoCapture(str(a.video));tensors=[];samples=[]
    for i in ids:
        cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,im=cap.read();assert ok
        row=rows[i];assert row['roi'] is not None
        for mirror in (False,True):
            roi=reflect_roi(row['roi'],im.shape[1]) if mirror else row['roi']
            image=cv2.flip(im,1) if mirror else im
            tensor,center,scale=preprocess(image,roi,[288,384],'RGB')
            tensors.append(tensor)
            samples.append(dict(frame=i,mirror=mirror,center=np.asarray(center).tolist(),scale=np.asarray(scale).tolist(),width=im.shape[1]))
    cap.release();a.output.mkdir(parents=True,exist_ok=False)
    np.save(a.output/'inputs.npy',np.concatenate(tensors))
    save(a.output/'inputs.json',dict(video_sha256=digest(a.video),records_sha256=digest(a.records),samples=samples,input_sha256=digest(a.output/'inputs.npy')))
    print('Prepared',len(samples),'paired inputs; no images displayed')
def pytorch(a):
    sys.path.insert(0,str(a.source));sys.path.insert(0,str(a.source/'projects/rtmpose3d'))
    import torch
    torch.set_num_threads(2)
    import faulthandler
    faulthandler.dump_traceback_later(45,repeat=True)
    print("Torch imported",flush=True)
    from mmengine.config import Config
    from mmpose.utils import register_all_modules
    from mmpose.registry import MODELS
    import rtmpose3d
    register_all_modules()
    print("Modules registered",flush=True)
    cfg=Config.fromfile(str(a.source/'projects/rtmpose3d/configs/rtmw3d-x_8xb32_cocktail14-384x288.py'))
    cfg.model.backbone.init_cfg=None
    print("Config loaded",flush=True)
    model=MODELS.build(cfg.model)
    print("Model built",flush=True)
    assert digest(a.weights)=='b0a0eab7ca501e2c88028fe1cfd78b50c7130e220d39541da7f669e5de25e6ca', 'Expected audited official checkpoint'
    checkpoint=torch.load(a.weights,map_location='cpu',weights_only=False) # Official checkpoint includes NumPy metadata.
    print('Checkpoint loaded',flush=True)
    state=checkpoint['state_dict']
    result=model.load_state_dict(state,strict=True)
    assert torch.cuda.is_available()
    model=model.cuda().eval()
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    class Raw(torch.nn.Module):
        def __init__(self,m):super().__init__();self.m=m
        def forward(self,x):return self.m.head(self.m.extract_feat(x))
    raw=Raw(model).eval();inputs=np.load(a.output/'inputs.npy');outputs=[]
    with torch.inference_mode():
        for i,t in enumerate(inputs):
            out=raw(torch.from_numpy(t[None]).cuda())
            assert len(out)==3
            outputs.append([x.cpu().numpy() for x in out])
            if (i+1)%20==0:print('PyTorch',i+1,flush=True)
        torch.onnx.export(raw,torch.from_numpy(inputs[:1]).cuda(),str(a.output/'reexport.onnx'),input_names=['input'],output_names=['simcc_x','simcc_y','simcc_z'],opset_version=17,do_constant_folding=True)
    np.savez(a.output/'pytorch.npz',**{n:np.concatenate([o[j] for o in outputs]) for j,n in enumerate(('x','y','z'))})
    save(a.output/'pytorch.json',dict(torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),weights_sha256=digest(a.weights),strict_load=str(result),tf32=False,reexport_sha256=digest(a.output/'reexport.onnx')))
    faulthandler.cancel_dump_traceback_later()
    print('PyTorch and export complete',flush=True)
def compare(a):
    import onnxruntime as ort
    ort.preload_dlls(directory='')
    inputs=np.load(a.output/'inputs.npy');reference=np.load(a.output/'pytorch.npz');report={}
    for name,path in [('community',ROOT/'models/rtmw3d-x-384/model.onnx'),('reexport',a.output/'reexport.onnx')]:
        session=ort.InferenceSession(str(path),providers=[('CUDAExecutionProvider',{'use_tf32':0})])
        session.disable_fallback();assert session.get_providers()[0]=='CUDAExecutionProvider'
        outputs=[session.run(None,{session.get_inputs()[0].name:t[None]}) for t in inputs]
        collected={n:np.concatenate([o[j] for o in outputs]) for j,n in enumerate(('x','y','z'))}
        np.savez(a.output/(name+'.npz'),**collected)
        report[name]={}
        for n,v in collected.items():
            r=reference[n];assert v.shape==r.shape and np.isfinite(v).all()
            delta=np.abs(v-r);bins=np.abs(v.argmax(-1)-r.argmax(-1))
            report[name][n]=dict(shape=list(v.shape),max_abs=float(delta.max()),mean_abs=float(delta.mean()),bin_difference_count=int((bins!=0).sum()),hand_bin_difference_count=int((bins[:,91:]!=0).sum()),max_bin_difference=int(bins.max()))
    save(a.output/'comparison.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','torch','compare'])
    p.add_argument('--output',type=Path,required=True);p.add_argument('--video',type=Path);p.add_argument('--records',type=Path)
    p.add_argument('--source',type=Path,default=ROOT/'.cache/mmpose-audit');p.add_argument('--weights',type=Path,default=ROOT/'models/rtmw3d-pytorch-audit/rtmw3d-x.pth')
    a=p.parse_args();{'prepare':prepare,'torch':pytorch,'compare':compare}[a.phase](a)
