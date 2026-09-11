import numpy as np
from capture_lab.arm_filter import filter_arm


def test_depth_outlier_does_not_delay_visible_arm_raise():
    old=np.zeros((2,3))
    clean=np.array([[0,.3,0],[0,.5,0]])
    noisy=clean.copy(); noisy[:,2]=3
    np.testing.assert_allclose(filter_arm(old,clean,.05)[:,:2],filter_arm(old,noisy,.05)[:,:2])
    assert np.max(filter_arm(old,noisy,.05)[:,2])<.3


def test_deliberate_arm_raise_reaches_target_promptly_without_overshoot():
    result=np.zeros((2,3)); target=np.array([[0,.5,0],[0,1.,0]])
    for _ in range(4):
        result=filter_arm(result,target,.05)
        assert (result<=target+1e-9).all()
    assert result[1,1]>.95


def test_small_stationary_noise_remains_attenuated():
    previous=np.zeros((2,3)); output=[]
    for i in range(100):
        target=np.full((2,3),.01*(-1)**i)
        previous=filter_arm(previous,target,.05)
        output.append(previous.copy())
    assert np.std(np.array(output)[20:,:,0])<.005
