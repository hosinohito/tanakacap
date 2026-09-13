import numpy as np
import pytest
from tanakacap.head_pose_size import SizeHeadPose
from tanakacap.head_pose import HeadPose
from test_head_pose import projected


def calibrated():
    model = SizeHeadPose()
    p, s = projected()
    packet = dict(faceTracked=True, headYaw=0, headRoll=0)
    for _ in range(10):model.update(p, s, packet, (1280,720))
    assert model.size_reference is not None
    return model, packet


def test_scale_translation_expression_do_not_change_head():
    model, packet = calibrated()
    p, s = projected(pitch=12)
    model.update(p, s, packet, (1280,720))
    expected = model.size_last.copy()
    p = p * 1.6 + [100,-70]
    p[23+48:23+68] += [25,35]
    p[23:23+17] += [0,40]
    model.update(p, s, packet, (1280,720))
    assert model.size_last == pytest.approx(expected)


def test_signed_pitch_and_loss_hold():
    model, packet = calibrated()
    for angle in [-15,15]:
        p, s = projected(pitch=angle)
        model.update(p, s, packet, (1280,720))
        assert packet['headPitch'] * angle > 0
    expected = model.size_last.copy()
    s[23+30] = 0
    model.update(p, s, packet, (1280,720))
    assert model.size_last == pytest.approx(expected)


def test_pnp_failure_cannot_drive_size_angles(monkeypatch):
    model, packet = calibrated()
    monkeypatch.setattr('tanakacap.head_pose.fit_pose', lambda *args: None)
    p, s = projected(pitch=15)
    model.update(p, s, packet, (1280,720))
    assert packet['headPitch'] > 5
    assert not packet['mouthContourTracked']


def test_expression_channels_equal_pnp():
    size, a = calibrated()
    pnp = HeadPose()
    for angle in [0]*10 + [-15,15]:
        p,s = projected(pitch=angle, expression=.003)
        a = dict(faceTracked=True, headYaw=0, headRoll=0)
        b = a.copy()
        size.update(p,s,a,(1280,720));pnp.update(p,s,b,(1280,720))
        for key in b:
            if not key.startswith('head'):assert a[key] == pytest.approx(b[key])


def test_ui_routes_trial_and_reversion():
    from tanakacap.control_panel import DEFAULT, commands
    for mode in ('size2d','pnp'):
        _, infer = commands(dict(DEFAULT, head_pose_mode=mode), 39500, 39501)
        assert infer[infer.index('--head-pose-mode')+1] == mode
