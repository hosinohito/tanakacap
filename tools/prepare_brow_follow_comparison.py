"""Identical packets and demo avatar; only adaptive eyebrow following changes."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'results/brow-demo/replay.jsonl'
    replay=source.read_bytes()
    frames=len(replay.splitlines())
    output=ROOT/'results/comparisons/brow-follow'
    output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name,extra in [('brow-direct',['--no-adaptive-brow-follow']),('brow-adaptive',[])]:
        folder=output/name;folder.mkdir()
        (folder/'replay.jsonl').write_bytes(replay)
        variants[name]=dict(frames=frames,player_args=[
            '--avatar',str(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap'),
            '--use-demo-shape-keys','--check-brow-sides',*extra])
    report=dict(status='complete',variants=variants,source=str(source),
        packet_sha256=hashlib.sha256(replay).hexdigest(),
        scope='Identical 30-second recording controls, PnP, brow gain 2, four-frame gate and independent demo eyebrow shapes. Left direct eyebrow transfer; right adaptive eyebrow following. Head/mouth/blink controls and render settings unchanged. Offline 30fps replay, not inference latency.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Identical packets:',frames)

if __name__=='__main__':main()
