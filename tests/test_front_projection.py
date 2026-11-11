import numpy as np
from tanakacap.front_projection import FrontProjection
from tanakacap.body_geometry import lateral_extension_evidence


def test_lateral_prior_preserves_image_geometry_without_shortening_learned_lengths():
    p=np.zeros((133,2));s=np.ones(133)
    p[5]=[400,300];p[6]=[200,300];p[7]=[490,300];p[9]=[570,300]
    assert lateral_extension_evidence(p,s,'left')==1
    solver=FrontProjection();lengths=np.array([.3,.28]);bones=np.array([[.2,0,.15],[.18,0,-.4]])
    for i in range(90):result=solver.solve(bones,lengths,i/30,lateral_evidence=1)
    np.testing.assert_allclose(result[:,:2],bones[:,:2])
    assert np.max(abs(result[:,2]))<1e-6
    np.testing.assert_equal(lengths,[.3,.28])
    # Raising/bending the forearm and an inward reach are not lateral extension.
    p[9]=[490,200];assert lateral_extension_evidence(p,s,'left')==0
    p[9]=[300,300];assert lateral_extension_evidence(p,s,'left')==0
    # Opposite wrist/fingers do not contribute to this side's evidence.
    p[9]=[570,300];p[10]=[9999,9999]
    assert lateral_extension_evidence(p,s,'left')==1
    s[7]=0;assert lateral_extension_evidence(p,s,'left')==0


def test_short_outward_forearm_gets_depth_without_moving_image_points():
    bones=np.array([[.20,-.16,.0],[.01,.13,.006]])
    lengths=np.array([.26,.313])
    result=FrontProjection().solve(bones,lengths,1.)
    np.testing.assert_allclose(result[:,:2],bones[:,:2])
    np.testing.assert_allclose(np.linalg.norm(result,axis=1),lengths,atol=1e-12)
    assert result[1,2]>.27
    assert result[:,2].sum()>=0


def test_real_planar_bent_arm_is_not_forbidden():
    bones=np.array([[.3,0,0],[0,.25,0]])
    result=FrontProjection().solve(bones,[.3,.25],1.)
    np.testing.assert_allclose(result,bones,atol=1e-12)


def test_front_wrist_can_have_posterior_forearm():
    bones=np.array([[.1,-.1,.3],[.15,.1,-.1]])
    result=FrontProjection().solve(bones,np.linalg.norm(bones,axis=1),1.)
    assert result[1,2]<0 and result[:,2].sum()>0


def test_posterior_elbow_with_front_wrist_is_possible():
    bones=np.array([[.20,-.10,-.17],[-.10,.10,.27]])
    result=FrontProjection().solve(bones,np.linalg.norm(bones,axis=1),1.)
    assert result[0,2]<0 and result[:,2].sum()>0


def test_longer_projection_is_never_shortened_to_stale_calibration():
    bones=np.array([[.31,0,0],[0,.32,0]])
    result=FrontProjection().solve(bones,[.3,.3],1.)
    np.testing.assert_allclose(result,bones)


def test_bad_lengths_do_not_invent_a_pose():
    solver=FrontProjection()
    assert solver.solve(np.zeros((2,3)),[0,.3],1.) is None
    assert solver.solve(np.full((2,3),np.nan),[.3,.3],1.) is None


def test_near_zero_z_jitter_does_not_flip_reach():
    solver=FrontProjection()
    for index,z in enumerate([.005,-.005,.008,-.01,.003]):
        result=solver.solve([[.1,-.15,z],[.01,.1,-z]],[.28,.30],index/30)
        assert result[0,2]>0 and result[1,2]>0


def test_lower_bound_calibration_does_not_flatten_observed_forward_reach():
    bones=np.array([[.02,-.21,.005],[-.18,-.12,.185]])
    result=FrontProjection().solve(bones,[.24,.192],1.)
    assert result[1,2]>.18
    np.testing.assert_allclose(result[:,:2],bones[:,:2])
    assert np.linalg.norm(result[1])>=np.linalg.norm(bones[1])-1e-10


def test_supported_full_extension_rejects_spurious_model_depth():
    for sign in (-1,1):
        bones=np.array([[sign*.30,0,.18],[sign*.28,0,-.16]])
        result=FrontProjection().solve(bones,[.30,.28],1.)
        np.testing.assert_allclose(result[:,:2],bones[:,:2])
        np.testing.assert_allclose(result[:,2],0,atol=1e-8)


def test_supported_shortening_uses_length_not_model_z_floor():
    bones=np.array([[.24,0,.28],[.224,0,.27]])
    result=FrontProjection().solve(bones,[.30,.28],1.)
    np.testing.assert_allclose(np.linalg.norm(result,axis=1),[.30,.28],atol=1e-8)
    np.testing.assert_allclose(result[:,:2],bones[:,:2])


def test_depth_branch_change_is_continuous_and_keeps_wrist_in_front():
    solver=FrontProjection();lengths=np.array([.3,.3])
    before=solver.solve([[.2,0,.2],[.23,0,-.19]],lengths,0)
    for i in range(1,25):
        result=solver.solve([[.23,0,.19],[.18,0,.24]],lengths,i/30)
        assert np.max(np.abs(result[:,2]-before[:,2])/lengths)<=4/30+1e-8
        assert result[:,2].sum()>=-1e-8
        before=result
    assert result[1,2]>0
