import numpy as np
from capture_lab.retarget import FaceFilter
from capture_lab.body_geometry import DepthAssist,visible_in_front_of_torso
from capture_lab.motion_gate import DirectionGate,RotationGate


def face(value):
    return dict(faceTracked=True,headPitch=value*20,headYaw=value*40,headRoll=value*10,
                mouth=value,leftBlink=value,rightBlink=value)


def test_head_and_every_expression_confirm_then_follow_without_extra_python_smoothing():
    f=FaceFilter(); f.update(face(0),0)
    p=f.update(face(1),.05)
    assert p['headYaw']==0 and p['mouth']==0 and p['leftBlink']==0 and p['rightBlink']==0
    p=f.update(face(1),.10)
    assert p['headYaw']==40 and p['mouth']==1 and p['leftBlink']==1 and p['rightBlink']==1
    p=f.update(face(.9),.15)
    assert p['mouth']==1
    p=f.update(face(1),.20)
    assert p['mouth']==1


def test_face_loss_does_not_carry_a_pending_direction_to_next_person():
    f=FaceFilter(); f.update(face(0),0); f.update(face(1),.05)
    f.update({'faceTracked':False},.1)
    assert f.update(face(.5),.15)['mouth']==.5


def test_large_arm_changes_also_need_two_observations():
    gate=DirectionGate(.006,float('inf')); gate.update([0.],0)
    assert gate.update([1.],.05)[0]==0
    assert gate.update([1.],.10)[0]==1


def test_front_wrist_does_not_reflect_observed_backward_upper_arm():
    assist=DepthAssist()
    for i in range(30): assist.update(np.array([.25,0,0]),np.array([.24,0,0]),i*.05)
    a=np.array([.10,0,-.04]); b=np.array([.24,0,-.05])
    bones,mode=assist.update(a,b,1.5,front_visible=True)
    assert bones[0,2]<=0 and mode!='front_prior'
    bones,mode=assist.update(a,b,1.55,front_visible=True)
    assert bones[0,2]<0 and bones[:,2].sum()>=.015-1e-8
    assert not assist.upper_forward
    np.testing.assert_allclose(bones[0,:2],a[:2])
    np.testing.assert_allclose(np.linalg.norm(bones[1]),np.linalg.norm(b))


def test_overlap_requires_visible_hand_and_torso_region():
    xy=np.zeros((133,2)); s=np.ones(133)
    xy[[5,6,11,12]]=[[400,100],[200,100],[380,350],[220,350]]
    xy[[9,91,96,100,108]]=[[320,200],[320,200],[320,220],[320,230],[330,220]]
    assert visible_in_front_of_torso(xy,s,'left')
    s[96]=.1
    assert not visible_in_front_of_torso(xy,s,'left')
    s[96]=1; xy[9,0]=600
    assert not visible_in_front_of_torso(xy,s,'left')


def test_turned_body_uses_uncompressed_width_and_wrist_agreement():
    xy=np.zeros((133,2));s=np.ones(133)
    xy[[5,6,11,12]]=[[340,100],[260,100],[340,350],[260,350]]
    xy[[9,91,100]]=[[440,180],[440,180],[440,200]]
    assert not visible_in_front_of_torso(xy,s,'left')
    assert not visible_in_front_of_torso(xy,s,'left',nominal_width=200)
    xy[91]=[250,200]
    assert not visible_in_front_of_torso(xy,s,'left',nominal_width=200)


def test_front_length_fit_preserves_lengths_and_allows_forearm_foldback():
    assist=DepthAssist()
    for i in range(10): assist.update(np.array([.3,0,0]),np.array([.25,0,0]),i*.05)
    for now in (.5,.55):
        bones,mode=assist.update(np.array([.1,0,.04]),np.array([.15,0,-.12]),now,True)
    assert mode=='front_length_fit'
    np.testing.assert_allclose(np.linalg.norm(bones,axis=1),[.3,.25])
    assert bones[0,2]>0 and bones[1,2]<0 and bones[:,2].sum()>0
    np.testing.assert_allclose(bones[:,:2],[[.1,0],[.15,0]])
    assist.update(bones[0],bones[1],.65,False)
    assert assist.front_active
    assist.update(bones[0],bones[1],.8,False)
    assert not assist.front_active


def test_front_length_fit_straight_toward_camera_does_not_stay_flat():
    assist=DepthAssist()
    for i in range(10): assist.update(np.array([.3,0,0]),np.array([.25,0,0]),i*.05)
    for now in (.5,.55):
        bones,_=assist.update(np.array([.01,0,0]),np.array([.01,0,.01]),now,True)
    assert bones[:,2].sum()>.5
