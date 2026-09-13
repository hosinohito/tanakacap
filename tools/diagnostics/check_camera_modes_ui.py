"""Exercise real Tk camera choices using fake devices only; never activates hardware."""
import sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tools'))
from check_control_panel_ui import FakeSession
from tanakacap import control_panel as ui
from tkinter import ttk


def run():
    errors=[];calls=[]
    def query(device):
        calls.append(device)
        return [(1920,1080,30.,'MJPG'),(1280,720,60.,'MJPG'),(640,480,120.,'YUY2')]
    def hook(window,v,session,actions):
        def widgets(parent):
            for child in parent.winfo_children():
                yield child
                yield from widgets(child)
        def first():
            try:
                assert not calls # Merely opening the UI does not connect.
                book=next(w for w in widgets(window) if isinstance(w,ttk.Notebook))
                book.select(next(t for t in book.tabs() if book.tab(t,'text')=='カメラ'))
                window.after(700,check)
            except Exception as e:errors.append(str(e));actions['close']()
        def check():
            try:
                assert calls==['fake-device']
                assert float(v['camera_fps'].get())==60
                assert (v['camera_width'].get(),v['camera_height'].get())==('1280','720')
                book=next(w for w in widgets(window) if isinstance(w,ttk.Notebook))
                pane=window.nametowidget(book.select())
                combos=[w for w in widgets(pane) if isinstance(w,ttk.Combobox)]
                fps=next(w for w in combos if w.grid_info().get('row')==0)
                fps.set('30');fps.event_generate('<<ComboboxSelected>>');window.update_idletasks()
                assert (v['camera_width'].get(),v['camera_height'].get())==('1920','1080')
            except Exception as e:errors.append(repr(e))
            actions['close']()
        window.after(100,first)
        window.after(5000,actions['close'])
    with patch.object(ui,'Session',FakeSession),patch.object(ui,'load_settings',return_value={**ui.DEFAULT,'camera_id':'fake-device'}),patch.object(ui,'query_modes',query),patch('tanakacap.camera_devices.enumerate_cameras',return_value=[dict(index=1,name='Fake',device_id='fake-device')]):
        ui.main(test_hook=hook)
    assert not errors,errors
    print('Camera mode Tk checks passed (fake devices only)')


if __name__=='__main__':run()
