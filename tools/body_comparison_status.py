"""Read-only progress of the full recorded three-model comparison."""
import json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ('dinov3','vith'):
    folder=ROOT/'results/comparisons'/('first-take-sam-'+name)
    try:r=json.loads((folder/'report.json').read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError):print(name,'not started');continue
    rows=[]
    try:
        with (folder/'raw.jsonl').open('rb') as f:
            f.seek(0,2);size=f.tell();f.seek(max(0,size-262144));data=f.read()
        for line in data.splitlines()[1:-1]:
            try:rows.append(json.loads(line))
            except json.JSONDecodeError:pass
    except OSError:pass
    last=rows[-1]['frame']+1 if rows else 0
    durations=[row['inference_ms'] for row in rows if 'inference_ms' in row]
    mean=sum(durations)/len(durations) if durations else 0
    eta=(5187-last)*mean/60000
    if r.get('status')=='complete':last=r['frames'];eta=0
    print(name,r.get('status'),str(last)+'/5187','recent inference %.0f ms, approximate remaining %.1f min'%(mean,eta),flush=True)
for label,folder in [('controls','results/comparisons/body-three-models'),('videos','results/avatar-videos/body-three-models')]:
    try:r=json.loads((ROOT/folder/'report.json').read_text(encoding='utf-8'));print(label,r['status'])
    except (OSError,json.JSONDecodeError):print(label,'waiting')
