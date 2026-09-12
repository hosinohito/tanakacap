import numpy as np
import pytest
import capture_lab.motion_gate as motion


@pytest.mark.parametrize('size,stride',[(1,1),(3,1),(3,3)])
def test_reused_windows_and_direction_match_exactly_without_aliasing(monkeypatch,size,stride):
    monkeypatch.setattr(motion,'REUSE_BUFFERS',False)
    old=motion.DirectionGate(.02,4,size,stride)
    monkeypatch.setattr(motion,'REUSE_BUFFERS',True)
    new=motion.DirectionGate(.02,4,size,stride)
    rng=np.random.default_rng(84)
    now=0
    for i in range(240):
        now+=.4 if i%47==0 else .033
        value=rng.normal(size=(2,3))
        a=old.update(value,now);b=new.update(value,now)
        value[:]=1234  # Input mutation must not change stored observations.
        assert (a is None)==(b is None)
        if a is not None:
            np.testing.assert_array_equal(a,b)
            a[:]=999;b[:]=999  # Caller owns both outputs.
        if i%61==0:old.reset();new.reset()


def test_rotation_buffer_matches_across_wrap_and_reset(monkeypatch):
    monkeypatch.setattr(motion,'REUSE_BUFFERS',False)
    old=motion.RotationGate(3,1)
    monkeypatch.setattr(motion,'REUSE_BUFFERS',True)
    new=motion.RotationGate(3,1)
    for i,degree in enumerate(np.linspace(160,240,120)):
        a=np.radians(degree);frame=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        x=old.update(frame,i*.033);y=new.update(frame,i*.033)
        assert (x is None)==(y is None)
        if x is not None:np.testing.assert_array_equal(x,y)
        if i==50:old.missing();new.missing()
