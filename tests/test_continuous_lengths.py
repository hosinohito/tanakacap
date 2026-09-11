import numpy as np
from capture_lab.body_geometry import SupportedLengths,DepthAssist,constrain_front_arm


def test_ten_frames_required_and_shorter_values_never_replace_length():
    lengths=SupportedLengths()
    for i in range(9): np.testing.assert_allclose(lengths.update([.3,.25],i*.05),[0,0])
    np.testing.assert_allclose(lengths.update([.3,.25],.45),[.3,.25])
    for i in range(20): lengths.update([.2,.15],6+i*.05)
    np.testing.assert_allclose(lengths.value,[.3,.25])
    for i in range(10): lengths.update([.35,.28],8+i*.05)
    np.testing.assert_allclose(lengths.value,[.35,.28])


def test_support_must_be_inside_five_seconds_and_outlier_not_maximum():
    lengths=SupportedLengths()
    for i in range(10): lengths.update([.3,.2],i*.6)
    np.testing.assert_allclose(lengths.value,[0,0])
    for i in range(10): lengths.update([.25,.2],10+i*.05)
    lengths.update([.49,.49],11)
    np.testing.assert_allclose(lengths.value,[.25,.2])


def test_fully_foreshortened_upper_arm_is_reconstructed_with_front_cue():
    assist=DepthAssist()
    for i in range(10): assist.update(np.array([.3,0,0]),np.array([.25,0,0]),i*.05)
    for now in [.5,.55]:
        bones,mode=assist.update(np.array([.01,0,0]),np.array([.2,0,.03]),now,front_visible=True)
    assert mode=='front_length_fit' and bones[0,2]>.2


def test_excessive_depth_does_not_disable_good_projection():
    assist=DepthAssist()
    for i in range(10): assist.update(np.array([.3,0,.03]),np.array([.25,0,.03]),i*.05)
    for now in [.5,.55]:
        bones,_=assist.update(np.array([.1,0,2]),np.array([.15,0,2]),now,front_visible=True)
    assert (np.linalg.norm(bones,axis=1)<.4).all()


def test_front_wrist_cannot_go_behind_with_backward_forearm():
    bones=np.array([[.1,-.2,.08],[.05,.2,-.3]])
    result=constrain_front_arm(bones,True)
    np.testing.assert_allclose(result[:,:2],bones[:,:2])
    assert result[:,2].sum()>=.015
    # Folding the forearm back is allowed when the hand is still in front.
    bones[:,2]=[.3,-.15]
    np.testing.assert_allclose(constrain_front_arm(bones,True),bones)


def test_front_constraint_also_works_during_length_warmup():
    assist=DepthAssist()
    for t in (0,.033):
        result,mode=assist.update(np.array([.1,-.1,-.1]),np.array([.05,.1,-.2]),t,True)
    assert mode=='front_learning'
    assert result[0,2]==-.1 and result[:,2].sum()>=.015
