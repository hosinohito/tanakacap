"""Same auto-custom avatar and controls; compare zero and maximum exaggeration."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'results/brow-demo/replay.jsonl';data=source.read_bytes()
    output=ROOT/'results/comparisons/facial-exaggeration';output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name,value in [('normal','0'),('exaggerated','1')]:
        extra=[arg for part in ('brow','eye','eyelid','mouth') for arg in ('--'+part+'-exaggeration',value)]
        folder=output/name;folder.mkdir();(folder/'replay.jsonl').write_bytes(data)
        variants[name]=dict(frames=len(data.splitlines()),player_args=[
            '--avatar',str(ROOT/'builds/player/avatars/haolan.tcap'),
            '--expression-mode','auto-custom','--check-brow-sides',*extra])
    report=dict(status='complete',variants=variants,packet_sha256=hashlib.sha256(data).hexdigest(),
        scope='Same 30-second recording, PnP, brow gain 2, adaptive independent brows, same auto-custom avatar and completed runtime mouth keys. Left additional exaggeration 0 for all parts; right maximum 1 for brow/gaze/eyelids/mouth. Both use current implementation; baseline is not a frozen old Player. Offline 30fps, not inference latency.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(len(data.splitlines()),'identical packets')

if __name__=='__main__':main()
