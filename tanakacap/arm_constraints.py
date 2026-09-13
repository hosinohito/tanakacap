"""Seated weak-perspective calibration and temporally selected depth branches.

Lengths are nominal shoulder-width units, not measured human centimetres.
Calibration requires straight arms in the camera plane and a fixed camera distance.
"""
import numpy as np
from collections import deque


class ArmCalibration:
    def __init__(self):
        self.value = None
        self.start = None
        self.samples = []
        self.status = 'K: calibrate arms (camera preview)'
        self.consistency = deque(maxlen=30)
        self.rejection = None

    def begin(self, now):
        self.start = now
        self.samples = []
        self.consistency.clear()
        self.rejection = None
        self.status = 'Hold straight arms out/down in camera plane'

    def observe(self, xy, scores, now):
        if self.start is None:
            return False
        if now-self.start > 12:
            self.start = None
            self.status = 'Calibration failed: K to retry; previous calibration kept'
            return False
        ids = [5,6,7,8,9,10]
        if xy is None or not np.isfinite(xy[ids]).all() or not (scores[ids]>.5).all():
            self.samples=[]
            return False
        span = np.linalg.norm(xy[6]-xy[5])
        lengths=[]
        for a,b,c in ([5,7,9],[6,8,10]):
            u,v=xy[b]-xy[a],xy[c]-xy[b]
            lu,lv=np.linalg.norm(u),np.linalg.norm(v)
            if min(lu,lv)<30 or np.dot(u,v)/max(lu*lv,1)<.9:
                self.samples=[]
                return False
            lengths.extend([lu,lv])
        if span<80 or abs(xy[6,1]-xy[5,1])>.15*span:
            self.samples=[]
            return False
        self.samples.append((now,np.array([span,*lengths])))
        self.samples=[s for s in self.samples if now-s[0]<=2.5]
        self.status=f'Hold still: {len(self.samples)} samples (2 seconds)'
        if len(self.samples)<30 or now-self.samples[0][0]<2:
            return False
        values=np.stack([s[1] for s in self.samples])
        median=np.median(values,axis=0)
        if np.max(np.std(values,axis=0)/median)>.08:
            self.status='Too much motion: hold arms still'
            return False
        lengths=median[1:]*.36/median[0]
        if not ((lengths>.12)&(lengths<.45)).all():
            self.status='Arms too short in image: face camera, extend sideways'
            return False
        self.value={'shoulder_pixels':float(median[0]), 'scale':float(.36/median[0]),
                    'left':lengths[:2].tolist(),'right':lengths[2:].tolist()}
        self.start=None
        self.consistency.clear()
        self.status='Arms calibrated | keep camera distance | K: redo'
        return True

    def check_consistency(self, xy, scores):
        """A calibrated length is an assumption; repeated contradiction disables it."""
        if self.value is None:
            return
        ids=[5,6,7,8,9,10]
        if not np.isfinite(xy[ids]).all() or not (scores[ids]>=.3).all():
            return
        inconsistent=False
        for side,chain in [('left',[5,7,9]),('right',[6,8,10])]:
            projected=np.linalg.norm(np.diff(xy[chain],axis=0),axis=1)*self.value['scale']
            inconsistent |= bool((projected>np.asarray(self.value[side])*1.15).any())
        self.consistency.append(inconsistent)
        if len(self.consistency)>=15 and sum(self.consistency)/len(self.consistency)>.5:
            self.rejection={'reason':'projection_exceeds_calibrated_length','value':self.value}
            self.value=None
            self.start=None
            self.status='Calibration rejected: MODEL tracking restored | K: redo'


def constrain_arm(a, b, lengths, previous=None, forward=None):
    """Enumerate per-bone depth signs; soft body-front prior, never camera clamp."""
    observed=np.stack([a,b])
    lengths=np.asarray(lengths)
    planar=observed[:,:2].copy()
    projected=np.linalg.norm(planar,axis=1)
    if (projected>lengths*1.3).any():
        return None  # inconsistent scale/occlusion; do not invent a new bone length
    planar *= np.minimum(1,lengths/np.maximum(projected,1e-8))[:,None]
    depth=np.sqrt(np.maximum(0,lengths**2-np.sum(planar**2,axis=1)))
    forward=np.array([0.,0.,1.]) if forward is None else forward
    candidates=[]
    for s1,s2 in ((1,1),(1,-1),(-1,1),(-1,-1)):
        candidate=np.column_stack((planar,depth*np.array([s1,s2])))
        unit=candidate/lengths[:,None]
        bend=np.degrees(np.arccos(np.clip(unit[0]@unit[1],-1,1)))
        if bend>155:
            continue
        cost=.25*np.sum((candidate-observed)**2)
        # Prefer forward forearm for seated use, but allow pulling elbow/hand back.
        cost+=.15*max(0,-candidate[1]@forward)**2
        if previous is not None:
            cost+=2*np.sum((candidate-previous)**2)
        candidates.append((cost,candidate))
    return min(candidates,key=lambda x:x[0])[1] if candidates else None


def smooth_fixed_bones(previous, target, lengths, dt):
    """Filter directions then restore lengths; linear joint smoothing shrinks bones."""
    result=[]
    for old,new,length in zip(previous,target,lengths):
        old=old/max(np.linalg.norm(old),1e-8)
        new=new/length
        angle=np.arccos(np.clip(old@new,-1,1))
        amount=min(1-np.exp(-10*dt),np.radians(240)*dt/max(angle,1e-8))
        # Spherical interpolation, including antipodal observations.
        tangent=new-old*np.dot(old,new)
        if np.linalg.norm(tangent)<1e-6:
            tangent=np.cross(old,[0,0,1])
            if np.linalg.norm(tangent)<1e-6:
                tangent=np.cross(old,[0,1,0])
        tangent/=max(np.linalg.norm(tangent),1e-8)
        result.append(length*(old*np.cos(angle*amount)+tangent*np.sin(angle*amount)))
    return np.array(result)
