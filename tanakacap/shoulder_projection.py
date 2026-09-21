"""Image-only shoulder yaw with continuous face/shoulder projection correction.

The ratio detects changed projection, not metric lean depth. Elbow-based yaw sign
is intentionally supplied by the existing caller, never inferred from width.
"""
from collections import deque
import numpy as np


class ShoulderProjection:
    def __init__(self):
        self.reference = None
        self.pending = deque(maxlen=10)
        self.width_samples = deque()
        self.width = None
        self.angle = 0.
        self.details = {}
        self.last_time = None

    def update(self, xy, scores, face_details, face_valid, packet, now, guard=True):
        self.details = {'status':'missing_face_geometry'}
        if self.last_time is not None and now-self.last_time > .3:
            self.pending.clear(); self.width_samples.clear()
        self.last_time = now
        ids = np.array([27,28,29,30,36,39,42,45])+23
        p=np.asarray(xy,float); s=np.asarray(scores,float)
        valid=np.r_[ids,[5,6]]
        if (not face_valid or not packet.get('faceTracked',False)
                or not np.isfinite(p[valid]).all() or not np.isfinite(s[valid]).all()
                or (s[ids]<.5).any() or (s[[5,6]]<.3).any()):
            self.pending.clear(); self.width_samples.clear(); return self.angle
        reference=np.asarray(face_details.get('reference',[]),float)
        size=float(face_details.get('relative_size',0))
        if reference.shape != (8,2) or not np.isfinite(reference).all() or not np.isfinite(size) or size<=0:
            return self.angle
        face_size=float(np.sqrt(np.mean(np.sum(reference**2,axis=1)))*size)
        shoulder=p[6]-p[5]; span=float(np.linalg.norm(shoulder))
        if face_size<5 or span<30: return self.angle
        axis=shoulder/span; normal=np.array([-axis[1],axis[0]])
        offset=p[ids].mean(axis=0)-p[[5,6]].mean(axis=0)
        gap=abs(float(offset@normal))/face_size
        lateral=abs(float(offset@axis))/span
        width=span/face_size
        pitch=float(packet.get('headPitch',0)); yaw=float(packet.get('headYaw',0))
        if not np.isfinite([gap,width,pitch,yaw,lateral]).all() or gap<.5: return self.angle
        self.details.update(gap=gap,face_size=face_size,width_observed=width,lateral=lateral)
        if self.reference is None:
            self.details['status']='reference_warmup'
            # Startup is only a provisional frontal assumption. Do not calibrate
            # while the face is visibly turned or far off the shoulder center.
            if abs(yaw)>15 or abs(pitch)>20 or lateral>.10:
                self.pending.clear(); return self.angle
            self.pending.append((now,gap,width,pitch,face_size))
            while self.pending and now-self.pending[0][0]>5: self.pending.popleft()
            if len(self.pending)<10: return self.angle
            a=np.asarray(self.pending)[:,1:]
            median=np.median(a,axis=0)
            if np.ptp(a[:,0])>.06*median[0] or np.ptp(a[:,1])>.05*median[1]:return self.angle
            self.reference=median
            self.width=float(median[1])
            self.pending.clear()
        gap_ratio=gap/self.reference[0]
        pitch_delta=abs(pitch-self.reference[2])
        # Gap changes now correct width continuously, rather than freezing as
        # soon as the face moves closer. Large/poorly fitted geometry remains
        # ambiguous: a nod, shrug or occlusion cannot be solved from these ratios.
        residual=float(face_details.get('residual',0.))
        ambiguous=(not .5<=gap_ratio<=1.15 or pitch_delta>15 or abs(yaw)>25
                   or lateral>.2 or not np.isfinite(residual) or residual>.08)
        learn=(.94<=gap_ratio<=1.06 and pitch_delta<8 and abs(yaw)<12
               and lateral<.08 and .92<=face_size/self.reference[3]<=1.08)
        while self.width_samples and now-self.width_samples[0][0]>5:self.width_samples.popleft()
        if learn:self.width_samples.append((now,width))
        else:self.width_samples.clear()
        if len(self.width_samples)>=10:
            # A single widened detection cannot set a permanent reference.
            candidate=sorted(v for _,v in self.width_samples)[-10]
            self.width=max(self.width,float(candidate))
        self.details.update(gap_ratio=gap_ratio,reference_width=self.width,
            reference_gap=float(self.reference[0]),reference_learning=bool(learn),
            projection_ambiguous=bool(ambiguous),pitch_delta=pitch_delta)
        if guard and ambiguous:
            self.details['status']='held_projection_ambiguous'
            return self.angle
        raw_ratio=width/self.width
        # Both normalized widths shrink when the face grows without equivalent
        # shoulder growth. Remove their common factor; never learn a narrower
        # frontal reference. This is a projection heuristic, not measured depth.
        # Correct common shrinkage only. Inverting gap growth would invent yaw
        # during head movement even when the shoulder/face width did not shrink.
        correction=1/min(1.,gap_ratio) if guard else 1.
        ratio=raw_ratio*correction
        self.details.update(raw_width_ratio=raw_ratio,correction_factor=correction,
                            width_ratio=ratio)
        # acos is very sensitive near frontal. Five percent is an experimental
        # image-width dead zone, not a measured camera error distribution.
        angle=float(min(80,np.degrees(np.arccos(np.clip(ratio/.95,0,1)))))
        if guard:
            # Avoid acos' sharp onset just outside the frontal dead zone.
            blend=float(np.clip((.95-ratio)/.10,0,1))
            angle*=blend*blend*(3-2*blend)
        self.angle=angle
        self.details.update(status='width_observed',width_ratio=ratio)
        return self.angle
