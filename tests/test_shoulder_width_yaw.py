import numpy as np
import pytest
from tanakacap.torso_yaw import shoulder_yaw_magnitude
from tanakacap.body3d import BodyRetarget
from test_body3d import body,packet


def test_width_angle_distance_and_roll_invariance():
    xy,_,_,_=body()
    for angle in (0,20,45,70):
        projected=.36*np.cos(np.radians(angle))/.002
        xy[5]=[400,200];xy[6]=[400-projected,200]
        value,_=shoulder_yaw_magnitude(xy,.002,.2)
        assert value==pytest.approx(angle,abs=1e-5)
        assert shoulder_yaw_magnitude(xy*.6,.002/.6,-.3)[0]==pytest.approx(value,abs=1e-5)
        a=.4;rotation=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
        assert shoulder_yaw_magnitude(xy@rotation,.002,0)[0]==pytest.approx(value,abs=1e-5)


def test_elbow_depth_magnitude_cannot_increase_shoulder_rotation():
    xy,s,z,ds=body();z[5]=-.1;z[6]=.1
    for delta in (.03,.1,.5):
        z[7]=-delta;z[8]=0
        tracker=BodyRetarget()
        p=tracker.update(packet(),xy,s,z,ds,now=0)
        assert p['torsoYaw']==pytest.approx(np.degrees(np.arcsin(.2/.36)))
    # Direction holds on small ambiguous differences, while width still sets amount.
    z[7]=.001
    for i in range(1,10):p=tracker.update(packet(),xy,s,z,ds,now=i*.04)
    assert p['torsoYaw']>0
