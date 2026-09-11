import numpy as np
import pytest
from capture_lab.face_distance import FaceDistance
from test_face_scale import add_face
from test_body3d import body


def test_distance_approach_retreat_ignores_jaw_roll_and_holds_on_loss():
    xy,s,_,_=body();add_face(xy,s)
    model=FaceDistance(3,1,mode="legacy")
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
    model=FaceDistance(3,1,mode="legacy");p=dict(faceTracked=True,headYaw=20.,headPitch=0.)
    for i in range(20):model.update(xy,s,p,i*.06)
    assert model.scale.reference is None and not p['faceDistanceTracked']
    p['headYaw']=0
    for i in range(20,40):model.update(xy,s,p,i*.06)
    for i in range(40,60):model.update(xy*2,s,p,i*.06)
    assert p['faceDistanceRatio']==pytest.approx(.5)
    for i in range(60,80):model.update(xy*.5,s,p,i*.06)
    assert p['faceDistanceRatio']==pytest.approx(2.)


@pytest.mark.parametrize('base',[.5,1.,2.])
def test_stable_distance_rejects_small_relative_noise(base):
    model=FaceDistance(3,1)
    model.scale.reference=1
    packet=dict(faceTracked=True,headYaw=0.,headPitch=0.)
    values=[]
    for i in range(120):
        ratio=base*np.exp(.006*np.sin(i*.8))
        model.scale.update=lambda *args,r=ratio:r
        model.update(None,None,packet,i/30)
        if packet['faceDistanceTracked']:values.append(packet['faceDistanceRatio'])
    assert np.ptp(values)<base*.002


def test_stable_distance_tracks_approach_and_retreat_and_loss_does_not_snap():
    model=FaceDistance(3,1);model.scale.reference=1
    packet=dict(faceTracked=True,headYaw=0.,headPitch=0.)
    now=0.
    for target in (1.,.6,1.4):
        model.scale.update=lambda *args:target
        for _ in range(45):
            model.update(None,None,packet,now);now+=1/30
        assert packet['faceDistanceRatio']==pytest.approx(target,abs=.002)
    before=model.filtered
    model.scale.update=lambda *args:None
    for _ in range(30):model.update(None,None,packet,now);now+=1/30
    assert model.filtered==before and not packet['faceDistanceTracked']
    model.scale.update=lambda *args:.7
    for _ in range(3):model.update(None,None,packet,now);now+=1/30
    assert .7<packet['faceDistanceRatio']<1.4


def test_stable_distance_large_step_response_within_300ms():
    model=FaceDistance(3,1);model.scale.reference=1
    packet=dict(faceTracked=True,headYaw=0.,headPitch=0.)
    for i in range(40):
        model.scale.update=lambda *args:1. if i<30 else .75
        model.update(None,None,packet,i/30)
    assert abs(packet['faceDistanceRatio']-.75)<.025
