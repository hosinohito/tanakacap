"""Relative avatar depth, independent of arm scale calibration and jaw motion."""
import numpy as np
from .face_scale import FaceScale
from .motion_gate import DirectionGate


class FaceDistance:
    def __init__(self, block=3, stride=1):
        self.scale=FaceScale()
        self.gate=DirectionGate(.008,float('inf'),block,stride)
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
            value=self.gate.update(np.array([scale]),now)
            if value is not None:
                packet.update(faceDistanceTracked=True,faceDistanceRatio=float(value[0]))
        else:self.gate.reset()
        self.diagnostics=dict(status=self.scale.status if valid else 'face_pose_or_missing',
                              raw_ratio=scale,tracked=packet['faceDistanceTracked'],
                              ratio=packet['faceDistanceRatio'])
        return self.diagnostics
