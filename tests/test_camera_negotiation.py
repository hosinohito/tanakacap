from tanakacap import capture


def test_format_selected_after_size_and_rate(monkeypatch):
    camera = capture.Camera(1, 1280, 720, 30, 'dshow')
    cv = capture.cv2
    calls = []
    values = {cv.CAP_PROP_FOURCC: cv.VideoWriter_fourcc(*'YUY2')}

    class Device:
        def isOpened(self): return True
        def set(self, key, value):
            calls.append(key)
            values[key] = value
            if key != cv.CAP_PROP_FOURCC:
                values[cv.CAP_PROP_FOURCC] = cv.VideoWriter_fourcc(*'YUY2')
            return True
        def get(self, key): return values.get(key, -1)
        def getBackendName(self): return 'DSHOW'
        def read(self):
            import numpy as np
            camera.stop.set()
            return True, np.zeros((720,1280,3),dtype=np.uint8)
        def release(self): pass

    monkeypatch.setattr(cv, 'VideoCapture', lambda *args: Device())
    camera._read()
    assert camera.mailbox.error is None
    assert calls == [cv.CAP_PROP_FRAME_WIDTH, cv.CAP_PROP_FRAME_HEIGHT,
                     cv.CAP_PROP_FPS, cv.CAP_PROP_FOURCC]
    assert camera.metadata['actual_format'] == 'MJPG'
    assert camera.metadata['format_matches_request'] is True
