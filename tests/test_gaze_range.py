import numpy as np
from tanakacap.gaze_range import GazeRange


def observe(c, value, start, count=10):
    for i in range(count):
        result=c.update(value,start+i*.03)
    return result


def test_supported_range_center_and_never_shrinks():
    c=GazeRange()
    np.testing.assert_allclose(observe(c,[.02,-.06],0),[0,0])
    observe(c,[-.10,-.12],1)
    observe(c,[.14,.04],2)
    np.testing.assert_allclose(c.center,[.02,-.04])
    low,high=c.low.copy(),c.high.copy()
    observe(c,[.02,-.04],10,100)
    np.testing.assert_equal(c.low,low)
    np.testing.assert_equal(c.high,high)
    np.testing.assert_allclose(c.update(c.center,14),[0,0])


def test_nine_outliers_expired_samples_and_duplicates_do_not_expand():
    c=GazeRange();observe(c,[0,0],0)
    observe(c,[.4,-.2],1,9)
    for _ in range(20): c.update([.4,-.2],1.24)
    np.testing.assert_equal(c.center,[0,0])
    c.update([.4,-.2],7)
    np.testing.assert_equal(c.center,[0,0])
    observe(c,[.4,-.2],7.1,9)
    np.testing.assert_allclose(c.center,[.2,-.1])


def test_single_eye_does_not_learn_but_uses_saved_center():
    c=GazeRange()
    for i in range(20): c.update([.1,.1],i*.03,learn=False)
    assert c.low is None
    observe(c,[.02,-.05],1)
    result=c.update([.04,-.03],5,learn=False)
    np.testing.assert_allclose(result,[.02,.02])
