import numpy as np
from tanakacap.head_region import HeadRegionTracker, crop_for

SHAPE = (720,1280,3)
BOX = np.array([500.,200.,140.,160.])


def test_acquire_loss_and_recovery_require_fresh_confirmation():
    t = HeadRegionTracker()
    assert t.update([(BOX,.95)],0,SHAPE) is None
    assert t.update([(BOX,.95)],.033,SHAPE) is not None
    assert t.update([],.066,SHAPE) is None
    assert t.state == 'lost'
    assert t.update([(BOX,.95)],.1,SHAPE) is None
    assert t.update([(BOX,.95)],.133,SHAPE) is not None


def test_no_immediate_jump_to_other_face_and_no_ambiguous_reacquisition():
    t = HeadRegionTracker()
    t.update([(BOX,.95)],0,SHAPE)
    t.update([(BOX,.95)],.033,SHAPE)
    other = BOX + [500,0,0,0]
    assert t.update([(other,.99)],.066,SHAPE) is None
    assert t.update([(other,.99),(other-[200,0,0,0],.9)],1.,SHAPE) is None
    assert t.update([(other,.99)],1.1,SHAPE) is None
    assert t.update([(other,.99)],1.133,SHAPE) is not None


def test_initial_multiple_faces_wait_for_selection():
    t = HeadRegionTracker()
    assert t.update([(BOX,.95),(BOX+[400,0,0,0],.99)],0,SHAPE) is None
    t = HeadRegionTracker(BOX)
    assert t.update([(BOX,.95),(BOX+[400,0,0,0],.99)],0,SHAPE) is None
    assert t.update([(BOX,.95),(BOX+[400,0,0,0],.99)],.03,SHAPE) is not None


def test_crop_preserves_square_near_frame_edge():
    for box in ([0,0,100,150],[1200,600,80,120],[0,0,1280,720]):
        x,y,w,h = crop_for(box,SHAPE)
        assert w == h and x >= 0 and y >= 0 and x+w <=1280 and y+h <=720


def test_auto_loop_loss_packets_and_no_log(monkeypatch):
    from tanakacap import head_only as app
    from tanakacap import __main__ as cli
    import sys
    packets=[]
    class Model:
        def __init__(self, output): assert output is None
        def predict(self, image, roi):
            assert image.any(), 'Must not infer a pose from missing head'
            return np.array([10.,5.,3.]), {'head_model_ms':1.}
        def finish(self): return {}
    class Detector:
        def __init__(self, output): assert output is None
        def detect(self,image): return ([(BOX,.95)] if image.any() else []), .1
        def finish(self): return {}
    class Video:
        index=0
        def isOpened(self): return True
        def read(self):
            self.index += 1
            return True, np.full(SHAPE, 0 if 7 <= self.index <=10 else 1,np.uint8)
        def get(self,key): return 30.
        def release(self): pass
    class Sender:
        def __init__(self,port): pass
        def send(self,p): packets.append(p)
        def close(self): pass
    def forbidden(*a,**k): raise AssertionError('Unexpected full model or log')
    for name in ('output_folder','SimCCModel','PersonDetector'):
        monkeypatch.setattr(cli,name,forbidden)
    monkeypatch.setattr(cli,'environment',lambda:{})
    monkeypatch.setattr(app,'HeadOnlyModel',Model)
    monkeypatch.setattr(app,'HeadRegionDetector',Detector)
    monkeypatch.setattr(app,'LocalSender',Sender)
    monkeypatch.setattr(app.cv2,'VideoCapture',lambda _:Video())
    monkeypatch.setattr(sys,'argv',['tanakacap','benchmark','--source','video','--video','dummy',
        '--head-only','--no-log','--frames','16','--warmup','0','--unity-port','39549'])
    cli.main()
    assert packets[5]['headTracked'] and packets[-1]['headTracked']
    assert all(not p['headTracked'] for p in packets[6:12])
    assert all(not p['faceTracked'] for p in packets)
