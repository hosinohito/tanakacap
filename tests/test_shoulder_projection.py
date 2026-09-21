import numpy as np
from tanakacap.shoulder_projection import ShoulderProjection

IDS=np.array([27,28,29,30,36,39,42,45])+23

def scene():
    xy=np.zeros((133,2));scores=np.ones(133)
    xy[5]=[250,350];xy[6]=[550,350]
    face=np.array([[-12,-20],[-4,-10],[4,0],[12,10],[-30,-5],[-15,-5],[15,-5],[30,-5]],float)
    face-=face.mean(axis=0);xy[IDS]=face+[400,150]
    return xy,scores,dict(reference=face.tolist(),relative_size=1.)

def feed(c,xy,s,d,t,guard=True,**kw):
    packet=dict(faceTracked=True,headPitch=0.,headYaw=0.);packet.update(kw)
    return c.update(xy,s,d,True,packet,t,guard)

def ready():
    c=ShoulderProjection();xy,s,d=scene()
    for i in range(12):feed(c,xy,s,d,i/30)
    assert c.reference is not None
    return c,xy,s,d

def test_uniform_distance_change_preserves_yaw_and_ratio():
    c,xy,s,d=ready()
    xy*=1.6;d['relative_size']=1.6
    assert feed(c,xy,s,d,.5)==0
    assert abs(c.details['gap_ratio']-1)<1e-12

def test_face_approach_is_corrected_instead_of_making_yaw():
    c,xy,s,d=ready();width=c.width
    center=xy[IDS].mean(0);xy[IDS]=(xy[IDS]-center)*1.5+center+[0,35]
    d['relative_size']=1.5
    assert feed(c,xy,s,d,.5)==0
    assert c.details['status']=='width_observed'
    assert c.details['correction_factor']>1
    assert c.width==width

def test_actual_shoulder_shortening_can_make_yaw_without_depth():
    c,xy,s,d=ready();xy[[5,6],0]=[280,520]
    assert feed(c,xy,s,d,.5)>25
    assert c.details['status']=='width_observed'

def test_reference_never_shortens_and_one_wide_outlier_does_not_raise_it():
    c,xy,s,d=ready();width=c.width
    xy[[5,6],0]=[280,520]
    for i in range(20):feed(c,xy,s,d,.5+i/30)
    assert c.width==width
    xy[[5,6],0]=[220,580];feed(c,xy,s,d,1.2)
    assert c.width==width

def test_ten_supported_wider_observations_can_raise_reference():
    c,xy,s,d=ready();width=c.width;xy[[5,6],0]=[240,560]
    for i in range(9):feed(c,xy,s,d,.5+i/30)
    assert c.width==width
    feed(c,xy,s,d,.8)
    assert c.width>width

def test_roll_does_not_change_gap_or_width():
    c,xy,s,d=ready();a=.4;rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
    xy=xy@rot.T
    assert feed(c,xy,s,d,.5)==0
    assert abs(c.details['gap_ratio']-1)<1e-12

def test_missing_geometry_holds_last_angle():
    c,xy,s,d=ready();xy[[5,6],0]=[280,520];angle=feed(c,xy,s,d,.5)
    s[IDS]=0
    assert feed(c,xy,s,d,.6)==angle

def test_guard_is_reversible_and_does_not_change_reference_rules():
    a,xy,s,d=ready();b,_,_,_=ready();d['relative_size']=1.5
    assert feed(a,xy,s,d,.5,True)==0
    assert feed(b,xy,s,d,.5,False)>30
    assert a.width==b.width


def test_ten_percent_face_growth_no_longer_leaks_yaw():
    c,xy,s,d=ready();width=c.width
    center=xy[IDS].mean(0);xy[IDS]=(xy[IDS]-center)*1.1+center
    d['relative_size']=1.1
    for i in range(30):assert feed(c,xy,s,d,.4+i/30)==0
    assert c.width==width
    assert np.isclose(c.details['width_ratio'],1)


def test_approach_and_real_turn_keep_residual_yaw_and_recover():
    a,xy,s,d=ready();b,_,_,_=ready()
    xy[[5,6],0]=[280,520]
    expected=feed(a,xy,s,d,.4)
    center=xy[IDS].mean(0)
    # Grow the face while preserving the projected face/shoulder center gap.
    for i in range(60):
        size=1+.5*np.sin(np.pi*i/59)
        sample=xy.copy();sample[IDS]=(xy[IDS]-center)*size+center
        actual=feed(b,sample,s,dict(d,relative_size=size),.4+i/30)
        assert np.isclose(actual,expected)


def test_uncertain_geometry_holds_then_resumes():
    c,xy,s,d=ready();xy[[5,6],0]=[280,520]
    expected=feed(c,xy,s,d,.4)
    frontal=xy.copy();frontal[[5,6],0]=[250,550]
    for i,kwargs in enumerate([dict(headPitch=20),dict(headYaw=30)]):
        assert feed(c,frontal,s,d,.5+i/30,**kwargs)==expected
        assert c.details['status']=='held_projection_ambiguous'
    assert feed(c,frontal,s,dict(d,residual=.1),.6)==expected
    assert c.details['status']=='held_projection_ambiguous'
    assert feed(c,frontal,s,d,.7)==0


def test_extreme_gap_and_lateral_displacement_hold():
    for displacement in ([0,130],[100,0]):
        c,xy,s,d=ready();xy[[5,6],0]=[280,520]
        expected=feed(c,xy,s,d,.4)
        xy[IDS]+=displacement
        assert feed(c,xy,s,d,.5)==expected
        assert c.details['status']=='held_projection_ambiguous'


def test_frontal_response_is_continuous_monotone_and_less_sensitive():
    c,xy,s,d=ready();b,_,_,_=ready();angles=[]
    for ratio in np.linspace(1,.75,101):
        xy[[5,6],0]=[400-150*ratio,400+150*ratio]
        angle=feed(c,xy,s,d,.4)
        old=feed(b,xy,s,d,.4,guard=False)
        assert 0<=angle<=old+1e-9
        angles.append(angle)
    assert np.all(np.diff(angles)>=-1e-9)
    assert max(np.diff(angles))<2
    assert angles[-1]>35


def test_gap_only_shrink_does_not_create_yaw_from_frontal():
    c,xy,s,d=ready();xy[IDS]+=[0,30]
    assert feed(c,xy,s,d,.4)==0


def test_gap_growth_must_not_be_inverted_into_artificial_yaw():
    c,xy,s,d=ready()
    xy[IDS]+=[0,-20]
    assert feed(c,xy,s,d,.4)==0
    assert c.details['correction_factor']==1
    xy[IDS]+=[0,-20]
    assert feed(c,xy,s,d,.5)==0
    assert c.details['status']=='held_projection_ambiguous'
