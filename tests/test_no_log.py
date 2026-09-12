import sys
import numpy as np
from capture_lab import __main__ as app


class Model:
    outputs = []
    calls = 0
    def __init__(self, name, output):
        self.identity = {'id': name}
        Model.outputs.append(output)
    def predict(self, image, roi):
        Model.calls += 1
        return np.zeros((133, 2)), np.zeros(133), dict(preprocess_ms=0., inference_call_ms=0., postprocess_ms=0., pipeline_ms=0.)
    def finish(self):
        return {'profiling': False}


def setup(monkeypatch, extra):
    Model.outputs = []
    Model.calls = 0
    monkeypatch.setattr(app, 'SimCCModel', Model)
    monkeypatch.setattr(app, 'environment', lambda: {})
    def forbidden(*args, **kwargs):
        raise AssertionError('No-log mode must not create result folders or write reports')
    monkeypatch.setattr(app, 'output_folder', forbidden)
    monkeypatch.setattr(app, 'write_json', forbidden)
    monkeypatch.setattr(sys, 'argv', ['capture_lab', 'benchmark', '--source', 'synthetic', '--no-log', '--warmup', '0'] + extra)


def test_no_log_never_opens_results(monkeypatch):
    setup(monkeypatch, ['--frames', '3'])
    app.main()
    assert Model.outputs == [None]
    assert Model.calls == 6  # Three initialization calls plus three observations.


def test_unlimited_stops_on_parent_exit(monkeypatch):
    setup(monkeypatch, ['--frames', '0', '--parent-pid', '123'])
    alive = iter([True] * 5 + [False])
    monkeypatch.setattr(app, 'parent_running', lambda pid: next(alive))
    app.main()
    assert Model.calls == 8


def test_conflicting_recording_request_rejected(monkeypatch):
    import pytest
    setup(monkeypatch, ['--frames', '3', '--landmarks'])
    with pytest.raises(SystemExit) as exc:
        app.main()
    assert exc.value.code == 2
    assert not Model.outputs
