import numpy as np
from tanakacap.retarget import FaceFilter
from tanakacap.body_geometry import DepthAssist
from tanakacap.motion_gate import DirectionGate,RotationGate


def face(value):
    return dict(faceTracked=True,headPitch=value*20,headYaw=value*40,headRoll=value*10,
                mouth=value,leftBlink=value,rightBlink=value)


def test_head_and_every_expression_confirm_then_follow_without_extra_python_smoothing():
    f=FaceFilter(); f.update(face(0),0)
    p=f.update(face(1),.05)
    assert p['headYaw']==0 and p['mouth']==0 and p['leftBlink']==0 and p['rightBlink']==0
    p=f.update(face(1),.10)
    assert p['headYaw']==40 and p['mouth']==1 and p['leftBlink']==1 and p['rightBlink']==1
    p=f.update(face(.9),.15)
    assert p['mouth']==1
    p=f.update(face(1),.20)
    assert p['mouth']==1


def test_face_loss_does_not_carry_a_pending_direction_to_next_person():
    f=FaceFilter(); f.update(face(0),0); f.update(face(1),.05)
    f.update({'faceTracked':False},.1)
    assert f.update(face(.5),.15)['mouth']==.5


def test_large_arm_changes_also_need_two_observations():
    gate=DirectionGate(.006,float('inf')); gate.update([0.],0)
    assert gate.update([1.],.05)[0]==0
    assert gate.update([1.],.10)[0]==1
