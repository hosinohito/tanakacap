import numpy as np
import pytest
from tanakacap.body3d import BodyRetarget
from tanakacap.inference import decode_simcc3d


def body():
    xy=np.zeros((133,2)); score=np.zeros(133); depth=np.zeros(133)
    xy[[5,6,7,8,9,10,11,12]] = [[300,100],[100,100],[350,200],[50,200],[350,250],[50,250],[270,350],[130,350]]
    score[[5,6,7,8,9,10,11,12]]=1
    depth[[7,9]]=[-.1,-.35]
    return xy,score,depth,score.copy()


def packet():
    return dict(faceTracked=False,tracked=True,leftArmTracked=True,rightArmTracked=True)


def test_depth_decode_uses_288_depth_axis_not_384_image_height():
    arrays=[np.zeros((1,133,n)) for n in (576,768,576)]
    for data,bin in zip(arrays,(288,384,288)): data[:,:,bin]=1
    _,_,z,_=decode_simcc3d(arrays,np.array([0,0]),np.array([288,384]),[288,384])
    assert np.all(z==0)
    arrays[2][:,:,288]=0; arrays[2][:,:,144]=1
    assert decode_simcc3d(arrays,np.array([0,0]),np.array([288,384]),[288,384])[2][0] == pytest.approx(-2.1744869/2)


def test_hand_toward_camera_has_positive_avatar_depth():
    p=BodyRetarget().update(packet(),*body(),now=0)
    assert p['leftArmTracked'] and p['leftWrist']['z']>.5
    assert p['torsoTracked'] and p['torsoYaw']==pytest.approx(0)


def test_shoulder_magnitude_uses_elbow_sign():
    xy,s,z,ds=body(); z[5]=.12; z[6]=-.12
    p=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    assert p['torsoTracked'] and p['torsoYaw']==pytest.approx(np.degrees(np.arcsin(.24/.36)))


def test_hidden_hips_do_not_invent_forward_lean():
    xy,s,z,ds=body(); z[[11,12]]=.25; s[[11,12]]=0
    p=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    assert p['torsoPitch']==pytest.approx(0)


def test_visible_hips_support_forward_lean():
    xy,s,z,ds=body(); z[[11,12]]=.25
    p=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    assert p['torsoPitch']>10


def test_hip_depth_and_shoulder_roll_do_not_invent_torso_yaw():
    xy,s,z,ds=body()
    xy[5,1]+=40
    a=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    z[[11,12]]=.25
    b=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    assert b['torsoYaw']==pytest.approx(a['torsoYaw'])
    assert b['torsoPitch']>10


@pytest.mark.parametrize('degrees',[-45,-20,0,20,45])
def test_torso_has_known_yaw_from_elbow_depths(degrees):
    xy,s,z,ds=body()
    angle=np.radians(degrees)
    xy[5,0]=200+100*np.cos(angle);xy[6,0]=200-100*np.cos(angle)
    z[5]=-.18*np.sin(angle);z[6]=.18*np.sin(angle)
    z[7]=-.18*np.tan(angle);z[8]=.18*np.tan(angle)
    tracker=BodyRetarget()
    for i in range(20): p=tracker.update(packet(),xy,s,z,ds,now=i*.05)
    assert p['torsoYaw']==pytest.approx(degrees,abs=.01)
    expected_source='shoulder_width_elbow_sign' if degrees else 'held_ambiguous_elbow_sign'
    assert tracker.diagnostics['torso_yaw_source']==expected_source


def test_missing_depth_disables_planar_arm_fallback():
    p=BodyRetarget().update(packet(),None,None,None,None,now=0)
    assert not p['leftArmTracked'] and not p['tracked']


def test_depth_jump_is_rate_limited_and_loss_resets_state():
    r=BodyRetarget(); xy,s,z,ds=body()
    a=r.update(packet(),xy,s,z,ds,now=0)
    z[9]=.2
    b=r.update(packet(),xy,s,z,ds,now=.033)
    assert abs(b['leftWrist']['z']-a['leftWrist']['z'])<.3
    r.update(packet(),None,None,None,None,now=.06)
    assert not r.previous


def test_opposite_shoulder_loss_does_not_stop_visible_arm_with_recent_scale():
    r=BodyRetarget(); xy,s,z,ds=body()
    assert r.update(packet(),xy,s,z,ds,now=0)['leftArmTracked']
    s[6]=0
    p=r.update(packet(),xy,s,z,ds,now=.033)
    assert p['leftArmTracked'] and p['rightArmTracked'] and p['rightArmHeld'] and not p['torsoTracked']
    p=r.update(packet(),xy,s,z,ds,now=.16)
    assert p['leftArmTracked'] and not p['rightArmTracked']
    p=r.update(packet(),xy,s,z,ds,now=.6)
    assert not p['leftArmTracked']


def test_invalid_torso_basis_does_not_stop_valid_arm():
    r=BodyRetarget(); xy,s,z,ds=body()
    r.update(packet(),xy,s,z,ds,now=0)
    xy[[5,6,7,8,9,10,11,12],0]=400-xy[[5,6,7,8,9,10,11,12],0]
    p=r.update(packet(),xy,s,z,ds,now=.033)
    assert not p['torsoTracked'] and p['leftArmTracked'] and p['rightArmTracked']


def test_depth_peak_crossing_point_one_does_not_toggle_tracking():
    r=BodyRetarget(); xy,s,z,ds=body()
    # Range seen in the user's recording, despite strong XY detections.
    for frame,peak in enumerate([.12,.08,.06,.11,.09]):
        ds[:]=peak
        p=r.update(packet(),xy,s,z,ds,now=frame/30)
        assert p['torsoTracked'] and p['leftArmTracked'] and p['rightArmTracked']


@pytest.mark.parametrize('bad',[0.,float('nan'),float('inf')])
def test_bad_xy_confidence_still_rejects_arm(bad):
    xy,s,z,ds=body(); s[9]=bad; ds[:]=.08
    p=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    assert not p['leftArmTracked'] and p['rightArmTracked']


def test_nonfinite_depth_response_is_rejected():
    xy,s,z,ds=body(); ds[9]=float('nan')
    p=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    assert not p['leftArmTracked'] and p['rightArmTracked']


def test_calibrated_packets_keep_bone_lengths_after_filtering():
    r=BodyRetarget(); xy,s,z,ds=body()
    r.calibration.value={'scale':.0018,'shoulder_pixels':200.,'left':[.3,.25],'right':[.3,.25]}
    for i in range(20):
        z[9]=-.15-i*.004
        p=r.update(packet(),xy,s,z,ds,now=i/30)
        assert p['leftArmTracked']
        elbow=np.array(list(p['leftElbow'].values()))*.36
        wrist=np.array(list(p['leftWrist'].values()))*.36
        np.testing.assert_allclose([np.linalg.norm(elbow),np.linalg.norm(wrist-elbow)],[.3,.25],atol=1e-7)


def test_calibrated_foreshortened_forearm_survives_old_minimum_length_gate():
    r=BodyRetarget(); xy,s,z,ds=body()
    r.calibration.value={'scale':.0018,'shoulder_pixels':200.,'left':[.3,.25],'right':[.3,.25]}
    xy[9]=xy[7]+[0,10]; z[9]=z[7]
    p=r.update(packet(),xy,s,z,ds,now=0)
    assert p['leftArmTracked']
    assert p['leftWrist']['z']-p['leftElbow']['z']>.6


def test_short_calibration_falls_back_without_disabling_visible_arms():
    r=BodyRetarget(); xy,s,z,ds=body()
    r.calibration.value={'scale':.0018,'shoulder_pixels':200.,'left':[.12,.12],'right':[.12,.12]}
    p=r.update(packet(),xy,s,z,ds,now=0)
    assert p['leftArmTracked'] and p['rightArmTracked']
    assert r.diagnostics['left_mode']=='model'
    assert r.diagnostics['left_fallback']=='calibration_inconsistent'
    # Repeated contradiction must disable the profile, not alternate forever.
    for i in range(1,40):
        p=r.update(packet(),xy,s,z,ds,now=i/30)
        assert p['leftArmTracked'] and p['rightArmTracked']
    assert r.calibration.value is None
    assert r.calibration.rejection['reason']=='projection_exceeds_calibrated_length'


def test_calibration_no_longer_changes_torso_scale():
    xy,s,z,ds=body(); z[5]=.1; z[6]=-.1
    baseline=BodyRetarget().update(packet(),xy,s,z,ds,now=0)
    r=BodyRetarget()
    r.calibration.value={'scale':.002,'shoulder_pixels':180.,'left':[.3,.25],'right':[.3,.25]}
    calibrated=r.update(packet(),xy,s,z,ds,now=0)
    assert calibrated['torsoYaw']==pytest.approx(baseline['torsoYaw'])


def test_short_loss_hold_expires_and_does_not_refresh_itself():
    r=BodyRetarget(); xy,s,z,ds=body()
    initial=r.update(packet(),xy,s,z,ds,now=0)
    s[9]=0
    for now in [.03,.07,.11]:
        p=r.update(packet(),xy,s,z,ds,now=now)
        assert p['leftArmHeld'] and p['leftWrist']==initial['leftWrist']
    p=r.update(packet(),xy,s,z,ds,now=.13)
    assert not p['leftArmTracked'] and not p['leftArmHeld']
    p=r.update(packet(),None,None,None,None,now=.14)
    assert not p['tracked'] and not r.held


def test_side_view_crossed_shoulders_keep_elbow_yaw():
    r=BodyRetarget(); xy,s,z,ds=body()
    xy[[5,6,7,8,9,10,11,12],0]=400-xy[[5,6,7,8,9,10,11,12],0]
    z[5]=-.15; z[6]=.15
    z[7]=-.2;z[8]=.2
    p=r.update(packet(),xy,s,z,ds,now=0)
    assert p['torsoTracked'] and abs(p['torsoYaw'])>40


def test_automatic_lengths_survive_person_absence():
    r=BodyRetarget(); xy,s,z,ds=body()
    for i in range(12): r.update(packet(),xy,s,z,ds,now=i*.05)
    lengths=r.automatic_lengths()
    assert lengths['left'][0]>0
    r.update(packet(),None,None,None,None,now=1)
    assert r.automatic_lengths()==lengths


def test_wrist_motion_cannot_change_yaw_and_missing_elbow_holds_it():
    xy,s,z,ds=body();tracker=BodyRetarget(3,1)
    z[7]=-.2;z[8]=.1
    for i in range(5):p=tracker.update(packet(),xy,s,z,ds,now=i*.05)
    yaw=p['torsoYaw']
    xy[[9,10]]+=[[50,-100],[-50,100]];z[[9,10]]=[.5,-.5]
    for i in range(5,10):p=tracker.update(packet(),xy,s,z,ds,now=i*.05)
    assert p['torsoYaw']==pytest.approx(yaw)
    s[7]=0;z[8]=-.6
    for i in range(10,15):p=tracker.update(packet(),xy,s,z,ds,now=i*.05)
    assert p['torsoYaw']==pytest.approx(yaw)
    assert tracker.diagnostics['torso_yaw_source']=='held_missing_elbows'
