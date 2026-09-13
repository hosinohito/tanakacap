import numpy as np
from tanakacap.motion_gate import DirectionGate,RotationGate
from tanakacap.body_geometry import DepthAssist


def test_single_alternating_small_changes_are_not_followed():
    gate=DirectionGate(.006,.08)
    gate.update([0.],0)
    for i in range(1,30):
        assert gate.update([.02*(-1)**i],i*.05)[0]==0


def test_two_same_direction_changes_and_persistent_endpoint_are_accepted():
    gate=DirectionGate(.006,.08); gate.update([0.],0)
    assert gate.update([.02],.05)[0]==0
    assert gate.update([.03],.10)[0]==.03
    assert gate.update([.05],.15)[0]==.05
    assert gate.update([.5],.20)[0]==.5  # large motion bypasses small-jitter gate
    gate=DirectionGate(.006,.08); gate.update([0.],0)
    gate.update([.02],.05)
    assert gate.update([.02],.10)[0]==.02  # do not freeze after a single real step


def turn(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


def test_rotation_gate_preserves_rotation_and_rejects_small_oscillation():
    gate=RotationGate(); gate.update(np.eye(3),0)
    for i in range(1,20):
        np.testing.assert_allclose(gate.update(turn(np.radians(2)*(-1)**i),i*.05),np.eye(3))
    gate.update(turn(np.radians(3)),1)
    actual=gate.update(turn(np.radians(4)),1.05)
    np.testing.assert_allclose(actual,turn(np.radians(4)))


def test_depth_assist_learns_then_supplements_confirmed_foreshortening():
    assist=DepthAssist()
    for i in range(30): assist.update(np.array([.25,0,.04]),np.array([.24,0,.04]),i*.05)
    bones,status=assist.update(np.array([.25,0,.04]),np.array([.10,0,.04]),1.5)
    assert status=='assisted' and bones[1,2]>.10
    np.testing.assert_allclose(bones[1,:2],[.1,0])
    bones,_=assist.update(np.array([.25,0,.04]),np.array([.10,0,0]),1.55)
    assert bones[1,2]==0  # ambiguous sign must not be invented
    bones,_=assist.update(np.array([.25,0,.04]),np.array([.10,0,-.04]),1.6)
    assert bones[1,2]==-.04  # a single opposite sign is not amplified


def test_depth_assist_does_not_reject_longer_projection_or_retain_absence():
    assist=DepthAssist()
    for i in range(30): assist.update(np.array([.2,0,0]),np.array([.2,0,0]),i*.05)
    bones,_=assist.update(np.array([.35,0,.02]),np.array([.35,0,.02]),1.5)
    np.testing.assert_allclose(bones,[[.35,0,.02]]*2)
    _,status=assist.update(np.array([.1,0,.04]),np.array([.1,0,.04]),3)
    assert status=='model'
    np.testing.assert_allclose(assist.lengths.value,[.2,.2])

