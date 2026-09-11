"""Summarize available replays, retaining observed-vs-held distinctions."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    result=[]
    for folder in sorted((ROOT/'results').glob('stability-20260911*')):
        rows=[json.loads(line) for line in (folder/'packets.jsonl').read_text().splitlines()]
        summary={'source':folder.name,'frames':len(rows),'parts':{}}
        for side in ('left','right'):
            for part in ('Arm','Hand'):
                key=side+part
                summary['parts'][key]={'active':sum(r['packet'].get(key+'Tracked',False) for r in rows),
                                       'held':sum(r['packet'].get(key+'Held',False) for r in rows)}
        for row in rows:
            packet=row['packet']
            assert len(json.dumps(packet).encode())<4096
            for field in ('leftElbow','leftWrist','rightElbow','rightWrist','leftHandNormal','rightHandNormal'):
                if field in packet: assert np.isfinite(list(packet[field].values())).all()
        result.append(summary)
    output=ROOT/'results'/'stability-summary.json'
    output.write_text(json.dumps({'scope':'Numerical replay continuity, not ground-truth accuracy','recordings':result},indent=2),encoding='utf-8')
    print(output)


if __name__=='__main__': main()
