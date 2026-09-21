"""Exercise actual Tk widgets with a fake process backend: no camera or inference."""
import json
import traceback
from unittest.mock import patch
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tanakacap import control_panel as panel
import queue

class FakeSession:
    def __init__(self):
        self.running=False;self.stopping=False;self.player=None;self.infer=None
        self.messages=queue.Queue();self.sock=self;self.started=[]
    def poll(self):return {'player':{'parts':[{'id':'head','state':'valid','intervalMs':33.3},{'id':'left_arm','state':'held','intervalMs':33.3}]}} if self.running else {}
    def close(self):pass
    def stop(self):self.running=False
    def start(self,config):
        assert config['source']=='video'
        self.started.append(config);self.running=True

def run():
    panel.Session=FakeSession
    output=ROOT/'results/ui-validation';output.mkdir(exist_ok=True)
    panel.SETTINGS=output/'widget-settings.json'
    errors=[]
    def hook(window,variables,session,actions):
        def check():
            try:
                def descendants(parent):
                    for child in parent.winfo_children():
                        yield child
                        yield from descendants(child)
                def widgets(text):
                    return [w for w in descendants(window) if 'text' in w.keys() and str(w.cget('text'))==text]
                assert widgets('保存して開始') and not widgets('保存して適用（実行中は再起動）')
                assert int(widgets('アバター (.tcap)')[0].grid_info()['row'])==0
                assert int(widgets('モーション入力')[0].grid_info()['row'])==2
                assert widgets('終了')[0].pack_info()['side']=='right'
                assert len(widgets('規定値'))==8
                from tkinter import ttk, Canvas
                notebook=next(w for w in descendants(window) if isinstance(w,ttk.Notebook))
                camera_tab=next(tab for tab in notebook.tabs() if notebook.tab(tab,'text')=='カメラ')
                assert widgets('ちらつき防止') and widgets('暗所補正（自動露出時）')
                variables['source'].set('camera');window.update_idletasks()
                assert notebook.tab(camera_tab,'state')=='normal'
                variables['camera_powerline'].set('60hz');variables['camera_lowlight'].set('fixed')
                notebook.select(next(tab for tab in notebook.tabs() if notebook.tab(tab,'text')=='実験'));window.geometry('770x730');window.update()
                pane=window.nametowidget(notebook.select())
                canvas=next(w for w in descendants(pane) if isinstance(w,Canvas))
                combo=next(w for w in descendants(pane) if isinstance(w,ttk.Combobox))
                original=combo.get();before=canvas.yview()
                combo.event_generate('<MouseWheel>',delta=-120);window.update_idletasks()
                assert canvas.yview()[0]>before[0] and combo.get()==original
                canvas.yview_moveto(0)
                label=next(w for w in descendants(pane) if isinstance(w,ttk.Label))
                label.event_generate('<MouseWheel>',delta=-120);window.update_idletasks()
                assert canvas.yview()[0]>0
                notebook.select(0);window.update()
                variables['source'].set('camera');window.update_idletasks()
                assert not widgets('録画のパス')[0].grid_info()
                variables['source'].set('video');window.update_idletasks()
                assert notebook.tab(camera_tab,'state')=='disabled'
                assert widgets('録画のパス')[0].grid_info()
                variables['source'].set('motion');window.update_idletasks()
                assert not widgets('推論モード')[0].grid_info()
                variables['source'].set('video');window.update_idletasks()
                assert widgets('推論モード')[0].grid_info()
                variables['rate'].set('60');window.update_idletasks()
                assert not widgets('自由入力 fps')[0].grid_info()
                variables['rate'].set('sync');window.update_idletasks()
                assert not widgets('自由入力 fps')[0].grid_info()
                variables['rate'].set('custom');window.update_idletasks()
                assert widgets('自由入力 fps')[0].grid_info()
                from tkinter import ttk
                combos=[w for w in descendants(window) if isinstance(w,ttk.Combobox)]
                widths={str(w):w.winfo_reqwidth() for w in combos}
                for key,values in [('source',['camera','video','motion']),('mode',['full','face_head','head_only']),('rate',['60','sync','custom'])]:
                    for value in values:
                        variables[key].set(value);window.update_idletasks()
                        assert all(w.winfo_reqwidth()==widths[str(w)] for w in combos)
                variables['preview'].set(False);window.update_idletasks()
                assert not widgets('背景')[0].master.grid_info()
                variables['preview'].set(True);window.update_idletasks()
                assert widgets('背景')[0].master.grid_info()
                variables['source'].set('video');variables['video'].set('recorded-only.avi')
                variables['gamma'].set('1.7');variables['suppression'].set('.4');variables['fps'].set('37')
                for key,value in [('brow_exaggeration',.2),('eye_exaggeration',.4),('eyelid_exaggeration',.6),('mouth_exaggeration',.8)]:variables[key].set(str(value))
                variables['rate'].set('custom');window.update_idletasks()
                assert variables['gamma'].get()=='1.7'
                actions['start']();assert session.running
                assert session.started[-1]['gamma']==1.7 and session.started[-1]['fps']==37
                assert [session.started[-1][key] for key in ('brow_exaggeration','eye_exaggeration','eyelid_exaggeration','mouth_exaggeration')]==[.2,.4,.6,.8]
                variables['mode'].set('head_only');actions['apply']()
                assert not session.running
                window.after(500,finish)
            except Exception as exc:errors.append(traceback.format_exc());actions['close']()
        def finish():
            try:
                assert len(session.started)==2 and session.started[-1]['mode']=='head_only'
                saved=json.loads(panel.SETTINGS.read_text(encoding='utf-8'))
                assert saved['source']=='video' and saved['gamma']==1.7
                assert saved['camera_powerline']=='60hz' and saved['camera_lowlight']=='fixed'
            except Exception as exc:errors.append(traceback.format_exc())
            def exit_buttons(parent):
                for child in parent.winfo_children():
                    if 'text' in child.keys() and str(child.cget('text'))=='終了':yield child
                    yield from exit_buttons(child)
            next(exit_buttons(window)).invoke()
            assert not session.running
        window.after(200,check)
        window.after(8000,actions['close'])
    with patch.object(panel,'load_settings',return_value={**panel.DEFAULT,'source':'video'}),patch('tanakacap.camera_devices.enumerate_cameras',return_value=[]),patch.object(panel,'query_modes',return_value=[]):
        panel.main(test_hook=hook)
    assert not errors,errors
    (output/'widgets.json').write_text(json.dumps(dict(status='complete',scope='Real Tk start/apply/restart/settings; mocked processes, no camera')),encoding='utf-8')
    print('Tk controls: start, apply/restart, settings and close passed')

if __name__=='__main__':run()
