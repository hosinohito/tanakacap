"""Small numeric/console development logs; no images, audio or model traces."""
import json
from pathlib import Path
import threading
import time

class DevelopmentLog:
    def __init__(self, root):
        directory=Path(root)/'logs';directory.mkdir(parents=True,exist_ok=True)
        self.path=directory/f'development-{time.time_ns()}.jsonl'
        self.lock=threading.Lock()
    def write(self, kind, data):
        record=json.dumps(dict(time=time.time(),kind=kind,data=data),ensure_ascii=False,allow_nan=False)
        try:
            with self.lock:
                if self.path.exists() and self.path.stat().st_size>8*1024*1024:
                    self.path.replace(self.path.with_suffix('.previous.jsonl'))
                with self.path.open('a',encoding='utf-8') as stream:stream.write(record+'\n')
        except OSError:
            pass
