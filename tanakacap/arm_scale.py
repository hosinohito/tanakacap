"""Preserve trusted face geometry while body tracking remains continuous."""
class ArmScale:
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.last_valid = None
        self.missing = False
        self.recovery = None
        self.source = 'unavailable'

    def update(self, face_scale, now):
        if face_scale is None:
            self.missing = True
            self.recovery = None
            if self.last_valid is not None and now >= self.last_valid:
                self.source = 'held_face'
                return self.value
            self.source = 'unavailable'
            return None
        if self.missing and self.value is not None:
            self.recovery = (now, self.value)
        self.missing = False
        self.last_valid = now
        self.source = 'face'
        if self.recovery is not None:
            start, initial = self.recovery
            amount = min(1., max(0., (now-start)/.2))
            self.value = initial + (face_scale-initial)*amount
            if amount < 1:
                self.source = 'recovering_face'
            else:
                self.recovery = None
        else:
            self.value = face_scale
        return self.value
