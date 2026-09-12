import numpy as np
from capture_lab.head_only import angles_from_rotation
def test_rotation_rejects_invalid_pose():
    assert angles_from_rotation(np.zeros((3,3))) is None
    assert angles_from_rotation(np.full((3,3),np.nan)) is None
    assert angles_from_rotation(np.diag([-1,1,1])) is None
def test_rotation_identity_and_camera_axes():
    assert np.allclose(angles_from_rotation(np.eye(3)),0)
    a=np.deg2rad(20);c,s=np.cos(a),np.sin(a)
    assert np.allclose(angles_from_rotation([[1,0,0],[0,c,-s],[0,s,c]]),[20,0,0])
    assert np.allclose(angles_from_rotation([[c,-s,0],[s,c,0],[0,0,1]]),[0,0,20])

def test_head_only_never_loads_other_models_or_creates_logs(monkeypatch):
    import sys
    from capture_lab import __main__ as app
    from capture_lab import head_only
    def forbidden(*args, **kwargs):
        raise AssertionError("Head-only must not load full models or create result files")
    monkeypatch.setattr(app,"output_folder",forbidden)
    monkeypatch.setattr(app,"SimCCModel",forbidden)
    monkeypatch.setattr(app,"PersonDetector",forbidden)
    monkeypatch.setattr(app,"environment",lambda:{})
    packets=[]
    class Model:
        def __init__(self, output): assert output is None
        def predict(self,image,roi): return np.array([10.,5.,3.]),dict(head_model_ms=1.)
        def finish(self): return dict(calls=5)
    class Video:
        def isOpened(self): return True
        def read(self): return True,np.zeros((64,64,3),np.uint8)
        def release(self): pass
    class Sender:
        def __init__(self,port): pass
        def send(self,p): packets.append(p)
        def close(self): pass
    monkeypatch.setattr(head_only,"HeadOnlyModel",Model)
    monkeypatch.setattr(head_only.cv2,"VideoCapture",lambda p:Video())
    monkeypatch.setattr(head_only,"LocalSender",Sender)
    monkeypatch.setattr(sys,"argv",["capture_lab","benchmark","--source","video","--video","dummy",
                                  "--head-only","--head-roi-mode","fixed","--no-log","--frames","5","--warmup","0",
                                  "--roi","0","0","32","32","--unity-port","39549"])
    app.main()
    assert len(packets)==5 and packets[-1]["headTracked"]
    assert all(not p["faceTracked"] for p in packets)
