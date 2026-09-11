import numpy as np
import pytest
from capture_lab.retarget import packet_from_landmarks,FaceFilter


def face_points(width=80):
    p=np.zeros((133,2));face=p[23:91]
    eye=np.array([[-10,0],[-5,-3],[5,-3],[10,0],[5,3],[-5,3]])
    face[36:42]=eye+[200,100];face[42:48]=eye+[300,100]
    face[30]=[250,155]
    face[48]=[250-width/2,180];face[54]=[250+width/2,180]
    face[62]=[250,178];face[66]=[250,182]
    face[51]=[250,176]
    return p,np.ones(133)


def test_width_separate_from_opening_and_scale_roll_invariant():
    p,s=face_points()
    assert packet_from_landmarks(p,s,0)['mouthWidth']==pytest.approx(0)
    for width in (60,110):
        p,s=face_points(width)
        packet=packet_from_landmarks(p,s,0)
        a=np.radians(25);rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
        other=packet_from_landmarks(p@rot*1.4+50,s,1)
        assert other['mouthWidth']==pytest.approx(packet['mouthWidth'])
        assert np.sign(packet['mouthWidth'])==np.sign(width-80)


def test_width_uses_shared_confirmation_and_holds_on_face_loss():
    filt=FaceFilter(3,1)
    p,s=face_points()
    for i in range(4): baseline=filt.update(packet_from_landmarks(p,s,i),i*.05)
    p,s=face_points(110)
    for i in range(4,10): wider=filt.update(packet_from_landmarks(p,s,i),i*.05)
    assert wider['mouthWidth']>.5
    assert not filt.update({'faceTracked':False},.6)['faceTracked']


def test_exaggerated_response_keeps_neutral_and_clamps_extremes():
    p,s=face_points(87)
    p[23+62,1]=174;p[23+66,1]=186
    result=packet_from_landmarks(p,s,0)
    assert result['mouthWidth']==pytest.approx(.7)
    assert result['mouth']==pytest.approx(3.5*(12/87-.035)/.45)
    p,s=face_points(150)
    assert packet_from_landmarks(p,s,0)['mouthWidth']==1


def test_round_and_raised_corners_are_independent():
    p,s=face_points(60)
    result=packet_from_landmarks(p,s,0)
    assert result['mouthRound']>.8 and result['mouthSmile']==0
    p,s=face_points(80)
    p[[23+48,23+54],1]-=14
    result=packet_from_landmarks(p,s,0)
    assert result['mouthSmile']>.8 and result['mouthRound']==0
    p,s=face_points(80)
    p[23+66,1]+=25
    assert packet_from_landmarks(p,s,0)['mouthSmile']==0
