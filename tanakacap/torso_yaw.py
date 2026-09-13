"""Shoulder projection sets yaw magnitude; elbows supply direction only."""
import numpy as np
from collections import deque


class ShoulderWidthReference:
    def __init__(self):
        self.samples=deque()
        self.width=None
        self.angle=0.
        self.frontal_samples=deque()

    def observe_frontal(self,span,scale,depth_difference,agreement,now):
        # Re-establish a face-relative zero only when the independent shoulder
        # depths agree on frontal and the projected width is stable. No max drift.
        if scale is None or not agreement or abs(depth_difference)>.02:
            self.frontal_samples.clear();return False
        width=span*scale
        if not np.isfinite(width) or not .1<width<.8:return False
        self.frontal_samples.append((now,width))
        while self.frontal_samples and (now-self.frontal_samples[0][0]>5 or len(self.frontal_samples)>10):self.frontal_samples.popleft()
        if len(self.frontal_samples)<10:return False
        values=np.array([v for _,v in self.frontal_samples]);center=float(np.median(values))
        if np.ptp(values)>center*.05:return False
        self.width=center
        return True

    def update(self,span,scale,now):
        while self.samples and now-self.samples[0][0]>5:self.samples.popleft()
        if scale is None:return self.angle
        width=span*scale
        if not np.isfinite(width) or not .1<width<.8:return self.angle
        if self.width is None:
            self.samples.append((now,width))
            while len(self.samples)>10:self.samples.popleft()
            if len(self.samples)==10:
                values=np.array([v for _,v in self.samples])
                center=float(np.median(values))
                if np.ptp(values)<=center*.05:
                    self.width=center
                    self.samples.clear()
        if self.width is not None:
            # Small shoulder-point errors near acos(1) otherwise make large yaw.
            ratio=width/self.width
            self.angle=float(min(80,np.degrees(np.arccos(np.clip(ratio/.98,0,1)))))
        return self.angle


def shoulder_yaw_magnitude(xy,face_scale,shoulder_depth_difference,nominal_width=.36):
    """Amount from shoulder projection; elbows never supply the magnitude.

    Face scale removes relative camera distance. Before face scale is available,
    use the shoulder model's own depth/nominal-width estimate as a fallback.
    """
    span=float(np.linalg.norm(np.asarray(xy)[6]-np.asarray(xy)[5]))
    if face_scale is not None:
        ratio=span*face_scale/nominal_width
        return float(min(80,np.degrees(np.arccos(np.clip(ratio,0,1))))),'face_scaled_shoulder_width'
    ratio=abs(shoulder_depth_difference)/nominal_width
    return float(min(80,np.degrees(np.arcsin(np.clip(ratio,0,1))))),'model_shoulders'


def elbow_yaw(xyz,scores,shoulder_width=.36):
    ids=[7,8]  # anatomical left/right elbow
    p=np.asarray(xyz)[ids];s=np.asarray(scores)[ids]
    if not np.isfinite(p).all() or not np.isfinite(s).all() or (s<.3).any():return None
    # Avatar +Z is forward: left elbow forward -> +yaw -> left shoulder forward.
    # Do not invert this mapping to compensate for an erroneous depth estimate.
    # Common translation cancels; moving both elbows together gives no turn.
    return float(np.clip(np.degrees(np.arctan2(p[0,2]-p[1,2],shoulder_width)),-80,80))


def elbow_agreement(xy,scores,reference_xy,reference_scores,image_size=None):
    """Cross-check already available 2D/3D upper arms; never read wrists.

    Disagreement indicates uncertainty, not which model is correct. Correlated
    sleeve errors remain undetectable. Threshold is a reversible trial value.
    """
    if reference_xy is None or reference_scores is None:
        return True, {'status':'not_available'}  # legacy callers/recordings
    ids=[5,6,7,8]
    a=np.asarray(xy,dtype=float)[ids];b=np.asarray(reference_xy,dtype=float)[ids]
    sa=np.asarray(scores)[ids];sb=np.asarray(reference_scores)[ids]
    if (not np.isfinite(a).all() or not np.isfinite(b).all() or
        not np.isfinite(sa).all() or not np.isfinite(sb).all() or
        (sa<.3).any() or (sb<.3).any()):
        return False, {'status':'missing_observation'}
    if image_size is not None:
        size=np.asarray(image_size)
        if (a<0).any() or (b<0).any() or (a>=size).any() or (b>=size).any():
            return False, {'status':'out_of_frame'}
    span=np.linalg.norm(a[1]-a[0])
    if span<30:return False, {'status':'small_shoulders'}
    # Compare shoulder-relative elbow positions to tolerate whole-ROI offsets.
    errors=np.linalg.norm((a[2:]-a[:2])-(b[2:]-b[:2]),axis=1)/span
    ok=bool((errors<=.25).all())
    return ok, {'status':'agreement' if ok else 'disagreement',
                'upper_arm_error_over_shoulder_span':errors.tolist(),'limit':.25}
