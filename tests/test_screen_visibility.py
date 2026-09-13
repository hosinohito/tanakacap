import numpy as np
from tanakacap.visibility import screen_visibility
from tanakacap.body3d import BodyRetarget
from test_body3d import body,packet


def test_boundary_wrist_is_not_an_arm_or_calibration_sample():
    xy,s,z,ds=body(); xy[91:112]=[350,250]
    tracker=BodyRetarget()
    tracker.update(packet(),xy,s,z,ds,now=0,image_size=(640,480))
    lengths=tracker.automatic_lengths()
    xy[[9,*range(91,112)]]=[639,479]
    for i in range(1,20):
        p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
        assert p['leftOutOfView'] and not p['leftArmTracked'] and not p['leftHandTracked']
        assert not p['leftUpperArmTracked']
        assert not any(p['leftFingerTracked'])
        assert p['rightArmTracked']
    assert tracker.automatic_lengths()['left']==lengths['left']


def test_offscreen_hand_ignores_visible_elbow_motion_after_rollback():
    xy,s,z,ds=body();xy[[9,*range(91,112)]]=[639,479]
    tracker=BodyRetarget(3,1)
    for i in range(4):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert not p['leftUpperArmTracked'] and not p['leftArmTracked']
    xy[7,1]-=50
    for i in range(4,10):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert not p['leftUpperArmTracked'] and not p['leftArmTracked']
    xy[7]=[639,479]
    p=tracker.update(packet(),xy,s,z,ds,now=.5,image_size=(640,480))
    assert not p['leftUpperArmTracked'] and not p['leftArmTracked']


def test_single_clipped_tip_does_not_disable_palm_or_arm():
    xy=np.full((133,2),[320.,240.]);s=np.ones(133)
    xy[99]=[640,240]
    scores,states=screen_visibility(xy,s,(640,480))
    assert not states['left'] and scores[9]==1 and scores[100]==1
    assert scores[99]==0
    assert s[99]==1


def test_border_hips_cannot_create_pitch_but_shoulders_still_turn():
    xy,s,z,ds=body();xy[[11,12],1]=479;z[[11,12]]=.3
    tracker=BodyRetarget()
    p=tracker.update(packet(),xy,s,z,ds,now=0,image_size=(640,480))
    assert p['torsoTracked'] and p['torsoPitch']==0
    assert tracker.diagnostics['torso_pitch_source']=='held_missing_hips'


def test_missing_pelvis_holds_accepted_pitch_without_stopping_yaw():
    xy,s,z,ds=body();z[[11,12]]=.2
    tracker=BodyRetarget()
    p=tracker.update(packet(),xy,s,z,ds,now=0,image_size=(640,480))
    pitch=p['torsoPitch'];assert pitch>10
    xy[[11,12],1]=479;z[5]=-.1;z[6]=.1
    z[7]=-.2;z[8]=.2
    for i in range(1,10):p=tracker.update(packet(),xy,s,z,ds,now=i*.05,image_size=(640,480))
    assert p['torsoPitch']==pitch and p['torsoYaw']>20
