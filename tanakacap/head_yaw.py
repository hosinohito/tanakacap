"""Weak-perspective yaw from the projected chord between two fixed eye points."""
import numpy as np


class CircularYaw:
    def __init__(self):
        self.reference=None
        self.samples=[]
        self.last=0.
        self.diagnostics={}

    def update(self, points, scores, distance_scale):
        p=np.asarray(points,float)[23:91];s=np.asarray(scores,float)[23:91]
        ids=[30,36,39,42,45]
        self.diagnostics={'state':'invalid'}
        if not np.isfinite(p[ids]).all() or not np.isfinite(s[ids]).all() or (s[ids]<.5).any():
            self.samples=[]
            return self.last
        # Fixed canthus midpoints avoid changes in eyelid opening.
        right=(p[36]+p[39])/2;left=(p[42]+p[45])/2
        axis=left-right;span=float(np.linalg.norm(axis))
        if span<15:return self.last
        axis/=span
        offset=float((p[30]-(right+left)/2)@axis)
        frontal=abs(offset)<.08*span
        # PnP translation supplies existing camera-distance compensation only.
        # Do not take its estimated yaw as the output angle.
        if not np.isfinite(distance_scale) or distance_scale<=0:return self.last
        width=span*distance_scale
        if self.reference is None:
            if not frontal:self.samples=[];return self.last
            self.samples=(self.samples+[width])[-10:]
            if len(self.samples)<10 or np.ptp(self.samples)/np.median(self.samples)>.03:
                self.diagnostics={'state':'calibrating'}
                return self.last
            self.reference=float(np.median(self.samples))
        ratio=float(np.clip(width/self.reference,0,1))
        angle=float(np.degrees(np.arccos(ratio)))
        # Chord length determines magnitude only; the nose resolves left vs right.
        self.last=float(np.clip(-np.sign(offset)*angle,-60,60))
        self.diagnostics=dict(state='tracked',width=width,reference=self.reference,cos_yaw=ratio,yaw=self.last)
        return self.last
