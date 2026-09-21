"""Single-person fixed-ROI SimCC inference with explicit CUDA verification.

Input contract follows the published RTMPose/RTMW ONNX SDK exports:
BGR, ImageNet mean/std in channel order, 1.25 ROI padding, SimCC split=2.
Geometry and decoding are implemented here; no rtmlib runtime dependency.
"""
import json
import time
from collections import Counter

import cv2
import numpy as np
import onnxruntime as ort

from .models import ROOT, catalog, model_path, sha256

# Provider discovery uses ORT's default logger before the session logger exists.
# Match the bundled-runtime check used by the UI's development logging policy.
# Keep native errors/fatal errors, and leave development logging unchanged.
if (ROOT / 'runtime/python.exe').is_file():
    ort.set_default_logger_severity(3)

from .gpu_runner import GpuRunner, provider_options


def preprocess(frame, roi, input_wh, color_order='BGR'):
    x, y, w, h = roi
    if w <= 0 or h <= 0:
        raise ValueError('ROI must have positive width and height')
    iw, ih = input_wh
    center = np.array([x + w / 2, y + h / 2], dtype=np.float32)
    scale = np.array([w, h], dtype=np.float32) * 1.25
    aspect = iw / ih
    if scale[0] / scale[1] > aspect:
        scale[1] = scale[0] / aspect
    else:
        scale[0] = scale[1] * aspect
    sx, sy = iw / scale[0], ih / scale[1]
    affine = np.array([[sx, 0, iw / 2 - center[0] * sx],
                       [0, sy, ih / 2 - center[1] * sy]], dtype=np.float32)
    crop = cv2.warpAffine(frame, affine, (iw, ih), flags=cv2.INTER_LINEAR)
    if color_order=='RGB': crop=crop[:,:,::-1]
    crop = (crop.astype(np.float32) - np.array([123.675, 116.28, 103.53], np.float32))
    crop /= np.array([58.395, 57.12, 57.375], np.float32)
    tensor = np.ascontiguousarray(crop.transpose(2, 0, 1)[None])
    return tensor, center, scale


def decode_simcc(outputs, center, scale, input_wh):
    xs, ys = outputs
    if xs.ndim != 3 or ys.ndim != 3 or xs.shape[:2] != ys.shape[:2]:
        raise ValueError('Expected two [batch, keypoints, bins] SimCC outputs')
    points = np.stack([xs.argmax(axis=-1), ys.argmax(axis=-1)], axis=-1).astype(np.float32)
    scores = np.minimum(xs.max(axis=-1), ys.max(axis=-1))
    points = points / 2.0 / np.asarray(input_wh) * scale + center - scale / 2
    points[scores <= 0] = np.nan
    return points[0], scores[0]


def provider_summary(path):
    events = json.loads(path.read_text(encoding='utf-8'))
    counts = Counter()
    cpu_ops = Counter()
    for event in events:
        args = event.get('args', {})
        provider = args.get('provider')
        if provider:
            counts[provider] += 1
            if provider == 'CPUExecutionProvider':
                cpu_ops[args.get('op_name', 'unknown')] += 1
    return {'node_events_by_provider': dict(counts), 'cpu_ops': dict(cpu_ops),
            'cuda_executed': counts['CUDAExecutionProvider'] > 0,
            'cpu_compute_ops': {op: count for op, count in cpu_ops.items()
                                if op in {'Conv', 'FusedConv', 'Gemm', 'MatMul', 'Attention'}}}


class SimCCModel:
    def __init__(self, name, output_dir, execution_mode='run', detector_graph=False, preprocess_mode='legacy'):
        if preprocess_mode not in ('legacy','crop'): raise ValueError('Unknown preprocessing mode')
        self.preprocess_mode=preprocess_mode
        self.info = catalog()[name]
        path = model_path(name)
        if not path.exists():
            raise FileNotFoundError(f'Run fetch first: {name}')
        ort.preload_dlls(directory='')
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            raise RuntimeError('CUDAExecutionProvider is unavailable. CPU fallback is not allowed.')
        options = ort.SessionOptions()
        self.profiling = output_dir is not None
        options.enable_profiling = self.profiling
        if self.profiling: options.profile_file_prefix = str(output_dir / name)
        options.log_severity_level = 3
        options.intra_op_num_threads = 2
        dynamic = self.info.get('kind') == 'detector'
        original_path=path
        tail_path=None
        # This legacy face network contains FP16 nodes that cannot all be captured
        # by the CUDA EP. Keep its verified FP32 CUDA graph; no CPU fallback.
        if name=='rtmw-l-384' and execution_mode=='graph-fp16':
            execution_mode='graph'
            print('RTMW-L compatibility: FP32 CUDA graph (full RTMW3D remains FP16)',flush=True)
        if detector_graph:
            if not dynamic: raise ValueError('Split graph is only for detectors')
            from .onnx_variants import split_detector
            path,tail_path=split_detector(path)
            dynamic=False
            if execution_mode != 'graph-fp16': execution_mode='graph'
        if execution_mode=='graph-fp16':
            from .onnx_variants import fp16_model
            path=fp16_model(path)
        self.session = ort.InferenceSession(str(path), sess_options=options,
                                           providers=provider_options(execution_mode,dynamic))
        self.runner = GpuRunner(self.session,execution_mode,dynamic)
        self.tail_session=None
        if tail_path is not None:
            from .gpu_runner import SplitDetectorRunner
            tail_options=ort.SessionOptions();tail_options.intra_op_num_threads=2;tail_options.log_severity_level=3
            tail_options.enable_profiling=self.profiling
            if self.profiling: tail_options.profile_file_prefix=str(output_dir/(name+'-nms'))
            self.tail_session=ort.InferenceSession(str(tail_path),sess_options=tail_options,providers=provider_options('binding',True))
            self.tail_session.disable_fallback()
            self.runner=SplitDetectorRunner(self.session,self.tail_session,execution_mode)
        self.session.disable_fallback()
        from .gpu_runner import require_provider
        require_provider(self.session)
        shape = self.session.get_inputs()[0].shape
        iw, ih = self.info['input_wh']
        if len(shape) != 4 or shape[1:] != [3, ih, iw] or (isinstance(shape[0], int) and shape[0] != 1):
            raise RuntimeError(f'Unexpected model input: {shape}')
        self.input_name = self.session.get_inputs()[0].name
        self.calls = 0
        self.depth = None
        self.depth_scores = None
        self.refine_body_peaks = True
        self.decode_diagnostics = None
        self.identity = {'id': name, 'sha256': sha256(original_path),
                         'execution_mode':self.runner.mode,
                         'providers': self.session.get_providers(), 'input_shape': shape,
                         'onnxruntime_version': ort.__version__}

    def predict(self, frame, roi):
        start = time.perf_counter()
        if self.preprocess_mode=='crop':
            tensor,center,scale=preprocess(frame,roi,self.info['input_wh'],self.info.get('color_order','BGR'))
        else:
            input_frame = frame[:,:,::-1] if self.info.get('color_order') == 'RGB' else frame
            tensor, center, scale = preprocess(input_frame, roi, self.info['input_wh'])
        ready = time.perf_counter()
        outputs = self.runner.run(tensor,self.input_name)
        self.calls += 1
        inferred = time.perf_counter()
        if self.info.get('dimensions') == 3:
            points, scores, self.depth, self.depth_scores = decode_simcc3d(outputs, center, scale, self.info['input_wh'],self.info['z_range'],refine_body=self.refine_body_peaks)
            ids=[5,6,7,8,11,12]
            self.decode_diagnostics={'mode':'local_peak' if self.refine_body_peaks else 'integer',
                'joint_ids':ids,'integer_z_bins':outputs[2][0,ids].argmax(axis=-1).tolist(),
                'refined_z_bins':local_peak_positions(outputs[2][0,ids]).tolist()}
        else:
            points, scores = decode_simcc(outputs, center, scale, self.info['input_wh'])
        if len(points) != self.info['keypoints']:
            raise RuntimeError('Unexpected landmark layout')
        finished = time.perf_counter()
        return points, scores, {'preprocess_ms': (ready-start)*1000,
                               'inference_call_ms': (inferred-ready)*1000,
                               'postprocess_ms': (finished-inferred)*1000,
                               'pipeline_ms': (finished-start)*1000}

    def finish(self):
        if not self.profiling:
            return {'profiling': False, 'providers': self.session.get_providers(), 'inference_calls': self.calls}
        from pathlib import Path
        path = Path(self.session.end_profiling())
        report = provider_summary(path)
        report['profile'] = str(path)
        report['inference_calls'] = self.calls
        if self.tail_session is not None:
            tail_path=Path(self.tail_session.end_profiling())
            report['tail_execution']=provider_summary(tail_path)
            report['tail_profile']=str(tail_path)
            if report['tail_execution']['cpu_compute_ops']: raise RuntimeError('NMS tail core compute on CPU')
        # CPU shape/control nodes are reported, not hidden. Compute must execute on CUDA.
        if self.calls and not report['cuda_executed']:
            raise RuntimeError(f'No measured CUDA execution in {path}')
        if report['cpu_compute_ops']:
            raise RuntimeError(f'Core compute fell back to CPU: {report["cpu_compute_ops"]}')
        return report


def local_peak_positions(distribution):
    """Bounded three-bin log-parabola fit, without temporal filtering.

    Refine only a positive, concave local maximum; never average distant modes.
    Flat, nonpositive and edge peaks retain the integer decode.
    """
    a=np.asarray(distribution,dtype=float)
    index=a.argmax(axis=-1)
    result=index.astype(float)
    flat=a.reshape(-1,a.shape[-1]);k=index.reshape(-1)
    rows=np.arange(len(k));safe=np.clip(k,1,a.shape[-1]-2)
    triplet=flat[rows[:,None],safe[:,None]+np.array([-1,0,1])]
    valid=(k>0)&(k<a.shape[-1]-1)&np.isfinite(triplet).all(axis=1)&(triplet>0).all(axis=1)
    logs=np.log(np.maximum(triplet,1e-30))
    curvature=logs[:,0]-2*logs[:,1]+logs[:,2]
    valid &= curvature < -1e-6
    offset=np.zeros(len(k))
    offset[valid]=.5*(logs[valid,0]-logs[valid,2])/curvature[valid]
    return result+np.clip(offset,-.5,.5).reshape(result.shape)


def decode_simcc3d(outputs, center, scale, input_wh, z_range=2.1744869,refine_body=True):
    if len(outputs) != 3:
        raise ValueError('Expected X/Y/Z SimCC outputs')
    points, scores = decode_simcc(outputs[:2], center, scale, input_wh)
    zs = outputs[2]
    if zs.ndim != 3 or zs.shape[:2] != outputs[0].shape[:2] or zs.shape[-1] != 576:
        raise ValueError(f'Unexpected depth distribution: {zs.shape}')
    # MMPose SimCC3DLabel: z is root-relative metres, XY is image pixels.
    # Never combine these units without a camera/scale approximation.
    # Official configuration input_size=(288,384,288), not the 384px image height.
    depth = (zs.argmax(axis=-1)[0] / (zs.shape[-1]/2) - 1.) * z_range
    if refine_body:
        ids=[5,6,7,8,11,12]  # torso/upper-arm observations only; leave fingers/face/wrists alone
        refined=np.stack([local_peak_positions(axis[0,ids]) for axis in outputs[:2]],axis=-1)
        points[ids]=refined/2/np.asarray(input_wh)*scale+center-scale/2
        points[scores<=0]=np.nan
        depth[ids]=(local_peak_positions(zs[0,ids])/(zs.shape[-1]/2)-1)*z_range
    depth_scores = zs.max(axis=-1)[0]
    depth[depth_scores <= 0] = np.nan
    return points, scores, depth, depth_scores


class PersonDetector(SimCCModel):
    def __init__(self, output_dir, execution_mode='run', name='yolox-m-human', detector_graph=False):
        super().__init__(name, output_dir,execution_mode,detector_graph)
        iw, ih = self.info['input_wh']
        grid_parts, stride_parts = [], []
        for stride in (8, 16, 32):
            yy, xx = np.mgrid[:ih//stride, :iw//stride]
            grid_parts.append(np.stack([xx, yy], axis=-1).reshape(-1, 2))
            stride_parts.append(np.full((xx.size, 1), stride))
        self.grid = np.concatenate(grid_parts).astype(np.float32)
        self.strides = np.concatenate(stride_parts).astype(np.float32)

    def detect(self, frame, threshold=.7):
        start = time.perf_counter()
        h, w = frame.shape[:2]
        iw, ih = getattr(self, 'info', {}).get('input_wh', (640,640))
        ratio = min(iw/w, ih/h)
        resized = cv2.resize(frame, (int(w*ratio), int(h*ratio)))
        padded = np.full((ih, iw, 3), 114, dtype=np.uint8)
        padded[:resized.shape[0], :resized.shape[1]] = resized
        tensor = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32)
        prepared = time.perf_counter()
        runner = getattr(self,'runner',None)
        result = (runner.run(tensor,self.input_name) if runner else self.session.run(None, {self.input_name: tensor}))[0][0]
        inferred = time.perf_counter()
        def finish(roi, confidence):
            done = time.perf_counter()
            self.timing = dict(detector_preprocess_ms=(prepared-start)*1000,
                              detector_inference_call_ms=(inferred-prepared)*1000,
                              detector_postprocess_ms=(done-inferred)*1000)
            return roi, confidence, (done-start)*1000
        self.calls += 1
        if result.ndim == 2 and result.shape[1] == 5:
            # This official export already includes decoding and NMS.
            if len(result) == 0:
                return finish(None, 0.)
            best = int(np.argmax(result[:, 4]))
            confidence = float(result[best, 4])
            box = result[best, :4] / ratio
            box[:2] = np.maximum(box[:2], [0, 0])
            box[2:] = np.minimum(box[2:], [w, h])
            roi = None
            if confidence >= threshold and (box[2:]-box[:2] > 1).all():
                roi = [float(box[0]), float(box[1]), float(box[2]-box[0]), float(box[3]-box[1])]
            return finish(roi, confidence)
        if result.shape[0] != len(self.grid) or result.shape[1] < 6:
            raise RuntimeError(f'Unsupported detector export: {result.shape}')
        scores = result[:, 4] * result[:, 5]
        best = int(np.argmax(scores))
        confidence = float(scores[best])
        roi = None
        if confidence >= threshold:
            center = (result[best, :2]+self.grid[best])*self.strides[best]
            size = np.exp(result[best, 2:4])*self.strides[best]
            xy0 = np.maximum((center-size/2)/ratio, [0, 0])
            xy1 = np.minimum((center+size/2)/ratio, [w, h])
            if (xy1-xy0 > 1).all():
                roi = [float(xy0[0]), float(xy0[1]), float(xy1[0]-xy0[0]), float(xy1[1]-xy0[1])]
        return finish(roi, confidence)


class DetectionGate:
    """Require a short run of overlapping detections before driving pose."""
    def __init__(self, required=3):
        self.required = required
        self.previous = None
        self.streak = 0

    def update(self, roi):
        if roi is None:
            self.previous, self.streak = None, 0
            return None
        overlap = 0.
        if self.previous is not None:
            a, b = np.asarray(roi), np.asarray(self.previous)
            size = np.maximum(0, np.minimum(a[:2]+a[2:], b[:2]+b[2:])-np.maximum(a[:2], b[:2]))
            intersection = float(np.prod(size))
            overlap = intersection / max(float(a[2]*a[3]+b[2]*b[3]-intersection), 1.)
        self.streak = self.streak+1 if overlap >= .3 else 1
        self.previous = roi
        return roi if self.streak >= self.required else None
