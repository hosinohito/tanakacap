import sys
import pytest
from capture_lab import control_panel as ui
from capture_lab.camera_display import DISPLAY_FLAG
from capture_lab.live_status import LiveStatus


def test_pacing_waits_before_work_and_does_not_catch_up():
    now=[10.];sleeps=[]
    def sleep(delay):sleeps.append(delay);now[0]+=delay
    status=LiveStatus(20,clock=lambda:now[0],sleep=sleep)
    status.wait();now[0]+=.01;status.wait()
    assert sleeps[0]==pytest.approx(.04)
    now[0]+=1;status.wait();assert len(sleeps)==1
    status.wait();assert sleeps[-1]==pytest.approx(.05)


@pytest.mark.parametrize('limit',[-1,float('nan'),float('inf'),241])
def test_bad_limit_rejected(limit):
    with pytest.raises(ValueError):LiveStatus(limit)


@pytest.mark.parametrize('rate,expected',[('60',60),('30',30),('custom',23),('sync',23)])
def test_matching_inference_cap_and_safe_command_arguments(rate,expected):
    config={**ui.DEFAULT,'rate':rate,'fps':23,'avatar':'D:/model with spaces/a.tcap','preview':True,DISPLAY_FLAG:True}
    player,infer=ui.commands(config,40001,40002,123)
    assert player[player.index('--render-fps')+1]==str(expected)
    assert infer[infer.index('--inference-limit')+1]==str(expected)
    assert ('--render-sync' in player)==(rate=='sync')
    assert DISPLAY_FLAG not in player+infer and '--preview' not in infer
    assert all(isinstance(item,str) for item in player+infer)


def test_modes_disable_real_models_not_just_avatar_parts():
    _,face=ui.commands({**ui.DEFAULT,'mode':'face_head'},1,2)
    assert '--no-body' in face and '--gaze' not in face and '--body3d' not in face
    assert face[face.index('--face-source')+1]=='separate'
    _,head=ui.commands({**ui.DEFAULT,'mode':'head_only'},1,2)
    assert '--head-only' in head and '--gaze' not in head
    player,infer=ui.commands({**ui.DEFAULT,'source':'motion'},1,2)
    assert infer is None and '--motion-demo' in player


def test_settings_roundtrip_preserves_null_and_drops_permission(monkeypatch,tmp_path):
    monkeypatch.setattr(ui,'SETTINGS',tmp_path/'settings.json')
    ui.save_settings({**ui.DEFAULT,'gamma':None,'raw_camera_preview':True})
    settings=ui.load_settings()
    assert settings['gamma'] is None
    assert 'raw_camera_preview' not in settings
    with pytest.raises(ValueError):ui.validate({**ui.DEFAULT,'width':0})
    with pytest.raises(ValueError):ui.validate({**ui.DEFAULT,'gamma':float('nan')})


def test_status_expires_instead_of_showing_old_speed():
    session=ui.Session()
    try:
        session.status={'inference':{'hz':100}}
        session.last={'inference':0}
        assert session.poll()=={}
    finally:session.sock.close()


@pytest.mark.parametrize('part',['brow','eye','eyelid','mouth'])
def test_independent_exaggeration_arguments_and_validation(part):
    config=dict(ui.DEFAULT,**{part+'_exaggeration':.65})
    player,_=ui.commands(config,40001,40002)
    for key in ('brow','eye','eyelid','mouth'):
        assert float(player[player.index('--'+key+'-exaggeration')+1])==(.65 if key==part else 0.)
    for bad in (-.1,1.1,float('nan'),float('inf')):
        with pytest.raises(ValueError):ui.validate(dict(config,**{part+'_exaggeration':bad}))


def test_demo_avatar_uses_demo_runtime():
    player,_=ui.commands(dict(ui.DEFAULT,avatar=str(ui.ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap')),40001,40002)
    assert '--use-demo-shape-keys' in player


def test_experiments_route_to_existing_runtime_and_background_only_for_preview():
    player,infer=ui.commands(dict(ui.DEFAULT,head_follow='adaptive',observation_mode='blocks',gaze_calibration='off',preview=False,background='green'),1,2)
    assert '--adaptive-head-follow' in player and '--preview-background' not in player
    assert '--no-gaze-range-calibration' in infer
    assert infer[infer.index('--observation-stride')+1]=='3'
    assert infer[infer.index('--backend')+1]=='dshow'
    player,_=ui.commands(dict(ui.DEFAULT,background='green'),1,2)
    assert player[player.index('--preview-background')+1]=='green'
    for key in ui.OPTIONS:
        with pytest.raises(ValueError):ui.validate(dict(ui.DEFAULT,**{key:'unknown'}))
