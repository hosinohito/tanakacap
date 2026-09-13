"""MHR70 metric camera joints to existing COCO WholeBody controls.

Confidence is the SAME RTMW3D visibility evidence, not a SAM confidence.
The SAM coordinates remain metres; all native XYZ is passed to BodyRetarget.
Face landmarks, gaze, expressions, source clock and correction settings stay fixed.
"""
import numpy as np
from tanakacap.visibility import screen_visibility

# COCO17 (two wrists precede hips), six foot landmarks, OpenPose21 hands.
BODY_MAP=np.array([0,1,2,3,4,5,6,7,8,62,41,9,10,11,12,13,14,15,16,17,18,19,20])
LEFT_MAP=np.array([62,45,44,43,42,49,48,47,46,53,52,51,50,57,56,55,54,61,60,59,58])
RIGHT_MAP=np.array([41,24,23,22,21,28,27,26,25,32,31,30,29,36,35,34,33,40,39,38,37])
TARGET=np.r_[np.arange(5,23),np.arange(91,133)]
SOURCE=np.r_[BODY_MAP[5:],LEFT_MAP,RIGHT_MAP]


def projection_error(prediction,image_size):
    xyz=np.asarray(prediction['pred_keypoints_3d'],float)
    uv=np.asarray(prediction['pred_keypoints_2d'],float)
    camera=xyz+np.asarray(prediction['pred_cam_t'],float)
    if xyz.shape!=(70,3) or uv.shape!=(70,2):raise ValueError('Expected MHR70')
    if not np.isfinite(camera).all() or (camera[:,2]<=0).any():raise ValueError('Invalid camera geometry')
    projected=camera[:,:2]/camera[:,2:]*float(prediction['focal_length'])+np.asarray(image_size)/2
    return float(np.max(np.abs(projected-uv)))


def adapt(common,prediction,image_size):
    if common['body_xy'] is None or prediction is None:return None
    xyz=np.asarray(prediction['pred_keypoints_3d'],float)
    projected=np.asarray(prediction['pred_keypoints_2d'],float)
    error=projection_error(prediction,image_size)
    if error>.02:raise ValueError(f'SAM coordinate/projection mismatch: {error} pixels')
    xy=np.asarray(common['body_xy'],float).copy()
    scores,_=screen_visibility(xy,common['body_scores'],image_size)
    depth=np.asarray(common['body_depth'],float).copy()
    depth_scores=np.asarray(common['body_depth_scores'],float).copy()
    native=np.full((133,3),np.nan)
    xy[TARGET]=projected[SOURCE]
    depth[TARGET]=xyz[SOURCE,2]
    native[TARGET]=xyz[SOURCE]
    # Do not invent a high confidence for generated hidden joints. Retain the
    # common model's observed visibility and additionally test SAM's image bounds.
    return dict(xy=xy,scores=scores,depth=depth,depth_scores=depth_scores,camera_xyz=native),error
