"""Read-only invariants and per-stage projection evidence from a completed trial."""
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np

def run(folder):
    report=json.loads((folder/'report.json').read_text());assert report['status']=='complete'
    result={}
    for name in ('shoulder-width','shoulder-face'):
        stages=defaultdict(list);statuses=defaultdict(Counter);previous=None;initial=None;maximum=0.;updates=0
        for line in (folder/name/'frames.jsonl').open():
            r=json.loads(line);d=r['body_diagnostics'].get('shoulder_projection',{})
            statuses[r['stage']][d.get('status','torso_missing')]+=1
            width=d.get('reference_width')
            if width is not None:
                if previous is not None:assert width>=previous
                if initial is None:initial=width
                if previous is not None and width>previous:updates+=1
                previous=width;maximum=max(maximum,width)
            if 'gap_ratio' in d:stages[r['stage']].append(d['gap_ratio'])
        result[name]=dict(reference_initial=initial,reference_maximum=maximum,reference_increases=updates,
            reference_never_shortened=True,stages={k:dict(gap_ratio_p10_p50_p90=np.percentile(v,[10,50,90]).tolist(),statuses=dict(statuses[k])) for k,v in stages.items()})
    (folder/'projection-audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='stages'} for k,v in result.items()},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args();run(a.folder)
