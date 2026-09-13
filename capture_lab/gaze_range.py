"""Session-local expanding gaze bounds, supported like automatic arm lengths."""
from collections import deque
import numpy as np


class GazeRange:
    def __init__(self):
        self.samples = deque()
        self.low = self.high = None
        self.last_time = None

    def update(self, value, now, learn=True):
        value = np.asarray(value, dtype=float)
        if value.shape != (2,) or not np.isfinite(value).all() or not np.isfinite(now):
            raise ValueError('Finite gaze and observation time required')
        # One inference observation gets one vote, even if a caller repeats it.
        if self.last_time is None or now > self.last_time:
            self.last_time = now
            while self.samples and now-self.samples[0][0] > 5:
                self.samples.popleft()
            if learn:
                self.samples.append((now, value.copy()))
                if len(self.samples) >= 10:
                    ordered = np.sort(np.stack([v for _, v in self.samples]), axis=0)
                    if self.low is None:
                        self.low = np.median(ordered, axis=0)
                        self.high = self.low.copy()
                    # At least ten observations must reach/past each candidate.
                    self.low = np.minimum(self.low, ordered[9])
                    self.high = np.maximum(self.high, ordered[-10])
        return value-self.center

    @property
    def center(self):
        return np.zeros(2) if self.low is None else (self.low+self.high)/2

    def report(self):
        return dict(ready=self.low is not None, samples=len(self.samples),
                    lower=None if self.low is None else self.low.tolist(),
                    upper=None if self.high is None else self.high.tolist(),
                    center=self.center.tolist(), window_seconds=5, min_observations=10)
