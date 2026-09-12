"""Direct head pose with independent CUDA region acquisition and loss handling."""
from . import camera_display
from .live_status import LiveStatus
import json
import time
from contextlib import nullcontext
from itertools import count
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from .models import ROOT, sha256
from .inference import provider_summary
from .motion_gate import DirectionGate
from .retarget import LocalSender
from .capture import Camera
from .head_region import HeadRegionDetector, HeadRegionTracker

MODEL = ROOT / "models/head-mobilenetv3-small.onnx"
HASH = "e8ae4d932b3d13221638fc72e171603e020c6da28b770753f76146867f40e190"


def angles_from_rotation(matrix):
    r = np.asarray(matrix, dtype=float).reshape(3, 3)
    if not np.isfinite(r).all() or not np.allclose(r.T @ r, np.eye(3), atol=.01) or np.linalg.det(r) < .99:
        return None
    sy = np.hypot(r[0, 0], r[1, 0])
    pitch = np.arctan2(r[2, 1], r[2, 2]) if sy >= 1e-6 else np.arctan2(-r[1, 2], r[1, 1])
    yaw = np.arctan2(-r[2, 0], sy)
    roll = np.arctan2(r[1, 0], r[0, 0]) if sy >= 1e-6 else 0.
    # Image axes: x right, y down. Unity avatar is facing the camera.
    return np.degrees([pitch, yaw, roll])


class HeadOnlyModel:
    def __init__(self, profile_dir=None):
        if not MODEL.exists() or sha256(MODEL) != HASH:
            raise RuntimeError("Head-only model missing/hash mismatch. See docs/HEAD_ONLY.md")
        ort.preload_dlls(directory="")
        if "CUDAExecutionProvider" not in ort.get_available_providers():
            raise RuntimeError("Head-only requires CUDA; no CPU fallback")
        opt = ort.SessionOptions()
        opt.intra_op_num_threads = 2
        opt.log_severity_level = 3
        opt.enable_profiling = profile_dir is not None
        self.profiling = opt.enable_profiling
        if profile_dir: opt.profile_file_prefix = str(profile_dir / "head-only")
        self.session = ort.InferenceSession(str(MODEL), sess_options=opt,
                                           providers=[("CUDAExecutionProvider", {"device_id": 0})])
        self.session.disable_fallback()
        if self.session.get_providers()[0] != "CUDAExecutionProvider":
            raise RuntimeError("Head-only did not select CUDA")
        cfg = self.session.get_inputs()[0]
        self.name = cfg.name
        self.wh = tuple(cfg.shape[2:][::-1])
        self.calls = 0

    def predict(self, image, roi):
        start = time.perf_counter()
        x, y, w, h = map(int, roi)
        crop = image[y:y+h, x:x+w]
        rgb = cv2.resize(crop[:, :, ::-1], self.wh).astype(np.float32) / 255.
        rgb = (rgb - np.array([.485, .456, .406], np.float32)) / np.array([.229, .224, .225], np.float32)
        tensor = np.ascontiguousarray(rgb.transpose(2, 0, 1)[None])
        prepared = time.perf_counter()
        rotation = self.session.run(None, {self.name: tensor})[0]
        inferred = time.perf_counter()
        angles = angles_from_rotation(rotation)
        self.calls += 1
        done = time.perf_counter()
        return angles, dict(preprocess_ms=(prepared-start)*1000,
                            inference_call_ms=(inferred-prepared)*1000,
                            postprocess_ms=(done-inferred)*1000,
                            head_model_ms=(done-start)*1000)

    def finish(self):
        if not self.profiling:
            return dict(profiling=False, providers=self.session.get_providers(), calls=self.calls)
        result = provider_summary(Path(self.session.end_profiling()))
        if self.calls and (not result["cuda_executed"] or result["cpu_compute_ops"]):
            raise RuntimeError("Head-only GPU execution verification failed")
        return result


def run(args):
    args.preview = camera_display.allowed()
    from .__main__ import output_folder, environment, parent_running, roi_for, stats, write_json
    automatic = args.head_roi_mode == 'auto'
    if not automatic and args.roi is None and not args.preview:
        raise ValueError("Fixed head crop requires --roi X Y W H, or the full camera display startup option")
    output = None if args.no_log else output_folder("head-only")
    live_status=LiveStatus(getattr(args, 'inference_limit', 0), getattr(args, 'status_port', None))
    model = detector = camera = video = sender = None
    rows = []
    report = dict(status="running", environment=environment(), arguments=vars(args),
                  model="head-mobilenetv3-small", model_sha256=HASH,
                  limitations="Single user; no identity recognition or audio lip sync. Fixed mode has no presence detection.",
                  region_model='yunet-2023mar' if automatic else None,
                  other_models_loaded=[])
    print(f"Head-only ({args.head_roi_mode}) | Results: {output}", flush=True)
    try:
        model = HeadOnlyModel(output if not args.no_ort_profile else None)
        if automatic:
            detector = HeadRegionDetector(output if not args.no_ort_profile else None)
        if args.unity_port: sender = LocalSender(args.unity_port)
        if args.source == "camera":
            camera = Camera(args.camera, args.width, args.height, args.fps, args.backend)
            camera.__enter__()
        elif args.source == "video":
            video = cv2.VideoCapture(args.video)
            if not video.isOpened(): raise RuntimeError("Cannot read head-only video input")
        else:
            raise ValueError("Head-only requires camera or video input")
        gate = DirectionGate(.25, float("inf"), args.observation_block, args.observation_stride)
        roi = args.roi
        tracker = HeadRegionTracker(roi)
        sequence = -1
        paused = False
        measured = 0
        with nullcontext(None) if output is None else (output/"frames.jsonl").open("w", encoding="utf-8") as log:
            for index in (count() if args.frames == 0 else range(args.frames + args.warmup)):
                if args.parent_pid and not parent_running(args.parent_pid): break
                live_status.wait()
                start = time.perf_counter()
                if camera:
                    frame = camera.mailbox.next(after=sequence)
                    sequence, image, acquired = frame.sequence, frame.image, frame.acquired
                else:
                    ok, image = video.read()
                    if not ok and args.loop_video:
                        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ok, image = video.read()
                        tracker = HeadRegionTracker(args.roi)
                        gate.reset()
                    if not ok: break
                    acquired = time.perf_counter()
                if not automatic and roi is None:
                    roi = list(camera_display.select_roi("Select head including a small margin; Enter confirms", image, False))
                    cv2.destroyAllWindows()
                    if roi[2] == 0 or roi[3] == 0: break
                    print("Fixed head crop selected. Keep head inside; P pauses; R reselects.", flush=True)
                if roi is not None: roi = roi_for(image, roi)
                read_done = time.perf_counter()
                region_ms = 0.
                if automatic and not paused:
                    detections, region_ms = detector.detect(image)
                    track_time = acquired if camera else index / max(1., video.get(cv2.CAP_PROP_FPS))
                    roi = tracker.update(detections, track_time, image.shape)
                values, timing = (None, {}) if paused or roi is None else model.predict(image, roi)
                # Matrix validity is NOT face presence confidence.
                if values is not None and np.any(np.abs(values) > [75, 85, 75]): values = None
                filtered = gate.update(values, read_done) if values is not None else None
                if values is None: gate.reset()
                packet = dict(version=1, sequence=index, tracked=filtered is not None,
                              headTracked=filtered is not None, faceTracked=False,
                              headPitch=0., headYaw=0., headRoll=0.,
                              inputReadTime=acquired, inputSentTime=time.perf_counter())
                if filtered is not None:
                    packet.update(zip(("headPitch", "headYaw", "headRoll"), map(float, filtered)))
                if sender: sender.send(packet)
                timing.update(frame=index, input_wait_read_ms=(read_done-start)*1000,
                              head_region_ms=region_ms, roi=roi,
                              region_state='paused' if paused else tracker.state if automatic else 'fixed',
                              region_score=tracker.score if automatic else None,
                              read_to_send_ms=(time.perf_counter()-read_done)*1000,
                              raw_angles=None if values is None else values.tolist(), sent_packet=packet)
                live_status.complete((time.perf_counter()-read_done)*1000, filtered is not None)
                if args.preview:
                    canvas = image.copy()
                    if roi is not None:
                        x, y, w, h = roi
                        cv2.rectangle(canvas, (x,y), (x+w,y+h), (0,220,255), 2)
                    cv2.putText(canvas, "HEAD ONLY | P pause / R reset / S select / Q quit | " + timing['region_state'],
                                (10,25), cv2.FONT_HERSHEY_SIMPLEX, .5, (255,255,255), 1)
                    camera_display.show("tanakacap head-only experimental", canvas)
                    key = cv2.waitKey(1) & 255
                    if key in (27, ord("q")): break
                    if key == ord("p"):
                        paused = not paused
                        gate.reset()
                        if automatic: tracker = HeadRegionTracker(roi)
                    if key == ord("r"):
                        roi = None
                        tracker = HeadRegionTracker()
                        gate.reset()
                    if key == ord('s') and automatic:
                        chosen = list(camera_display.select_roi('Select target head; Enter confirms', image, False))
                        cv2.destroyWindow('Select target head; Enter confirms')
                        if chosen[2] > 0 and chosen[3] > 0:
                            roi = chosen
                            tracker = HeadRegionTracker(roi)
                            gate.reset()
                timing["iteration_ms"] = (time.perf_counter()-start)*1000
                if index >= args.warmup:
                    measured += 1
                    if log:
                        rows.append(timing)
                        log.write(json.dumps(timing, allow_nan=False)+"\n")
        report.update(status="completed", measured_frames=measured, roi=roi)
        if camera: report['camera'] = camera.metadata
        if rows:
            report['tracked_frames'] = sum(r['sent_packet']['headTracked'] for r in rows)
        report["execution"] = model.finish()
        model = None
        if detector:
            report['region_execution'] = detector.finish()
            detector = None
        if rows:
            report["timings"] = {k: stats([r[k] for r in rows if k in r]) for k in
                                ("preprocess_ms","inference_call_ms","postprocess_ms","head_model_ms","head_region_ms",
                                 "input_wait_read_ms","read_to_send_ms","iteration_ms")}
        print(json.dumps(report.get("timings", {"measured_frames": measured})), flush=True)
    except BaseException as exc:
        report.update(status="failed", error=str(exc))
        raise
    finally:
        try:
            if model: report["execution"] = model.finish()
            if detector: report['region_execution'] = detector.finish()
        finally:
            if sender: sender.close()
            if camera: camera.__exit__()
            if video: video.release()
            live_status.close()
            if args.preview: cv2.destroyAllWindows()
            if output: write_json(output/"report.json", report)
