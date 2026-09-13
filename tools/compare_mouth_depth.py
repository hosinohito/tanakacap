"""Recompute only mouth contours from saved RTMW3D observations, then replay."""
import argparse
import copy
import json
import sys
import time
from contextlib import ExitStack
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanakacap.comparison import dump, line, fingerprint
from tanakacap.models import sha256
from tanakacap.retarget import packet_from_landmarks, FaceFilter
from tanakacap.head_pose import HeadPose
from tanakacap.head_pose3d import PnPPitchDepthMouth

MOUTH = ('mouthLeftCorner', 'mouthRightCorner', 'mouthBow', 'mouthShift', 'mouthContourTracked')


def run(source, output):
    parent = json.loads((source.parent.parent/'report.json').read_text(encoding='utf-8'))
    if parent['status'] != 'complete':
        raise ValueError('A completed source comparison is required')
    settings = json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    models = {'mouth-z': PnPPitchDepthMouth(settings['head_pitch_gain']),
              'mouth-no-z': HeadPose(settings['head_pitch_gain'], settings['mouth_lip_depth_scale'])}
    filters = {name: FaceFilter(settings['observation_block'], settings['observation_stride']) for name in models}
    output.mkdir(parents=True, exist_ok=False)
    report = dict(status='running', partial_test=False, variants={}, controls=fingerprint(settings),
                  source=str(source), source_sha256=sha256(source),
                  source_video_sha256=parent['source_video_sha256'],
                  scope='Saved identical RTMW3D observations and timestamps. Only four mouth contour controls and their validity differ. Head, eyes, opening/width, body, arms and fingers are fixed recorded controls. No-Z uses existing PnP/template frontal correction, not learned Z; it is not raw uncorrected image XY. Mouth emphasis 0. Offline, not latency or accuracy proof.')
    dump(output/'report.json', report)
    metrics = {name: [] for name in models}
    elapsed = {name: [] for name in models}
    pitch_difference = 0.
    previous = None
    try:
        with ExitStack() as stack:
            streams = {}
            for name in models:
                (output/name).mkdir()
                streams[name] = stack.enter_context((output/name/'replay.jsonl').open('w', encoding='utf-8'))
            with source.open(encoding='utf-8') as records:
                for record in records:
                    row = json.loads(record)
                    xy = np.asarray(row['points_xy'], float)
                    scores = np.asarray(row['scores'], float)
                    packets = {}
                    for name, model in models.items():
                        packet = packet_from_landmarks(xy, scores, row['frame'])
                        start = time.perf_counter()
                        extra = dict(depth=row['depth'], depth_scores=row['depth_scores']) if name == 'mouth-z' else {}
                        model.update(xy, scores, packet, (1280, 720), **extra)
                        elapsed[name].append((time.perf_counter()-start)*1000)
                        filters[name].update(packet, row['time'])
                        packets[name] = packet
                        # Keep every other field byte-for-byte equivalent across variants.
                        sent = copy.deepcopy(row['sent_packet'])
                        sent.update({key: packet.get(key, 0.) for key in MOUTH})
                        line(streams[name], dict(packet=sent, dt=1/30 if previous is None else row['time']-previous))
                        metrics[name].append({key: packet.get(key, 0.) for key in MOUTH})
                    pitch_difference = max(pitch_difference, abs(packets['mouth-z']['headPitch']-packets['mouth-no-z']['headPitch']))
                    previous = row['time']
        for name, rows in metrics.items():
            # Only compare adjacent valid observations; this includes intentional expressions.
            active = np.array([r['mouthContourTracked'] for r in rows], bool)
            steps = active[1:] & active[:-1]
            report['variants'][name] = dict(frames=len(rows), active_frames=int(active.sum()),
                pose_ms_mean=float(np.mean(elapsed[name][30:])),
                adjacent_valid_step_p95={key: float(np.percentile(np.abs(np.diff([r[key] for r in rows]))[steps], 95)) if steps.any() else None for key in MOUTH[:-1]})
        report.update(status='complete', head_pitch_max_difference=pitch_difference)
        if pitch_difference != 0:
            raise AssertionError('Mouth mode changed head pitch')
    except BaseException as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        dump(output/'report.json', report)
    print(json.dumps({k: v for k, v in report.items() if k in ('status','variants','head_pitch_max_difference')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'results/comparisons/face-depth-trial/body3d/frames.jsonl')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source.resolve(), args.output.resolve())
