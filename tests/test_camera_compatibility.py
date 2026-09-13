import json
import pytest
from tanakacap.camera_devices import resolve_camera
from tanakacap.camera_compatibility import choose_format, fourcc_name, hints
from tanakacap.camera_settings import PowerlineSession
from tanakacap.windows_camera_controls import identity_key
from tanakacap import camera_settings, control_panel as ui


def mode(fmt):
    return dict(width=1280,height=720,fps=30.,fourcc=int.from_bytes(fmt.encode(),'little'))


def test_auto_uses_supported_format_without_assuming_every_facecam_supports_mjpeg():
    assert choose_format('auto','dshow',[mode('NV12')],1280,720,30)=='NV12'
    assert choose_format('auto','dshow',[mode('NV12'),mode('MJPG')],1280,720,30)=='MJPG'
    assert choose_format('native','dshow',[mode('MJPG')],1280,720,30) is None
    assert choose_format('YUY2','dshow',[mode('MJPG')],1280,720,30)=='YUY2'
    assert fourcc_name(22) is None # MSMF API-specific subtype is not a printable FourCC.
    assert fourcc_name(float('nan')) is None


def test_reordering_unplug_and_duplicate_model_names():
    devices=[dict(index=0,name='Same camera',device_id='B'),dict(index=3,name='Same camera',device_id='A')]
    assert resolve_camera(0,'a',devices)['index']==3
    with pytest.raises(RuntimeError):resolve_camera(0,'removed',devices)
    assert resolve_camera(0,'',devices)['device_id']=='B'
    with pytest.raises(RuntimeError):resolve_camera(4,'',devices)


def test_cross_api_identity_preserves_pnp_instance_and_pin():
    d=r'\\?\usb#vid_1&pid_2#instance1#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global'
    m=d.replace('65e8773d-8f56-11d0-a3b9-00a0c9223196','e5323777-f976-4f5b-9b55-b94699c46e44')
    assert identity_key(d)==identity_key(m)
    assert identity_key(d)!=identity_key(m.replace('instance1','instance2'))
    assert identity_key(d)!=identity_key(m.replace('global','pin2'))


class Provider:
    def __init__(self):self.current=(1,0);self.writes=[]
    def read(self):return self.current
    def write(self,value,flags):
        self.writes.append((value,flags));self.current=(value,0);return self.current


def test_powerline_apply_and_restore_before_deleting_journal(tmp_path):
    provider=Provider();session=PowerlineSession('ID','60hz',directory=tmp_path,provider=provider,warn=lambda _:None)
    assert session.start()['applied']
    assert json.loads(session.path.read_text())['original']==[1,0]
    assert provider.current==(2,0)
    session.verify();session.close()
    assert provider.current==(1,0) and not session.path.exists()


def test_recover_previous_crash_even_when_keep_selected(tmp_path,monkeypatch):
    provider=Provider();session=PowerlineSession('ID','keep',directory=tmp_path,provider=provider,warn=lambda _:None)
    session.path.write_text(json.dumps(dict(device_id='ID',pid=9876,original=[2,0])))
    monkeypatch.setattr(camera_settings,'process_alive',lambda pid:False)
    session.start()
    assert provider.current==(2,0) and not session.path.exists()


def test_other_process_journal_is_not_overwritten(tmp_path,monkeypatch):
    provider=Provider();session=PowerlineSession('ID','off',directory=tmp_path,provider=provider)
    original=json.dumps(dict(device_id='ID',pid=9876,original=[2,0]));session.path.write_text(original)
    monkeypatch.setattr(camera_settings,'process_alive',lambda pid:True)
    with pytest.raises(RuntimeError):session.start()
    assert session.path.read_text()==original and not provider.writes


def test_unsupported_control_continues_without_mutation(tmp_path):
    class Unsupported(Provider):
        def read(self):raise OSError('Unsupported')
    provider=Unsupported();messages=[]
    session=PowerlineSession('ID','off',directory=tmp_path,provider=provider,warn=messages.append)
    assert not session.start()['applied']
    assert messages and not provider.writes and not session.path.exists()


def test_partial_set_failure_rolls_back(tmp_path):
    class Reject(Provider):
        def write(self,value,flags):
            super().write(value,flags)
            if value==2:raise OSError('Partial failure')
            return self.current
    provider=Reject();session=PowerlineSession('ID','60hz',directory=tmp_path,provider=provider,warn=lambda _:None)
    assert not session.start()['applied']
    assert provider.current==(1,0) and not session.path.exists()


def test_control_reset_on_stream_start_is_reported(tmp_path):
    provider=Provider();messages=[]
    session=PowerlineSession('ID','off',directory=tmp_path,provider=provider,warn=messages.append)
    session.start();provider.current=(1,0);session.verify()
    assert not session.status['applied'] and any('撮影開始' in x for x in messages)
    session.close()


def test_restore_failure_preserves_journal(tmp_path):
    class NoRestore(Provider):
        def write(self,value,flags):
            if value==1:raise OSError('Disconnected')
            return super().write(value,flags)
    provider=NoRestore();session=PowerlineSession('ID','off',directory=tmp_path,provider=provider,warn=lambda _:None)
    session.start()
    with pytest.raises(OSError):session.close()
    assert session.path.exists() and json.loads(session.path.read_text())['original']==[1,0]


def test_unknown_driver_control_value_never_mutates(tmp_path):
    provider=Provider();provider.current=(-1,0)
    session=PowerlineSession('ID','off',directory=tmp_path,provider=provider,warn=lambda _:None)
    assert not session.start()['applied'] and not provider.writes


def test_nonfinite_or_unsupported_capture_properties():
    from tanakacap.capture import safe_get,safe_set
    import cv2
    class Device:
        def get(self,key):return float('nan')
        def set(self,key,value):raise cv2.error('not supported')
    assert safe_get(Device(),1) is None
    assert not safe_set(Device(),1,2)


def test_lowlight_control_has_independent_journal_and_no_exposure_write(tmp_path):
    provider=Provider();session=PowerlineSession('ID','fixed',directory=tmp_path,provider=provider,kind='lowlight',warn=lambda _:None)
    session.start()
    assert provider.current==(0,0) and session.path.name.endswith('-lowlight.json')
    session.close();assert provider.current==(1,0)


def test_vendor_advice_does_not_apply_original_facecam_rule_to_other_models():
    assert any('可変' in x for x in hints('Elgato Facecam',1280,720,30))
    assert not any('初代' in x for x in hints('Elgato Facecam MK.2',1280,720,30,slow=True))
    assert any('USB 2.0' in x for x in hints('Elgato Facecam MK.2',1280,720,30,slow=True))
    assert any('C922' in x for x in hints('C922 Pro Stream Webcam',1920,1080,60,slow=True))
    assert not hints('C920',1920,1080,60,slow=True)


@pytest.mark.parametrize('mode',['full','face_head','head_only'])
def test_all_inference_modes_receive_camera_options(mode):
    _,args=ui.commands(dict(ui.DEFAULT,mode=mode,camera_id='test-id',camera_backend='msmf',
                           camera_powerline='60hz',camera_lowlight='fixed',camera_fps=60),1,2)
    for flag,value in [('--camera-id','test-id'),('--camera-powerline','60hz'),('--camera-lowlight','fixed'),('--fps','60'),('--backend','msmf')]:
        assert args[args.index(flag)+1]==value
    _,args=ui.commands(dict(ui.DEFAULT,source='video',video='test.avi',camera_powerline='60hz'),1,2)
    assert '--camera-powerline' not in args
