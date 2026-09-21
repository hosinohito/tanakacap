import json
import pytest
from tanakacap import comparison_capture as capture


def test_recording_uses_saved_identity_even_with_video_selected(tmp_path,monkeypatch):
    monkeypatch.setattr(capture,'ROOT',tmp_path)
    (tmp_path/'ui-settings.json').write_text(json.dumps(dict(source='video',camera=-1,camera_id='saved-device',
        camera_width=1920,camera_height=1080,camera_fps=59.94,camera_backend='dshow',camera_format='MJPG',
        camera_powerline='60hz',camera_lowlight='keep')),encoding='utf-8-sig')
    options=capture.camera_options()
    assert options==dict(index=-1,device_id='saved-device',width=1920,height=1080,fps=59.94,
                         backend='dshow',pixel_format='MJPG',powerline='60hz',lowlight='keep')
    explicit=capture.camera_options(2)
    assert explicit['index']==2 and explicit['device_id']==''
    assert explicit['powerline']==explicit['lowlight']=='keep'


def test_unselected_camera_cannot_silently_fall_back(tmp_path,monkeypatch):
    monkeypatch.setattr(capture,'ROOT',tmp_path)
    (tmp_path/'ui-settings.json').write_text('{"camera":-1}',encoding='utf-8')
    with pytest.raises(ValueError):capture.camera_options()


def test_default_capture_does_not_change_camera_controls(tmp_path,monkeypatch):
    monkeypatch.setattr(capture,'ROOT',tmp_path)
    options=capture.camera_options()
    assert options['powerline']==options['lowlight']=='keep'
