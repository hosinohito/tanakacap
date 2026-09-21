import numpy as np
import pytest
from tanakacap.arm_scale import ArmScale
from tanakacap.body3d import BodyRetarget
from test_body3d import body, packet
from test_face_scale import add_face


def test_cache_has_no_face_timeout_and_recovers():
    cache=ArmScale()
    assert cache.update(None,0) is None
    assert cache.update(.002,.1)==.002
    assert cache.update(None,.5)==.002
    assert cache.update(None,1.1)==.002
    assert cache.update(None,120)==.002
    assert cache.update(.004,120.2)==.002
    assert cache.update(.004,120.3)==pytest.approx(.003)
    assert cache.update(.004,120.41)==.004
    assert cache.source=='face'
    cache.reset()
    assert cache.update(None,1.42) is None


def ready_tracker():
    xy,s,z,ds=body();add_face(xy,s);ds[:]=1
    tracker=BodyRetarget(3,1,arm_depth_mode='front_projection')
    for i in range(40):
        p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p['leftArmTracked'] and not p['leftArmHeld']
    return tracker,xy,s,z,ds,p


def test_face_missing_arms_move_without_learning_or_shoulder_scale_fallback():
    tracker,xy,s,z,ds,p=ready_tracker()
    previous=p['leftWrist'].copy();lengths=tracker.automatic_lengths()
    scale=tracker.arm_scale.value
    s[23:91]=0
    xy[[7,9],1]-=30
    xy[6,0]+=20  # This changes the torso fallback scale, not the arm cache.
    for i in range(40,48):
        p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
        assert not tracker.diagnostics['arm_length_learning']
    assert p['leftArmTracked'] and not p['leftArmHeld']
    assert p['leftWrist']!=previous
    assert tracker.automatic_lengths()==lengths
    assert tracker.diagnostics['arm_geometry_scale']==scale
    for i in range(48,64):
        p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p['leftArmTracked'] and not p['leftArmHeld']
    assert tracker.diagnostics['arm_scale_source']=='held_face'


def test_missing_joint_and_unlearned_arm_do_not_use_cached_scale():
    tracker,xy,s,z,ds,_=ready_tracker()
    s[23:91]=0;s[9]=0
    p=tracker.update(packet(),xy,s,z,ds,now=2,image_size=(640,480))
    assert not p['leftArmTracked'] or p['leftArmHeld']
    assert p['rightArmTracked'] and not p['rightArmHeld']
    tracker.depth_assist['right'].lengths.value[:]=0
    p=tracker.update(packet(),xy,s,z,ds,now=2.05,image_size=(640,480))
    assert not p['rightArmTracked'] or p['rightArmHeld']


def test_person_loss_clears_cache_and_recovery_does_not_learn_lengths():
    tracker,xy,s,z,ds,_=ready_tracker()
    s[23:91]=0
    tracker.update(packet(),xy,s,z,ds,now=2,image_size=(640,480))
    lengths=tracker.automatic_lengths()
    add_face(xy,s);xy[23:91]*=1.1
    tracker.update(packet(),xy,s,z,ds,now=2.05,image_size=(640,480))
    assert tracker.diagnostics['arm_scale_source']=='recovering_face'
    assert not tracker.diagnostics['arm_length_learning']
    assert tracker.automatic_lengths()==lengths
    tracker.update(packet(),None,None,None,None,now=2.1)
    s[23:91]=0
    p=tracker.update(packet(),xy,s,z,ds,now=2.15,image_size=(640,480))
    assert tracker.diagnostics['arm_geometry_scale'] is None
    assert not p['leftArmTracked'] or p['leftArmHeld']


def test_missing_opposite_shoulder_does_not_expire_visible_arm():
    tracker,xy,s,z,ds,_=ready_tracker()
    lengths=tracker.automatic_lengths()
    s[23:91]=0;s[6]=0
    for i in range(40,140):
        p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p['leftArmTracked'] and not p['leftArmHeld']
    assert not p['rightArmTracked'] or p['rightArmHeld']
    assert tracker.automatic_lengths()==lengths
