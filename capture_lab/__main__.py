import argparse
import importlib.metadata
import json
import platform
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from .capture import Camera
from .inference import DetectionGate, PersonDetector, SimCCModel
from .models import ROOT, catalog, fetch
from .retarget import LocalSender, packet_from_landmarks, FaceFilter
from .body3d import BodyRetarget
from .arm_width import measure_arm_widths


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def output_folder(label):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-%fZ')
    path = ROOT / 'results' / f'{stamp}-{label}'
    path.mkdir(parents=True)
    return path


def environment():
    try:
        gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
                              '--format=csv,noheader'], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        gpu = 'unavailable'
    packages = {name: importlib.metadata.version(name) for name in
                ('numpy', 'opencv-python', 'onnxruntime-gpu')}
    return {'os': platform.platform(), 'python': platform.python_version(),
            'gpu': gpu, 'packages': packages}


def stats(values):
    if not values:
        return None
    a = np.asarray(values)
    return {'count': len(values), 'mean': float(a.mean()), 'p50': float(np.percentile(a, 50)),
            'p95': float(np.percentile(a, 95)), 'max': float(a.max())}


def roi_for(image, roi):
    height, width = image.shape[:2]
    if roi is None:
        return [0, 0, width, height]
    x, y, w, h = roi
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
        raise ValueError(f'ROI {roi} is outside image {width}x{height}')
    return roi


def annotate(image, points, scores, threshold, lines, roi):
    canvas = image.copy()
    for i, (point, score) in enumerate(zip(points, scores)):
        if score < threshold or not np.isfinite(point).all():
            continue
        color = (0, 220, 255) if i < 23 else ((255, 170, 0) if i < 91 else (80, 255, 80))
        cv2.circle(canvas, tuple(np.rint(point).astype(int)), 2, color, -1)
    for a, b in [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12)]:
        if min(scores[a], scores[b]) >= threshold and np.isfinite(points[[a, b]]).all():
            cv2.line(canvas, tuple(np.rint(points[a]).astype(int)), tuple(np.rint(points[b]).astype(int)), (0, 220, 255), 2)
    x, y, w, h = [int(round(v)) for v in roi]
    cv2.rectangle(canvas, (x, y), (x+w-1, y+h-1), (255, 255, 255), 1)
    for i, line in enumerate(lines):
        cv2.putText(canvas, line, (12, 24+i*24), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
    return canvas


def part_coverage(scores, threshold):
    # Model scores are not calibrated probabilities or accuracy measurements.
    return {name: float((scores[indices] >= threshold).mean()) for name, indices in {
        'upper_body': slice(0, 11), 'face': slice(23, 91),
        'left_hand': slice(91, 112), 'right_hand': slice(112, 133)}.items()}


def benchmark(args):
    if args.observation_block==1: args.observation_stride=1
    output = output_folder(args.model)
    print(f'Results: {output}', flush=True)
    report = {'status': 'running', 'environment': environment(), 'arguments': vars(args),
              'scope': '2D face diagnostic with optional learned 3D body (--body3d). Single person; no identity tracking. Approximate retargeting.',
              'latency_note': 'Inference call includes tensor upload/output readback. Camera age starts AFTER capture read, not exposure. No end-to-end/display latency claim.',
              'quality_note': 'Confidence coverage is not measured accuracy. Synthetic input is performance-only.'}
    write_json(output / 'report.json', report)
    model = body_model = detector = camera = video = sender = gaze = None
    body_retarget = BodyRetarget(args.observation_block,args.observation_stride,args.arm_depth_mode)
    face_filter = FaceFilter(args.observation_block,args.observation_stride)
    from .face_distance import FaceDistance
    face_distance=FaceDistance(args.observation_block,args.observation_stride,args.face_distance_filter)
    from .head_pose import HeadPose
    head_pose=HeadPose(args.head_pitch_gain,args.mouth_lip_depth_scale) if args.head_pose_mode=="pnp" else None
    rows = []
    try:
        if args.unity_port:
            sender = LocalSender(args.unity_port)
        model = SimCCModel(args.model, output)
        if args.gaze:
            from .gaze import IrisGaze
            gaze=IrisGaze(output,args.observation_block,args.observation_stride,args.gaze_reference)
        if args.body3d:
            body_model = SimCCModel('rtmw3d-x-384', output)
            body_model.refine_body_peaks=not args.integer_body_peaks
            report['body_model'] = body_model.identity
            report['body_note'] = 'Learned relative depth; XY scale uses nominal 0.36m shoulder span. Not metric ground truth.'
        report['model'] = model.identity
        # Warm the pose network even if the camera initially contains no person.
        dummy = np.zeros((args.height, args.width, 3), np.uint8)
        for _ in range(3):
            model.predict(dummy, [0, 0, args.width, args.height])
            if body_model:
                body_model.predict(dummy,[0,0,args.width,args.height])
        report['initialization_pose_warmup_calls'] = 3
        gate = DetectionGate()
        if args.source != 'synthetic' and args.roi is None and not args.fixed_roi:
            detector = PersonDetector(output)
            report['detector'] = detector.identity
        if args.source == 'camera':
            camera = Camera(args.camera, args.width, args.height, args.fps, args.backend)
            camera.__enter__()
            report['camera'] = camera.metadata
        elif args.source == 'video':
            if not args.video:
                raise ValueError('--video is required for source=video')
            video = cv2.VideoCapture(args.video)
            if not video.isOpened():
                raise RuntimeError(f'Cannot open video: {args.video}')
        last_sequence = -1
        previous_points = previous_scores = None
        previous_time = None
        last_acquired = None
        with (output / 'frames.jsonl').open('w', encoding='utf-8') as log:
            for index in range(args.warmup + args.frames):
                if camera:
                    frame = camera.mailbox.next(after=last_sequence)
                    skipped = max(0, frame.sequence-last_sequence-1) if last_sequence >= 0 else 0
                    last_sequence = frame.sequence
                    image, acquired = frame.image, frame.acquired
                elif video:
                    ok, image = video.read()
                    if not ok:
                        break
                    acquired = time.perf_counter()
                    skipped = 0
                else:
                    image = np.zeros((args.height, args.width, 3), dtype=np.uint8)
                    acquired = time.perf_counter()
                    skipped = 0
                roi = roi_for(image, args.roi)
                detect_ms, person_score = 0., None
                if detector:
                    roi, person_score, detect_ms = detector.detect(image)
                    roi = gate.update(roi)
                if roi is not None:
                    points, scores, timing = model.predict(image, roi)
                    pose_executed = True
                else:
                    points = np.full((133, 2), np.nan)
                    scores = np.zeros(133)
                    timing = {'preprocess_ms': 0., 'inference_call_ms': 0., 'postprocess_ms': 0., 'pipeline_ms': 0.}
                    pose_executed = False
                timing['detector_ms'] = detect_ms
                timing['pipeline_ms'] += detect_ms
                body_xy = body_scores = None
                timing['body3d_ms'] = 0.
                if body_model and roi is not None:
                    body_xy, body_scores, body_timing = body_model.predict(image,roi)
                    # Out-of-frame landmarks (notably seated hips) are not observed.
                    inside = (body_xy[:,0]>=0)&(body_xy[:,0]<image.shape[1])&(body_xy[:,1]>=0)&(body_xy[:,1]<image.shape[0])
                    body_scores = np.where(inside,body_scores,0)
                    timing['body3d_ms'] = body_timing['pipeline_ms']
                    timing['pipeline_ms'] += timing['body3d_ms']
                if sender:
                    timing['gaze_ms']=0.
                    packet = packet_from_landmarks(points, scores, index, args.threshold)
                    timing["head_pose_ms"]=0.
                    if head_pose:
                        pose_start=time.perf_counter()
                        head_pose.update(points,scores,packet,(image.shape[1],image.shape[0]))
                        timing["head_pose_ms"]=(time.perf_counter()-pose_start)*1000
                        timing["pipeline_ms"]+=timing["head_pose_ms"]
                    if gaze:
                        gaze.update(image,points,scores,packet,time.perf_counter())
                        timing['gaze_ms']=gaze.diagnostics['elapsed_ms']
                        timing['pipeline_ms']+=timing['gaze_ms']
                    face_filter.update(packet,time.perf_counter())
                    distance_start=time.perf_counter()
                    face_distance.update(points,scores,packet,distance_start)
                    timing['face_distance_ms']=(time.perf_counter()-distance_start)*1000
                    timing['pipeline_ms']+=timing['face_distance_ms']
                    if body_model:
                        packet = body_retarget.update(packet,body_xy,body_scores,
                            body_model.depth if body_xy is not None else None,body_model.depth_scores,
                            image_size=(image.shape[1],image.shape[0]),
                            reference_xy=points,reference_scores=scores)
                    sender.send(packet)
                done = time.perf_counter()
                row = {'frame': index, 'sequence': last_sequence if camera else index,
                       'image_size':[image.shape[1],image.shape[0]],
                       'pose_executed': pose_executed, 'person_score': person_score,
                       **timing, 'skipped_camera_frames': skipped,
                       'capture_read_to_result_ms': (done-acquired)*1000 if camera else None,
                       'coverage': part_coverage(scores, args.threshold)}
                if sender and body_model:
                    if gaze: row['gaze']=gaze.diagnostics
                    row['face_distance']=face_distance.diagnostics
                    if head_pose:row['head_pose']=head_pose.diagnostics
                    row['mouth_corner_reference']=None if face_filter.corner_neutral is None else face_filter.corner_neutral.tolist()
                    row['mouth_bow_reference']=face_filter.bow_neutral
                    row['body_decode']=body_model.decode_diagnostics if body_xy is not None else None
                    if args.landmarks:
                        width_start=time.perf_counter()
                        # Diagnostic only: no unvalidated pixel-width cue drives bones.
                        face_scale=body_retarget.scale if body_retarget.diagnostics.get('geometry_scale_source')=='face' else None
                        row['arm_image_width']=measure_arm_widths(image,body_xy,body_scores,face_scale)
                        row['arm_image_width_ms']=(time.perf_counter()-width_start)*1000
                    row['body_tracking'] = {key: packet[key] for key in ('torsoTracked','leftArmTracked','rightArmTracked','torsoYaw','torsoPitch')}
                    row['body_diagnostics'] = body_retarget.diagnostics
                    if args.landmarks:
                        row['sent_packet'] = packet
                if previous_time is not None:
                    row['result_interval_ms'] = (done-previous_time)*1000
                if camera and last_acquired is not None:
                    row['capture_interval_per_sequence_ms'] = (acquired-last_acquired[1])*1000 / (last_sequence-last_acquired[0])
                if previous_points is not None:
                    visible = (scores >= args.threshold) & (previous_scores >= args.threshold)
                    visible &= np.isfinite(points).all(axis=1) & np.isfinite(previous_points).all(axis=1)
                    # Motion plus noise. Only a separately marked static clip can evaluate jitter.
                    row['interframe_displacement_px'] = float(np.linalg.norm(points[visible]-previous_points[visible], axis=1).mean()) if visible.any() else None
                if args.landmarks:
                    row['points_xy'] = [[float(v) if np.isfinite(v) else None for v in p] for p in points]
                    row['scores'] = [float(v) for v in scores]
                    if body_xy is not None:
                        row['body_xy'] = [[float(v) if np.isfinite(v) else None for v in p] for p in body_xy]
                        row['body_scores'] = [float(v) for v in body_scores]
                        row['body_depth'] = [float(v) if np.isfinite(v) else None for v in body_model.depth]
                        row['body_depth_scores'] = [float(v) for v in body_model.depth_scores]
                if index >= args.warmup:
                    rows.append(row)
                    log.write(json.dumps(row, allow_nan=False)+'\n')
                previous_points, previous_scores, previous_time = points, scores, done
                if camera:
                    last_acquired = last_sequence, acquired
                if args.preview:
                    display = annotate(image, points, scores, args.threshold,
                                       [f'{args.model} | CUDA | 2D diagnostic',
                                        f'Pipeline {timing["pipeline_ms"]:.1f} ms | frame {index}',
                                        ('Person detected' if pose_executed else 'No person - pose suppressed') + ' | Q / Esc: stop'],
                                       roi if roi is not None else [0, 0, image.shape[1], image.shape[0]])
                    if body_model and sender:
                        cv2.putText(display,body_retarget.calibration.status,(12,125),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,255),2)
                    cv2.putText(display,f'Confirmation: mean {args.observation_block}, stride {args.observation_stride}',(12,150),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,255),2)
                    cv2.imshow('tanakacap capture lab', display)
                    key=cv2.waitKey(1) & 0xff
                    if key in (27, ord('q')):
                        break
                if args.snapshot and index == args.warmup:
                    canvas = annotate(image, points, scores, args.threshold,
                                      [f'{args.model} | CUDA | 2D diagnostic',
                                       'Person detected' if pose_executed else 'No person - pose suppressed'],
                                      roi if roi is not None else [0, 0, image.shape[1], image.shape[0]])
                    if not cv2.imwrite(str(output / 'diagnostic.png'), canvas):
                        raise RuntimeError('Could not save requested diagnostic snapshot')
                if index and index % 100 == 0:
                    print(f'{index} frames processed', flush=True)
        report['execution'] = model.finish()
        if gaze:
            report['gaze_execution']=gaze.finish()
            gaze=None
        model = None
        if body_model:
            report['body_execution'] = body_model.finish()
            body_model = None
        if detector:
            report['detector_execution'] = detector.finish()
            detector = None
        if not rows:
            raise RuntimeError('No measured frames after warmup')
        report['status'] = 'completed'
        report['measured_frames'] = len(rows)
        report['pose_frames'] = sum(row['pose_executed'] for row in rows)
        report['active_pose_timings'] = {key: stats([row[key] for row in rows if row['pose_executed']])
                                          for key in ('inference_call_ms', 'pipeline_ms')}
        report['inactive_detection_pipeline_ms'] = stats([row['pipeline_ms'] for row in rows
                                                          if not row['pose_executed']])
        report['timings'] = {key: stats([row[key] for row in rows if row.get(key) is not None])
                             for key in ('preprocess_ms', 'inference_call_ms', 'postprocess_ms', 'detector_ms',
                                         'body3d_ms','gaze_ms','pipeline_ms', 'capture_read_to_result_ms', 'result_interval_ms',
                                         'capture_interval_per_sequence_ms')}
        report['coverage'] = {key: stats([row['coverage'][key] for row in rows]) for key in rows[0]['coverage']}
        report['skipped_camera_frames'] = sum(row['skipped_camera_frames'] for row in rows)
        print(json.dumps({'status': report['status'], 'model': args.model, 'pipeline_ms': report['timings']['pipeline_ms'],
                          'execution': report['execution']}, indent=2), flush=True)
    except BaseException as exc:
        report['status'] = 'interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed'
        report['error'] = f'{type(exc).__name__}: {exc}'
        if model is not None:
            try:
                report['execution'] = model.finish()
            except Exception as profile_error:
                report['profile_error'] = str(profile_error)
        if detector is not None:
            try:
                report['detector_execution'] = detector.finish()
            except Exception as profile_error:
                report['detector_profile_error'] = str(profile_error)
        raise
    finally:
        if gaze:
            try: report['gaze_execution']=gaze.finish()
            except Exception as exc: report['gaze_profile_error']=str(exc)
        report['measured_frames'] = len(rows)
        report['pose_frames'] = sum(row['pose_executed'] for row in rows)
        report['body_rejection_counts'] = {part:dict(Counter(row['body_diagnostics'][part] for row in rows if 'body_diagnostics' in row))
                                           for part in ('torso','left','right')}
        report['body_held_frames'] = {key:sum(row.get('body_diagnostics',{}).get(key+'_state')=='held' for row in rows)
                                      for key in ('leftArm','rightArm','leftHand','rightHand')}
        if args.body3d and sender:
            write_json(output/'arm-calibration.json',dict(mode='continuous_supported_maximum',
                        lengths=body_retarget.automatic_lengths(),window_seconds=5,min_frames=10))
            write_json(output/'arm-calibration-status.json',dict(status=body_retarget.calibration.status,
                        rejection=body_retarget.calibration.rejection))
        if body_model:
            try:
                report['body_execution'] = body_model.finish()
            except Exception as exc:
                report['body_profile_error'] = str(exc)
        if sender:
            sender.close()
        if camera:
            camera.__exit__()
        if video:
            video.release()
        if args.preview:
            cv2.destroyAllWindows()
        write_json(output / 'report.json', report)


def probe(args):
    output = output_folder('camera')
    with Camera(args.camera, args.width, args.height, args.fps, args.backend) as camera:
        frames = []
        previous = -1
        for _ in range(args.frames):
            frame = camera.mailbox.next(after=previous)
            previous = frame.sequence
            frames.append((frame.sequence, frame.acquired))
        elapsed = frames[-1][1]-frames[0][1]
        measured_fps = (frames[-1][0]-frames[0][0])/elapsed
        result = {'environment': environment(), 'camera': camera.metadata,
                  'frame_shape': list(frame.image.shape), 'effective_read_fps': measured_fps,
                  'frames_observed': len(frames), 'images_saved': False,
                  'note': 'Capture read timing, not sensor exposure timestamps.'}
    write_json(output / 'report.json', result)
    print(json.dumps(result, indent=2))
    print(f'Results: {output}')


def main():
    parser = argparse.ArgumentParser(description='GPU capture evaluation (development only)')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('environment')
    downloader = commands.add_parser('fetch')
    downloader.add_argument('models', nargs='+', choices=list(catalog()))
    for command in ('benchmark', 'probe-camera'):
        sub = commands.add_parser(command)
        sub.add_argument('--camera', type=int, default=0)
        sub.add_argument('--width', type=int, default=1280)
        sub.add_argument('--height', type=int, default=720)
        sub.add_argument('--fps', type=int, default=30)
        sub.add_argument('--backend', choices=['dshow', 'msmf'], default='msmf')
        sub.add_argument('--frames', type=int, default=180)
        if command == 'benchmark':
            sub.add_argument('--model', choices=[k for k,v in catalog().items() if v.get('kind') != 'detector' and v.get('dimensions',2)==2], default='rtmw-l-384')
            sub.add_argument('--source', choices=['synthetic', 'camera', 'video'], default='synthetic')
            sub.add_argument('--video')
            sub.add_argument('--roi', nargs=4, type=int, metavar=('X', 'Y', 'W', 'H'))
            sub.add_argument('--fixed-roi', action='store_true', help='Skip person detection; diagnostic only, may predict on an empty scene')
            sub.add_argument('--warmup', type=int, default=20)
            sub.add_argument('--threshold', type=float, default=.3)
            sub.add_argument('--preview', action='store_true')
            sub.add_argument('--snapshot', action='store_true', help='Explicitly save one annotated diagnostic frame locally')
            sub.add_argument('--landmarks', action='store_true', help='Save numeric landmarks locally; never raw camera frames')
            sub.add_argument('--unity-port', type=int, help='Send experimental controls to Unity over loopback UDP')
            sub.add_argument('--observation-stride',type=int,choices=(1,3),default=1,help='1: overlapping means, 3: disjoint means (block size 3 only)')
            sub.add_argument('--observation-block',type=int,choices=(1,3),default=3,help='1: original confirmation; 3: three-frame means (stride controls overlap)')
            sub.add_argument('--body3d', action='store_true', help='Add RTMW3D body inference; keep the existing face model')
            sub.add_argument('--head-pose-mode',choices=['pnp','legacy'],default='pnp')
            sub.add_argument('--head-pitch-gain',type=float,default=1.8)
            sub.add_argument('--mouth-lip-depth-scale',type=float,default=1.5)
            sub.add_argument('--face-distance-filter',choices=['stable','legacy'],default='stable')
            sub.add_argument('--arm-depth-mode',choices=['legacy','front_projection'],default='legacy')
            sub.add_argument('--gaze',action='store_true',help='Experimental CUDA iris-driven eye rotation')
            sub.add_argument('--gaze-reference',choices=['contour','legacy'],default='contour',help='Legacy restores the previous ROI reference and eye flips')
            sub.add_argument('--integer-body-peaks',action='store_true',help='Restore integer body coordinate decoding for comparison')
    args = parser.parse_args()
    if hasattr(args, 'frames') and args.frames < 2:
        parser.error('--frames must be at least 2')
    if hasattr(args, 'warmup') and args.warmup < 0:
        parser.error('--warmup must be non-negative')
    if args.command == 'fetch':
        for name in args.models:
            print(f'Downloading {name}...', flush=True)
            print(json.dumps(fetch(name), indent=2), flush=True)
    elif args.command == 'environment':
        print(json.dumps(environment(), indent=2))
    elif args.command == 'probe-camera':
        probe(args)
    else:
        benchmark(args)


if __name__ == '__main__':
    main()
