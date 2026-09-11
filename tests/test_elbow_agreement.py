import numpy as np
import pytest
from capture_lab.torso_yaw import elbow_agreement
from capture_lab.body3d import BodyRetarget
from test_body3d import body,packet


def test_disagreement_is_distance_invariant_and_never_reads_wrists():
    xy,s,_,_=body();ref=xy.copy()
    ref[[9,10]]+=1000
    assert elbow_agreement(xy,s,ref,s)[0]
    ref[7,1]+=80
    for scale in (1.,.6):
        ok,d=elbow_agreement(xy*scale,s,ref*scale,s)
        assert not ok and d['status']=='disagreement'
        assert d['upper_arm_error_over_shoulder_span'][0]==pytest.approx(.4)


def test_hold_only_yaw_on_disagreement_and_resume_when_consistent():
    xy,s,z,ds=body();z[5]=-.1;z[6]=.1;ref=xy.copy();tracker=BodyRetarget(3,1)
    for i in range(30):p=tracker.update(packet(),xy,s,z,ds,now=i*.04,reference_xy=ref,reference_scores=s)
    yaw=p['torsoYaw']
    xy[7,1]+=80;xy[5,1]+=15;z[7]=.15
    for i in range(30,60):p=tracker.update(packet(),xy,s,z,ds,now=i*.04,reference_xy=ref,reference_scores=s)
    assert p['torsoTracked'] and p['leftArmTracked'] and p['rightArmTracked']
    assert p['torsoYaw']==pytest.approx(yaw)
    assert abs(p['torsoRoll'])>1
    assert tracker.diagnostics['torso_yaw_source']=='held_elbow_disagreement'
    for i in range(60,90):p=tracker.update(packet(),xy,s,z,ds,now=i*.04,reference_xy=xy,reference_scores=s)
    assert p['torsoYaw']<0
    assert tracker.diagnostics['torso_yaw_source']=='shoulder_width_elbow_sign'


def test_missing_secondary_is_not_fabricated_agreement():
    xy,s,_,_=body();low=s.copy();low[7]=0
    assert not elbow_agreement(xy,s,xy,low)[0]
    xy[7]=np.nan
    assert not elbow_agreement(xy,s,xy,s)[0]
