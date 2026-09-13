"""Bounded latest-frame camera reader. No image or audio recording by default."""
import threading
import time
from dataclasses import dataclass

import cv2


@dataclass
class Frame:
    sequence: int
    acquired: float
    image: object


class LatestFrame:
    def __init__(self):
        self.condition = threading.Condition()
        self.latest = None
        self.error = None
        self.closed = False

    def publish(self, frame):
        with self.condition:
            self.latest = frame
            self.condition.notify_all()

    def fail(self, error):
        with self.condition:
            self.error = error
            self.closed = True
            self.condition.notify_all()

    def next(self, after=-1, timeout=5):
        with self.condition:
            ok = self.condition.wait_for(lambda: self.error or self.closed or
                                         (self.latest is not None and self.latest.sequence > after), timeout)
            if self.error:
                raise RuntimeError(self.error)
            if not ok or self.closed:
                raise TimeoutError('Camera did not deliver a new frame')
            return self.latest


class Camera:
    def __init__(self, index=0, width=1280, height=720, fps=30, backend='msmf', pixel_format=None):
        self.mailbox = LatestFrame()
        self.stop = threading.Event()
        self.metadata = {}
        self.args = index, width, height, fps, backend, pixel_format
        self.thread = threading.Thread(target=self._read, daemon=True)

    def _read(self):
        index, width, height, fps, backend, pixel_format = self.args
        cap = None
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW if backend == 'dshow' else cv2.CAP_MSMF)
            if not cap.isOpened():
                raise RuntimeError(f'Cannot open camera {index} with {backend}')
            requested_format=pixel_format or ('MJPG' if backend=='dshow' else None)
            format_accepted=cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*requested_format)) if requested_format else None
            accepted = {'width': cap.set(cv2.CAP_PROP_FRAME_WIDTH, width),
                        'height': cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height),
                        'fps': cap.set(cv2.CAP_PROP_FPS, fps)}
            self.metadata = {'index': index, 'backend': cap.getBackendName(),
                             'requested': [width, height, fps],
                             'reported': [cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                                          cap.get(cv2.CAP_PROP_FPS)],
                             'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)), 'requested_format':requested_format,
                             'format_accepted':format_accepted, 'exposure':cap.get(cv2.CAP_PROP_EXPOSURE),
                             'auto_exposure':cap.get(cv2.CAP_PROP_AUTO_EXPOSURE), 'settings_accepted': accepted}
            if self.metadata['reported'][:2] != [width, height]:
                print(f'WARNING: requested {width}x{height}, received {self.metadata["reported"][:2]}. Check camera index.', flush=True)
            sequence = 0
            while not self.stop.is_set():
                ok, image = cap.read()
                acquired = time.perf_counter()
                if not ok:
                    raise RuntimeError('Camera read failed or camera disconnected')
                self.mailbox.publish(Frame(sequence, acquired, image))
                sequence += 1
        except Exception as exc:
            self.mailbox.fail(str(exc))
        finally:
            if cap is not None:
                cap.release()

    def __enter__(self):
        self.thread.start()
        try:
            self.mailbox.next(timeout=15)
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(timeout=3)
        if self.thread.is_alive():
            print('WARNING: camera driver did not stop within 3 seconds; process exit will release it.')
