import pytest
from tanakacap.camera_modes import supported_modes, default_fps, resolutions
from tanakacap.control_panel import validate, DEFAULT, commands


def modes(*entries):
    return supported_modes([dict(width=w,height=h,fps=f,fourcc=int.from_bytes(fmt.encode(),'little')) for w,h,f,fmt in entries])


def test_default_prefers_sixty_over_high_speed_and_resolution_follows_fps():
    data=modes((1920,1080,30,'MJPG'),(1280,720,60,'MJPG'),(640,480,120,'YUY2'))
    assert default_fps(data)==60
    assert resolutions(data,60)==[(1280,720)]
    assert resolutions(data,30)==[(1920,1080)]


def test_lower_maximum_and_fractional_sixty_are_preserved():
    assert default_fps(modes((1280,720,30,'MJPG'),(640,480,25,'MJPG')))==30
    fps=60000/1001
    data=modes((1280,720,fps,'NV12'),(1920,1080,30,'NV12'))
    assert default_fps(data)==fps
    config=validate({**DEFAULT,'camera_fps':fps})
    assert float(commands(config,1,2)[1][commands(config,1,2)[1].index('--fps')+1])==fps


def test_modes_ignore_bad_or_unsupported_formats_and_deduplicate():
    assert supported_modes([{},dict(width=1280,height=720,fps=float('nan'),fourcc=0)])==[]
    assert len(modes((1280,720,30,'MJPG'),(1280,720,30,'MJPG')))==1
    with pytest.raises(ValueError):default_fps([])
    for value in (0,float('nan'),241):
        with pytest.raises(ValueError):validate({**DEFAULT,'camera_fps':value})
