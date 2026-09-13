import numpy as np
from tanakacap.arm_constraints import ArmCalibration,constrain_arm,smooth_fixed_bones
from tanakacap.hand_orientation import PalmFilter


def test_calibration_requires_stable_straight_visible_arms():
    xy=np.zeros((133,2)); scores=np.ones(133)
    xy[[5,6,7,8,9,10]]=[[400,100],[200,100],[500,180],[100,180],[600,260],[0,260]]
    c=ArmCalibration(); c.begin(0)
    for i in range(70): c.observe(xy,scores,i/30)
    assert c.value is not None
    np.testing.assert_allclose(c.value['left'],[np.hypot(100,80)*.0018]*2)
    old=c.value
    c.begin(3); scores[9]=0
    for i in range(400): c.observe(xy,scores,3+i/30)
    assert c.value is old and c.start is None


def test_shorter_projection_recovers_forward_depth_with_fixed_lengths():
    result=constrain_arm(np.array([0,-.3,0]),np.array([0,-.1,0]),[.3,.25])
    np.testing.assert_allclose(np.linalg.norm(result,axis=1),[.3,.25])
    assert result[1,2]>.22


def test_previous_branch_and_body_orientation_allow_backwards_motion():
    a=np.array([0,-.25,-.1]); b=np.array([0,-.1,-.2])
    r=constrain_arm(a,b,[.3,.25],np.stack([a,b]),np.array([0,0,-1]))
    assert (r[:,2]<0).all()


def test_impossible_projection_is_not_silently_recalibrated():
    assert constrain_arm(np.array([1.,0,0]),np.array([0,.2,0]),[.3,.25]) is None


def test_smoothing_keeps_lengths_and_limits_angular_speed():
    old=np.array([[.3,0,0],[.25,0,0]])
    target=-old
    r=smooth_fixed_bones(old,target,[.3,.25],1/30)
    np.testing.assert_allclose(np.linalg.norm(r,axis=1),[.3,.25])
    assert np.degrees(np.arccos(r[0,0]/.3))<=8.01


def palm(normal):
    return dict(leftHandTracked=True,leftHandForward=dict(x=0,y=1,z=0),leftHandNormal=dict(zip('xyz',normal)))


def test_palm_rejects_single_flip_but_accepts_sustained_half_turn():
    f=PalmFilter(); p=palm([0,0,1]); f.update(p,0)
    p=palm([0,0,-1]); f.update(p,1/30)
    assert p['leftHandNormal']['z']>.99
    for i in range(2,80):
        p=palm([0,0,-1]); f.update(p,i/30)
        normal=np.array(list(p['leftHandNormal'].values()))
        forward=np.array(list(p['leftHandForward'].values()))
        assert abs(normal@forward)<1e-6
        assert abs(np.linalg.norm(normal)-1)<1e-6
    assert p['leftHandNormal']['z']<-.99


def test_fast_confirmed_palm_turn_does_not_wait_120ms():
    f=PalmFilter(); p=palm([0,0,1]); f.update(p,0)
    p=palm([0,0,-1]); f.update(p,.05)
    assert p['leftHandNormal']['z']>.99
    p=palm([0,0,-1]); f.update(p,.10)
    assert p['leftHandNormal']['z']<.95
    for now in [.15,.20,.25,.30]:
        p=palm([0,0,-1]); f.update(p,now)
    assert p['leftHandNormal']['z']<-.95


def test_palm_missing_frame_breaks_reversal_confirmation():
    f=PalmFilter(); p=palm([0,0,1]); f.update(p,0)
    p=palm([0,0,-1]); f.update(p,.05)
    f.update({'leftHandTracked':False},.1)
    p=palm([0,0,-1]); f.update(p,.15)
    assert p['leftHandNormal']['z']>.99
