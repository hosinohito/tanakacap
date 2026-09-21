"""Check packet-paced avatar rendering with synthetic packets, never a camera."""
import json
import sys
from pathlib import Path
import socket
import statistics
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.partial_tracking import LocalSender


def main():
    out=ROOT/'results/render-sync-ui';out.mkdir(parents=True,exist_ok=True)
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as status:
        status.bind(('127.0.0.1',0));status.setblocking(False)
        process=subprocess.Popen([str(ROOT/'builds/player/TanakaCap.exe'),'-batchmode','--render-sync',
            '--port',str(port),'--ui-status-port',str(status.getsockname()[1]),
            '--avatar',str(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap'),
            '--use-demo-shape-keys','-logFile',str(out/'player.log')],creationflags=subprocess.CREATE_NO_WINDOW)
        sender=LocalSender(port)
        report=[];sequence=0
        try:
            time.sleep(2)
            for rate in (15,35):
                samples=[];start=time.perf_counter();next_packet=start
                while time.perf_counter()-start<3:
                    assert process.poll() is None,'Player exited'
                    now=time.perf_counter()
                    if now>=next_packet:
                        pose=dict(sequence=sequence,headTracked=True,headYaw=0)
                        # Three independently delivered groups still render at source Hz.
                        for group in (('head',),('left_arm',),('gaze',)):
                            sender.send(pose,group)
                        sequence+=1;next_packet=now+1/rate
                    try:
                        packet=json.loads(status.recv(4096))
                        if now-start>1:samples.append(packet)
                    except BlockingIOError:pass
                    time.sleep(.001)
                observed=statistics.median(p['renderHz'] for p in samples)
                assert abs(observed-rate)<5,(rate,observed,samples)
                report.append(dict(input_hz=rate,render_hz=observed,samples=samples))
        finally:
            sender.close()
            if process.poll() is None:process.terminate()
            process.wait(timeout=10)
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print([(r['input_hz'],r['render_hz']) for r in report])


if __name__=='__main__':main()
