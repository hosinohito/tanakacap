from tanakacap.body3d import BodyRetarget
from test_body3d import body,packet


def test_crossing_constraint_is_zero_immediately_when_observed_outside():
    xy,s,z,ds=body();tracker=BodyRetarget(3,1)
    # Explicitly reproduce a held sub-deadband nonzero crossing amount.
    tracker.cross_motion['left'].update([.01],0)
    xy[9,0]=xy[5,0]+40
    for i in range(1,15):
        p=tracker.update(packet(),xy,s,z,ds,now=i*.03)
        if p['leftArmTracked']:
            assert p['leftCrossBody']==0


def test_frontal_reference_can_recover_from_initial_width_error_using_face_scale():
    from tanakacap.torso_yaw import ShoulderWidthReference
    reference=ShoulderWidthReference();reference.width=.36
    assert reference.update(150,.002,0)>20
    for i in range(10):reference.observe_frontal(150,.002,.01,True,i*.04)
    assert reference.update(150,.002,.5)==0
    assert reference.update(100,.003,.6)==0
    for i in range(10):assert not reference.observe_frontal(100,.002,.15,True,1+i*.04)
    assert reference.width==.3
