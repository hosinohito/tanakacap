import numpy as np
import pytest
from tanakacap.mouth_detail import contour_controls
from tanakacap.retarget import packet_from_landmarks
from tanakacap.body3d import BodyRetarget
from tanakacap.torso_yaw import elbow_yaw
from test_mouth_width import face_points


def detailed_face():
    p,s=face_points()
    p[23+48:23+60]=np.array([[-40,0],[-30,-8],[-15,-12],[0,-14],[15,-12],[30,-8],
                            [40,0],[30,8],[15,12],[0,14],[-15,12],[-30,8]])+[250,180]
    p[23+62]=[250,178];p[23+66]=[250,184]
    return p,s


def test_contour_changes_with_fixed_width_height_and_anatomical_side():
    p,s=detailed_face();base=contour_controls(p,s)
    p[23+54,1]-=10
    changed=contour_controls(p,s)
    assert changed['mouthLeftCorner']>base['mouthLeftCorner']+.8
    assert changed['mouthRightCorner']==pytest.approx(base['mouthRightCorner'])
    p,s=detailed_face();p[23+51,1]-=5
    assert contour_controls(p,s)['mouthBow']>base['mouthBow']


def test_head_body_roll_same_sign_and_anatomical_left_wink():
    p,s=face_points();p[[5,6]]=[[350,250],[150,250]]
    angle=np.radians(20);rot=np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]])
    p=p@rot+100
    face=packet_from_landmarks(p,s,0)
    body=BodyRetarget().update(face.copy(),p,s,np.zeros(133),s,now=0)
    assert face['headRoll']==pytest.approx(20)
    assert body['torsoRoll']==pytest.approx(20)
    p,s=face_points();p[23+42:23+48,1]=100
    result=packet_from_landmarks(p,s,0)
    assert result['leftBlink']==1 and result['rightBlink']<.1


def test_tongue_output_removed():
    p,s=detailed_face();packet=packet_from_landmarks(p,s,0)
    assert 'tongueOut' not in packet and 'tongueTracked' not in packet


def test_elbows_choose_yaw_without_wrist_or_common_translation():
    xyz=np.zeros((133,3));s=np.ones(133)
    xyz[7,2]=.36
    assert elbow_yaw(xyz,s)==pytest.approx(45)
    xyz[[9,10],2]=[-100,100]
    assert elbow_yaw(xyz,s)==pytest.approx(45)
    xyz[:,2]+=2
    assert elbow_yaw(xyz,s)==pytest.approx(45)
    xyz[8,2]=xyz[7,2]
    assert elbow_yaw(xyz,s)==0
    xyz[8,2]+=.36
    assert elbow_yaw(xyz,s)==pytest.approx(-45)
    s[7]=0
    assert elbow_yaw(xyz,s) is None
