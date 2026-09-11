import numpy as np
import pytest
from capture_lab.face_distance import FaceDistance
from test_face_scale import add_face
from test_body3d import body


def test_distance_approach_retreat_ignores_jaw_roll_and_holds_on_loss():
    xy,s,_,_=body();add_face(xy,s)
    model=FaceDistance(3,1)
    p=dict(faceTracked=True,headYaw=0.,headPitch=0.)
    for i in range(20):model.update(xy,s,p,i*.06)
    assert p['faceDistanceTracked'] and p['faceDistanceRatio']==pytest.approx(1)
    for i in range(20,30):model.update(xy*1.25+30,s,p,i*.06)
    assert p['faceDistanceRatio']==pytest.approx(.8)
    changed=xy.copy();changed[23:40]+=50
    r=np.array([[np.cos(.2),-np.sin(.2)],[np.sin(.2),np.cos(.2)]])
    for i in range(30,40):model.update(changed@np.diag([.8,1.])@r*.8,s,p,i*.06)
    assert p['faceDistanceRatio']==pytest.approx(1.25)
    p['headYaw']=40
    model.update(xy,s,p,2.5)
    assert not p['faceDistanceTracked']
    p['headYaw']=0;s[23:91]=0
    model.update(xy,s,p,2.6)
    assert not p['faceDistanceTracked']


def test_reference_not_initialized_while_turned_and_no_old_distance_clamp():
    xy,s,_,_=body();add_face(xy,s)
    model=FaceDistance(3,1);p=dict(faceTracked=True,headYaw=20.,headPitch=0.)
    for i in range(20):model.update(xy,s,p,i*.06)
    assert model.scale.reference is None and not p['faceDistanceTracked']
    p['headYaw']=0
    for i in range(20,40):model.update(xy,s,p,i*.06)
    for i in range(40,60):model.update(xy*2,s,p,i*.06)
    assert p['faceDistanceRatio']==pytest.approx(.5)
    for i in range(60,80):model.update(xy*.5,s,p,i*.06)
    assert p['faceDistanceRatio']==pytest.approx(2.)
