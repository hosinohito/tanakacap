"""Same demo/controls; compare no additional exaggeration with demo maximum."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'results/brow-demo/replay.jsonl';data=source.read_bytes()
    output=ROOT/'results/comparisons/facial-exaggeration';output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name,extra in [('normal',['--comparison-neutral-exaggeration']),('exaggerated',[])]:
        folder=output/name;folder.mkdir();(folder/'replay.jsonl').write_bytes(data)
        variants[name]=dict(frames=len(data.splitlines()),player_args=[
            '--avatar',str(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap'),
            '--use-demo-shape-keys','--check-brow-sides',*extra])
    report=dict(status='complete',variants=variants,packet_sha256=hashlib.sha256(data).hexdigest(),
        scope='Same 30-second recording, PnP, brow gain 2, adaptive independent brows, same demo avatar and completed runtime mouth keys. Left additional exaggeration 0 for all parts; right demo maximum 1 for brow/gaze/eyelids/mouth. Both use current implementation; baseline is not a frozen old Player. Offline 30fps, not inference latency.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(len(data.splitlines()),'identical packets')

if __name__=='__main__':main()
