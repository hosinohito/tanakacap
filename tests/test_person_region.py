import cv2
import numpy as np

from capture_lab.person_region import PersonRegionTracker


class Detector:
    def __init__(self):
        self.calls = 0
        self.roi = [20., 20., 260., 200.]
        self.timing = {}

    def detect(self, image):
        self.calls += 1
        return self.roi, .9, 0.


def fixture():
    image = np.random.default_rng(7).integers(0, 256, (240, 320, 3), dtype=np.uint8)
    points = np.array([[60+x*40, 60+y*40] for y in range(3) for x in range(4)]+[[150, 150]], np.float32)
    detector = Detector()
    tracker = PersonRegionTracker(detector, 3)
    for index in range(3):
        tracker.update(image, index/30)
        tracker.observe(points, np.ones(13))
    return image, points, detector, tracker


def test_confirm_real_detections_then_track_translation_and_refresh():
    image, points, detector, tracker = fixture()
    assert detector.calls == 3
    for index in (3, 4):
        offset = (index-2)*3
        shifted = cv2.warpAffine(image, np.float32([[1, 0, offset], [0, 1, 0]]), (320, 240))
        roi, _, _ = tracker.update(shifted, index/30)
        tracker.observe(points+[offset, 0], np.ones(13))
        assert abs(roi[0]-(20+offset)) < .3
        assert not tracker.diagnostics['detection_ran']
    assert detector.calls == 3
    tracker.update(shifted, 5/30)
    assert detector.calls == 4


def test_blank_triggers_same_frame_detection_and_loss_requires_reconfirmation():
    image, points, detector, tracker = fixture()
    detector.roi = None
    roi, _, _ = tracker.update(np.zeros_like(image), .1)
    assert roi is None and detector.calls == 4
    detector.roi = [20., 20., 260., 200.]
    for i in range(2):
        assert tracker.update(image, .14+i/30)[0] is None
    assert tracker.update(image, .21)[0] is not None


def test_time_gap_and_low_confidence_force_detection():
    image, points, detector, tracker = fixture()
    tracker.update(image, 1.)
    assert detector.calls == 4 and tracker.diagnostics['reason'] == 'expired'
    tracker.observe(points, np.zeros(13))
    tracker.update(image, 1.01)
    assert detector.calls == 5


def test_interval_one_has_original_gate_behavior():
    detector = Detector()
    tracker = PersonRegionTracker(detector)
    image = np.zeros((240, 320, 3), np.uint8)
    assert tracker.update(image, 0)[0] is None
    assert tracker.update(image, .03)[0] is None
    assert tracker.update(image, .06)[0] == detector.roi
    assert detector.calls == 3
    tracker.reset()
    assert tracker.update(image, .09)[0] is None
