"""Same recorded timeline, independent F off/on tracking, fixed other settings."""
import argparse
import json
import sys
from contextlib import ExitStack
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture_lab.comparison import SharedFace, load_take, images, dump, line, fingerprint, frame_mask, clean
from capture_lab.inference import SimCCModel, PersonDetector
from capture_lab.person_region import PersonRegionTracker
from capture_lab.body3d import BodyRetarget


def run(take, output, limit=None):
    meta, timeline = load_take(take)
    settings = json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    frozen = fingerprint(settings)
    output.mkdir(parents=True, exist_ok=False)
    names = ('F-OFF', 'F-ON')
    report = dict(status='running', partial_test=limit is not None,
                  scope='F detector CUDA Graph OFF vs ON. Same recorded images/timestamps, same model weights and correction settings, independent ROI/face/body temporal state. Each branch performs inference; no copied control tracks. Offline synchronized replay compares appearance, not processing speed or live latency.',
                  source_video_sha256=meta['video_sha256'], source_timeline_sha256=meta['timeline_sha256'],
                  controls=frozen, variants={name: {} for name in names})
    dump(output/'report.json', report)
    model = SimCCModel('rtmw3d-x-384', None, 'graph', preprocess_mode=settings['preprocess_mode'])
    detectors = {n: PersonDetector(None, 'graph', settings['detector_model'], detector_graph=n=='F-ON') for n in names}
    trackers = {n: PersonRegionTracker(detectors[n], settings['detector_interval']) for n in names}
    faces = {n: SharedFace(settings, None, execution_mode='graph') for n in names}
    bodies = {n: BodyRetarget(settings['observation_block'], settings['observation_stride'], settings['arm_depth_mode'], settings['shoulder_yaw_mode']) for n in names}
    different_packets = different_roi = count = 0
    try:
        with ExitStack() as stack:
            replays, records = {}, {}
            for name in names:
                (output/name).mkdir()
                replays[name] = stack.enter_context((output/name/'replay.jsonl').open('w', encoding='utf-8'))
                records[name] = stack.enter_context((output/name/'frames.jsonl').open('w', encoding='utf-8'))
            previous = None
            for clock, image in images(take, timeline, limit):
                index, now = clock['frame'], clock['time']
                packets, rois = {}, {}
                for name in names:
                    roi, score, _ = trackers[name].update(image, now)
                    xy = np.full((133, 2), np.nan); scores = np.zeros(133)
                    body_xy = body_scores = depth = depth_scores = None
                    if roi is not None:
                        xy, scores, _ = model.predict(image, roi)
                        body_xy = xy.copy()
                        body_scores = frame_mask(xy, scores, image.shape[1::-1])
                        depth, depth_scores = model.depth.copy(), model.depth_scores.copy()
                    trackers[name].observe(xy, scores)
                    packet = faces[name].update(image, xy, scores, index, now, depth, depth_scores)
                    packet = bodies[name].update(packet, body_xy, body_scores, depth, depth_scores,
                                                now=now, image_size=image.shape[1::-1], reference_xy=xy, reference_scores=scores)
                    row = dict(**clock, roi=roi, detector_score=score, sent_packet=packet)
                    line(records[name], row)
                    line(replays[name], dict(packet=packet, dt=1/30 if previous is None else now-previous))
                    packets[name], rois[name] = clean(packet), clean(roi)
                different_packets += packets[names[0]] != packets[names[1]]
                different_roi += rois[names[0]] != rois[names[1]]
                previous = now
                count += 1
                if count % 300 == 0: print(f'{count}/{limit or len(timeline)}', flush=True)
        report.update(status='complete', observations=count, unequal_packet_frames=different_packets,
                      unequal_roi_frames=different_roi, models=dict(body=model.identity, detectors={n: d.identity for n,d in detectors.items()}))
        for name in names: report['variants'][name] = dict(frames=count, detector_graph=name=='F-ON')
        if fingerprint(settings) != frozen: raise RuntimeError('Control code changed during comparison')
    except BaseException as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        dump(output/'report.json', report)
    print(json.dumps({k: report[k] for k in ('status','observations','unequal_packet_frames','unequal_roi_frames')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--take', type=Path, default=ROOT/'results/comparison-takes/20260911T235327-031115Z')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    run(args.take.resolve(), args.output.resolve(), args.limit)
