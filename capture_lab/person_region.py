"""Bounded person ROI tracking between real detections; pose still runs every frame."""
import time

import cv2
import numpy as np

from .inference import DetectionGate


class PersonRegionTracker:
    def __init__(self, detector, interval=1):
        if interval not in (1, 2, 3):
            raise ValueError('Detector interval must be 1, 2 or 3')
        self.detector = detector
        self.interval = interval
        self.reset()

    def reset(self):
        self.gate = DetectionGate()
        self.roi = self.gray = self.anchors = None
        self.last_detection = None
        self.age = 0
        self.score = 0.
        self.healthy = False
        self.diagnostics = {}
        self.timing = {}

    def observe(self, points, scores):
        if self.interval == 1 or self.roi is None:
            return
        p = np.asarray(points[:13], dtype=np.float32)
        s = np.asarray(scores[:13])
        x, y, w, h = self.roi
        good = np.isfinite(p).all(axis=1) & (s >= .5)
        good &= (p[:, 0] >= x) & (p[:, 0] <= x+w)
        good &= (p[:, 1] >= y) & (p[:, 1] <= y+h)
        self.anchors = np.ascontiguousarray(p[good] * self.scale, dtype=np.float32).reshape(-1, 1, 2)
        # Wrists near a crop edge request immediate detection, so broad gestures
        # cannot keep a crop that was appropriate only for the preceding pose.
        edge = (s >= .5) & np.isfinite(p).all(axis=1) & (
            (p[:, 0] < x+.02*w) | (p[:, 0] > x+.98*w))
        self.healthy = len(self.anchors) >= 6 and not edge.any()

    def _flow(self, gray):
        if self.gray is None or self.gray.shape != gray.shape or self.anchors is None:
            return None
        options = dict(winSize=(21, 21), maxLevel=2,
                       criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 15, .03))
        moved, valid, error = cv2.calcOpticalFlowPyrLK(self.gray, gray, self.anchors, None, **options)
        if moved is None:
            return None
        back, reverse, _ = cv2.calcOpticalFlowPyrLK(gray, self.gray, moved, None, **options)
        if back is None:
            return None
        good = (valid[:, 0] != 0) & (reverse[:, 0] != 0)
        good &= np.isfinite(moved[:, 0]).all(axis=1) & (error[:, 0] < 25)
        good &= np.linalg.norm(back[:, 0]-self.anchors[:, 0], axis=1) < 1.5
        if good.sum() < 6 or good.mean() < .65:
            return None
        shifts = moved[good, 0]-self.anchors[good, 0]
        shift = np.median(shifts, axis=0)
        # Flow is a short-lived translation estimate, not a rigid-body pose.
        if np.linalg.norm(shift) > 35 or np.median(np.linalg.norm(shifts-shift, axis=1)) > 5:
            return None
        result = np.array(self.roi, dtype=float)
        result[:2] += shift / self.scale
        return result.tolist()

    def update(self, image, timestamp):
        start = time.perf_counter()
        self.scale = min(1., 640 / image.shape[1])
        gray = None
        reason = 'every_frame' if self.interval == 1 else 'scheduled'
        tracked = None
        elapsed = None if self.last_detection is None else timestamp-self.last_detection
        if self.interval > 1:
            small = cv2.resize(image, (round(image.shape[1]*self.scale), round(image.shape[0]*self.scale)))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            if self.roi is None or not self.healthy:
                reason = 'unconfirmed_or_poor_pose'
            elif elapsed is None or elapsed < 0 or elapsed >= .12:
                reason = 'expired'
            elif self.age+1 < self.interval:
                tracked = self._flow(gray)
                reason = 'flow' if tracked is not None else 'flow_failed'
        detection_ran = tracked is None
        if detection_ran:
            raw, self.score, _ = self.detector.detect(image)
            self.roi = self.gate.update(raw)
            self.last_detection = timestamp
            self.age = 0
            self.timing = dict(getattr(self.detector, 'timing', {}))
        else:
            x, y, w, h = tracked
            x0, y0 = max(0., x), max(0., y)
            x1, y1 = min(image.shape[1], x+w), min(image.shape[0], y+h)
            self.roi = [x0, y0, max(1., x1-x0), max(1., y1-y0)]
            self.age += 1
            self.timing = {key: 0. for key in ('detector_preprocess_ms', 'detector_inference_call_ms', 'detector_postprocess_ms')}
        self.gray = gray
        if self.roi is None:
            self.healthy = False
            self.anchors = None
        duration = (time.perf_counter()-start)*1000
        self.diagnostics = dict(detection_ran=detection_ran, reason=reason,
                                cached_frames=self.age, roi=self.roi,
                                detection_age_ms=0. if detection_ran else elapsed*1000)
        self.timing['roi_tracking_ms'] = max(0., duration-sum(self.timing.values()))
        return self.roi, self.score, duration
