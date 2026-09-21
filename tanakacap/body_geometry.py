"""Conservative online geometry cues; never treat projected lengths as ground truth."""
from collections import deque
import numpy as np


def visible_hand_inward(xy,scores,side):
    """Image-space medial wrist test used by the cross-body correction.

    No upper/lower image-height limit, and no palm-facing requirement. Visibility
    is already censored at the frame boundary by BodyRetarget.
    """
    shoulder,wrist,other=(5,9,6) if side=='left' else (6,10,5)
    ids=[shoulder,wrist,other]
    p=np.asarray(xy)[ids];s=np.asarray(scores)[ids]
    if not np.isfinite(p).all() or not np.isfinite(s).all() or (s<.3).any():return False
    inward=p[2,0]-p[0,0]
    if abs(inward)<30:return False
    return bool((p[1,0]-p[0,0])*np.sign(inward)>=0)


def cross_body_amount(xy,scores,side):
    if not visible_hand_inward(xy,scores,side):return 0.
    shoulder,wrist,other=(5,9,6) if side=='left' else (6,10,5)
    p=np.asarray(xy)
    fraction=(p[wrist,0]-p[shoulder,0])/(p[other,0]-p[shoulder,0])
    return float(np.clip((fraction-.35)/.30,0,1))


class SupportedLengths:
    """Largest per-segment lower bound supported by >=10 samples in 5 seconds."""
    def __init__(self):
        self.samples=[deque(),deque()]
        self.value=np.zeros(2)

    def update(self,projected,now):
        for i,length in enumerate(projected):
            history=self.samples[i]
            while history and now-history[0][0]>5:
                history.popleft()
            if np.isfinite(length) and .04<length<.5:
                history.append((now,float(length)))
            if len(history)>=10:
                candidate=sorted(v for _,v in history)[-10]
                self.value[i]=max(self.value[i],candidate)
        return self.value.copy()


class DepthAssist:
    def __init__(self):
        self.previous=None
        self.time=None
        self.lengths=SupportedLengths()

    def update(self, a, b, now, learn_lengths=True):
        bones=np.stack([a,b]); projected=np.linalg.norm(bones[:,:2],axis=1)
        if self.time is None or now-self.time>.3:
            self.previous=None
        self.time=now
        # Do not learn lengths from a held face scale.
        lengths=self.lengths.update(projected,now) if learn_lengths else np.zeros(2)
        if (lengths<=0).any():
            return bones,'learning'
        # A supported maximum is only a lower-bound length estimate. Use a soft
        # depth supplement, not the old hard length constraint or arm rejection.
        result=bones.copy()
        for i in range(2):
            ratio=projected[i]/lengths[i]
            # Outward hands no longer receive the front prior. A collapsed
            # segment still has the same supported length: recover its depth
            # in the observed/previous hemisphere, without inventing +Z.
            if np.linalg.norm(bones[i])<.07 and lengths[i]>=.07 and projected[i]<lengths[i]:
                sign=np.sign(bones[i,2]) if abs(bones[i,2])>=.005 else np.sign(self.previous[i]) if self.previous is not None else 0
                if sign:
                    result[i,2]=sign*np.sqrt(max(0,lengths[i]**2-projected[i]**2))
                    continue
            # Recover a gross model-depth outlier without discarding valid XY.
            if np.linalg.norm(bones[i])>=.65 and projected[i]<lengths[i]*1.05:
                sign=np.sign(bones[i,2])
                result[i,2]=sign*np.sqrt(max(0,lengths[i]**2-projected[i]**2))
            if ratio>=.85 or ratio<.15:
                continue
            magnitude=np.sqrt(max(0,lengths[i]**2-projected[i]**2))
            z=bones[i,2]
            # Only supplement a direction supported by the model; no guessed
            # camera-facing sign when model depth is ambiguous.
            if abs(z)<.035 or abs(z)>=magnitude:
                continue
            if self.previous is None or self.previous[i]*z<=0:
                continue
            result[i,2]=np.sign(z)*(.5*abs(z)+.5*magnitude)
        self.previous=result[:,2].copy()
        return result,'assisted' if not np.allclose(result,bones) else 'model'

