import numpy as np
import pytest
from tanakacap.body_geometry import cross_body_amount
from tanakacap.mouth_detail import contour_controls
from tanakacap.retarget import FaceFilter
from test_mouth_detail import detailed_face


def test_crossing_is_mirrored_and_excludes_outward_hand():
    p=np.zeros((133,2));s=np.ones(133);p[5]=[400,200];p[6]=[200,200]
    for side,wrist,own,sign in [('left',9,400,-1),('right',10,200,1)]:
        for fraction,expected in [(-.2,0),(.2,0),(.5,.5),(.7,1),(1.2,1)]:
            p[wrist]=[own+sign*200*fraction,300]
            assert cross_body_amount(p,s,side)==pytest.approx(expected)
        s[wrist]=0
        assert cross_body_amount(p,s,side)==0


def test_closed_mouth_translation_is_separate_from_corners_and_roll_invariant():
    p,s=detailed_face();p[[23+31,23+35]]=[[240,150],[260,150]];base=contour_controls(p,s)
    p[23+48:23+68,0]+=8
    shifted=contour_controls(p,s)
    assert shifted['mouthShift']>base['mouthShift']
    assert shifted['mouthLeftCorner']==pytest.approx(base['mouthLeftCorner'])
    angle=.4;rotation=np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]])
    rotated=contour_controls(p@rotation+100,s)
    assert rotated['mouthShift']==pytest.approx(shifted['mouthShift'])


def test_shift_neutral_and_both_directions_use_shared_observation_rule():
    f=FaceFilter(3,1)
    def packet(shift):return dict(faceTracked=True,mouthContourTracked=True,mouthLeftCorner=0.,mouthRightCorner=0.,mouthBow=0.,mouthShift=shift,
        mouth=0.,headPitch=0.,headYaw=0.,headRoll=0.,leftBlink=0.,rightBlink=0.)
    for i in range(20):p=f.update(packet(.2),i*.04)
    assert abs(p['mouthShift'])<1e-8
    for i in range(20,30):p=f.update(packet(.6),i*.04)
    assert p['mouthShift']>.5
    for i in range(30,40):p=f.update(packet(-.2),i*.04)
    assert p['mouthShift']<-.5
