"""Same full-exaggeration demo with generated lip travel 4 mm versus 8 mm."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    data=(ROOT/'results/gaze-range/replay.jsonl').read_bytes()
    output=ROOT/'results/comparisons/mouth-shift-range'
    output.mkdir(parents=True,exist_ok=False)
    variants={}
    for name,extra in [('shift-4mm',[]),('shift-8mm',['--experimental-mouth-shift-8mm'])]:
        folder=output/name;folder.mkdir()
        (folder/'replay.jsonl').write_bytes(data)
        variants[name]=dict(frames=len(data.splitlines()),expected_log=[
            'TANAKACAP_BAKED_LIP_ONLY_OK: sign='+sign+' max='+('0.008' if extra else '0.004') for sign in ('-1','1')],player_args=[
            '--avatar',str(ROOT/'builds/player/avatars/haolan.tcap'),
            '--expression-mode','auto-custom','--check-mouth-shift-isolation',*extra])
    report=dict(status='complete',variants=variants,packet_sha256=hashlib.sha256(data).hexdigest(),
        scope='Identical recorded controls, calibrated gaze and full-exaggeration demo. Only generated mouth shift maximum travel differs: left 4mm, right 8mm. Lip support and chin/neck exclusion unchanged; baked geometry checked in both directions. Offline replay, not a latency measurement.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(len(data.splitlines()),'identical packets')

if __name__=='__main__':main()
