import numpy as np
import pytest
from capture_lab.face_scale import FaceScale
from capture_lab.body3d import BodyRetarget
from test_body3d import body,packet


def add_face(xy,s):
    ids=np.array([27,28,29,30,36,39,42,45])+23
    xy[ids]=np.array([[0,0],[0,8],[0,16],[0,25],[-30,0],[-15,0],[15,0],[30,0]])+[200,45]
    s[ids]=1


def test_distance_scale_ignores_jaw_and_handles_roll_and_foreshortening():
    xy,s,_,_=body();add_face(xy,s)
    scale=FaceScale()
    for i in range(9):assert scale.update(xy,s,.002,now=i*.05) is None
    assert scale.update(xy,s,.002,now=.45)==pytest.approx(.002)
    jaw=xy.copy();jaw[23:40]+=70
    assert scale.update(jaw,s,.002)==pytest.approx(.002)
    a=.3;r=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
    moved=xy@np.diag([.75,1.])@r*.6+40
    assert scale.update(moved,s,None)==pytest.approx(.002/.6)
    s[23+30]=0
    assert scale.update(moved,s,None) is None


def test_moving_away_does_not_shorten_supported_arm_or_add_depth():
    xy,s,z,ds=body();add_face(xy,s);z[:]=0;ds[:]=1
    tracker=BodyRetarget()
    for i in range(30): tracker.update(packet(),xy,s,z,ds,now=i*.05)
    lengths=tracker.automatic_lengths()
    before=tracker.previous['left'].copy()
    for i in range(30,60): tracker.update(packet(),xy*.65+30,s,z,ds,now=i*.05)
    np.testing.assert_allclose(tracker.previous['left'],before,atol=1e-6)
    for side in lengths: np.testing.assert_allclose(tracker.automatic_lengths()[side],lengths[side],atol=1e-6)
    assert tracker.diagnostics['distance_source']=='face_affine'


def test_face_scale_failure_does_not_disable_observed_body_or_calibrate_lengths():
    xy,s,z,ds=body();add_face(xy,s);ds[:]=1
    tracker=BodyRetarget(3,1)
    for i in range(30):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    lengths=tracker.automatic_lengths()
    original=p['leftWrist'].copy()
    # Face estimate can disappear while shoulders/elbows/wrists remain visible.
    s[23:91]=0
    xy[[7,9],1]-=45;z[7]-=.08
    for i in range(30,60):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p['torsoTracked'] and p['leftArmTracked'] and p['rightArmTracked']
    assert not p['leftArmHeld'] and p['leftWrist']!=original
    assert tracker.automatic_lengths()==lengths


def test_bad_face_reference_cannot_latch_whole_body_off():
    xy,s,z,ds=body();add_face(xy,s);ds[:]=1
    tracker=BodyRetarget()
    for i in range(30):tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    # Reproduce the bad-startup-reference failure independently of camera warmup.
    tracker.face_scale.reference[3]+=[40,40]
    lengths=tracker.automatic_lengths()
    for i in range(30,70):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p['torsoTracked'] and p['leftArmTracked'] and p['rightArmTracked']
    assert tracker.automatic_lengths()==lengths


def test_one_bad_startup_face_is_not_selected_as_session_reference():
    xy,s,_,_=body();add_face(xy,s)
    distorted=xy.copy();distorted[23+30]+=[40,40]
    scale=FaceScale()
    assert scale.update(distorted,s,.002,now=0) is None
    for i in range(1,10):value=scale.update(xy,s,.002,now=i*.05)
    assert value==pytest.approx(.002)
    assert scale.status=='face_affine'
    assert scale.details['residual']<1e-6


def test_fallback_tracks_distance_but_never_overwrites_arm_maxima():
    xy,s,z,ds=body();add_face(xy,s);z[:]=0;ds[:]=1
    tracker=BodyRetarget(3,1)
    for i in range(30):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    lengths=tracker.automatic_lengths();pose=p['leftWrist'].copy()
    s[23:91]=0
    for i in range(30,60):p=tracker.update(packet(),xy*.65+40,s,z,ds,now=i*.05,image_size=(640,480))
    assert tracker.diagnostics['geometry_scale_source']=='shoulder_fallback'
    assert not tracker.diagnostics['arm_length_learning']
    assert tracker.automatic_lengths()==lengths
    assert p['leftWrist']==pytest.approx(pose)
    # Independent face recovery resumes calibration; missing shoulders+face
    # still stop after the short cache rather than inventing observations.
    s[23:91]=1
    for i in range(60,70):p=tracker.update(packet(),xy*.65+40,s,z,ds,now=i*.05,image_size=(640,480))
    assert tracker.diagnostics['geometry_scale_source']=='face'
    s[23:91]=0;s[[5,6]]=0
    for i in range(70,90):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert not p['torsoTracked'] and not p['leftArmTracked']
    assert tracker.diagnostics['geometry_scale_source']=='unavailable'
