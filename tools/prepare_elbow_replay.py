import json
from pathlib import Path
root=Path('results/elbow-face-research')
previous=0.;out=[]
for line in (root/'replay-verified-second/packets.jsonl').read_text().splitlines():
    r=json.loads(line);now=r['time_seconds']
    out.append(json.dumps(dict(packet=r['packet'],dt=max(.001,min(.2,now-previous)))))
    previous=now
(root/'unity-input.jsonl').write_text('\n'.join(out),encoding='utf-8')
