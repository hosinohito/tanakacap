import sys
import numpy as np
import pytest
from tanakacap import __main__ as app


@pytest.mark.parametrize('source,expected_models', [('separate', 2), ('body3d', 1)])
def test_shared_face_runs_and_finishes_body_model_once(monkeypatch, source, expected_models):
    instances = []
    class Model:
        def __init__(self, name, output, execution_mode):
            assert execution_mode == 'graph-fp16'
            self.identity = {'id': name}
            self.calls = self.finishes = 0
            instances.append(self)
        def predict(self, image, roi):
            self.calls += 1
            return np.zeros((133,2)), np.zeros(133), dict(preprocess_ms=0., inference_call_ms=0., postprocess_ms=0., pipeline_ms=0.)
        def finish(self):
            self.finishes += 1
            return {'profiling': False}
    monkeypatch.setattr(app, 'SimCCModel', Model)
    monkeypatch.setattr(app, 'environment', lambda: {})
    monkeypatch.setattr(sys, 'argv', ['tanakacap', 'benchmark', '--source', 'synthetic', '--no-log',
                                    '--frames', '3', '--warmup', '0', '--body3d', '--face-source', source])
    app.main()
    assert len(instances) == expected_models
    assert all(model.calls == 6 and model.finishes == 1 for model in instances)
    assert instances[-1].identity['id'] == 'rtmw3d-x-384'
