"""Measure current UI defaults on recorded input; never open a camera or show footage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tanakacap.control_panel import DEFAULT, commands, close_player


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--frames', type=int, default=600)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--write-costs',action='store_true',help='Update the UI reference after all runs succeed')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    results = {}
    for mode in ('full', 'face_head', 'head_only', 'full_repeat'):
        config = dict(DEFAULT, source='video', video=str(a.video.resolve()),
                      mode='full' if mode=='full_repeat' else mode, expression='auto-custom')
        player_cmd, infer = commands(config, 39740, 39741)
        # Finite, unpaced inference for service-time measurement. Render stays Full HD 60.
        infer.remove('--no-log'); infer.remove('--loop-video')
        for flag, value in (('--frames',str(a.frames)),('--warmup','30'),('--inference-limit','0')):
            infer[infer.index(flag)+1] = value
        infer += ['--no-ort-profile']
        env = dict(os.environ, TANAKACAP_UI_PRECISION=config['precision'], PYTHONUTF8='1')
        with (a.output/(mode+'-player.log')).open('wb') as plog:
            player = subprocess.Popen(player_cmd, cwd=ROOT, stdout=plog, stderr=subprocess.STDOUT)
            try:
                time.sleep(8)
                if player.poll() is not None: raise RuntimeError('Player exited before benchmark')
                with (a.output/(mode+'.log')).open('wb') as log:
                    subprocess.run(infer, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   check=True, timeout=600)
            finally:
                close_player(player)
                try: player.wait(timeout=15)
                except subprocess.TimeoutExpired: player.terminate(); player.wait(timeout=15)
        log = (a.output/(mode+'.log')).read_text(encoding='utf-8', errors='replace')
        folder = Path(re.search(r'Results: ([^\r\n]+)',log)[1])
        report = json.loads((folder/'report.json').read_text(encoding='utf-8'))
        if report['status'] != 'completed': raise RuntimeError('Incomplete benchmark')
        results[mode] = dict(config=config, report=str(folder/'report.json'), timings=report['timings'])
        (a.output/'summary.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
        print(mode, report['timings']['read_to_send_ms'], flush=True)
    if a.write_costs: write_costs(a.output,a.video)


def write_costs(output,video):
    results=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    full=[results[k]['timings'] for k in ('full','full_repeat')]
    mean=lambda key:sum(r[key]['mean'] for r in full)/len(full)
    total=mean('read_to_send_ms')
    with video.open('rb') as stream:video_hash=hashlib.file_digest(stream,'sha256').hexdigest()
    samples=full[0]['read_to_send_ms']['count']
    costs=dict(source=(output.relative_to(ROOT)/'summary.json').as_posix(),
               scope=f'RTX 4090; current UI default FP16 (RTMW-L retains FP32), recorded 1280x720; Player configured Full HD 60, auto-custom, AA/window/Spout on; OBS receiver not verified. 30 warmup + {samples} samples per run, full repeated. Inference unpaced. Stage service time excludes video read, pacing, render work and logging.',
               video_sha256=video_hash,
               total_ms=total,parts={},modes={},valid_for_current_configuration=True,
               display_note='Default full-mode stage shares, not checkbox OFF savings; experiments and devices change costs.')
    for part,stage in [('body','body3d_ms'),('gaze','gaze_ms'),('detector','detector_ms')]:
        ms=mean(stage)
        costs['parts'][part]=dict(ms=ms,reference_tenths=int(ms/total*10+.5))
    head=results['head_only']['timings']['read_to_send_ms']['mean']
    for mode in ('full','face_head','head_only'):
        ms=total if mode=='full' else results[mode]['timings']['read_to_send_ms']['mean']
        costs['modes'][mode]=dict(ms=ms,reference_multiple=int(ms/head+.5))
    (ROOT/'docs/ui-part-costs.json').write_text(json.dumps(costs,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__': main()
