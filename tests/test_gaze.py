import numpy as np
from capture_lab.gaze import eye_crop, iris_offset, contour_offset
from capture_lab.gaze import IrisGaze
from capture_lab.motion_gate import DirectionGate
import json


def iris(x=32,y=32):
    return np.array([[x,y,0],[x+4,y,0],[x,y+4,0],[x-4,y,0],[x,y-4,0]])


def test_iris_sign_and_mirror():
    assert np.allclose(iris_offset(iris(),False),[0,0])
    a=iris_offset(iris(36,34),False)
    b=iris_offset(iris(28,34),True)
    assert np.allclose(a,b) and np.all(a>0)


def test_invalid_iris_rejected():
    assert iris_offset(iris(60),False) is None
    assert iris_offset(np.full((5,3),np.nan),False) is None
    assert iris_offset(np.zeros((5,3)),False) is None


def test_closed_outside_low_detail_eyes_rejected():
    image=np.full((100,100,3),127,np.uint8)
    eye=np.array([[30,50],[35,45],[45,45],[50,50],[45,55],[35,55]])
    assert eye_crop(image,eye,False) is None
    image[45:55,36:44]=0
    assert eye_crop(image,eye,False).shape==(1,3,64,64)
    eye[:,1]=50
    assert eye_crop(image,eye,False) is None
    eye[:,0]-=40
    assert eye_crop(image,eye,False) is None


def test_invalid_model_output_diagnostics_remain_json_safe():
    class Session:
        def run(self,*args): return [np.full((1,15),np.nan),np.full((1,213),np.nan)]
    model=IrisGaze.__new__(IrisGaze)
    model.session=Session();model.calls=0;model.gate=DirectionGate(.35,float('inf'),3,1)
    image=np.random.default_rng(3).integers(0,255,(130,130,3),dtype=np.uint8)
    points=np.zeros((133,2));eye=np.array([[30,60],[35,55],[45,55],[50,60],[45,65],[35,65]])
    points[59:65]=eye;points[65:71]=eye+[45,0]
    packet=dict(faceTracked=True,headYaw=0,headPitch=0,rightBlink=0,leftBlink=0)
    result=model.update(image,points,np.ones(133),packet,0)
    assert model.calls==2 and not packet['gazeTracked']
    assert result['eyes']['left']['offset'] is None
    json.dumps(result,allow_nan=False)


def test_contour_reference_cancels_crop_translation_scale_and_roll():
    c=np.zeros((71,3));c[0,:2]=[18,32];c[8,:2]=[46,32]
    p=iris(35,33)
    expected=contour_offset(p,c,False)
    angle=.2;r=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    transformed=[]
    for value in (p,c):
        v=value.astype(float);v[:,:2]=(v[:,:2]-32)@r.T*1.1+[36,30];transformed.append(v)
    np.testing.assert_allclose(contour_offset(*transformed,False),expected,atol=1e-8)
    for v in transformed:v[:,0]=64-v[:,0]
    np.testing.assert_allclose(contour_offset(*transformed,True),expected,atol=1e-8)
    c[8]=c[0]
    assert contour_offset(p,c,False) is None


def test_official_image_side_flip_and_legacy_rollback():
    class Session:
        def run(self,*args):
            c=np.zeros((71,3));c[0,:2]=[18,32];c[8,:2]=[46,32]
            return [iris(35).reshape(1,15),c.reshape(1,213)]
    image=np.random.default_rng(4).integers(0,255,(130,130,3),dtype=np.uint8)
    points=np.zeros((133,2));eye=np.array([[30,60],[35,55],[45,55],[50,60],[45,65],[35,65]])
    points[59:65]=eye;points[65:71]=eye+[45,0]
    for reference in ('contour','legacy'):
        m=IrisGaze.__new__(IrisGaze);m.reference=reference;m.session=Session();m.calls=0
        m.gate=DirectionGate(.35,float('inf'),3,1)
        p=dict(faceTracked=True,headYaw=0,headPitch=0,rightBlink=0,leftBlink=0)
        d=m.update(image,points,np.ones(133),p,0)
        assert d['eyes']['right']['flipped']==(reference=='legacy')
        assert d['eyes']['left']['flipped']==(reference!='legacy')
