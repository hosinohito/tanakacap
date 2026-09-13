import numpy as np
from tanakacap.body_geometry import DepthAssist, visible_in_front_of_torso, visible_hand_inward
from tanakacap.retarget import FaceFilter


def test_outward_hand_and_posterior_elbow_are_not_forced_forward_mirrored():
    for side,sign in [('left',1),('right',-1)]:
        xy=np.zeros((133,2));scores=np.ones(133)
        xy[5]=[360,200];xy[6]=[280,200]
        wrist,offset=(9,91) if side=='left' else (10,112)
        xy[[wrist,offset,offset+9]]=[[320+sign*65,260]]*3
        assert not visible_hand_inward(xy,scores,side)
        assert not visible_in_front_of_torso(xy,scores,side,nominal_width=250)
        assist=DepthAssist()
        a=np.array([sign*.08,-.18,-.18]);b=np.array([sign*.08,.1,.12])
        for i in range(20):bones,_=assist.update(a,b,i*.04,False)
        assert bones[0,2]<0 and not assist.upper_forward


def test_visible_wrist_can_coexist_with_backward_elbow_at_supported_lengths():
    assist=DepthAssist()
    for i in range(10):assist.update(np.array([.25,0,0]),np.array([.3,0,0]),i*.04)
    for t in (.4,.44):
        bones,mode=assist.update(np.array([.15,0,-.2]),np.array([.1,0,.28]),t,True)
    assert mode=='front_length_fit'
    assert bones[0,2]<0 and bones[:,2].sum()>.015
    np.testing.assert_allclose(np.linalg.norm(bones,axis=1),[.25,.3])


def test_outward_foreshortened_forearm_remains_tracked_without_front_prior():
    for sign in (-1,1):
        assist=DepthAssist()
        for i in range(10):assist.update(np.array([.25,0,0]),np.array([.15,0,sign*.01]),i*.04)
        bones,_=assist.update(np.array([.15,-.15,-.1]),np.array([.03,0,sign*.01]),.4,False)
        assert bones[0,2]<0 and np.sign(bones[1,2])==sign
        np.testing.assert_allclose(np.linalg.norm(bones[1]),.15)


def test_natural_bow_is_neutral_but_corner_asymmetry_survives():
    f=FaceFilter()
    def packet(l=.3,r=.2,b=.7):
        return dict(faceTracked=True,mouthContourTracked=True,mouthLeftCorner=l,mouthRightCorner=r,mouthBow=b,
                    mouth=0.,headPitch=0.,headYaw=0.,headRoll=0.,leftBlink=0.,rightBlink=0.)
    for i in range(15):p=f.update(packet(),i*.04)
    assert p['mouthBow']==0 and abs(p['mouthLeftCorner'])<1e-8 and abs(p['mouthRightCorner'])<1e-8
    for i in range(15,20):p=f.update(packet(.1,.4,1.),i*.04)
    assert p['mouthLeftCorner']<0<p['mouthRightCorner']
    assert abs(p['mouthBow']-.3)<1e-8
