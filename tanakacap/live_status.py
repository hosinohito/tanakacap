"""Pace work before input acquisition and send numeric UI status over loopback."""
import json
import math
import socket
import time


class LiveStatus:
    def __init__(self, limit=0, port=None, clock=time.perf_counter, sleep=time.sleep):
        if not math.isfinite(limit) or not 0 <= limit <= 240:
            raise ValueError('inference limit must be 0..240')
        if port is not None and not 1 <= port <= 65535:
            raise ValueError('status port must be 1..65535')
        self.period=1/limit if limit else 0
        self.port=port; self.clock=clock; self.sleep=sleep
        self.next_start=0; self.since=clock(); self.count=0; self.busy=0
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM) if port else None

    def wait(self):
        now=self.clock()
        if self.period and now<self.next_start:
            self.sleep(self.next_start-now)
        self.next_start=self.clock()+self.period

    def complete(self, milliseconds, tracked=False):
        if not self.sock:return
        self.count+=1; self.busy+=max(0,milliseconds)
        now=self.clock();elapsed=now-self.since
        if elapsed<.5:return
        packet=dict(kind='inference', hz=self.count/elapsed, busyMs=self.busy/self.count,
                    tracked=bool(tracked), limit=1/self.period if self.period else 0)
        try:self.sock.sendto(json.dumps(packet).encode(),('127.0.0.1',self.port))
        except OSError:pass
        self.count=0;self.busy=0;self.since=now

    def close(self):
        if self.sock:self.sock.close()
