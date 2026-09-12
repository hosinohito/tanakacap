"""Recorded-input face source comparison with shared ROI/body output and clock."""
import argparse
import copy
import json
import sys
from contextlib import ExitStack
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture_lab.comparison import SharedFace, load_take, images, dump, line, fingerprint, frame_mask
from capture_lab.inference import SimCCModel, PersonDetector
from capture_lab.person_region import PersonRegionTracker
from capture_lab.body3d import BodyRetarget


def run(take, output, limit=None, pose_comparison=False):
    meta, timeline = load_take(take)
    settings = json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    frozen = fingerprint(settings)
    output.mkdir(parents=True, exist_ok=False)
    report = dict(status='running', scope='Same recorded frames, timestamps, baseline ROI and body model output. Face/head/gaze/distance and body agreement reference use the selected XY; correction code/settings unchanged. Not live latency or ground-truth accuracy.',
                  source_video_sha256=meta['video_sha256'], source_timeline_sha256=meta['timeline_sha256'],
                  controls=frozen, partial_test=limit is not None, variants={})
    dump(output/'report.json', report)
    if pose_comparison:
        report['scope']='Same RTMW3D XY/Z, ROI, body and timestamps. Only head pitch and mouth contour solve differs: PnP/template lips versus learned Z. Other corrections unchanged. Not live latency or ground-truth accuracy.'
    face_model = None if pose_comparison else SimCCModel('rtmw-l-384', None, 'graph')
    body_model = SimCCModel('rtmw3d-x-384', None, 'graph')
    detector = PersonDetector(None, 'graph')
    tracker = PersonRegionTracker(detector, settings.get('detector_interval', 3))
    names = ('body3d','depth3d') if pose_comparison else ('separate', 'body3d')
    faces = {name: SharedFace(({**settings, 'head_pose_mode': 'depth3d' if name=='depth3d' else 'pnp'} if pose_comparison else settings), None, execution_mode='graph') for name in names}
    pose_timings = {name: [] for name in names}
    bodies = {name: BodyRetarget(settings['observation_block'], settings['observation_stride'],
                               settings['arm_depth_mode'], settings['shoulder_yaw_mode']) for name in names}
    metrics = {name: [] for name in names}
    try:
        with ExitStack() as stack:
            streams, replays = {}, {}
            for name in names:
                (output/name).mkdir()
                streams[name] = stack.enter_context((output/name/'frames.jsonl').open('w', encoding='utf-8'))
                replays[name] = stack.enter_context((output/name/'replay.jsonl').open('w', encoding='utf-8'))
            previous_time = None
            for clock, image in images(take, timeline, limit):
                index, now = clock['frame'], clock['time']
                roi, _, _ = tracker.update(image, now)
                xy = np.full((133,2), np.nan); scores = np.zeros(133)
                body_xy = body_scores = depth = depth_scores = None
                raw_body_xy, raw_body_scores = xy, scores
                if roi is not None:
                    if face_model is not None: xy, scores, _ = face_model.predict(image, roi)
                    raw_body_xy, raw_body_scores, _ = body_model.predict(image, roi)
                    if face_model is None: xy, scores = raw_body_xy, raw_body_scores
                    body_xy = raw_body_xy.copy()
                    body_scores = frame_mask(body_xy, raw_body_scores, image.shape[1::-1])
                    depth, depth_scores = body_model.depth.copy(), body_model.depth_scores.copy()
                tracker.observe(xy, scores)
                for name in names:
                    points, confidence = (xy, scores) if name == 'separate' else (raw_body_xy, raw_body_scores)
                    packet = faces[name].update(image, points, confidence, index, now, depth, depth_scores)
                    pose_timings[name].append(faces[name].pose_ms)
                    packet = bodies[name].update(packet, body_xy, body_scores, depth, depth_scores,
                                                now=now, image_size=image.shape[1::-1],
                                                reference_xy=points, reference_scores=confidence)
                    line(streams[name], {**clock, 'roi': roi, 'points_xy': points, 'scores': confidence,
                                        'depth': depth, 'depth_scores': depth_scores, 'pose_ms': faces[name].pose_ms,
                                        'sent_packet': packet, 'head_pose': faces[name].pose.diagnostics if faces[name].pose else None,
                                        'gaze': faces[name].gaze.diagnostics if faces[name].gaze else None})
                    line(replays[name], {'packet': packet, 'dt': 1/30 if previous_time is None else now-previous_time})
                    metrics[name].append(copy.deepcopy(packet))
                previous_time = now
                if index % 300 == 0:
                    print(f'{index+1}/{min(len(timeline),limit or len(timeline))}', flush=True)
        for name in names:
            rows = metrics[name]
            flags = ('faceTracked','gazeTracked','mouthContourTracked','faceDistanceTracked','torsoTracked','leftArmTracked','rightArmTracked')
            controls = ('headPitch','headYaw','headRoll','mouth','mouthWidth','mouthLeftCorner','mouthRightCorner','mouthShift','leftBlink','rightBlink','gazeYaw','gazePitch')
            report['variants'][name] = dict(status='complete', frames=len(rows),
                pose_ms=dict(mean=float(np.mean((pose_timings[name][30:] or pose_timings[name]))), p50=float(np.median((pose_timings[name][30:] or pose_timings[name])))),
                active_frames={flag: sum(bool(p.get(flag)) for p in rows) for flag in flags},
                control_ranges={key: np.percentile([p.get(key, 0.) for p in rows], [5,50,95]).tolist() for key in controls})
        report['models'] = dict(face=face_model.identity if face_model is not None else body_model.identity, body=body_model.identity, detector=detector.identity)
        if fingerprint(settings) != frozen:
            raise RuntimeError('Control source changed during comparison')
        report['status'] = 'complete'
    except BaseException as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        dump(output/'report.json', report)
    print(output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--take', type=Path, default=ROOT/'results/comparison-takes/20260911T235327-031115Z')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--pose-comparison', action='store_true')
    args = parser.parse_args()
    run(args.take, args.output.resolve(), args.limit, args.pose_comparison)
