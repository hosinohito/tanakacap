import pytest
from capture_lab.parallel_gaze import ParallelGaze


def test_same_frame_snapshot_and_merge_without_overwriting_body():
    class Gaze:
        def update(self,image,points,scores,packet,now):
            packet.update(gazeTracked=True,gazeYaw=packet['headPitch'],gazePitch=now,body=999)
    worker=ParallelGaze(Gaze())
    try:
        for frame in range(4):
            packet=dict(headPitch=frame,body=1)
            worker.start(None,None,None,packet,frame)
            with pytest.raises(RuntimeError):worker.start(None,None,None,packet,frame+1)
            packet.update(headPitch=100,body=2)
            worker.join(packet)
            assert packet==dict(headPitch=100,body=2,gazeTracked=True,gazeYaw=frame,gazePitch=frame)
    finally:worker.close()
