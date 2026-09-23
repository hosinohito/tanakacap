"""Compare per-part wire targets against the real Player's composed targets."""
import argparse,json
from pathlib import Path
import numpy as np

def run(folder):
    meta=json.loads((folder/'session.json').read_text(encoding='utf-8'))
    wire=[json.loads(line)['packet'] for line in (folder/'wire.jsonl').read_text().splitlines()]
    renders=[json.loads(line) for line in (folder/'player-hands.jsonl').read_text().splitlines()]
    samples={(p['id'],w['frameId']):p for w in wire for p in w['parts']}
    checked=mismatches=0;worst=0.
    for row in renders:
        for part in row['parts']:
            if part['state']!='valid' or part['id'] not in ('left_palm','right_palm','left_fingers','right_fingers'):continue
            source=samples.get((part['id'],part['frameId']))
            if not source or source['state']!='valid':continue
            for key,value in source['values'].items():
                actual=row['target'][key]
                if isinstance(value,dict):
                    value=[value[k] for k in 'xyz'];actual=[actual[k] for k in 'xyz']
                error=float(np.max(np.abs(np.asarray(value,float)-np.asarray(actual,float))))
                worst=max(worst,error);checked+=1
                if error>1e-4:mismatches+=1
    windows={}
    for center in ((6,15) if meta["source"]=="video" else ()):
        group=[r for r in renders if r['target'] and abs(r['target']['sequence']/30-center)<=.5 and r['live']]
        info={}
        for side in ('left','right'):
            normals=[list(r[side+'Normal'].values()) for r in group]
            if not normals:continue
            array=np.array(normals);array/=np.linalg.norm(array,axis=1)[:,None]
            info[side]=dict(normal_span_degrees=float(np.degrees(np.arccos(np.clip(array@array.T,-1,1))).max()),
                            twist_range=[min(r[side+'Twist'] for r in group),max(r[side+'Twist'] for r in group)],
                            finger_max_degrees=float(np.max([r[side+'Fingers'] for r in group])))
        windows[str(center)]=info
    result=dict(status=meta['status'],wire_packets=len(wire),render_rows=len(renders),
                checked_fields=checked,mismatched_fields=mismatches,max_numeric_error=worst,
                windows=windows,window_note='Frame index / 30 estimates source video seconds; not applicable to camera dropped frames.',
                scope='Per-part frame IDs and valid fields only; float conversion tolerance 1e-4. This does not validate capture accuracy.')
    (folder/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not checked or mismatches:raise RuntimeError('No validated fields or wire/receiver mismatch')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    run(p.parse_args().folder)
