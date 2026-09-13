import importlib.util
import json
from pathlib import Path


spec = importlib.util.spec_from_file_location('camera_diagnostic_suite',
    Path(__file__).resolve().parents[1]/'tools/diagnostics/diagnose_camera.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


def test_exposure_trials_respect_driver_range_and_capabilities():
    control = dict(exposure_available=1, exposure=-5, minimum=-9,
                   maximum=-3, step=2, caps=3)
    assert suite.exposure_trials(control) == [('auto', -5, 1), ('manual-7', -7, 2)]
    assert suite.exposure_trials({}) == []
    assert suite.exposure_trials(dict(control, caps=1)) == [('auto', -5, 1)]


def test_suite_order_restores_each_mutation_and_maps_mf_index(tmp_path, monkeypatch):
    native = tmp_path/'native.exe'
    native.touch()
    pending = tmp_path/'pending.json'
    monkeypatch.setattr(suite, 'ROOT', tmp_path)
    monkeypatch.setattr(suite, 'NATIVE', native)
    monkeypatch.setattr(suite, 'PENDING', pending)
    monkeypatch.setattr(suite, 'enumerate_cameras', lambda: [{'name':'HD webcam-CMS-V43BK', 'index':1}])
    calls=[]
    controls=dict(power_available=1,power=1,power_flags=2,exposure_available=1,
                  exposure=-6,exposure_flags=1,minimum=-10,maximum=-1,step=1,caps=3)
    def run(command, log, timeout=40):
        calls.append(command)
        if command[1] in ('power','exposure'):
            assert json.loads(pending.read_text())['controls']==controls
        return {'exit_code':0,'events':[{'controls':controls},{'mf_index':4},
                {'restore_power':1},{'restore_exposure':1}], 'log':str(log)}, ''
    monkeypatch.setattr(suite, 'run_logged', run)
    suite.main()
    actions=[cmd[1] for cmd in calls if cmd[0]==str(native)]
    assert actions==['inspect','capture','power','restore','power','restore','power','restore',
                     'capture','exposure','restore','exposure','restore','exposure','restore',
                     'capture','capture']
    cv_calls=[cmd for cmd in calls if '--backend' in cmd]
    assert [(cmd[cmd.index('--backend')+1],cmd[cmd.index('--camera')+1]) for cmd in cv_calls]==[('dshow','1'),('msmf','4')]
    assert not pending.exists()


def test_restore_failure_keeps_recovery_record(tmp_path, monkeypatch):
    import pytest
    pending=tmp_path/'pending.json'; pending.write_text('{}')
    monkeypatch.setattr(suite,'PENDING',pending)
    monkeypatch.setattr(suite,'run_logged',lambda *args,**kwargs: ({'exit_code':0,'events':[]},''))
    with pytest.raises(RuntimeError, match='復元'):
        suite.restore_controls({'controls':dict(power_available=1,power=1,power_flags=2,
                                               exposure_available=0,exposure_flags=0)},tmp_path)
    assert pending.exists()
