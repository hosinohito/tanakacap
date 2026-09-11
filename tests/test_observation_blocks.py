import numpy as np
from capture_lab.motion_gate import DirectionGate,RotationGate,ObservationMean
from capture_lab.retarget import FaceFilter
from capture_lab.fingers import FingerTracker
from capture_lab.body3d import BodyRetarget
from capture_lab.hand_orientation import PalmFilter


def test_three_frame_blocks_require_six_new_frames_to_confirm():
    gate=DirectionGate(.01,float('inf'),3)
    assert gate.update([0],0) is None
    assert gate.update([0],.033) is None
    np.testing.assert_allclose(gate.update([0],.066),[0])
    for i in range(5):
        np.testing.assert_allclose(gate.update([3],.099+i*.033),[0])
    np.testing.assert_allclose(gate.update([3],.264),[3])


def test_nonoverlapping_means_not_rolling_and_low_fps_does_not_reset():
    gate=DirectionGate(.01,float('inf'),3)
    for i in range(3): gate.update([0],i*.1)
    for i,v in enumerate([1,2,3,4,5,6]): result=gate.update([v],.3+i*.1)
    np.testing.assert_allclose(result,[5])
    assert gate.update([100],2) is None # real raw-observation gap


def test_rotation_average_crosses_180_without_turning_via_zero():
    def frame(degrees):
        a=np.radians(degrees)
        return np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    mean=ObservationMean(3,rotation=True)
    for i,a in enumerate([179,-179,180]): result=mean.update(frame(a),i*.03)
    np.testing.assert_allclose(result,frame(180),atol=1e-6)
    np.testing.assert_allclose(result.T@result,np.eye(3),atol=1e-6)
    assert np.linalg.det(result)>.999


def test_block_setting_reaches_every_part_and_legacy_is_retained():
    body=BodyRetarget(3);face=FaceFilter(3)
    assert body.motion['left'].mean.size==body.torso_motion.mean.size==3
    assert body.palms.block_size==body.fingers.block_size==3
    assert face.head.mean.size==face.expression.mean.size==3
    gate=DirectionGate(.01,float('inf'),1)
    gate.update([0],0); gate.update([3],.03)
    np.testing.assert_allclose(gate.update([3],.06),[3])


def test_missing_palm_discards_partial_block():
    gate=RotationGate(3)
    gate.update(np.eye(3),0);gate.update(np.eye(3),.03)
    gate.missing()
    assert gate.update(np.eye(3),.06) is None
    assert gate.update(np.eye(3),.09) is None
    np.testing.assert_allclose(gate.update(np.eye(3),.12),np.eye(3))


def test_near_half_turn_does_not_look_like_opposite_motion_to_gate():
    def frame(degrees):
        a=np.radians(degrees)
        return np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    gate=RotationGate()
    gate.update(frame(0),0)
    gate.update(frame(179),.033)
    np.testing.assert_allclose(gate.update(frame(181),.066),frame(181),atol=1e-6)


def test_face_and_expression_both_wait_for_two_complete_means():
    filter=FaceFilter(3)
    def packet(value):
        return dict(faceTracked=True,headPitch=value,headYaw=value,headRoll=value,
                    mouth=value/10,leftBlink=value/10,rightBlink=value/10)
    for i in range(3): p=filter.update(packet(0),i*.033)
    assert p['faceTracked']
    for i in range(5):
        p=filter.update(packet(10),(3+i)*.033)
        assert p['headYaw']==0 and p['mouth']==0
    p=filter.update(packet(10),8*.033)
    assert p['headYaw']==10 and p['mouth']==1


def test_overlapping_mean_uses_123_then_234_and_updates_every_frame():
    mean=ObservationMean(3,stride=1)
    assert mean.update([1],0) is None
    assert mean.update([2],.03) is None
    np.testing.assert_allclose(mean.update([3],.06),[2])
    np.testing.assert_allclose(mean.update([4],.09),[3])
    np.testing.assert_allclose(mean.update([5],.12),[4])
    gate=DirectionGate(.01,float('inf'),3,stride=1)
    for i in range(3):gate.update([0],i*.03)
    np.testing.assert_allclose(gate.update([1],.09),[0])
    np.testing.assert_allclose(gate.update([2],.12),[1])
    np.testing.assert_allclose(gate.update([3],.15),[2])


def test_stride_setting_reaches_all_capture_parts():
    body=BodyRetarget(3,1);face=FaceFilter(3,1)
    assert body.motion['left'].mean.stride==body.torso_motion.mean.stride==1
    assert body.palms.stride==body.fingers.stride==1
    assert face.head.mean.stride==face.expression.mean.stride==1
