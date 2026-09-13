import cv2
import numpy as np
import pytest
from tanakacap.head_pose import TEMPLATE, camera_matrix
from tanakacap.head_pose3d import fit_face3d, HeadPose3D
from tanakacap.mouth_detail import contour_controls


def observed(pitch=0, yaw=0, roll=0, distance=.7, expression=0, root_offset=0):
    r = cv2.Rodrigues(np.array([0.,0.,np.radians(roll)]))[0] @ cv2.Rodrigues(np.array([0.,np.radians(yaw),0.]))[0] @ cv2.Rodrigues(np.array([np.radians(pitch),0.,0.]))[0]
    p = np.zeros((133,2)); z = np.zeros(133)
    for i, v in TEMPLATE.items():
        v=v.copy()
        if i==54: v[1]-=expression
        q=r@v+np.array([.08,-.04,distance])
        p[23+i]=(camera_matrix((1280,720))@q)[:2]/q[2]
        z[23+i]=q[2]-distance+root_offset
    return p, np.ones(133), z, np.ones(133)


@pytest.mark.parametrize('pitch',[-30,0,30])
@pytest.mark.parametrize('distance',[.4,1.2])
def test_learned_depth_removes_pose_but_preserves_asymmetric_lips(pitch,distance):
    p,s,z,zs=observed(pitch,20,10,distance,.003,2.3)
    fit=fit_face3d(p,s,z,zs,(1280,720))
    assert fit is not None
    assert fit[0][0]==pytest.approx(pitch,abs=1e-5)
    actual=contour_controls(fit[1],fit[2])
    p,s,z,zs=observed(expression=.003)
    neutral=fit_face3d(p,s,z,zs,(1280,720))
    expected=contour_controls(neutral[1],neutral[2])
    for key in expected: assert actual[key]==pytest.approx(expected[key],abs=1e-5)


def test_loss_holds_pitch_and_does_not_fall_back_to_pnp():
    model=HeadPose3D();packet=dict(faceTracked=True,headYaw=0,headRoll=0)
    p,s,z,zs=observed()
    for _ in range(10): model.update(p,s,packet,(1280,720),z,zs)
    p,s,z,zs=observed(20)
    model.update(p,s,packet,(1280,720),z,zs)
    assert packet['headPitch']==pytest.approx(36,abs=1e-5)
    model.update(p,s,packet,(1280,720))
    assert packet['headPitch']==pytest.approx(36,abs=1e-5)
    assert not packet['mouthContourTracked']


def test_missing_lip_depth_holds_expression_without_losing_head():
    p,s,z,zs=observed(10);zs[23+54]=0
    model=HeadPose3D();packet=dict(faceTracked=True)
    model.update(p,s,packet,(1280,720),z,zs)
    assert model.diagnostics['tracked'] and not packet['mouthContourTracked']


def test_mixed_mode_preserves_pnp_pitch_and_depth_lips_independently():
    from tanakacap.head_pose import HeadPose
    from tanakacap.head_pose3d import PnPPitchDepthMouth
    models=[HeadPose(),HeadPose3D(),PnPPitchDepthMouth()]
    for pitch in [0]*10+[20,-20,10]:
        p,s,z,zs=observed(pitch,expression=.003)
        packets=[dict(faceTracked=True,headYaw=0,headRoll=0) for _ in models]
        models[0].update(p,s,packets[0],(1280,720))
        for model,packet in zip(models[1:],packets[1:]): model.update(p,s,packet,(1280,720),z,zs)
        assert packets[2]['headPitch']==pytest.approx(packets[0]['headPitch'])
        for key in ('mouthLeftCorner','mouthRightCorner','mouthShift','mouthContourTracked'):
            assert packets[2][key]==packets[1][key]
    models[2].update(p,s,packets[2],(1280,720))
    assert packets[2]['headPitch']==pytest.approx(packets[0]['headPitch'])
    assert not packets[2]['mouthContourTracked']
