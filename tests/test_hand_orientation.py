import numpy as np
from tanakacap.hand_orientation import palm_basis,add_hands


def hand():
    xyz=np.zeros((133,3)); scores=np.zeros(133)
    xyz[[91,96,100,108]]=[[0,0,0],[-.03,.08,0],[0,.1,0],[.035,.07,0]]
    scores[[91,96,100,108]]=1
    return xyz,scores


def test_palm_turn_changes_normal_with_forward_preserved():
    xyz,s=hand(); a=palm_basis(xyz,s,s,91)
    angle=np.pi/2
    rotation=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
    b=palm_basis(xyz@rotation.T,s,s,91)
    np.testing.assert_allclose(b[0],a[0],atol=1e-6)
    assert abs(np.dot(a[1],b[1]))<1e-6


def test_missing_or_collinear_knuckles_are_rejected():
    xyz,s=hand(); s[96]=0
    assert palm_basis(xyz,s,s,91) is None
    s[96]=1; xyz[108]=xyz[96]*.8
    assert palm_basis(xyz,s,s,91) is None


def test_hands_require_corresponding_arm_and_do_not_enable_other_side():
    xyz,s=hand(); p={'leftArmTracked':True,'rightArmTracked':False}
    add_hands(p,xyz,s,s)
    assert p['leftHandTracked'] and not p['rightHandTracked']
    p['leftArmTracked']=False; add_hands(p,xyz,s,s)
    assert not p['leftHandTracked']


def test_small_depth_response_preserves_palm_orientation():
    xyz,s=hand()
    assert palm_basis(xyz,s,np.full(133,.06),91) is not None
    s[96]=np.nan
    assert palm_basis(xyz,s,np.full(133,.06),91) is None


def test_confirmed_palm_turn_reaches_ninety_percent_without_extra_wait():
    from tanakacap.hand_orientation import PalmFilter
    filter= PalmFilter()
    def packet(degrees):
        angle=np.radians(degrees)
        return dict(leftHandTracked=True,leftHandForward=dict(x=0,y=1,z=0),
                    leftHandNormal=dict(x=float(np.sin(angle)),y=0,z=float(np.cos(angle))))
    filter.update(packet(0),0)
    p=packet(20); filter.update(p,.05)
    assert abs(p['leftHandNormal']['x'])<1e-6
    p=packet(20); filter.update(p,.1)
    angle=np.degrees(np.arctan2(p['leftHandNormal']['x'],p['leftHandNormal']['z']))
    assert 18<angle<20
