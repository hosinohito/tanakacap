"""Exercise a recorded input through the regular UI controller, without camera access."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tanakacap.control_panel import DEFAULT,Session
p=argparse.ArgumentParser();p.add_argument('--avatar',type=Path,required=True);p.add_argument('--video',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.parent.mkdir(parents=True,exist_ok=True)
s=Session();rows=[];messages=[];started=time.monotonic()
try:
 s.start({**DEFAULT,'avatar':str(a.avatar.resolve()),'source':'video','video':str(a.video.resolve()),'expression':'auto-custom','preview':False},frames=900)
 while time.monotonic()-started<180:
  rows.append({'at':time.monotonic()-started,'status':dict(s.poll())})
  while not s.messages.empty():messages.append(s.messages.get_nowait())
  if s.infer.poll() is not None:break
  if s.player.poll() is not None:raise RuntimeError('Player ended unexpectedly')
  time.sleep(.25)
 if s.infer.poll()!=0:raise RuntimeError('Inference failed or timed out: '+str(messages[-10:]))
 if not any(r['status'].get('player',{}).get('receiveHz',0)>0 for r in rows):raise RuntimeError('No receiver telemetry')
 print('Recorded session passed',flush=True)
finally:
 s.stop();deadline=time.monotonic()+15
 while s.running and time.monotonic()<deadline:time.sleep(.1)
 s.sock.close()
 a.output.write_text(json.dumps({'rows':rows,'messages':messages},ensure_ascii=False,indent=2),encoding='utf-8')
