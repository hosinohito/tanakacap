import ast
import sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import pytest
from tanakacap import camera_display, __main__ as app, comparison_capture, head_only


def test_exact_startup_token_required(monkeypatch):
    for token in ('--preview', '--diagnose', camera_display.DISPLAY_FLAG[:35],
                  camera_display.DISPLAY_FLAG + '=true', ''):
        monkeypatch.setattr(sys, 'argv', ['tanakacap', token])
        assert not camera_display.allowed()
    monkeypatch.setattr(sys, 'argv', ['tanakacap', camera_display.DISPLAY_FLAG])
    assert camera_display.allowed()


def test_all_display_sinks_closed_without_opt_in(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tanakacap', '--preview', '--diagnose'])
    def forbidden(*args, **kwargs):
        raise AssertionError('Raw camera image reached display')
    monkeypatch.setattr(cv2, 'imshow', forbidden)
    monkeypatch.setattr(cv2, 'selectROI', forbidden)
    monkeypatch.setattr(cv2, 'resize', forbidden)
    camera_display.show('test', object())
    camera_display.update_tk_preview(object(), object())
    with pytest.raises(RuntimeError, match='full startup option'):
        camera_display.select_roi('test', object())


def test_opt_in_can_display_and_does_not_persist(monkeypatch):
    seen=[]
    monkeypatch.setattr(cv2, 'imshow', lambda *args: seen.append(args))
    monkeypatch.setattr(sys, 'argv', ['tanakacap', camera_display.DISPLAY_FLAG])
    frame=object()
    camera_display.show('test', frame)
    assert seen == [('test', frame)]
    monkeypatch.setattr(sys, 'argv', ['tanakacap'])
    camera_display.show('test', frame)
    assert len(seen)==1


@pytest.mark.parametrize('flag', ['--preview', camera_display.DISPLAY_FLAG[:35]])
def test_old_or_abbreviated_flags_rejected_before_execution(monkeypatch, flag):
    monkeypatch.setattr(sys, 'argv', ['tanakacap', 'benchmark', flag])
    with pytest.raises(SystemExit) as error:
        app.main()
    assert error.value.code==2
    monkeypatch.setattr(sys, 'argv', ['comparison_capture', flag])
    with pytest.raises(SystemExit) as error:
        comparison_capture.main()
    assert error.value.code==2


def test_fixed_head_selection_cannot_bypass_gate(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['tanakacap'])
    args=SimpleNamespace(head_roi_mode='fixed', roi=None, preview=True)
    with pytest.raises(ValueError, match='full camera display'):
        head_only.run(args)
    assert not args.preview


def test_complete_flag_is_accepted_by_both_entry_points(monkeypatch):
    seen=[]
    monkeypatch.setattr(app, 'benchmark', lambda args: seen.append(args.preview))
    monkeypatch.setattr(sys, 'argv', ['tanakacap', 'benchmark', camera_display.DISPLAY_FLAG])
    app.main()
    monkeypatch.setattr(comparison_capture, 'record', lambda index, profile='body': seen.append(camera_display.allowed()))
    monkeypatch.setattr(sys, 'argv', ['comparison_capture', camera_display.DISPLAY_FLAG])
    comparison_capture.main()
    assert seen==[True, True]


def test_raw_display_api_is_centralized():
    root=Path(__file__).resolve().parents[1]
    forbidden={'imshow','namedWindow','selectROI','selectROIs','PhotoImage','ImageTk'}
    for folder in ('tanakacap','tools'):
        for path in (root/folder).glob('**/*.py'):
            if path.name=='camera_display.py':continue
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Call):
                    name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                    assert name not in forbidden, f'{path}:{node.lineno}: route camera images through camera_display'
    launcher=(root/'run-avatar.ps1').read_text(encoding='utf-8-sig')
    assert '--preview' not in launcher
    assert camera_display.DISPLAY_FLAG not in launcher
