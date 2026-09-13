"""Exercise actual Tk widgets with a fake process backend: no camera or inference."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from capture_lab import control_panel as panel
import queue

class FakeSession:
    def __init__(self):
        self.running=False;self.stopping=False;self.player=None;self.infer=None
        self.messages=queue.Queue();self.sock=self;self.started=[]
    def poll(self):return {}
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
                assert len(widgets('規定値'))==8
                variables['source'].set('camera');window.update_idletasks()
                assert not widgets('録画のパス')[0].grid_info()
                variables['source'].set('video');window.update_idletasks()
                assert widgets('録画のパス')[0].grid_info()
                variables['rate'].set('60');window.update_idletasks()
                assert not widgets('自由入力 fps / 同期時の上限')[0].grid_info()
                variables['rate'].set('custom');window.update_idletasks()
                assert widgets('自由入力 fps / 同期時の上限')[0].grid_info()
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
            except Exception as exc:errors.append(repr(exc));actions['close']()
        def finish():
            try:
                assert len(session.started)==2 and session.started[-1]['mode']=='head_only'
                saved=json.loads(panel.SETTINGS.read_text(encoding='utf-8'))
                assert saved['source']=='video' and saved['gamma']==1.7
            except Exception as exc:errors.append(repr(exc))
            actions['close']()
        window.after(200,check)
        window.after(8000,actions['close'])
    panel.main(test_hook=hook)
    assert not errors,errors
    (output/'widgets.json').write_text(json.dumps(dict(status='complete',scope='Real Tk start/apply/restart/settings; mocked processes, no camera')),encoding='utf-8')
    print('Tk controls: start, apply/restart, settings and close passed')

if __name__=='__main__':run()
