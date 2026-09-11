import json
import threading
import time

import numpy as np
import pytest

from capture_lab.capture import Frame, LatestFrame
from capture_lab.inference import DetectionGate, PersonDetector, decode_simcc, preprocess, provider_summary
from capture_lab.__main__ import roi_for


def test_latest_frame_drops_backlog_and_waits_for_new_frame():
    stream = LatestFrame()
    stream.publish(Frame(1, 1., None))
    stream.publish(Frame(7, 2., None))
    assert stream.next().sequence == 7
    with pytest.raises(TimeoutError):
        stream.next(after=7, timeout=.01)
    thread = threading.Thread(target=lambda: (time.sleep(.02), stream.publish(Frame(9, 3., None))))
    thread.start()
    assert stream.next(after=7).sequence == 9
    thread.join()


def test_disconnect_is_reported_instead_of_repeating_old_frame():
    stream = LatestFrame()
    stream.publish(Frame(1, 1., None))
    stream.fail('disconnected')
    with pytest.raises(RuntimeError, match='disconnected'):
        stream.next()


def test_center_and_non_square_crop_roundtrip():
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    tensor, center, scale = preprocess(image, [100, 50, 500, 400], [288, 384])
    assert tensor.shape == (1, 3, 384, 288)
    assert tensor.dtype == np.float32 and tensor.flags.c_contiguous
    xs = np.zeros((1, 2, 576), np.float32)
    ys = np.zeros((1, 2, 768), np.float32)
    xs[0, 0, 288] = .8
    ys[0, 0, 384] = .6
    points, scores = decode_simcc([xs, ys], center, scale, [288, 384])
    np.testing.assert_allclose(points[0], [350, 250])
    assert scores[0] == pytest.approx(.6)
    assert np.isnan(points[1]).all()


def test_roi_rejects_outside_image():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        roi_for(image, [80, 0, 40, 50])


def test_gpu_evidence_requires_execution_events(tmp_path):
    profile = tmp_path / 'profile.json'
    profile.write_text(json.dumps([{'args': {'provider': 'CPUExecutionProvider', 'op_name': 'Conv'}}]))
    assert not provider_summary(profile)['cuda_executed']
    assert provider_summary(profile)['cpu_compute_ops'] == {'Conv': 1}
    profile.write_text(json.dumps([{'args': {'provider': 'CUDAExecutionProvider', 'op_name': 'Conv'}},
                                  {'args': {'provider': 'CPUExecutionProvider', 'op_name': 'Shape'}}]))
    result = provider_summary(profile)
    assert result['cuda_executed'] and result['cpu_ops'] == {'Shape': 1}


def test_person_gate_rejects_transient_detection_and_resets_on_loss():
    gate = DetectionGate()
    box = [100, 100, 200, 300]
    assert gate.update(box) is None
    assert gate.update(None) is None
    assert gate.update(box) is None
    assert gate.update(box) is None
    assert gate.update(box) == box
    assert gate.update(None) is None
    assert gate.update(box) is None


def test_person_gate_does_not_confirm_unrelated_boxes():
    gate = DetectionGate(required=2)
    assert gate.update([0, 0, 10, 10]) is None
    assert gate.update([100, 100, 10, 10]) is None


@pytest.mark.parametrize('boxes, expected', [
    ([], None),
    ([[50, 25, 200, 150, .2]], None),
    ([[50, 25, 200, 150, .9]], [100, 50, 300, 250]),
    ([[-20, -10, 900, 900, .95]], [0, 0, 1280, 720]),
])
def test_official_detector_nms_outputs_map_to_camera_coordinates(boxes, expected):
    class Session:
        def run(self, outputs, inputs):
            assert inputs['image'].shape == (1, 3, 640, 640)
            return [np.asarray(boxes, dtype=np.float32).reshape(1, -1, 5)]

    detector = PersonDetector.__new__(PersonDetector)
    detector.session = Session()
    detector.input_name = 'image'
    detector.calls = 0
    roi, _, elapsed = detector.detect(np.zeros((720, 1280, 3), np.uint8))
    assert detector.calls == 1 and elapsed >= 0
    if expected is None:
        assert roi is None
    else:
        np.testing.assert_allclose(roi, expected)
