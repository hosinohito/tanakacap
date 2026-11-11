import sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tanakacap.control_panel import DEFAULT,commands
base=ROOT/'results/arm-release-fix';base.mkdir(exist_ok=True)
for take in ('20260911T235327-031115Z',):
 out=base/(take+'-baseline.log')
 if out.exists():continue
 c={**DEFAULT,'source':'video','video':str(ROOT/'results/comparison-takes'/take/'camera.avi')}
 _,cmd=commands(c,39589,39590)
 cmd.remove('--no-log');cmd.remove('--loop-video');cmd[cmd.index('--frames')+1]='1200'
 cmd+=['--landmarks','--no-ort-profile']
 with out.open('w',encoding='utf-8') as f:
  subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 print(out,flush=True)
