"""Independent precision runs on the same recording; no live camera."""
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture_lab.comparison import SharedFace, load_take, images, dump, line, fingerprint, frame_mask
from capture_lab.inference import SimCCModel, PersonDetector
from capture_lab.person_region import PersonRegionTracker
from capture_lab.body3d import BodyRetarget


def run(args):
    meta, timeline = load_take(args.take)
    settings = json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    path = output/'report.json'
    report = json.loads(path.read_text()) if path.exists() else dict(
        status='running', source_video_sha256=meta['video_sha256'],
        source_timeline_sha256=meta['timeline_sha256'], source_size=meta['size'], controls=fingerprint(settings), variants={},
        scope='Same recorded timeline; independent inference and temporal state. All parts ON, F ON, correction settings fixed. Synchronized avatar replay does not show inference latency.')
    if report['controls'] != fingerprint(settings):
        raise ValueError('Comparison controls changed')
    if report['source_video_sha256'] != meta['video_sha256'] or report['source_timeline_sha256'] != meta['timeline_sha256']:
        raise ValueError('Comparison recording changed')
    folder = output/args.name
    folder.mkdir(exist_ok=False)
    report['status'] = 'running'
    dump(path, report)
    profile = folder/'profiles'
    profile.mkdir()
    model = SimCCModel('rtmw3d-x-384', profile, args.mode, preprocess_mode=settings['preprocess_mode'])
    detector = PersonDetector(profile, args.mode, settings['detector_model'], detector_graph=True)
    tracker = PersonRegionTracker(detector, settings['detector_interval'])
    face = SharedFace(settings, profile, execution_mode=args.mode)
    body = BodyRetarget(settings['observation_block'], settings['observation_stride'], settings['arm_depth_mode'], settings['shoulder_yaw_mode'])
    timings = []
    try:
        with (folder/'replay.jsonl').open('w', encoding='utf-8') as replay, (folder/'frames.jsonl').open('w', encoding='utf-8') as records:
            previous = None
            for clock, image in images(args.take, timeline, args.limit):
                start = time.perf_counter()
                index, now = clock['frame'], clock['time']
                roi, score, _ = tracker.update(image, now)
                xy = np.full((133, 2), np.nan); scores = np.zeros(133)
                body_xy = body_scores = depth = depth_scores = None
                if roi is not None:
                    xy, scores, _ = model.predict(image, roi)
                    if not np.isfinite(xy).all() or not np.isfinite(scores).all():
                        raise ValueError('Non-finite model result')
                    body_xy = xy.copy()
                    body_scores = frame_mask(xy, scores, image.shape[1::-1])
                    depth, depth_scores = model.depth.copy(), model.depth_scores.copy()
                    if not np.isfinite(depth).all(): raise ValueError('Non-finite depth')
                tracker.observe(xy, scores)
                packet = face.update(image, xy, scores, index, now, depth, depth_scores)
                packet = body.update(packet, body_xy, body_scores, depth, depth_scores,
                                     now=now, image_size=image.shape[1::-1], reference_xy=xy, reference_scores=scores)
                elapsed = (time.perf_counter()-start)*1000
                timings.append(elapsed)
                line(records, dict(**clock, roi=roi, xy=xy, scores=scores, depth=depth, sent_packet=packet, pipeline_ms=elapsed))
                line(replay, dict(packet=packet, dt=1/30 if previous is None else now-previous))
                previous = now
                if len(timings)%300 == 0: print(args.name, len(timings), flush=True)
        execution = dict(body=model.finish(), detector=detector.finish(), gaze=face.gaze.finish() if face.gaze else None)
        stable = timings[30:]
        report['variants'][args.name] = dict(frames=len(timings), mode=args.mode, execution=execution,
            timing_scope='Inference + CPU controls, excluding decode/JSON/Unity/OBS; first 30 observations excluded',
            pipeline_ms=dict(mean=float(np.mean(stable)), p50=float(np.median(stable)), p95=float(np.percentile(stable,95))),
            models=dict(body=model.identity, detector=detector.identity))
        if report['controls'] != fingerprint(settings): raise ValueError('Controls changed during inference')
        report['status'] = 'complete'
    except BaseException as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        dump(path, report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--take', type=Path, default=ROOT/'results/comparison-takes/20260911T235327-031115Z')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--mode', choices=('graph','graph-fp16'), required=True)
    parser.add_argument('--limit', type=int)
    run(parser.parse_args())
