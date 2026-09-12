"""Experimental iris displacement, not calibrated screen-point gaze estimation."""
from pathlib import Path
import time
import cv2
import numpy as np
import onnxruntime as ort
from .inference import provider_summary
from .models import sha256
from .motion_gate import DirectionGate
from .gpu_runner import GpuRunner, provider_options

MODEL = Path(__file__).resolve().parents[1]/'models/iris-landmark.onnx'
MODEL_HASH = 'e3c8ae73a21415e396688d655d5f1d9e1cb5a01b7ed19962de76c06458bfddcb'


def eye_crop(frame, eye, flip):
    """Unroll corners and pad 2.3x. Model's left means image-left, not anatomy."""
    eye=np.asarray(eye,dtype=float)
    if eye.shape!=(6,2) or not np.isfinite(eye).all(): return None
    axis=eye[3]-eye[0]; width=np.linalg.norm(axis)
    if width<14: return None
    axis/=width; vertical=np.array([-axis[1],axis[0]])
    center=(eye[0]+eye[3])/2
    aperture=(np.linalg.norm(eye[1]-eye[5])+np.linalg.norm(eye[2]-eye[4]))/(2*width)
    if aperture<.16: return None
    size=width*2.3
    corners=np.array([center+(axis*x+vertical*y)*size/2 for x,y in [(-1,-1),(-1,1),(1,-1),(1,1)]])
    if np.any(corners<0) or np.any(corners[:,0]>=frame.shape[1]) or np.any(corners[:,1]>=frame.shape[0]): return None
    matrix=np.stack([axis,vertical])*64/size
    affine=np.column_stack([matrix,32-matrix@center]).astype(np.float32)
    crop=cv2.warpAffine(frame,affine,(64,64))
    if crop[24:40,18:46].std()<8: return None
    if flip: crop=crop[:,::-1]
    return np.ascontiguousarray(crop[:,:,::-1].transpose(2,0,1)[None],dtype=np.float32)/255


def iris_offset(iris, flip):
    p=np.asarray(iris,dtype=float).reshape(5,3)[:,:2].copy()
    if not np.isfinite(p).all(): return None
    if flip: p[:,0]=64-p[:,0]
    center=p[0]; radii=np.linalg.norm(p[1:]-center,axis=1)
    if np.min(radii)<1.5 or np.max(radii)>12 or np.max(radii)>2.5*np.min(radii): return None
    if np.linalg.norm(p[1:].mean(axis=0)-center)>3: return None
    offset=(center-32)/(64/2.3)
    if abs(offset[0])>.42 or abs(offset[1])>.20: return None
    return offset


def contour_offset(iris, contour, flip):
    """Corners 0/8 map to FaceMesh 33/133 in the official contour map.

    Use the corner line (not moving eyelids) as origin, in eye-width units.
    Unmirror both predictions together before finding image-right/down axes.
    """
    p=np.asarray(iris,dtype=float).reshape(5,3)[:,:2].copy()
    c=np.asarray(contour,dtype=float).reshape(71,3)[:,:2].copy()
    if not np.isfinite(p).all() or not np.isfinite(c[[0,8]]).all():return None
    if flip:p[:,0]=64-p[:,0];c[:,0]=64-c[:,0]
    radii=np.linalg.norm(p[1:]-p[0],axis=1)
    if min(radii)<1.5 or max(radii)>12 or max(radii)>2.5*min(radii):return None
    if np.linalg.norm(p[1:].mean(0)-p[0])>3:return None
    corners=c[[0,8]];corners=corners[np.argsort(corners[:,0])]
    axis=corners[1]-corners[0];width=np.linalg.norm(axis)
    if not 14<width<48:return None
    axis/=width
    if axis[0]<.7:return None
    delta=p[0]-corners.mean(0)
    value=np.array([delta@axis,delta@np.array([-axis[1],axis[0]])])/width
    if abs(value[0])>.42 or abs(value[1])>.20:return None
    return value


class IrisGaze:
    def __init__(self, output, block=3, stride=1, reference='contour', execution_mode='run', batch_eyes=False):
        if reference not in ('contour','legacy'):raise ValueError('Unknown gaze reference')
        self.reference=reference
        self.batch_eyes=bool(batch_eyes)
        if not MODEL.exists() or sha256(MODEL)!=MODEL_HASH: raise RuntimeError('Iris model missing or hash mismatch')
        ort.preload_dlls(directory='')
        self.profiling=output is not None
        options=ort.SessionOptions(); options.enable_profiling=self.profiling
        if self.profiling: options.profile_file_prefix=str(output/'iris')
        options.log_severity_level=3
        options.intra_op_num_threads=2
        model_path=MODEL
        if self.batch_eyes:
            from .onnx_variants import iris_batch_model
            model_path=iris_batch_model(MODEL)
        if execution_mode=='graph-fp16':
            from .onnx_variants import fp16_model
            model_path=fp16_model(model_path)
        self.session=ort.InferenceSession(str(model_path),sess_options=options,providers=provider_options(execution_mode,model_path=model_path))
        self.runner=GpuRunner(self.session,execution_mode)
        self.session.disable_fallback()
        from .tensorrt_backend import require_provider
        require_provider(self.session,execution_mode)
        self.tensorrt_required=execution_mode in ('trt-fp32','trt-fp16')
        self.gate=DirectionGate(.35,float('inf'),block,stride)
        self.calls=0
        self.diagnostics={}

    def update(self, frame, points, scores, packet, now):
        start=time.perf_counter(); values=[]; reasons=[]; observations={}
        packet.update(gazeTracked=False,gazeYaw=0.,gazePitch=0.)
        if packet.get('faceTracked') and abs(packet['headYaw'])<35 and abs(packet['headPitch'])<25:
            legacy=getattr(self,'reference','contour')=='legacy'
            prepared=[]
            for side,idx,flip in [('right',59,legacy),('left',65,not legacy)]:
                eye=np.asarray(points[idx:idx+6])
                tensor=eye_crop(frame,eye,flip) if np.all(np.asarray(scores[idx:idx+6])>.4) and packet.get(side+'Blink',1)<.55 else None
                if tensor is None: reasons.append(side+':unobserved'); continue
                prepared.append((side,eye,flip,tensor))
            predictions=[]
            names=['output_iris','output_eyes_contours_and_brows']
            runner=getattr(self,'runner',None)
            if prepared and getattr(self,'batch_eyes',False):
                tensor=np.concatenate([item[3] for item in prepared]+[np.zeros_like(prepared[0][3])]*(2-len(prepared)),axis=0)
                outputs=runner.run(tensor,'input_1',names) if runner else self.session.run(names,{'input_1':tensor})
                self.calls+=1
                predictions=[(outputs[0][i:i+1],outputs[1][i:i+1]) for i in range(len(prepared))]
            else:
                for _,_,_,tensor in prepared:
                    predictions.append(runner.run(tensor,'input_1',names) if runner else self.session.run(names,{'input_1':tensor}))
                    self.calls+=1
            for (side,eye,flip,_),(iris,contour) in zip(prepared,predictions):
                roi_value=iris_offset(iris,flip)
                refined=contour_offset(iris,contour,flip)
                value=roi_value if legacy else refined
                observations[side]=dict(iris_crop=np.where(np.isfinite(iris),iris,None).reshape(5,3)[:,:2].tolist(),
                                       offset=None if value is None else value.tolist(),
                                       roi_offset=None if roi_value is None else roi_value.tolist(),
                                       contour_offset=None if refined is None else refined.tolist(),
                                       corners_crop=np.where(np.isfinite(contour),contour,None).reshape(71,3)[[0,8],:2].tolist(),
                                       flipped=flip,
                                       eye_width=float(np.linalg.norm(eye[3]-eye[0])))
                if value is not None: values.append(value)
                else: reasons.append(side+':geometry')
        else: reasons.append('face_or_head_pose')
        if len(values)==2 and np.linalg.norm(values[0]-values[1])>.20:
            values=[]; reasons.append('eyes_disagree')
        if values:
            value=np.mean(values,axis=0)
            angles=np.clip(value*[-80,60],[-20,-12],[20,12])
            accepted=self.gate.update(angles,now)
            if accepted is not None:
                packet.update(gazeTracked=True,gazeYaw=float(accepted[0]),gazePitch=float(accepted[1]))
        else: self.gate.reset()
        self.diagnostics=dict(reference=getattr(self,'reference','contour'),valid_eyes=len(values),rejections=reasons,calls=self.calls,
                              eyes=observations,output_tracked=packet['gazeTracked'],
                              output_angles=[packet['gazeYaw'],packet['gazePitch']],
                              elapsed_ms=(time.perf_counter()-start)*1000)
        return self.diagnostics

    def finish(self):
        if not self.profiling: return dict(profiling=False,providers=self.session.get_providers(),calls=self.calls,batch_size=2 if self.batch_eyes else 1)
        profile=Path(self.session.end_profiling()); result=provider_summary(profile)
        result.update(profile=str(profile),calls=self.calls,sha256=MODEL_HASH,batch_size=2 if self.batch_eyes else 1)
        if self.calls and (not result['gpu_executed'] or result['cpu_compute_ops']):
            raise RuntimeError('Iris core compute did not execute exclusively on CUDA')
        if self.calls and self.tensorrt_required and not result['tensorrt_executed']:
            raise RuntimeError('No measured TensorRT iris execution')
        return result
