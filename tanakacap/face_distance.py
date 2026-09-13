"""Relative avatar depth, independent of arm scale calibration and jaw motion."""
import numpy as np
from .face_scale import FaceScale
from .motion_gate import DirectionGate


class FaceDistance:
    def __init__(self, block=3, stride=1, mode="stable"):
        if mode not in ("stable","legacy"):raise ValueError("invalid face distance filter")
        self.mode=mode
        self.filtered=None
        self.time=None
        self.scale=FaceScale()
        self.gate=DirectionGate(.02 if mode=='stable' else .008,float('inf'),block,stride)
        self.diagnostics={}

    def update(self, points, scores, packet, now):
        packet.update(faceDistanceTracked=False,faceDistanceRatio=1.)
        valid=packet.get('faceTracked') and abs(packet['headYaw'])<30 and abs(packet['headPitch'])<25
        # Learn near frontal; otherwise a turned startup can inflate the scale
        # when the person later looks straight at the camera.
        if self.scale.reference is None:
            valid=valid and abs(packet['headYaw'])<12 and abs(packet['headPitch'])<12
        scale=self.scale.update(points,scores,1.,now) if valid else None
        if scale is not None:
            value=self.gate.update(np.array([np.log(scale) if self.mode=="stable" else scale]),now)
            if value is not None:
                target=float(value[0])
                if self.mode=="stable":
                    if self.filtered is None:self.filtered=target
                    # Seconds-based response: small jitter is slow, large approach fast.
                    dt=0. if self.time is None else float(np.clip(now-self.time,0,.1))
                    movement=abs(target-self.filtered)
                    blend=float(np.clip((movement-.02)/.06,0,1))
                    tau=.22+(.06-.22)*blend
                    self.filtered+=(target-self.filtered)*(-np.expm1(-dt/tau))
                    ratio=float(np.exp(self.filtered))
                else:ratio=target
                packet.update(faceDistanceTracked=True,faceDistanceRatio=ratio)
        else:self.gate.reset()
        self.time=now
        self.diagnostics=dict(filter_mode=self.mode,scale_details=self.scale.details if valid else {},status=self.scale.status if valid else 'face_pose_or_missing',
                              raw_ratio=scale,tracked=packet['faceDistanceTracked'],
                              ratio=packet['faceDistanceRatio'])
        return self.diagnostics
