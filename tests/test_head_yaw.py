import numpy as np
import pytest
from tanakacap.head_pose import HeadPose
from tanakacap.head_yaw import CircularYaw
from test_head_pose import projected


def calibrated():
    model=HeadPose();packet=dict(faceTracked=True,headPitch=0,headYaw=0,headRoll=0)
    for _ in range(15):
        points,scores=projected();model.update(points,scores,packet,(1280,720))
    assert model.yaw.reference is not None
    return model,packet


@pytest.mark.parametrize('yaw',[-45,-30,-10,0,10,30,45])
@pytest.mark.parametrize('depth',[.45,.7,1.0])
def test_projected_circle_recovers_rotation_with_distance_change(yaw,depth):
    model,packet=calibrated()
    points,scores=projected(yaw=yaw,depth=depth)
    model.update(points,scores,packet,(1280,720))
    assert packet['headYaw']==pytest.approx(yaw,abs=4)


def test_pitch_and_roll_do_not_become_yaw():
    for pitch in (-20,20):
        model,packet=calibrated()
        points,scores=projected(pitch=pitch,roll=20,yaw=30)
        model.update(points,scores,packet,(1280,720))
        assert packet['headYaw']==pytest.approx(30,abs=4)


def test_missing_points_hold_and_sideways_start_does_not_calibrate():
    model=CircularYaw();points,scores=projected(yaw=45)
    for _ in range(20):model.update(points,scores,.7/1280)
    assert model.reference is None
    head,packet=calibrated();points,scores=projected(yaw=30)
    head.update(points,scores,packet,(1280,720));previous=packet['headYaw']
    scores[:]=0
    head.update(points,scores,packet,(1280,720))
    assert packet['headYaw']==previous


def test_closed_eyelids_do_not_change_eye_chord():
    model,packet=calibrated();points,scores=projected(yaw=30)
    model.update(points,scores,packet,(1280,720));previous=packet['headYaw']
    points[np.array([37,38,40,41,43,44,46,47])+23,1]+=5
    model.update(points,scores,packet,(1280,720))
    assert packet['headYaw']==pytest.approx(previous,abs=1e-5)
