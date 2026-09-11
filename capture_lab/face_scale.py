"""Relative camera distance from rigid upper-face landmarks, not jaw opening.

Weak-perspective affine fit: the largest singular value estimates image scale
while the smaller one may shrink with head rotation. Not metric face ranging.
"""
import numpy as np
import time
from collections import deque


class FaceScale:
    def __init__(self):
        self.reference = None
        self.reference_scale = None
        self.status = 'uninitialized'
        self.pending=deque(maxlen=10)
        self.details={}

    def update(self, xy, scores, initial_scale,now=None):
        now=time.perf_counter() if now is None else now
        self.details={}
        while self.pending and now-self.pending[0][2]>5:self.pending.popleft()
        ids = np.array([27,28,29,30,36,39,42,45])+23
        p = np.asarray(xy)[ids]
        s = np.asarray(scores)[ids]
        self.status = 'face_missing'
        if not np.isfinite(p).all() or not np.isfinite(s).all() or (s<.5).any():
            return None
        p = p-p.mean(axis=0)
        singular = np.linalg.svd(p,compute_uv=False)
        if singular[-1]<5 or singular[0]<20: return None
        if self.reference is None:
            if initial_scale is None: return None
            # Never lock the whole session to a single startup observation.
            # Choose a supported actual shape (medoid), not an average of poses.
            self.pending.append((p.copy(),float(initial_scale),now))
            self.status='face_reference_collecting'
            self.details['reference_samples']=len(self.pending)
            if len(self.pending)<10:return None
            choices=[]
            for candidate,scale,_ in self.pending:
                errors=[]
                for observed,_,_ in self.pending:
                    fit=np.linalg.lstsq(candidate,observed,rcond=None)[0]
                    errors.append(np.linalg.norm(candidate@fit-observed)/np.linalg.norm(observed))
                if np.count_nonzero(np.asarray(errors)<.08)>=8:
                    choices.append((float(np.median(errors)),candidate,scale))
            if not choices:return None
            _,reference,scale=min(choices,key=lambda item:item[0])
            self.reference=reference.copy()
            self.reference_scale=scale
            self.pending.clear()
        affine=np.linalg.lstsq(self.reference,p,rcond=None)[0]
        scales=np.linalg.svd(affine,compute_uv=False)
        error=np.linalg.norm(self.reference@affine-p)/np.linalg.norm(p)
        self.details.update(residual=float(error),axis_ratio=float(scales[-1]/scales[0]),relative_size=float(scales[0]),
                            reference=self.reference.tolist(),reference_scale=self.reference_scale)
        if error>.12 or scales[-1]/scales[0]<.45 or not .35<scales[0]<3:
            self.status='face_geometry_rejected'
            return None
        self.status='face_affine'
        return self.reference_scale/float(scales[0])
