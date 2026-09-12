"""Recorded input only: exercise the UI's exact process controller and telemetry."""
import json
import statistics
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from capture_lab.control_panel import DEFAULT,Session


def run():
    video=next((ROOT/'results/comparison-takes').glob('*/camera.avi'))
    output=ROOT/'results/ui-validation';output.mkdir(exist_ok=True)
    results={}
    for name,mode,rate,fps,frames in [('full','full','60',60,600),('face_head','face_head','60',60,600),
                                     ('head_only','head_only','60',60,600),('custom23','full','custom',23,180),
                                     ('sync','full','sync',60,300)]:
        session=Session();seen={};samples=[];messages=[];start=time.monotonic()
        config={**DEFAULT,'source':'video','video':str(video),'mode':mode,'rate':rate,'fps':fps}
        cached=output/(name+'.json')
        if '--resume' in sys.argv and cached.exists():
            previous=json.loads(cached.read_text(encoding='utf-8'))
            if previous['config']==config:results[name]=previous;session.sock.close();continue
        try:
            session.start(config,frames=frames)
            while time.monotonic()-start<120:
                values=session.poll()
                for kind,stamp in session.last.items():
                    if seen.get(kind)!=stamp and kind in values:
                        seen[kind]=stamp;samples.append(dict(kind=kind,at=time.monotonic()-start,**{k:v for k,v in values[kind].items() if k!='kind'}))
                while not session.messages.empty():messages.append(session.messages.get_nowait())
                if session.infer.poll() is not None:break
                if session.player.poll() is not None:raise RuntimeError('Player ended unexpectedly')
                time.sleep(.1)
            assert session.infer.poll()==0, messages[-20:]
            rows=[r for r in samples if r['kind']=='inference'][2:]
            renders=[r for r in samples if r['kind']=='player' and rows and rows[0]['at']<=r['at']<=rows[-1]['at']]
            assert rows and renders
            result=dict(config=config,samples=samples,inference_hz=statistics.mean(r['hz'] for r in rows),
                        busy_ms=statistics.mean(r['busyMs'] for r in rows),render_hz=statistics.mean(r['renderHz'] for r in renders),
                        receive_hz=statistics.mean(r['receiveHz'] for r in renders))
            assert result['inference_hz']<=fps+1,result
            assert result['receive_hz']>10,result
            if rate=='custom':assert 18<result['render_hz']<25,result
            if rate=='sync':assert result['render_hz']<=result['receive_hz']+12,result
            results[name]=result
            (output/(name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
            (output/(name+'.log')).write_text('\n'.join(messages),encoding='utf-8')
            print(name,{k:v for k,v in result.items() if k not in ('config','samples')},flush=True)
        finally:
            session.stop()
            deadline=time.monotonic()+15
            while session.stopping and time.monotonic()<deadline:time.sleep(.1)
            assert not session.running
            session.sock.close()
    baseline=results['head_only']['busy_ms']
    costs=dict(scope='RTX4090, recorded video, UI controller, FullHD60. Inference and retarget per observation, excluding decode/rate wait/render. Mean of .5-second telemetry windows after first two samples.',
               results='results/ui-validation',modes={k:dict(ms=results[k]['busy_ms'],ratio=max(1,int(results[k]['busy_ms']/baseline+.5))) for k in ('full','face_head','head_only')})
    (ROOT/'docs/ui-costs.json').write_text(json.dumps(costs,indent=2),encoding='utf-8')
    (output/'report.json').write_text(json.dumps(dict(status='complete',cases=list(results)),indent=2),encoding='utf-8')

if __name__=='__main__':run()
