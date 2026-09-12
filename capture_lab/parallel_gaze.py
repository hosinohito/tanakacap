"""One observation at a time: overlap iris GPU work with independent CPU controls."""
from concurrent.futures import ThreadPoolExecutor


class ParallelGaze:
    def __init__(self,gaze):
        self.gaze=gaze
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='iris')
        self.pending=None

    def start(self,image,points,scores,packet,now):
        if self.pending is not None:raise RuntimeError('Previous gaze observation has not joined')
        snapshot=dict(packet)
        def run():
            self.gaze.update(image,points,scores,snapshot,now)
            return {key:snapshot[key] for key in ('gazeTracked','gazeYaw','gazePitch')}
        self.pending=self.pool.submit(run)

    def join(self,packet):
        if self.pending is None:raise RuntimeError('No pending gaze observation')
        try:packet.update(self.pending.result())
        finally:self.pending=None

    def close(self):
        self.pool.shutdown(wait=True)
