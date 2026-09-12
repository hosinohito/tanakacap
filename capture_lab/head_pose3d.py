"""Face pose/lips from learned relative Z; no PnP or assumed lip depths.

XY pixels and relative-Z metres are unprojected with approximate intrinsics.
Generic rigid face distances estimate the missing absolute camera distance.
The template supplies rigid shape/scale only; lip depths come from the model.
"""
import cv2
import numpy as np
from .head_pose import TEMPLATE, POSE_IDS
from .mouth_detail import contour_controls

OBJECT = np.array([TEMPLATE[i] for i in POSE_IDS])
CENTERED = OBJECT - OBJECT.mean(axis=0)
PAIR_I, PAIR_J = np.triu_indices(len(POSE_IDS), 1)
LENGTH2 = np.sum((OBJECT[PAIR_I] - OBJECT[PAIR_J])**2, axis=1)
KEEP = LENGTH2 > .03**2
PAIR_I, PAIR_J, LENGTH2 = PAIR_I[KEEP], PAIR_J[KEEP], LENGTH2[KEEP]


def fit_face3d(points, scores, depth, depth_scores, image_size):
    if depth is None or depth_scores is None:
        return None
    p = np.asarray(points, float)[23:91]
    z = np.asarray(depth, float)[23:91]
    zs = np.asarray(depth_scores, float)[23:91]
    s = np.asarray(scores, float)[23:91]
    valid = np.isfinite(p).all(axis=1) & np.isfinite(z) & np.isfinite(zs) & (zs > 0) & np.isfinite(s) & (s >= .3)
    if not valid[POSE_IDS].all() or np.min(s[POSE_IDS]) < .4:
        return None
    if np.linalg.norm(p[45]-p[36]) < 25:
        return None
    width, height = image_size
    rays = (p - [width/2, height/2]) / max(width, height)
    z = z - np.median(z[POSE_IDS])
    r, dz = rays[POSE_IDS], z[POSE_IDS]
    a = r[PAIR_I] - r[PAIR_J]
    b = r[PAIR_I]*dz[PAIR_I,None] - r[PAIR_J]*dz[PAIR_J,None]
    aa = np.sum(a*a, axis=1)
    ab = np.sum(a*b, axis=1)
    cc = np.sum(b*b, axis=1) + (dz[PAIR_I]-dz[PAIR_J])**2 - LENGTH2
    discriminant = ab*ab - aa*cc
    candidates = (-ab + np.sqrt(np.maximum(discriminant, 0))) / np.maximum(aa, 1e-12)
    usable = (discriminant >= 0) & (aa > 1e-8) & (candidates > .15) & (candidates < 4)
    if usable.sum() < 6:
        return None
    distance = float(np.median(candidates[usable]))
    xyz = np.column_stack((rays*(distance+z[:,None]), z))
    observed = xyz[POSE_IDS]
    center = observed.mean(axis=0)
    u, _, vt = np.linalg.svd(CENTERED.T @ (observed-center))
    correction = np.eye(3)
    correction[2,2] = np.linalg.det(vt.T @ u.T)
    rotation = vt.T @ correction @ u.T
    residual = float(np.sqrt(np.mean(np.sum((CENTERED@rotation.T-(observed-center))**2,axis=1))))
    angles = np.asarray(cv2.RQDecomp3x3(rotation)[0])
    if not np.isfinite(angles).all() or residual > .025 or rotation[2,2] < .25:
        return None
    if abs(angles[0]) > 55 or abs(angles[1]) > 65 or abs(angles[2]) > 45:
        return None
    frontal = np.array(points, float, copy=True)
    frontal[23:91] = ((xyz-center) @ rotation)[:,:2]*1000 + [320,240]
    confidence = np.array(scores, float, copy=True)
    confidence[23:91] = np.where(valid & (distance+z > .05), s, 0)
    return angles, frontal, confidence, distance, residual


class HeadPose3D:
    def __init__(self, gain=1.8):
        self.gain = float(gain)
        if not np.isfinite(self.gain) or not .5 <= self.gain <= 3:
            raise ValueError('head pitch gain must be 0.5..3')
        self.reference = None
        self.samples = []
        self.last_pitch = 0.
        self.diagnostics = {}

    def update(self, points, scores, packet, image_size, depth=None, depth_scores=None):
        fit = fit_face3d(points, scores, depth, depth_scores, image_size) if packet.get('faceTracked') else None
        self.diagnostics = dict(mode='depth3d', tracked=fit is not None)
        if fit is None:
            if self.reference is None:
                self.samples = []
            packet['headPitch'] = self.last_pitch
            packet['mouthContourTracked'] = False
            return self.diagnostics
        angles, frontal, confidence, distance, error = fit
        if self.reference is None and abs(packet.get('headYaw',0)) < 20 and abs(packet.get('headRoll',0)) < 15:
            self.samples = (self.samples+[float(angles[0])])[-10:]
            if len(self.samples) == 10 and np.ptp(self.samples) < 6:
                self.reference = float(np.median(self.samples))
        self.last_pitch = 0. if self.reference is None else float(np.clip((angles[0]-self.reference)*self.gain,-40,40))
        packet['headPitch'] = self.last_pitch
        detail = contour_controls(frontal, confidence)
        packet['mouthContourTracked'] = detail is not None
        if detail is not None:
            packet.update(detail)
        self.diagnostics.update(raw_pitch=float(angles[0]), pitch=self.last_pitch, pitch_reference=self.reference,
                                pose_angles=angles.tolist(), face_camera_distance=distance,
                                rigid_residual_m=error, mouth_normalized=detail is not None)
        return self.diagnostics


class PnPPitchDepthMouth:
    """Keep the accepted PnP pitch; independently retain the trial Z lips."""
    def __init__(self, gain=1.8):
        from .head_pose import HeadPose
        self.pitch = HeadPose(gain)
        self.mouth = HeadPose3D(gain)
        self.diagnostics = {}

    def update(self, points, scores, packet, image_size, depth=None, depth_scores=None):
        self.mouth.update(points, scores, packet, image_size, depth, depth_scores)
        pitch_packet = dict(packet)
        self.pitch.update(points, scores, pitch_packet, image_size, normalize_mouth=False)
        packet['headPitch'] = pitch_packet['headPitch']
        self.diagnostics = dict(self.pitch.diagnostics, mode='pnp_depthmouth',
                                mouth_depth=self.mouth.diagnostics,
                                mouth_normalized=bool(packet.get('mouthContourTracked')))
        return self.diagnostics
