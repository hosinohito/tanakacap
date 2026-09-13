import json
from tanakacap.development_log import DevelopmentLog
from tanakacap.live_status import LiveStatus

def test_development_log_keeps_numeric_status_and_console(tmp_path):
    log=DevelopmentLog(tmp_path)
    log.write('status',dict(hz=11,busyMs=25))
    log.write('console','カメラ情報')
    rows=[json.loads(line) for line in log.path.read_text(encoding='utf-8').splitlines()]
    assert rows[0]['data']==dict(hz=11,busyMs=25)
    assert rows[1]['data']=='カメラ情報'

def test_status_stage_means_include_input_wait():
    now=[0.]
    status=LiveStatus(clock=lambda:now[0])
    class Socket:
        def sendto(self,payload,address):self.packet=json.loads(payload)
    status.sock=Socket();status.port=1
    status.complete(20,True,dict(input_wait_read_ms=60,detector_ms=6))
    now[0]=.6
    status.complete(30,True,dict(input_wait_read_ms=80,detector_ms=8))
    assert status.sock.packet['busyMs']==25
    assert status.sock.packet['timings']==dict(input_wait_read_ms=70,detector_ms=7)
    assert status.details=={}
