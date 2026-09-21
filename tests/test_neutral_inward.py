import numpy as np
import pytest
from tanakacap.body_geometry import visible_hand_inward
from tanakacap.torso_yaw import ShoulderWidthReference
from tanakacap.body3d import BodyRetarget
from tanakacap.retarget import FaceFilter
from test_body3d import body,packet
from tanakacap.hand_orientation import palm_basis


def test_observed_front_shoulder_width_is_neutral_not_nominal_width():
    reference=ShoulderWidthReference()
    for i in range(20):angle=reference.update(150,.0018,i*.05)
    assert angle==0  # observed .27m proxy is not forced to a fictitious .36m
    assert reference.update(150*.8,.0018,1)>30
    assert reference.update(150*.7,.0018/.7,1.1)==0
    assert reference.update(150*.99,.0018,1.2)==0
    for i in range(30,60):reference.update(190,.0018,i*.05)
    assert reference.update(150,.0018,3.1)==0


@pytest.mark.parametrize('side,wrist',[('left',9),('right',10)])
def test_legacy_inward_hand_no_longer_forces_front_including_above_head(side,wrist):
    xy,s,z,ds=body();xy[wrist]=[200,30];z[wrist]=.3
    assert visible_hand_inward(xy,s,side)
    tracker=BodyRetarget()
    for i in range(20):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p[side+'ArmTracked'] and p[side+'Wrist']['z']<0
    assert not p.get(side+'WristInFront',False) and not p.get(side+'UpperInFront',False)
    s[wrist]=0
    assert not visible_hand_inward(xy,s,side)


def test_corner_reference_allows_asymmetric_up_and_down():
    f=FaceFilter()
    def p(left=.3,right=.25):
        return dict(faceTracked=True,mouthContourTracked=True,mouthLeftCorner=left,mouthRightCorner=right,mouthBow=0.,
            mouth=0.,leftBlink=0.,rightBlink=0.,headPitch=0.,headYaw=0.,headRoll=0.)
    for i in range(20):result=f.update(p(),i*.04)
    assert result['mouthLeftCorner']==pytest.approx(0)
    for i in range(20,30):result=f.update(p(.6,-.05),i*.04)
    assert result['mouthLeftCorner']>.4 and result['mouthRightCorner']<-.4


def test_palm_can_use_middle_axis_when_wrist_triangle_collapses():
    xyz=np.zeros((133,3));s=np.zeros(133)
    xyz[[91,96,100,108]]=[[0,0,0],[-.035,0,0],[0,.06,0],[.035,0,0]]
    s[[91,96,100,108]]=1
    basis=palm_basis(xyz,s,s,91)
    assert basis is not None
    assert np.linalg.norm(basis[1])==pytest.approx(1)
