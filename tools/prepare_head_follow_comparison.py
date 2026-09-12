"""Compare Unity head following with byte-identical recorded control packets."""
import json
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'results/comparisons/head-follow-input'
    output=ROOT/'results/comparisons/head-follow'
    report=json.loads((source/'report.json').read_text())
    if report['status']!='complete':raise ValueError('Inference incomplete')
    replay=(source/'source/replay.jsonl').read_bytes()
    rows=[json.loads(s) for s in replay.splitlines()]
    output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name,args in [('fixed',[]),('adaptive',['--adaptive-head-follow'])]:
        folder=output/name;folder.mkdir();(folder/'replay.jsonl').write_bytes(replay)
        variants[name]=dict(frames=len(rows),player_args=['--expression-mode','auto-custom',*args])
    result=dict(status='complete',variants=variants,source_report=str(source/'report.json'),
                packet_sha256=hashlib.sha256(replay).hexdigest(),
                scope='Same new 30-second face recording, size2d, FP16, all parts ON, existing 4-frame gate. Byte-identical controls and recorded clock; only Unity head following differs. Fixed rate 45 versus adaptive rate 6..45 over error 0..12 degrees. Both auto-custom expressions. Offline replay, not end-to-end latency.')
    (output/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Packets:',len(rows),'Face tracked:',sum(r['packet'].get('faceTracked',False) for r in rows))

if __name__=='__main__':main()
