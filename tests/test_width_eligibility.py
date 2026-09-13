import numpy as np
from tanakacap.arm_width import width_eligibility,measure_arm_widths,consistent_section_width

def test_eligibility_does_not_depend_on_successful_contour_or_palm():
    xy=np.zeros((133,2));s=np.zeros(133)
    xy[[7,9]]=[[100,50],[100,250]];s[[7,9]]=1
    assert width_eligibility(xy,s,(400,300),'left')=='eligible'
    image=np.zeros((300,400,3),np.uint8)
    result=measure_arm_widths(image,xy,s)['left']
    assert result['eligibility']=='eligible' and result['status']=='ambiguous_contour'
    xy[9,1]=299
    assert width_eligibility(xy,s,(400,300),'left')=='out_of_frame'
    xy[9,1]=250;s[9]=.2
    assert width_eligibility(xy,s,(400,300),'left')=='low_confidence'

def test_visible_arm_is_measured_even_when_search_rays_cross_image_edge():
    image=np.zeros((300,400,3),np.uint8);image[20:280,15:45]=[90,150,210]
    xy=np.zeros((133,2));s=np.zeros(133)
    xy[[7,9]]=[[30,50],[30,250]];s[[7,9]]=1
    result=measure_arm_widths(image,xy,s)['left']
    assert result['status']=='measured' and 29<=result['width_pixels']<=32
    image[:]=0
    assert measure_arm_widths(image,xy,s)['left']['status']=='ambiguous_contour'


def test_taper_and_one_bad_cross_section_are_distinct_from_unstable_edges():
    assert abs(consistent_section_width([[0,50],[1,45],[2,40],[3,35],[4,30]])-40)<1e-8
    assert abs(consistent_section_width([[0,50],[1,45],[2,80],[3,35],[4,30]])-40)<1e-8
    assert consistent_section_width([[0,10],[1,80],[2,20],[3,70],[4,25]]) is None
