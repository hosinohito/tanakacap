import argparse
import importlib.metadata
import json
import platform
import subprocess
import time
from collections import Counter, deque
from contextlib import nullcontext
from itertools import count
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from .capture import Camera
from .inference import PersonDetector, SimCCModel
from .person_region import PersonRegionTracker
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


def parent_running(pid):
    # Only query our launcher's Player process; do not terminate unrelated processes.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle: return False
    try:
        code = wintypes.DWORD()
        return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
    finally:
        kernel.CloseHandle(handle)


def benchmark(args):
    if args.observation_block==1: args.observation_stride=1
    if getattr(args, 'head_only', False):
        from .head_only import run
        return run(args)
    if getattr(args, 'no_body', False): args.body3d=False
    if args.head_pose_mode in ('depth3d','pnp_depthmouth') and args.face_source != 'body3d':
        raise ValueError('depth3d requires --face-source body3d')
    face_name = 'rtmw3d-x-384' if args.face_source == 'body3d' else args.model
    output = None if args.no_log else output_folder(face_name)
    print(f'Results: {output}', flush=True)
    report = {'status': 'running', 'environment': environment(), 'arguments': vars(args),
              'scope': '2D face diagnostic with optional learned 3D body (--body3d). Single person; no identity tracking. Approximate retargeting.',
              'latency_note': 'Inference call includes tensor upload/output readback. Camera age starts AFTER capture read, not exposure. No end-to-end/display latency claim.',
              'quality_note': 'Confidence coverage is not measured accuracy. Synthetic input is performance-only.'}
    if output is not None: write_json(output / 'report.json', report)
    model = body_model = detector = camera = video = sender = gaze = None
    body_retarget = BodyRetarget(args.observation_block,args.observation_stride,args.arm_depth_mode,args.shoulder_yaw_mode)
    face_filter = FaceFilter(args.observation_block,args.observation_stride)
    from .face_distance import FaceDistance
    face_distance=FaceDistance(args.observation_block,args.observation_stride,args.face_distance_filter)
    from .head_pose import HeadPose
    head_pose=HeadPose(args.head_pitch_gain,args.mouth_lip_depth_scale) if args.head_pose_mode=="pnp" else None
    if args.head_pose_mode in ('depth3d','pnp_depthmouth'):
        from .head_pose3d import HeadPose3D, PnPPitchDepthMouth
        head_pose = (PnPPitchDepthMouth if args.head_pose_mode=='pnp_depthmouth' else HeadPose3D)(args.head_pitch_gain)
    rows = deque(maxlen=1) if args.no_log else []
    try:
        if args.unity_port:
            sender = LocalSender(args.unity_port)
        profile_output = None if getattr(args, 'no_ort_profile', False) else output
        execution = {} if args.inference_mode=='run' else dict(execution_mode=args.inference_mode)
        pose_execution={**execution}
        if args.gpu_decode:pose_execution['gpu_decode']=True
        if args.gpu_preprocess:pose_execution['gpu_preprocess']=True
        if args.preprocess_mode!='legacy': pose_execution['preprocess_mode']=args.preprocess_mode
        model = SimCCModel(face_name, profile_output, **pose_execution)
        report['face_source'] = args.face_source
        if args.gaze:
            from .gaze import IrisGaze
            gaze_execution={**execution}
            if args.batch_eyes:gaze_execution['batch_eyes']=True
            gaze=IrisGaze(profile_output,args.observation_block,args.observation_stride,args.gaze_reference, **gaze_execution)
        if args.body3d:
            body_model = model if args.face_source == 'body3d' else SimCCModel('rtmw3d-x-384', profile_output, **pose_execution)
            body_model.refine_body_peaks=not args.integer_body_peaks
            report['body_model'] = body_model.identity
            report['body_note'] = 'Learned relative depth; XY scale uses nominal 0.36m shoulder span. Not metric ground truth.'
        report['model'] = model.identity
        # Warm the pose network even if the camera initially contains no person.
        dummy = np.zeros((args.height, args.width, 3), np.uint8)
        for _ in range(3):
            model.predict(dummy, [0, 0, args.width, args.height])
            if body_model and body_model is not model:
                body_model.predict(dummy,[0,0,args.width,args.height])
        report['initialization_pose_warmup_calls'] = 3
        region_tracker = None
        if args.source != 'synthetic' and args.roi is None and not args.fixed_roi:
            detector_options = {} if args.detector_model == 'yolox-m-human' else {'name': args.detector_model}
            if args.detector_graph: detector_options['detector_graph']=True
            detector = PersonDetector(profile_output, **execution, **detector_options)
            report['detector'] = detector.identity
            region_tracker = PersonRegionTracker(detector, args.detector_interval)
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
        with (nullcontext(None) if args.no_log else (output / 'frames.jsonl').open('w', encoding='utf-8')) as log:
            for index in (count() if args.frames == 0 else range(args.warmup + args.frames)):
                iteration_start = time.perf_counter()
                if args.parent_pid and not parent_running(args.parent_pid): break
                if camera:
                    frame = camera.mailbox.next(after=last_sequence)
                    skipped = max(0, frame.sequence-last_sequence-1) if last_sequence >= 0 else 0
                    last_sequence = frame.sequence
                    image, acquired = frame.image, frame.acquired
                elif video:
                    ok, image = video.read()
                    if not ok and getattr(args,'loop_video',False):
                        video.set(cv2.CAP_PROP_POS_FRAMES,0)
                        if region_tracker: region_tracker.reset()
                        ok, image = video.read()
                    if not ok:
                        break
                    acquired = time.perf_counter()
                    skipped = 0
                else:
                    image = np.zeros((args.height, args.width, 3), dtype=np.uint8)
                    acquired = time.perf_counter()
                    skipped = 0
                read_done = time.perf_counter()
                roi = roi_for(image, args.roi)
                detect_ms, person_score = 0., None
                if detector:
                    stamp = acquired if camera else video.get(cv2.CAP_PROP_POS_FRAMES)/max(1.,video.get(cv2.CAP_PROP_FPS))
                    roi, person_score, detect_ms = region_tracker.update(image, stamp)
                if roi is not None:
                    points, scores, timing = model.predict(image, roi)
                    pose_executed = True
                else:
                    points = np.full((133, 2), np.nan)
                    scores = np.zeros(133)
                    timing = {'preprocess_ms': 0., 'inference_call_ms': 0., 'postprocess_ms': 0., 'pipeline_ms': 0.}
                    pose_executed = False
                if region_tracker: region_tracker.observe(points, scores)
                primary_ms = timing['pipeline_ms']
                timing['face_model_ms'] = 0. if body_model is model else primary_ms
                timing['face_body_shared'] = body_model is model
                timing['input_wait_read_ms'] = (read_done-iteration_start)*1000
                timing['detector_ms'] = detect_ms
                if region_tracker: timing.update(region_tracker.timing)
                timing['pipeline_ms'] += detect_ms
                body_xy = body_scores = None
                timing['body3d_ms'] = 0.
                if body_model and roi is not None:
                    if body_model is model:
                        body_xy, body_scores = points.copy(), scores.copy()
                        body_timing = {'pipeline_ms': primary_ms}
                    else:
                        body_xy, body_scores, body_timing = body_model.predict(image,roi)
                    # Out-of-frame landmarks (notably seated hips) are not observed.
                    inside = (body_xy[:,0]>=0)&(body_xy[:,0]<image.shape[1])&(body_xy[:,1]>=0)&(body_xy[:,1]<image.shape[0])
                    body_scores = np.where(inside,body_scores,0)
                    timing['body3d_ms'] = body_timing['pipeline_ms']
                    if body_model is not model: timing['pipeline_ms'] += timing['body3d_ms']
                if sender:
                    timing['gaze_ms']=0.
                    controls_start=time.perf_counter()
                    packet = packet_from_landmarks(points, scores, index, args.threshold)
                    timing['landmark_controls_ms']=(time.perf_counter()-controls_start)*1000
                    timing["head_pose_ms"]=0.
                    if head_pose:
                        pose_start=time.perf_counter()
                        pose_extra = dict(depth=model.depth if pose_executed else None, depth_scores=model.depth_scores if pose_executed else None) if args.head_pose_mode in ('depth3d','pnp_depthmouth') else {}
                        head_pose.update(points,scores,packet,(image.shape[1],image.shape[0]),**pose_extra)
                        timing["head_pose_ms"]=(time.perf_counter()-pose_start)*1000
                        timing["pipeline_ms"]+=timing["head_pose_ms"]
                    if gaze:
                        gaze.update(image,points,scores,packet,time.perf_counter())
                        timing['gaze_ms']=gaze.diagnostics['elapsed_ms']
                        timing['pipeline_ms']+=timing['gaze_ms']
                    filter_start=time.perf_counter()
                    face_filter.update(packet,time.perf_counter())
                    timing['face_filter_ms']=(time.perf_counter()-filter_start)*1000
                    distance_start=time.perf_counter()
                    face_distance.update(points,scores,packet,distance_start)
                    timing['face_distance_ms']=(time.perf_counter()-distance_start)*1000
                    timing['pipeline_ms']+=timing['face_distance_ms']
                    retarget_start=time.perf_counter()
                    if body_model:
                        packet = body_retarget.update(packet,body_xy,body_scores,
                            body_model.depth if body_xy is not None else None,body_model.depth_scores,
                            image_size=(image.shape[1],image.shape[0]),
                            reference_xy=points,reference_scores=scores)
                    timing['retarget_ms']=(time.perf_counter()-retarget_start)*1000
                    timing['pipeline_ms']+=timing['retarget_ms']
                    # Windows 3.11 perf_counter is system-wide QPC, shared with
                    # the Player's diagnostic-only QueryPerformanceCounter.
                    if getattr(args, 'no_body', False):
                        from .tracking_modes import suppress_body
                        suppress_body(packet)
                    packet['inputReadTime']=acquired
                    packet['inputSentTime']=time.perf_counter()
                    send_start=time.perf_counter()
                    sender.send(packet)
                    timing['send_ms']=(time.perf_counter()-send_start)*1000
                done = time.perf_counter()
                timing['read_to_send_ms']=(done-read_done)*1000
                accounted=sum(timing.get(k,0.) for k in ('face_model_ms','detector_ms','body3d_ms','gaze_ms','head_pose_ms','landmark_controls_ms','face_filter_ms','face_distance_ms','retarget_ms','send_ms'))
                timing['other_before_send_ms']=max(0.,timing['read_to_send_ms']-accounted)
                row = {'frame': index, 'sequence': last_sequence if camera else index,
                       'image_size':[image.shape[1],image.shape[0]],
                       'pose_executed': pose_executed, 'person_score': person_score,
                       'person_region': region_tracker.diagnostics if region_tracker else None,
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

                previous_points, previous_scores, previous_time = points, scores, done
                if camera:
                    last_acquired = last_sequence, acquired
                if args.preview:
                    display = annotate(image, points, scores, args.threshold,
                                       [f'{face_name} | CUDA | XY diagnostic',
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
                                      [f'{face_name} | CUDA | XY diagnostic',
                                       'Person detected' if pose_executed else 'No person - pose suppressed'],
                                      roi if roi is not None else [0, 0, image.shape[1], image.shape[0]])
                    if not cv2.imwrite(str(output / 'diagnostic.png'), canvas):
                        raise RuntimeError('Could not save requested diagnostic snapshot')
                row['diagnostics_preview_ms']=(time.perf_counter()-done)*1000
                row['iteration_ms']=(time.perf_counter()-iteration_start)*1000
                if index >= args.warmup and log is not None:
                    log.write(json.dumps(row, allow_nan=False)+'\n')
                # The following iteration's result_interval includes JSON serialization/write.
                if not args.no_log and index and index % 100 == 0:
                    print(f'{index} frames processed', flush=True)
        report['execution'] = model.finish()
        if body_model is model:
            report['body_execution'] = {**report['execution'], 'shared_with_face': True}
            body_model = None
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
        if args.no_log: return
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
                                         'capture_interval_per_sequence_ms','face_model_ms','input_wait_read_ms',
                                         'head_pose_ms','landmark_controls_ms','face_filter_ms','face_distance_ms',
                                         'retarget_ms','send_ms','read_to_send_ms','other_before_send_ms',
                                         'diagnostics_preview_ms','iteration_ms',
                                         'detector_preprocess_ms','detector_inference_call_ms','detector_postprocess_ms')}
        report['coverage'] = {key: stats([row['coverage'][key] for row in rows]) for key in rows[0]['coverage']}
        report['skipped_camera_frames'] = sum(row['skipped_camera_frames'] for row in rows)
        print(json.dumps({'status': report['status'], 'model': face_name, 'pipeline_ms': report['timings']['pipeline_ms'],
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
        if output is not None and args.body3d and sender:
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
        if output is not None: write_json(output / 'report.json', report)


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
            sub.add_argument('--no-log',action='store_true',help='No result files, snapshots or ORT profiling; bounded in-memory history')
            sub.add_argument('--no-ort-profile',action='store_true',help='Keep timing results but disable expensive ORT node traces')
            sub.add_argument('--head-only',action='store_true',help='Direct head pose with automatic CUDA head region detection; no expression/gaze/body networks')
            sub.add_argument('--head-roi-mode', choices=('auto','fixed'), default='auto', help='Head-only: auto acquisition/loss/recovery, or legacy fixed crop')
            sub.add_argument('--inference-mode',choices=('run','binding','graph'),default='run',help='Same CUDA models: legacy run, reusable GPU buffers, or CUDA graph replay')
            sub.add_argument('--no-body',action='store_true',help='Disable body network and all body/arm/hand/distance controls; retain face/head')
            sub.add_argument('--parent-pid',type=int,help='Stop when the avatar player exits (Windows)')
            sub.add_argument('--face-source', choices=('separate','body3d'), default='separate', help='Use the existing 2D face network or reuse RTMW3D XY for face/head/gaze')
            sub.add_argument('--batch-eyes',action='store_true')
            sub.add_argument('--preprocess-mode',choices=('legacy','crop'),default='legacy')
            sub.add_argument('--gpu-decode',action='store_true')
            sub.add_argument('--gpu-preprocess',action='store_true')
            sub.add_argument('--detector-graph',action='store_true')
            sub.add_argument('--detector-model', choices=('yolox-m-human','yolox-tiny-human'), default='yolox-m-human')
            sub.add_argument('--detector-interval', type=int, choices=(1,2,3), default=1)
            sub.add_argument('--model', choices=[k for k,v in catalog().items() if v.get('kind') != 'detector' and v.get('dimensions',2)==2], default='rtmw-l-384')
            sub.add_argument('--source', choices=['synthetic', 'camera', 'video'], default='synthetic')
            sub.add_argument('--video')
            sub.add_argument('--loop-video',action='store_true',help='Diagnostic stress loop; requires source=video and --no-log, no capture or recording')
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
            sub.add_argument('--head-pose-mode',choices=['pnp','legacy','depth3d','pnp_depthmouth'],default='pnp')
            sub.add_argument('--head-pitch-gain',type=float,default=1.8)
            sub.add_argument('--mouth-lip-depth-scale',type=float,default=1.5)
            sub.add_argument('--face-distance-filter',choices=['stable','legacy'],default='stable')
            sub.add_argument('--shoulder-yaw-mode',choices=['legacy','width_only','face_ratio'],default='legacy')
            sub.add_argument('--arm-depth-mode',choices=['legacy','front_projection'],default='legacy')
            sub.add_argument('--gaze',action='store_true',help='Experimental CUDA iris-driven eye rotation')
            sub.add_argument('--gaze-reference',choices=['contour','legacy'],default='contour',help='Legacy restores the previous ROI reference and eye flips')
            sub.add_argument('--integer-body-peaks',action='store_true',help='Restore integer body coordinate decoding for comparison')
    args = parser.parse_args()
    if hasattr(args, 'frames') and args.frames < 2 and not (args.command=='benchmark' and args.frames==0 and args.no_log):
        parser.error('--frames must be at least 2; 0 is unlimited with benchmark --no-log')
    if getattr(args,'no_log',False) and (args.landmarks or args.snapshot):
        parser.error('--no-log cannot be combined with --landmarks or --snapshot')
    if getattr(args,'loop_video',False) and (args.source!='video' or not args.no_log):
        parser.error('--loop-video requires --source video --no-log')
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
