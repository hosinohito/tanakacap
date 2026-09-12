import numpy as np
import pytest
from tools.sam_body_adapter import adapt,projection_error,BODY_MAP,LEFT_MAP,RIGHT_MAP
from capture_lab.body3d import BodyRetarget


def prediction():
    xyz=np.zeros((70,3));xyz[:,0]=np.linspace(-.2,.2,70);xyz[:,1]=np.linspace(-.1,.1,70)
    xyz[5:9]=[[.18,0,0],[-.18,0,0],[.3,.2,-.15],[-.3,.2,.1]]
    xyz[62]=[.2,.1,-.3];xyz[41]=[-.2,.1,-.2]
    camera=xyz+[0,0,2]
    return {'pred_keypoints_3d':xyz,'pred_keypoints_2d':camera[:,:2]/camera[:,2:]*1000+[640,360],'pred_cam_t':[0,0,2],'focal_length':1000}


def common():
    return {'body_xy':np.tile([640.,360.],(133,1)),'body_scores':np.full(133,.73),'body_depth':np.zeros(133),'body_depth_scores':np.full(133,.017)}


def test_mhr70_wrist_finger_and_hip_order():
    assert BODY_MAP[9:13].tolist()==[62,41,9,10]
    assert LEFT_MAP[:5].tolist()==[62,45,44,43,42]
    assert RIGHT_MAP[:5].tolist()==[41,24,23,22,21]
    assert len(set(LEFT_MAP)&set(RIGHT_MAP))==0
    assert LEFT_MAP[-4:].tolist()==[61,60,59,58]


def test_native_xyz_and_shared_confidence_are_not_fabricated():
    c=common();c['body_scores'][7]=.1;p=prediction()
    a,error=adapt(c,p,[1280,720])
    assert error<1e-8
    np.testing.assert_array_equal(a['camera_xyz'][9],p['pred_keypoints_3d'][62])
    assert a['scores'][7]==.1 and a['scores'][8]==.73
    assert a['depth_scores'][9]==.017
    np.testing.assert_array_equal(a['xy'][23:91],c['body_xy'][23:91])
    assert np.isnan(a['camera_xyz'][23:91]).all()


def test_projection_axes_and_bad_projection_rejected():
    p=prediction();assert projection_error(p,[1280,720])<1e-8
    p['pred_keypoints_2d'][7,0]+=2
    with pytest.raises(ValueError,match='projection mismatch'):adapt(common(),p,[1280,720])


def test_missing_sam_and_boundary_evidence_stay_missing():
    c=common();assert adapt(c,None,[1280,720]) is None
    c['body_xy'][9]=[1279,360]
    a,_=adapt(c,prediction(),[1280,720])
    assert a['scores'][9]==0 and (a['scores'][91:112]==0).all()


def test_native_depth_axes_drive_forward_elbow():
    # Use genuinely metric XYZ with an elbow nearer the camera. Screen XY
    # remains for visibility; native Y and Z must not be reconstructed from it.
    c=common();p=prediction();a,_=adapt(c,p,[1280,720]);control=BodyRetarget()
    for i in range(10):
        packet=control.update({'faceTracked':True},**a,now=i/30,image_size=[1280,720])
    assert control.diagnostics['native_metric_geometry']
    assert packet['leftArmTracked']
    assert packet['leftElbow']['z']>0
    assert packet['leftElbow']['y']<0
