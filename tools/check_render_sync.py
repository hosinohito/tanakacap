"""Check packet-paced avatar rendering with synthetic packets, never a camera."""
import json
from pathlib import Path
import socket
import statistics
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'results/render-sync-ui';out.mkdir(parents=True,exist_ok=True)
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as status, socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sender:
        status.bind(('127.0.0.1',0));status.setblocking(False)
        process=subprocess.Popen([str(ROOT/'builds/lab/TanakaCap.exe'),'-batchmode','--render-sync',
            '--port',str(port),'--ui-status-port',str(status.getsockname()[1]),
            '--avatar',str(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap'),
            '--use-demo-shape-keys','-logFile',str(out/'player.log')],creationflags=subprocess.CREATE_NO_WINDOW)
        report=[];sequence=0
        try:
            time.sleep(2)
            for rate in (15,35):
                samples=[];start=time.perf_counter();next_packet=start
                while time.perf_counter()-start<3:
                    assert process.poll() is None,'Player exited'
                    now=time.perf_counter()
                    if now>=next_packet:
                        sender.sendto(json.dumps(dict(version=1,sequence=sequence,tracked=False)).encode(),('127.0.0.1',port))
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
            if process.poll() is None:process.terminate()
            process.wait(timeout=10)
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print([(r['input_hz'],r['render_hz']) for r in report])


if __name__=='__main__':main()
