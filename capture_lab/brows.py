"""Eyebrow geometry from existing landmarks, with a fixed neutral reference."""
import numpy as np
from .motion_gate import DirectionGate

KEYS = ('browLeftInner','browLeftOuter','browRightInner','browRightOuter')


def measure(points, scores):
    p=np.asarray(points,float)[23:91]; s=np.asarray(scores,float)[23:91]
    ids=[17,18,20,21,22,23,25,26,36,39,42,45]
    if not np.isfinite(p[ids]).all() or not np.isfinite(s[ids]).all() or (s[ids]<.4).any(): return None
    right=(p[36]+p[39])*.5; left=(p[42]+p[45])*.5
    axis=left-right; span=np.linalg.norm(axis)
    if span<15: return None
    down=np.array([-axis[1],axis[0]])/span
    values=np.array([np.dot(eye-p[index].mean(0),down)/span for eye,index in
        [(left,[22,23]),(left,[25,26]),(right,[20,21]),(right,[17,18])]])
    return values if np.isfinite(values).all() and (values>-.05).all() and (values<.8).all() else None


def observe(points,scores,packet):
    value=measure(points,scores) if packet.get('faceTracked') else None
    packet['browTracked']=value is not None
    if value is not None: packet.update(zip(KEYS,map(float,value)))


def frontal_brows(points,frontal,rotation,translation,image_size):
    # A fixed brow plane in head space; no learned Z or second pose solve.
    from .head_pose import camera_matrix,TEMPLATE
    result=np.array(frontal,copy=True)
    inverse=np.linalg.inv(camera_matrix(image_size)); center=-rotation.T@translation
    for i in range(17,27):
        ray=rotation.T@(inverse@np.r_[points[23+i],1.])
        if not np.isfinite(ray).all() or abs(ray[2])<.15: return None
        length=(TEMPLATE[27][2]-center[2])/ray[2]
        if length<=0:return None
        result[23+i]=(center+ray*length)[:2]*1000+[320,240]
    return result


class BrowFilter:
    def __init__(self,block,stride):
        self.gate=DirectionGate(.015,float('inf'),block,stride)
        self.samples=[]; self.reference=None

    def update(self,packet,now):
        if not packet.get('faceTracked') or not packet.get('browTracked'):
            packet['browTracked']=False; self.gate.reset()
            if self.reference is None:self.samples=[]
            return
        values=np.array([packet[k] for k in KEYS],float)
        if self.reference is None:
            if abs(packet.get('headYaw',0))>20 or abs(packet.get('headRoll',0))>15:
                self.samples=[]
            else:self.samples=(self.samples+[values])[-10:]
            if len(self.samples)==10 and np.max(np.ptp(self.samples,axis=0))<.035:
                self.reference=np.median(self.samples,axis=0)
            else:
                packet['browTracked']=False
                return
        output=self.gate.update(np.clip((values-self.reference)/.10,-1,1),now)
        packet['browTracked']=output is not None
        if output is not None:packet.update(zip(KEYS,map(float,output)))
