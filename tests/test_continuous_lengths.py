import numpy as np
from tanakacap.body_geometry import SupportedLengths,DepthAssist


def test_ten_frames_required_and_shorter_values_never_replace_length():
    lengths=SupportedLengths()
    for i in range(9): np.testing.assert_allclose(lengths.update([.3,.25],i*.05),[0,0])
    np.testing.assert_allclose(lengths.update([.3,.25],.45),[.3,.25])
    for i in range(20): lengths.update([.2,.15],6+i*.05)
    np.testing.assert_allclose(lengths.value,[.3,.25])
    for i in range(10): lengths.update([.35,.28],8+i*.05)
    np.testing.assert_allclose(lengths.value,[.35,.28])


def test_support_must_be_inside_five_seconds_and_outlier_not_maximum():
    lengths=SupportedLengths()
    for i in range(10): lengths.update([.3,.2],i*.6)
    np.testing.assert_allclose(lengths.value,[0,0])
    for i in range(10): lengths.update([.25,.2],10+i*.05)
    lengths.update([.49,.49],11)
    np.testing.assert_allclose(lengths.value,[.25,.2])


def test_excessive_depth_does_not_disable_good_projection():
    assist=DepthAssist()
    for i in range(10): assist.update(np.array([.3,0,.03]),np.array([.25,0,.03]),i*.05)
    for now in [.5,.55]:
        bones,_=assist.update(np.array([.1,0,2]),np.array([.15,0,2]),now)
    assert (np.linalg.norm(bones,axis=1)<.4).all()
