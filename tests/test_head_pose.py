import cv2
import numpy as np
import pytest
from capture_lab.head_pose import TEMPLATE,POSE_IDS,fit_pose,frontal_landmarks,camera_matrix,HeadPose
from capture_lab.mouth_detail import contour_controls


def projected(pitch=0,yaw=0,roll=0,depth=.7,shift=(0,0),expression=0):
    rx=cv2.Rodrigues(np.array([np.radians(pitch),0.,0.]))[0]
    ry=cv2.Rodrigues(np.array([0.,np.radians(yaw),0.]))[0]
    rz=cv2.Rodrigues(np.array([0.,0.,np.radians(roll)]))[0]
    rotation=rz@ry@rx;t=np.array([*shift,depth])
    points=np.zeros((133,2));scores=np.ones(133)
    for i,point in TEMPLATE.items():
        point=point.copy()
        if i==54:point[1]-=expression
        points[23+i]=cv2.projectPoints(point[None],cv2.Rodrigues(rotation)[0],t,camera_matrix((1280,720)),None)[0].reshape(2)
    return points,scores


@pytest.mark.parametrize('pitch',[-30,-15,0,15,30])
def test_pitch_and_mouth_pose_separation(pitch):
    points,scores=projected(pitch,yaw=15,roll=10,depth=.9,shift=(.08,-.04))
    pose=fit_pose(points,scores,(1280,720));assert pose is not None
    r,t,angles,error=pose
    assert angles[0]==pytest.approx(pitch,abs=.05)
    frontal=frontal_landmarks(points,r,t,(1280,720))
    controls=contour_controls(frontal,scores)
    base,bs=projected();br,bt,_,_=fit_pose(base,bs,(1280,720))
    expected=contour_controls(frontal_landmarks(base,br,bt,(1280,720)),bs)
    for key in expected:assert controls[key]==pytest.approx(expected[key],abs=1e-5)


def test_real_asymmetric_expression_survives_pose_correction():
    p,s=projected(pitch=25,expression=.003)
    r,t,_,_=fit_pose(p,s,(1280,720))
    changed=contour_controls(frontal_landmarks(p,r,t,(1280,720)),s)
    p,s=projected(pitch=25)
    r,t,_,_=fit_pose(p,s,(1280,720))
    neutral=contour_controls(frontal_landmarks(p,r,t,(1280,720)),s)
    assert changed['mouthLeftCorner']>neutral['mouthLeftCorner']+.2
    assert changed['mouthRightCorner']==pytest.approx(neutral['mouthRightCorner'],abs=1e-6)


def test_pitch_reference_gain_and_missing_pose_hold():
    model=HeadPose();p,s=projected(pitch=5)
    packet=dict(faceTracked=True,headPitch=0,headYaw=0,headRoll=0)
    for _ in range(10):model.update(p,s,packet,(1280,720))
    assert model.reference==pytest.approx(5,abs=.05)
    p,s=projected(pitch=20);model.update(p,s,packet,(1280,720))
    assert packet['headPitch']==pytest.approx(27,abs=.1)
    before=packet['headPitch'];s[23+30]=0
    model.update(p,s,packet,(1280,720))
    assert packet['headPitch']==before and not packet['mouthContourTracked']
    assert packet['faceTracked']


def test_degenerate_input_is_rejected():
    assert fit_pose(np.zeros((133,2)),np.ones(133),(1280,720)) is None
    assert fit_pose(np.full((133,2),np.nan),np.ones(133),(1280,720)) is None
