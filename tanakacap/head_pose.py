"""Generic-template pose and pose-normalized lips; RTMW detection stays on GPU.

PnP is a small geometry solve, not a second face inference model. Intrinsics and
subject shape are approximate, so reprojection residual is not gaze/pose accuracy.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from .mouth_detail import contour_controls

_DATA=json.loads((Path(__file__).parent/'data/face_template.json').read_text())
TEMPLATE={int(k):np.array(v,dtype=float) for k,v in _DATA['points'].items()}
POSE_IDS=np.array([27,30,31,33,35,36,39,42,45])


def camera_matrix(image_size):
    width,height=image_size
    focal=float(max(width,height))
    return np.array([[focal,0,width/2],[0,focal,height/2],[0,0,1.]])


def fit_pose(points,scores,image_size):
    p=np.asarray(points,dtype=float)[23:91];s=np.asarray(scores)[23:91]
    if not np.isfinite(p[POSE_IDS]).all() or not np.isfinite(s[POSE_IDS]).all() or (s[POSE_IDS]<.4).any():return None
    span=np.linalg.norm(p[45]-p[36])
    if span<25:return None
    obj=np.array([TEMPLATE[i] for i in POSE_IDS]);cam=camera_matrix(image_size)
    try:
        ok,rvec,tvec=cv2.solvePnP(obj,p[POSE_IDS],cam,None,flags=cv2.SOLVEPNP_SQPNP)
        if not ok:return None
        rvec,tvec=cv2.solvePnPRefineLM(obj,p[POSE_IDS],cam,None,rvec,tvec)
        rotation=cv2.Rodrigues(rvec)[0]
        projected=cv2.projectPoints(obj,rvec,tvec,cam,None)[0].reshape(-1,2)
        error=float(np.sqrt(np.mean(np.sum((projected-p[POSE_IDS])**2,axis=1)))/span)
        angles=np.array(cv2.RQDecomp3x3(rotation)[0])
        if not np.isfinite(angles).all() or not np.isfinite(tvec).all() or error>.06:return None
        if np.min((obj@rotation.T+tvec.reshape(3))[:,2])<.05 or rotation[2,2]<.25:return None
        if abs(angles[0])>55 or abs(angles[1])>65 or abs(angles[2])>45:return None
        return rotation,tvec.reshape(3),angles,error
    except cv2.error:return None


def frontal_landmarks(points,rotation,translation,image_size,lip_depth_scale=1.):
    # Intersect each image ray with its generic facial depth in head space.
    # Using different lip depths removes tilt-induced apparent corner elevation.
    output=np.array(points,dtype=float,copy=True)
    inverse=np.linalg.inv(camera_matrix(image_size))
    center=-rotation.T@translation
    lip_center_depth=float(np.mean([TEMPLATE[i][2] for i in range(48,68)]))
    for i,template in TEMPLATE.items():
        point=output[23+i]
        if not np.isfinite(point).all():return None
        ray=rotation.T@(inverse@np.r_[point,1.])
        if abs(ray[2])<.15:return None
        depth=lip_center_depth+(template[2]-lip_center_depth)*lip_depth_scale if 48<=i<68 else template[2]
        length=(depth-center[2])/ray[2]
        if length<=0:return None
        recovered=center+ray*length
        output[23+i]=recovered[:2]*1000+[320,240]
    return output


class HeadPose:
    def __init__(self,gain=1.8,lip_depth_scale=1.5):
        self.lip_depth_scale=float(lip_depth_scale)
        if not np.isfinite(self.lip_depth_scale) or not .5<=self.lip_depth_scale<=2:raise ValueError("lip depth scale must be 0.5..2")
        self.gain=float(gain)
        if not np.isfinite(self.gain) or not .5<=self.gain<=3:raise ValueError("head pitch gain must be 0.5..3")
        self.reference=None
        self.samples=[]
        from .head_yaw import CircularYaw
        self.yaw=CircularYaw()
        self.last_pitch=0.
        self.diagnostics={}

    def update(self,points,scores,packet,image_size,normalize_mouth=True):
        legacy_pitch=packet.get('headPitch',0.)
        pose=fit_pose(points,scores,image_size) if packet.get('faceTracked') else None
        self.diagnostics=dict(tracked=pose is not None,legacy_pitch=legacy_pitch,lip_depth_scale=self.lip_depth_scale)
        if pose is None:
            if self.reference is None:self.samples=[]
            packet['headYaw']=self.yaw.last
            packet['headPitch']=self.last_pitch
            packet['mouthContourTracked']=False
            packet['browTracked']=False
            return self.diagnostics
        rotation,translation,angles,error=pose
        eye_center=np.mean([TEMPLATE[i] for i in (36,39,42,45)],axis=0)
        eye_distance=float((rotation@eye_center+translation)[2])
        packet['headYaw']=self.yaw.update(points,scores,eye_distance/max(image_size))
        self.diagnostics['yaw']=dict(self.yaw.diagnostics)
        if self.reference is None and abs(packet.get('headYaw',0))<20 and abs(packet.get('headRoll',0))<15:
            self.samples=(self.samples+[float(angles[0])])[-10:]
            if len(self.samples)==10 and np.ptp(self.samples)<6:
                self.reference=float(np.median(self.samples))
        self.last_pitch=0. if self.reference is None else float(np.clip((angles[0]-self.reference)*self.gain,-40,40))
        packet['headPitch']=self.last_pitch
        if not normalize_mouth:
            self.diagnostics.update(pitch=self.last_pitch,pitch_reference=self.reference,raw_pitch=float(angles[0]),pose_angles=angles.tolist(),normalized_reprojection_error=error,mouth_normalized=False)
            return self.diagnostics
        frontal=frontal_landmarks(points,rotation,translation,image_size,self.lip_depth_scale)
        from .brows import frontal_brows,observe
        normalized_brows=frontal_brows(points,frontal,rotation,translation,image_size) if frontal is not None else None
        if normalized_brows is not None:observe(normalized_brows,scores,packet)
        else:packet['browTracked']=False
        detail=contour_controls(frontal,scores) if frontal is not None else None
        packet['mouthContourTracked']=detail is not None
        if detail is not None:packet.update(detail)
        self.diagnostics.update(pitch=self.last_pitch,pitch_reference=self.reference,raw_pitch=float(angles[0]),pose_angles=angles.tolist(),normalized_reprojection_error=error,
                                mouth_normalized=detail is not None)
        return self.diagnostics
