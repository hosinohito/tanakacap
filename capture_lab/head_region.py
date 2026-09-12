"""Head crop acquisition using YuNet on CUDA, independent of expression models.

YuNet model: OpenCV Zoo, MIT (docs/YUNET_LICENSE.txt). Boxes only are used.
"""
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from .inference import provider_summary
from .models import ROOT, sha256

MODEL = ROOT / 'models/head-region-yunet.onnx'
HASH = '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'


class HeadRegionDetector:
    def __init__(self, profile_dir=None):
        if not MODEL.exists() or sha256(MODEL) != HASH:
            raise RuntimeError('Head region model missing/hash mismatch. See docs/HEAD_ONLY.md')
        ort.preload_dlls(directory='')
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            raise RuntimeError('Head region requires CUDA')
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.log_severity_level = 3
        options.enable_profiling = profile_dir is not None
        self.profiling = options.enable_profiling
        if profile_dir: options.profile_file_prefix = str(profile_dir / 'head-region')
        self.session = ort.InferenceSession(str(MODEL), sess_options=options,
                                           providers=[('CUDAExecutionProvider', {'device_id': 0})])
        self.session.disable_fallback()
        if self.session.get_providers()[0] != 'CUDAExecutionProvider':
            raise RuntimeError('Head region did not select CUDA')
        self.calls = 0

    def detect(self, image):
        start = time.perf_counter()
        height, width = image.shape[:2]
        scale = 640 / max(width, height)
        resized = cv2.resize(image, (round(width*scale), round(height*scale)))
        canvas = np.zeros((640, 640, 3), np.uint8)
        canvas[:resized.shape[0], :resized.shape[1]] = resized
        tensor = np.ascontiguousarray(canvas.transpose(2, 0, 1)[None], dtype=np.float32)
        names = [f'{kind}_{stride}' for kind in ('cls', 'obj', 'bbox') for stride in (8,16,32)]
        out = dict(zip(names, self.session.run(names, {'input': tensor})))
        self.calls += 1
        boxes, scores = [], []
        for stride in (8,16,32):
            score = np.sqrt(np.clip(out[f'cls_{stride}'].reshape(-1), 0, 1) *
                            np.clip(out[f'obj_{stride}'].reshape(-1), 0, 1))
            ids = np.flatnonzero(score >= .8)
            pred = out[f'bbox_{stride}'].reshape(-1,4)[ids]
            centers = (pred[:,:2] + np.stack((ids % (640//stride), ids // (640//stride)), axis=1))*stride
            sizes = np.exp(np.clip(pred[:,2:], -10, 10))*stride
            for center, size, confidence in zip(centers, sizes, score[ids]):
                xy = (center-size/2)/scale
                size = size/scale
                # Reject boxes mostly outside the real image, including letterbox padding.
                lo = np.maximum(xy, 0)
                hi = np.minimum(xy+size, [width,height])
                if np.any(hi-lo < 24) or np.prod(hi-lo) < .85*np.prod(size): continue
                boxes.append([*map(float, lo), *map(float, hi-lo)])
                scores.append(float(confidence))
        keep = cv2.dnn.NMSBoxes(boxes, scores, .8, .3) if boxes else []
        detections = [(np.asarray(boxes[int(i)], dtype=float), scores[int(i)])
                      for i in np.asarray(keep).reshape(-1)]
        return detections, (time.perf_counter()-start)*1000

    def finish(self):
        if not self.profiling:
            return dict(profiling=False, providers=self.session.get_providers(), calls=self.calls)
        result = provider_summary(Path(self.session.end_profiling()))
        if self.calls and (not result['cuda_executed'] or result['cpu_compute_ops']):
            raise RuntimeError('Head region GPU execution verification failed')
        return result


def crop_for(box, image_shape):
    """Square face crop with 20% margin; shift at edges without changing its size."""
    x,y,w,h = box
    height,width = image_shape[:2]
    side = min(max(w,h)*1.2, width, height)
    return [int(round(np.clip(x+w/2-side/2, 0, width-side))),
            int(round(np.clip(y+h/2-side/2, 0, height-side))),
            int(round(side)), int(round(side))]


class HeadRegionTracker:
    """Confirm acquisition twice, invalidate immediately on loss, avoid bystander jumps.

    This is spatial association for a single-user app, not identity recognition.
    After 0.8 seconds lost, a sole visible face can be reacquired anywhere.
    """
    def __init__(self, seed=None):
        self.box = None if seed is None else np.asarray(seed, dtype=float)
        self.pending = None
        self.last_seen = None
        self.state = 'searching'
        self.score = 0.

    @staticmethod
    def near(a,b):
        size = max(a[2],a[3],b[2],b[3])
        distance = np.linalg.norm(a[:2]+a[2:]/2-b[:2]-b[2:]/2)/size
        ratio = max(a[2]*a[3],b[2]*b[3])/max(1,min(a[2]*a[3],b[2]*b[3]))
        return distance < .85 and ratio < 3

    def update(self, detections, now, image_shape):
        self.score = 0.
        candidates = detections
        if self.box is not None:
            candidates = [(b,s) for b,s in detections if self.near(self.box,b)]
            if not candidates and self.last_seen is not None and now-self.last_seen >= .8 and len(detections)==1:
                candidates = detections
        if not candidates or (len(candidates)>1 and self.box is None):
            self.pending = None
            self.state = 'lost' if self.box is not None else 'searching'
            return None
        if self.box is None:
            chosen,score = candidates[0]
        else:
            chosen,score = min(candidates, key=lambda item: np.linalg.norm(
                item[0][:2]+item[0][2:]/2-self.box[:2]-self.box[2:]/2))
        if self.state != 'tracking':
            if self.pending is None or not self.near(self.pending,chosen):
                self.pending = chosen.copy()
                self.state = 'confirming'
                return None
            self.box = chosen.copy()
        else:
            # Box stabilization only. No additional temporal filtering of the pose.
            self.box = self.box*.25 + chosen*.75
        self.pending = None
        self.state = 'tracking'
        self.last_seen = now
        self.score = score
        return crop_for(self.box, image_shape)
