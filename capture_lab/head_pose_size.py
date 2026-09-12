"""Experimental XY face proportions for head angles; PnP only for expressions."""
import numpy as np
from .head_pose import HeadPose


class SizeHeadPose(HeadPose):
    def __init__(self, gain=1.8, lip_depth_scale=1.5):
        super().__init__(gain, lip_depth_scale)
        self.size_reference = None
        self.size_samples = []
        self.size_last = np.zeros(3)

    def update(self, points, scores, packet, image_size, normalize_mouth=True):
        # Preserve the existing expression correction, including its failure flags.
        expression_diagnostics = super().update(points, scores, packet, image_size, normalize_mouth).copy()
        p = np.asarray(points, float)[23:91]
        s = np.asarray(scores, float)[23:91]
        ids = [30, 31, 33, 35, 36, 39, 42, 45]
        valid = bool(packet.get('faceTracked') and np.isfinite(p[ids]).all()
                     and np.isfinite(s[ids]).all() and (s[ids] >= .4).all())
        ratios = None
        if valid:
            # Eye corners avoid eyelid opening and jaw/lip expression changes.
            right = (p[36] + p[39]) / 2
            left = (p[42] + p[45]) / 2
            axis = left - right
            span = float(np.linalg.norm(axis))
            valid = span >= 15
            if valid:
                horizontal = axis / span
                vertical = np.array([-horizontal[1], horizontal[0]])
                nose = np.mean(p[[30, 31, 33, 35]], axis=0) - (left + right) / 2
                ratios = np.array([nose @ vertical / span, nose @ horizontal / span])
                roll = float(np.degrees(np.arctan2(axis[1], axis[0])))
                if self.size_reference is None:
                    if abs(ratios[1]) < .2 and abs(roll) < 15:
                        self.size_samples = (self.size_samples + [ratios])[-10:]
                        if len(self.size_samples) == 10 and np.max(np.ptp(self.size_samples, axis=0)) < .04:
                            self.size_reference = np.median(self.size_samples, axis=0)
                    else:
                        self.size_samples = []
                if self.size_reference is not None:
                    delta = ratios - self.size_reference
                    # Display gain, not a recovered metric 3D rotation.
                    self.size_last = np.array([np.clip(delta[0] * 100 * self.gain, -40, 40),
                                               np.clip(-delta[1] * 100, -60, 60), np.clip(roll, -35, 35)])
        if not valid and self.size_reference is None:
            self.size_samples = []
        packet.update(zip(('headPitch', 'headYaw', 'headRoll'), map(float, self.size_last)))
        self.diagnostics = dict(mode='size2d', tracked=valid, calibrated=self.size_reference is not None,
                                ratios=None if ratios is None else ratios.tolist(),
                                angles=self.size_last.tolist(), expression_pose=expression_diagnostics)
        return self.diagnostics
