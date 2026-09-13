import numpy as np
import pytest
from tanakacap.inference import local_peak_positions,decode_simcc3d
from tanakacap.arm_width import measure_arm_widths


def test_fractional_peak_has_no_quantization_step_and_does_not_average_modes():
    x=np.arange(576)
    centers=np.linspace(200.3,200.7,11)
    distributions=np.exp(-.5*((x[None,:]-centers[:,None])/3)**2)
    assert local_peak_positions(distributions)==pytest.approx(centers,abs=1e-8)
    bimodal=distributions[0]+.9*np.exp(-.5*((x-300)/3)**2)
    assert local_peak_positions(bimodal)==pytest.approx(200.3,abs=1e-8)
    for a in (np.zeros((2,10)),np.ones((2,10)),np.eye(10)):
        np.testing.assert_array_equal(local_peak_positions(a),a.argmax(axis=-1))


def test_refine_is_reversible_and_leaves_hands_and_face_unchanged():
    arrays=[np.tile(np.exp(-.5*((np.arange(n)-100.3)/3)**2),(1,133,1)) for n in (576,768,576)]
    old=decode_simcc3d(arrays,np.array([300,300]),np.array([288,384]),[288,384],refine_body=False)
    new=decode_simcc3d(arrays,np.array([300,300]),np.array([288,384]),[288,384])
    ids=[i for i in range(133) if i not in (5,6,7,8,11,12)]
    np.testing.assert_array_equal(old[0][ids],new[0][ids]);np.testing.assert_array_equal(old[2][ids],new[2][ids])
    assert abs(new[2][7]-old[2][7])<2.1744869/576


def fixture(width):
    image=np.zeros((300,400,3),np.uint8)
    image[30:270,200-width//2:200+width//2]=[90,150,210]
    xy=np.zeros((133,2));s=np.zeros(133)
    xy[[7,9]]=[[200,50],[200,250]];s[[7,9]]=1
    return image,xy,s


def test_image_width_reads_pixels_not_landmark_distance():
    small=measure_arm_widths(*fixture(30),face_scale=.002)['left']
    big=measure_arm_widths(*fixture(50),face_scale=.002)['left']
    assert small['status']==big['status']=='measured'
    assert big['width_pixels']>small['width_pixels']*1.5
    assert not big['drives_pose']
    image,xy,s=fixture(30);image[:]=80
    assert measure_arm_widths(image,xy,s)['left']['status']=='ambiguous_contour'
