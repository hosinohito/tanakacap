"""Confirm small motion direction before following it; retain fast motion response."""
import numpy as np


class ObservationMean:
    """Configurable mean windows of inference observations, never render frames."""
    def __init__(self, size=1, rotation=False, stride=None):
        if size not in (1, 3):
            raise ValueError('Observation block size must be 1 or 3')
        self.size, self.rotation = size, rotation
        self.stride=size if stride is None else stride
        if self.stride not in (1,size):
            raise ValueError('Observation stride must be 1 or block size')
        self.reset()

    def reset(self):
        self.samples=[]
        self.time=None

    def update(self, value, now):
        if self.time is not None and now-self.time>.2:
            self.samples.clear()
        self.time=now
        self.samples.append(np.asarray(value,dtype=float).copy())
        if len(self.samples)<self.size:
            return None
        value=np.mean(self.samples,axis=0)
        del self.samples[:self.stride]
        if self.rotation and self.size>1:
            # Project the mean matrix onto SO(3), avoiding Euler +/-180 wrap.
            u,_,vt=np.linalg.svd(value)
            value=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
        return value


class DirectionGate:
    def __init__(self, deadband, fast, block_size=1, stride=None):
        self.deadband=deadband
        self.fast=fast
        self.mean=ObservationMean(block_size,stride=stride)
        self.reset()

    def reset(self):
        self.mean.reset()
        self.accepted=self.raw=self.direction=None
        self.time=None

    def update(self, value, now):
        if self.mean.time is not None and now-self.mean.time>.2:
            self.reset()
        value=self.mean.update(value,now)
        if value is None:
            return None if self.accepted is None else self.accepted.copy()
        if self.time is None:
            self.accepted=value.copy(); self.raw=value.copy()
            self.direction=np.zeros_like(value)
        else:
            displacement=value-self.accepted
            step=value-self.raw
            direction=np.sign(displacement)
            continuing=(direction==self.direction)&((step*direction>=-self.deadband))
            adopt=(np.abs(displacement)>=self.fast)|((np.abs(displacement)>self.deadband)&continuing)
            self.accepted=np.where(adopt,value,self.accepted)
            self.direction=np.where(np.abs(displacement)>self.deadband,direction,0)
            self.raw=value.copy()
        self.time=now
        return self.accepted.copy()


def rotation_vector(matrix):
    angle=np.arccos(np.clip((np.trace(matrix)-1)/2,-1,1))
    if angle<1e-7: return np.zeros(3)
    if np.pi-angle<1e-4:
        _,vectors=np.linalg.eigh((matrix+matrix.T)/2)
        return vectors[:,-1]*angle
    vector=np.array([matrix[2,1]-matrix[1,2],matrix[0,2]-matrix[2,0],matrix[1,0]-matrix[0,1]])
    return vector/np.linalg.norm(vector)*angle


class RotationGate:
    def __init__(self, block_size=1, stride=None):
        self.mean=ObservationMean(block_size,rotation=True,stride=stride)
        self.frame=None; self.raw=None; self.direction=None; self.time=None

    def missing(self):
        self.mean.reset()
        self.direction=None
        self.raw=None if self.frame is None else self.frame.copy()

    def update(self, frame, now):
        if self.mean.time is not None and now-self.mean.time>.2:
            self.mean.reset(); self.frame=None; self.time=None
        frame=self.mean.update(frame,now)
        if frame is None:
            return None if self.frame is None else self.frame.copy()
        if self.time is None:
            self.frame=frame.copy(); self.direction=None
        else:
            delta=rotation_vector(frame@self.frame.T)
            step=rotation_vector(frame@self.raw.T)
            magnitude=np.linalg.norm(delta)
            # The axis sign is ambiguous at a half turn. Near the branch cut,
            # use the pending direction for confirmation, not a new reversal.
            if magnitude>np.radians(175) and self.direction is not None and delta@self.direction<0:
                delta=-delta
            continuing=(self.direction is not None and delta@self.direction>0
                        and step@self.direction>=-np.radians(.2))
            if magnitude>np.radians(.6) and continuing:
                self.frame=frame.copy()
            self.direction=delta/max(magnitude,1e-8) if magnitude>np.radians(.6) else None
        self.time=now; self.raw=frame.copy()
        return self.frame.copy()
