from capture_lab.body3d import BodyRetarget
from test_body3d import body,packet


def test_old_width_angle_cannot_turn_frontal_depth_shoulders():
    xy,s,z,ds=body();z[5]=z[6]=0
    z[7]=-.1;z[8]=.1  # elbow direction alone must not invent yaw magnitude
    tracker=BodyRetarget();tracker.shoulder_width_reference.width=.4
    tracker.shoulder_width_reference.angle=30
    for i in range(12):p=tracker.update(packet(),xy,s,z,ds,now=i*.04)
    assert p['torsoTracked'] and p['torsoYaw']==0
    assert not tracker.diagnostics['torso_yaw_evidence_consistent']
