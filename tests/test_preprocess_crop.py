import numpy as np
import pytest
from tanakacap.inference import preprocess


@pytest.mark.parametrize('roi',[[0,0,1280,720],[137.2,25.7,563.8,620.1],[-20,10,1300,800]])
def test_rgb_after_warp_is_exactly_the_original_tensor(roi):
    image=np.random.default_rng(4).integers(0,256,(720,1280,3),dtype=np.uint8)
    before=preprocess(image[:,:,::-1],roi,(288,384))
    after=preprocess(image,roi,(288,384),'RGB')
    for a,b in zip(before,after):np.testing.assert_array_equal(a,b)
