import numpy as np
from tanakacap.fingers import FingerTracker


def hand(bent=False):
    xyz=np.zeros((133,3)); s=np.ones(133)
    for offset in (91,112):
        for f,start in enumerate((1,5,9,13,17)):
            base=np.array([(f-2)*.02,.07,0.])
            xyz[offset+start]=base
            for j in range(1,4):
                angle=np.radians(30*j if bent else 0)
                xyz[offset+start+j]=xyz[offset+start+j-1]+np.array([0,np.cos(angle),np.sin(angle)*(-1 if offset==91 else 1)])*.025
    return xyz,s


def test_open_closed_and_rotation_invariant():
    for bent in (False,True):
        xyz,s=hand(bent); p={}; FingerTracker().update(p,xyz,s,s,0)
        assert all(p['leftFingerTracked']) and all(p['rightFingerTracked'])
        expected=np.array([23*80/73,23*110/103,23*90/83]) if bent else np.zeros(3)
        np.testing.assert_allclose(p['leftFingerFlex'],[0]*3+list(expected)*4,atol=.01)
        rotation=np.array([[0,0,1],[1,0,0],[0,1,0]])
        q={}; FingerTracker().update(q,xyz@rotation,s,s,0)
        np.testing.assert_allclose(q['leftFingerFlex'],p['leftFingerFlex'])


def test_two_observations_and_independent_missing_finger():
    tracker=FingerTracker(); xyz,s=hand(); p={}
    tracker.update(p,xyz,s,s,0)
    xyz,s=hand(True); tracker.update(p,xyz,s,s,.033)
    assert p['leftFingerFlex']==[0]*15
    tracker.update(p,xyz,s,s,.066)
    np.testing.assert_allclose(p['leftFingerFlex'],[0]*3+[23*80/73,23*110/103,23*90/83]*4,atol=.01)
    s[99]=0 # left index tip only
    tracker.update(p,xyz,s,s,.099)
    assert p['leftFingerTracked']==[True,False,True,True,True]
    assert all(p['rightFingerTracked'])


def test_thumb_curls_toward_index_without_folding_cmc_or_reverse_extension():
    for sign in (1,-1):
        xyz,s=hand()
        for offset in (91,112):
            for j,deg in enumerate((0,35,70),start=1):
                a=np.radians(deg*sign)
                xyz[offset+1+j]=xyz[offset+j]+np.array([np.sin(a),np.cos(a),0])*.025
        p={};FingerTracker().update(p,xyz,s,s,0)
        expected=[0,30,30] if sign==1 else [0,0,0]
        np.testing.assert_allclose(p['leftFingerFlex'][:3],expected,atol=.01)


def test_extension_and_lateral_noise_are_not_positive_curl():
    xyz,s=hand(True)
    xyz[:,2]*=-1
    p={};FingerTracker().update(p,xyz,s,s,0)
    np.testing.assert_allclose(p['leftFingerFlex'][3:],0)
    np.testing.assert_allclose(p['rightFingerFlex'][3:],0)
    xyz,s=hand()
    for offset in (91,112):
        xyz[offset+6,0]+=.003;xyz[offset+7,0]-=.003
    p={};FingerTracker().update(p,xyz,s,s,0)
    np.testing.assert_allclose(p['leftFingerFlex'][3:],0)


def test_signed_noise_is_averaged_before_positive_curl():
    tracker=FingerTracker(3,1);p={}
    for i in range(20):
        xyz,s=hand()
        for offset in (91,112):
            xyz[offset+6,2]=.002*(-1)**i
        tracker.update(p,xyz,s,s,i*.05)
    assert max(p['leftFingerFlex'][3:6])<1


def test_length_history_rejection_is_removed():
    tracker=FingerTracker();p={}
    for i in range(6):
        xyz,s=hand();tracker.update(p,xyz,s,s,i*.05)
    xyz,s=hand();xyz+=np.array([.1,.1,.1])
    tracker.update(p,xyz,s,s,.3)
    assert all(p['rightFingerTracked'])
    xyz[112+8]+=[0,0,.06]
    tracker.update(p,xyz,s,s,.35)
    assert all(p['rightFingerTracked'])
    xyz,s=hand(True)
    for i in range(8,14):tracker.update(p,xyz,s,s,i*.05)
    assert p['rightFingerTracked'][1] and p['rightFingerFlex'][4]>10


def test_closed_mcp_does_not_flip_longitudinal_axis_on_either_hand():
    for mcp in (80,89,90,91,100):
        xyz,s=hand()
        for offset in (91,112):
            for start in (5,9,13,17):
                for j,deg in enumerate((mcp,mcp+60,mcp+90),1):
                    angle=np.radians(deg)
                    xyz[offset+start+j]=xyz[offset+start+j-1]+.025*np.array([0,np.cos(angle),np.sin(angle)*(-1 if offset==91 else 1)])
        p={};FingerTracker().update(p,xyz,s,s,0)
        for side in ('left','right'):
            assert all(p[side+'FingerTracked'][1:])
            flex=np.array(p[side+'FingerFlex'][3:]).reshape(4,3)
            assert (flex[:,0]>70).all() and (flex[:,1]>50).all()
