"""Asymmetric hand observations must retain independent filter histories."""
import numpy as np
import pytest
from tanakacap.fingers import FingerTracker
from tanakacap.hand_orientation import PalmFilter, add_hands
from test_fingers import hand

@pytest.mark.parametrize('moving,offset,still', [('left',91,'right'),('right',112,'left')])
def test_hand_side_isolation(moving,offset,still):
    palms=PalmFilter(3,1); fingers=FingerTracker(3,1)
    for i in range(45):
        xyz,scores=hand(False)
        if i>=12:
            closed,_=hand(True); xyz[offset:offset+21]=closed[offset:offset+21]
            a=np.radians(min(80,(i-12)*4));c,s=np.cos(a),np.sin(a)
            xyz[offset:offset+21]=xyz[offset:offset+21]@np.array([[c,0,s],[0,1,0],[-s,0,c]]).T
        p=dict(leftArmTracked=True,rightArmTracked=True)
        add_hands(p,xyz,scores,scores);palms.update(p,i/30)
        fingers.update(p,xyz,scores,scores,i/30)
        if i==11:initial=p
        if i>=12:
            for suffix in ('HandNormal','HandForward','FingerTracked','FingerFlex'):
                assert p[still+suffix]==initial[still+suffix]
    assert all(p[moving+'FingerTracked'])
    assert max(p[moving+'FingerFlex'])>20
    assert p[moving+'HandNormal']!=initial[moving+'HandNormal']
    assert palms.motion['left'] is not palms.motion['right']
    for f in range(5): assert fingers.gates['left',f] is not fingers.gates['right',f]
