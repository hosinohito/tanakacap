"""Desktop controls. No camera image surfaces or raw-display permission forwarding."""
import json
import math
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import threading
import time
from .ui_experiments import OPTIONS
from .player_diagnostics import PlayerDiagnostics

ROOT=Path(__file__).resolve().parents[1]
def player_path():
    packaged=ROOT/'app/TanakaCap.exe'
    return packaged if packaged.is_file() else ROOT/'builds/player/TanakaCap.exe'

SETTINGS=ROOT/'ui-settings.json'
MODES={'full':'全部 ON（顔・頭・体・腕・指・目線）','face_head':'顔・頭（表情あり・目線なし）','head_only':'頭のみ（軽量・表情なし）'}
DEFAULT=dict(source='camera',camera=1,video='',avatar=str(ROOT/'builds/player/avatars/haolan.tcap'),
             mode='full',body=True,gaze=True,detector=True,rate='60',fps=60,width=1920,height=1080,
             aa=True,preview=True,background='none',expression='existing',gamma=None,suppression=None,emphasis=0.,gaze_gain=4.,head_pose_mode='pnp',
             brow_exaggeration=0.,eye_exaggeration=0.,eyelid_exaggeration=0.,mouth_exaggeration=0.)
DEFAULT.update({key:value[1] for key,value in OPTIONS.items()})


def validate(values):
    data={k:values.get(k,v) for k,v in DEFAULT.items()}
    for key,(_,_,choices) in OPTIONS.items():
        if data[key] not in choices:raise ValueError('Invalid '+key)
    for key,choices in dict(source=('camera','video','motion'),mode=tuple(MODES),rate=('60','sync','30','custom'),expression=('existing','auto-custom'),background=('none','green','blue','magenta')).items():
        if data[key] not in choices:raise ValueError('Invalid '+key)
    if data['head_pose_mode'] not in ('pnp','size2d','legacy','depth3d','pnp_depthmouth'):raise ValueError('Invalid head_pose_mode')
    for key,lo,hi in [('camera',0,31),('fps',1,240),('width',64,4096),('height',64,4096)]:
        value=float(data[key])
        if not math.isfinite(value) or value!=int(value) or not lo<=value<=hi:raise ValueError(f'{key}: {lo}〜{hi} の整数を指定してください')
        data[key]=int(value)
    for key,lo,hi in [('gamma',.25,4),('suppression',0,1),('emphasis',0,1),('gaze_gain',.5,6),
                      *[(k,0,1) for k in ('brow_exaggeration','eye_exaggeration','eyelid_exaggeration','mouth_exaggeration')]]:
        if data[key] is None and key in ('gamma','suppression'):continue
        value=float(data[key])
        if not math.isfinite(value) or not lo<=value<=hi:raise ValueError(f'{key}: {lo}〜{hi} を指定してください')
        data[key]=value
    for key in ('body','gaze','detector','aa','preview'):
        if type(data[key]) is not bool:raise ValueError('Invalid '+key)
    for key in ('avatar','video'):
        if not isinstance(data[key],str):raise ValueError('Invalid '+key)
    return data


def load_settings():
    values=DEFAULT.copy()
    tracking=json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    values['head_pose_mode']=tracking.get('head_pose_mode','pnp')
    for key,source in [('gamma','mouth_corner_gamma'),('suppression','mouth_open_smile_suppression'),('emphasis','mouth_corner_emphasis'),('gaze_gain','gaze_gain')]:
        values[key]=tracking.get(source,values[key])
    if SETTINGS.exists():values.update(json.loads(SETTINGS.read_text(encoding='utf-8')))
    return validate(values)


def save_settings(values):
    data=validate(values);temp=SETTINGS.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(SETTINGS)


def commands(config, port, status_port, player_pid=0):
    c=validate(config);tracking=json.loads((ROOT/'tracking-settings.json').read_text(encoding='utf-8'))
    cap=0 if c['rate']=='sync' else c['fps'] if c['rate']=='custom' else int(c['rate'])
    player=[str(player_path()),'-nolog','--error-log',str(ROOT/'logs/player-errors.log'),'--port',str(port),'--ui-status-port',str(status_port),
            '--avatar',str(Path(c['avatar']).resolve()),'--output-width',str(c['width']),
            '--output-height',str(c['height']),'--expression-mode',c['expression'],'--mouth-corner-emphasis',str(c['emphasis']),
            '--gaze-gain',str(c['gaze_gain'])]
    for key in ('brow_exaggeration','eye_exaggeration','eyelid_exaggeration','mouth_exaggeration'):
        player+=['--'+key.replace('_','-'),str(c[key])]
    if Path(c['avatar']).resolve()==(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap').resolve():player+=['--use-demo-shape-keys']
    if c['rate']=='sync':player+=['--render-sync']
    else:player+=['--render-fps',str(cap)]
    if not c['aa']:player+=['--no-edge-aa']
    if not c['preview']:player+=['--no-preview']
    if c['preview'] and c['background']!='none':player+=['--preview-background',c['background']]
    for key,value,flag in [('gaze_response','legacy','--legacy-gaze-response'),('head_follow','adaptive','--adaptive-head-follow'),('brow_follow','direct','--no-adaptive-brow-follow')]:
        if c[key]==value:player+=[flag]
    for key,value,flag in [('face_distance_mode','off','--no-face-distance'),('face_distance_mode','translate','--face-distance-translate'),('face_distance_mode','seated','--face-distance-seated'),('gaze_render_mode','bones','--gaze-bones'),('preview_path','legacy','--legacy-preview'),('mouth_shift_range','8','--experimental-mouth-shift-8mm')]:
        if c[key]==value:player+=[flag]
    for key,flag in [('gamma','--mouth-corner-gamma'),('suppression','--mouth-open-smile-suppression')]:
        if c[key] is not None:player += [flag,str(c[key])]
    if c['source']=='motion':return player+['--motion-demo'],None
    python=ROOT/'runtime/python.exe' if (ROOT/'runtime/python.exe').exists() else ROOT/'.venv/Scripts/python.exe'
    infer=[str(python),'-m',__package__,'benchmark','--source',c['source'],'--no-log',
           '--frames','0','--warmup','0','--unity-port',str(port),'--parent-pid',str(player_pid),
           '--status-port',str(status_port),'--inference-limit',str(cap)]
    if c['source']=='video':infer+=['--video',str(Path(c['video']).resolve()),'--loop-video']
    else:infer+=['--camera',str(c['camera']),'--backend','dshow']
    body=c['mode']=='full' and c['body']
    infer+=['--face-source',tracking.get('face_source','body3d') if body else 'separate']
    for key,default in [('observation_block',3),('observation_stride',1),('head_pose_mode','pnp'),('head_pitch_gain',1.8),
                        ('brow_gain',2.),('mouth_lip_depth_scale',1.5),('face_distance_filter','stable'),('arm_depth_mode','front_projection'),
                        ('shoulder_yaw_mode','face_ratio'),('gaze_reference','contour'),('preprocess_mode','crop'),
                        ('detector_interval',3),('detector_model','yolox-m-human')]:
        value=tracking.get(key,default)
        if key in OPTIONS:value=c[key]
        if key in ('observation_block','observation_stride'):
            value=dict(overlap=(3,1),blocks=(3,3),direct=(1,1))[c['observation_mode']][0 if key=='observation_block' else 1]
        if key=='head_pose_mode':value=c['head_pose_mode']
        if key=='head_pose_mode' and not body and value in ('depth3d','pnp_depthmouth'):value='pnp'
        infer+=['--'+key.replace('_','-'),str(value)]
    for key in ('batch_eyes','detector_graph'):
        if c[key]=='on':infer+=['--'+key.replace('_','-')]
    if c['gaze_calibration']=='off':infer+=['--no-gaze-range-calibration']
    infer+=['--body3d' if body else '--no-body']
    if c['mode']=='head_only':infer+=['--head-only','--head-roi-mode','auto']
    if c['mode']=='full' and c['gaze']:infer+=['--gaze']
    if c['mode']=='full' and not c['detector']:infer+=['--fixed-roi']
    return player,infer


def close_player(process):
    if process is None or process.poll() is not None:return
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        user=ctypes.windll.user32
        user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
        callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        def visit(hwnd,_):
            pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value==process.pid:user.PostMessageW(hwnd,0x0010,0,0)
            return True
        user.EnumWindows(callback(visit),0)
    else:process.terminate()


class Session:
    def __init__(self):
        self.player=None;self.infer=None;self.status={};self.last={};self.messages=queue.Queue();self.stopping=False
        self.diagnostics=PlayerDiagnostics(ROOT/'logs/player-errors.log')
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.sock.bind(('127.0.0.1',0));self.sock.setblocking(False)
    @property
    def running(self):return any(p is not None and p.poll() is None for p in (self.player,self.infer))
    def start(self,config, *, frames=0):
        if self.running:raise ValueError('停止が完了してから開始してください')
        c=validate(config)
        if not Path(c['avatar']).is_file():raise ValueError('アバターファイルが見つかりません')
        if c['source']=='video' and not Path(c['video']).is_file():raise ValueError('録画ファイルが見つかりません')
        exe=player_path()
        if not exe.is_file():raise ValueError('Playerをビルドしてください（build-player.ps1）')
        self.poll();self.status={};self.last={}
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        player,_=commands(c,port,self.sock.getsockname()[1])
        self.diagnostics.reset()
        self.player=subprocess.Popen(player,cwd=ROOT)
        try:
            _,infer=commands(c,port,self.sock.getsockname()[1],self.player.pid)
            if infer and frames:infer[infer.index('--frames')+1]=str(frames)
            self.infer=None
            if infer:
                env=dict(os.environ,TANAKACAP_UI_PRECISION=c['precision'])
                self.infer=subprocess.Popen(infer,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                    text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                process=self.infer
                def read():
                    for line in process.stdout:
                        clean=re.sub(r'\x1b\[[0-9;]*m','',line.replace('\x00','')).rstrip()
                        self.messages.put(clean[:1200])
                    process.stdout.close()
                threading.Thread(target=read,daemon=True).start()
        except Exception:
            close_player(self.player);raise
    def stop(self):
        if self.stopping:return
        self.stopping=True
        def worker():
            try:
                close_player(self.player)
                for proc in (self.player,self.infer):
                    if proc and proc.poll() is None:
                        try:proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.terminate()
                            try:proc.wait(timeout=3)
                            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            finally:self.stopping=False
        threading.Thread(target=worker,daemon=True).start()
    def poll(self):
        for message in self.diagnostics.poll():self.messages.put(message)
        for _ in range(200):
            try:raw,_=self.sock.recvfrom(16384)
            except BlockingIOError:break
            try:
                data=json.loads(raw);kind=data['kind']
                if kind in ('inference','player'):
                    self.status[kind]=data;self.last[kind]=time.monotonic()
            except (ValueError,KeyError,TypeError):continue
        now=time.monotonic()
        return {k:v for k,v in self.status.items() if now-self.last[k]<2 and self.running}


def main(test_hook=None):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    window=tk.Tk();window.title('TanakaCap — コントロール');window.geometry('770x820');window.minsize(700,730)
    style=ttk.Style();style.theme_use('vista' if 'vista' in style.theme_names() else 'clam');style.configure('.',font=('Yu Gothic UI',10))
    style.configure('TLabel',wraplength=610)
    style.configure('Title.TLabel',font=('Yu Gothic UI',19,'bold'));style.configure('Metric.TLabel',font=('Yu Gothic UI',13,'bold'))
    session=Session();pending=None;closing=False;was_running=False;last_error=''
    try:settings=load_settings()
    except Exception as error:settings=DEFAULT.copy();messagebox.showerror('設定を読み込めません',str(error))
    variables={k:(tk.BooleanVar(value=v) if type(v) is bool else tk.StringVar(value='' if v is None else str(v))) for k,v in settings.items()}
    outer=ttk.Frame(window,padding=20);outer.pack(fill='both',expand=True)
    metrics=ttk.Label(outer,text='停止中',style='Metric.TLabel');metrics.pack(anchor='w',pady=8)
    state=ttk.Label(outer,text='');state.pack(anchor='w')
    tabs=ttk.Notebook(outer);tabs.pack(fill='both',expand=True,pady=12)
    frames={};scroll_panes=[]
    for name in ('入力・推論','描画・OBS','表情','実験'):
        pane=ttk.Frame(tabs);tabs.add(pane,text=name)
        canvas=tk.Canvas(pane,highlightthickness=0,background=style.lookup('TFrame','background'))
        scroll=ttk.Scrollbar(pane,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y')
        canvas.configure(yscrollcommand=scroll.set);canvas.pack(fill='both',expand=True)
        frame=ttk.Frame(canvas,padding=15);frame.columnconfigure(0,minsize=210);frame.columnconfigure(1,weight=1)
        item=canvas.create_window((0,0),window=frame,anchor='nw')
        frame.bind('<Configure>',lambda event,c=canvas:c.configure(scrollregion=c.bbox('all')))
        canvas.bind('<Configure>',lambda event,c=canvas,i=item:c.itemconfigure(i,width=event.width))
        scroll_panes.append((pane,canvas))
        frames[name]=frame
    display_names={'source':{'camera':'カメラ','video':'保存済み録画','motion':'デモモーション'},
                   'mode':MODES,'rate':{'60':'60 fps','sync':'推論同期（結果が届くと更新）','30':'30 fps','custom':'自由入力（推論上限をつけて負荷を軽減できます）'},
                   'expression':{'existing':'既存キー優先','auto-custom':'自動独自キー（実験用）'}}
    display_names.update({key:value[2] for key,value in OPTIONS.items()})
    def row(frame,index,label,key,choices=None):
        ttk.Label(frame,text=label,width=20,wraplength=190).grid(row=index,column=0,sticky='w',padx=(0,15),pady=9)
        if choices and key in display_names:
            names=display_names[key];shown=tk.StringVar(value=names[variables[key].get()])
            widget=ttk.Combobox(frame,textvariable=shown,values=list(names.values()),state='readonly',width=32)
            widget.bind('<<ComboboxSelected>>',lambda event:variables[key].set(next(k for k,v in names.items() if v==shown.get())))
            variables[key].trace_add('write',lambda *args:shown.set(names[variables[key].get()]))
        else:widget=ttk.Combobox(frame,textvariable=variables[key],values=choices,state='readonly',width=32) if choices else ttk.Entry(frame,textvariable=variables[key],width=32)
        widget.grid(row=index,column=1,sticky='ew');return widget
    f=frames['入力・推論']
    row(f,2,'モーション入力','source',['camera','video','motion'])
    from .camera_devices import enumerate_cameras
    try:cameras=enumerate_cameras()
    except OSError:cameras=[]
    display_names['camera']={str(d['index']):f"{d['name']} ({d['index']})" for d in cameras}
    current=variables['camera'].get()
    if current not in display_names['camera']:display_names['camera'][current]='カメラ '+current+'（未検出）'
    camera_choice=row(f,3,'カメラ','camera',list(display_names['camera']))
    row(f,4,'録画のパス','video')
    takes=sorted((ROOT/'results/comparison-takes').glob('*/camera.avi'))
    def choose_take():
        picker=tk.Toplevel(window);picker.title('録画を選択');picker.geometry('650x280')
        box=tk.Listbox(picker,font=('Yu Gothic UI',10));box.pack(fill='both',expand=True)
        for path in takes:box.insert('end',path.parent.name)
        def choose():
            if box.curselection():variables['video'].set(str(takes[box.curselection()[0]]));variables['source'].set('video');picker.destroy()
        ttk.Button(picker,text='この録画を使う',command=choose).pack(pady=8)
    ttk.Button(f,text='保存済み録画から選択',command=choose_take).grid(row=5,column=1,sticky='w')
    def source_state(*args):
        for index,wanted in [(3,'camera'),(4,'video'),(5,'video')]:
            for widget in f_input.winfo_children():
                info=widget.grid_info() or getattr(widget,'_saved_grid',{})
                if int(info.get('row',-1))==index:
                    widget._saved_grid=info
                    if variables['source'].get()==wanted:widget.grid()
                    else:widget.grid_remove()
    f_input=f
    variables['source'].trace_add('write',source_state);source_state()
    row(f,0,'アバター (.tcap)','avatar')
    def avatar():
        path=filedialog.askopenfilename(filetypes=[('TanakaCap avatar','*.tcap')])
        if path:variables['avatar'].set(path)
    ttk.Button(f,text='アバターを選択',command=avatar).grid(row=1,column=1,sticky='w')
    row(f,6,'推論モード','mode',list(MODES))
    parts=ttk.Frame(f);parts.grid(row=8,column=0,columnspan=2,sticky='w',pady=12)
    costs=json.loads((ROOT/'docs/ui-part-costs.json').read_text(encoding='utf-8'))['parts']
    for key,text in [('body','体・腕・指（顔と共有）'),('gaze','目線'),('detector','人物検出')]:
        ttk.Checkbutton(parts,text=text+' 負荷'+str(costs[key]['tenths'])+'割',variable=variables[key]).pack(anchor='w',pady=4)
    def parts_state(*args):
        motion=variables['source'].get()=='motion'
        for widget in f_input.winfo_children():
            info=widget.grid_info() or getattr(widget,'_saved_grid',{})
            if int(info.get('row',-1))==6:
                widget._saved_grid=info
                if motion:widget.grid_remove()
                else:widget.grid()
        if not motion and variables['mode'].get()=='full':parts.grid()
        else:parts.grid_remove()
    variables['source'].trace_add('write',parts_state)
    variables['mode'].trace_add('write',parts_state);parts_state()
    for index,(key,(label,_,choices)) in enumerate(OPTIONS.items()):row(frames['実験'],index,label,key,list(choices))
    f=frames['描画・OBS']
    row(f,0,'描画レート','rate',['60','sync','30','custom'])
    row(f,2,'自由入力 fps','fps')
    rate_widgets=list(f.grid_slaves(row=2))
    def rate_state(*args):
        for widget in rate_widgets:
            if variables['rate'].get()=='custom':widget.grid()
            else:widget.grid_remove()
    variables['rate'].trace_add('write',rate_state);rate_state()
    row(f,3,'出力の幅','width');row(f,4,'出力の高さ','height')
    ttk.Button(f,text='Full HD に戻す',command=lambda:(variables['width'].set('1920'),variables['height'].set('1080'))).grid(row=5,column=1,sticky='w')
    ttk.Checkbutton(f,text='軽量アンチエイリアス',variable=variables['aa']).grid(row=6,column=0,columnspan=2,sticky='w',pady=12)
    ttk.Checkbutton(f,text='アバターのウインドウを表示（オフにすると負荷軽減になります）',variable=variables['preview']).grid(row=7,column=0,columnspan=2,sticky='w')
    background=ttk.Frame(f);background.grid(row=8,column=0,columnspan=2,sticky='w',pady=8)
    ttk.Label(background,text='背景').pack(side='left',padx=(0,12))
    for value,label in [('none','指定しない'),('green','緑'),('blue','青'),('magenta','マゼンタ')]:
        ttk.Radiobutton(background,text=label,value=value,variable=variables['background']).pack(side='left',padx=5)
    def preview_state(*args):
        if variables['preview'].get():background.grid()
        else:background.grid_remove()
    variables['preview'].trace_add('write',preview_state);preview_state()
    ttk.Label(f,text='OBS用のソースとしてSpoutを出力します。OBSにSpoutを導入し、ソース名TanakaCapを選んでください。Spoutを使用すると、透過出力が可能です。',wraplength=610).grid(row=9,column=0,columnspan=2,sticky='w',pady=20)
    f=frames['表情']
    row(f,0,'表情方式','expression',['existing','auto-custom'])
    exaggeration_widgets=[]
    for index,key,label,lo,hi in [(2,'brow_exaggeration','眉の大げさ度',0,1),(4,'eye_exaggeration','目（目線）の大げさ度',0,1),
                                 (6,'eyelid_exaggeration','まぶた（閉じ）の大げさ度',0,1),(8,'mouth_exaggeration','口の大げさ度',0,1),
                                 (10,'gamma','口角ガンマ',.25,4),(12,'suppression','開口時の口角上げ抑制',0,1),(14,'emphasis','口角の追加強調',0,1),(16,'gaze_gain','目線の基準感度',.5,6)]:
        entry=row(f,index,label,key)
        def reset_value(k=key):
            value=DEFAULT[k]
            if k in ('gamma','suppression'):value=(2 if k=='gamma' else .9) if variables['expression'].get()=='auto-custom' else (1 if k=='gamma' else 0)
            if k.endswith('_exaggeration') and Path(variables['avatar'].get()).resolve()==(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap').resolve():value=1
            variables[k].set(str(value))
        ttk.Button(f,text='規定値',command=reset_value).grid(row=index,column=2,padx=(8,0))
        initial=variables[key].get()
        default=2 if key=='gamma' and variables['expression'].get()=='auto-custom' else .9 if key=='suppression' and variables['expression'].get()=='auto-custom' else 1 if key=='gamma' else 0
        slider=tk.DoubleVar(value=float(initial) if initial else default)
        scale=ttk.Scale(f,from_=lo,to=hi,variable=slider,command=lambda value,k=key:variables[k].set(f'{float(value):.3f}'))
        scale.grid(row=index+1,column=1,sticky='ew')
        if key.endswith('_exaggeration'):exaggeration_widgets.append((key,entry,scale))
        def sync_slider(*args,k=key,v=slider):
            value=variables[k].get()
            if not value:value=(2 if k=='gamma' else .9) if variables['expression'].get()=='auto-custom' else (1 if k=='gamma' else 0)
            try:v.set(float(value))
            except ValueError:pass
        variables[key].trace_add('write',sync_slider)
        variables['expression'].trace_add('write',sync_slider)
    def demo_strength_state(*args):
        try:is_demo=Path(variables['avatar'].get()).resolve()==(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap').resolve()
        except (OSError,ValueError):is_demo=False
        for key,entry,scale in exaggeration_widgets:
            if is_demo:variables[key].set('1')
            entry.configure(state='disabled' if is_demo else 'normal');scale.configure(state='disabled' if is_demo else 'normal')
    variables['avatar'].trace_add('write',demo_strength_state);demo_strength_state()
    messages=tk.Text(outer,height=10,font=('Yu Gothic UI',9),state='disabled');messages.pack(fill='x')
    messages.tag_configure('warning',foreground='#9a5700')
    messages.tag_configure('error',foreground='#b00020')
    buttons=ttk.Frame(outer);buttons.pack(fill='x',pady=(12,0))
    def config():return validate({k:(None if k in ('gamma','suppression') and v.get()=='' else v.get()) for k,v in variables.items()})
    def start():
        nonlocal last_error
        try:
            c=config();save_settings(c);session.start(c);last_error='';state.configure(text='起動中：モデルの準備を待っています')
        except Exception as e:messagebox.showerror('開始できません',str(e))
    def apply():
        nonlocal pending
        try:
            c=config();save_settings(c)
            if session.running:pending=c;session.stop();state.configure(text='設定を保存しました。再起動しています')
            else:state.configure(text='設定を保存しました')
        except Exception as e:messagebox.showerror('設定を確認してください',str(e))
    start_button=ttk.Button(buttons,text='保存して開始',command=lambda:apply() if session.running else start());start_button.pack(side='left',padx=(0,8))
    ttk.Button(buttons,text='停止',command=lambda:stop()).pack(side='left',padx=8)
    def stop():
        nonlocal pending
        pending=None;session.stop()
    def close():
        nonlocal closing
        closing=True;stop()
    ttk.Button(buttons,text='終了',command=close).pack(side='right')
    # Canvas bindings alone do not receive events over embedded entries/labels.
    # Run before widget class bindings so a closed combobox does not change value.
    for pane,canvas in scroll_panes:
        tag='TanakaCapScroll'+str(canvas)
        def wheel(event,c=canvas):
            if event.delta and c.yview()!=(0.0,1.0):
                steps=max(1,abs(int(event.delta/120)))
                c.yview_scroll(-steps if event.delta>0 else steps,'units')
            return 'break'
        window.bind_class(tag,'<MouseWheel>',wheel)
        def bind_subtree(widget,t=tag):
            widget.bindtags((t,)+widget.bindtags())
            for child in widget.winfo_children():bind_subtree(child,t)
        bind_subtree(pane)
    window.protocol('WM_DELETE_WINDOW',close)
    def tick():
        nonlocal pending,was_running,last_error
        statuses=session.poll();running=session.running
        start_button.configure(state='disabled' if session.stopping else 'normal')
        if was_running and not running:state.configure(text=last_error or '停止しました')
        if session.infer is not None and session.infer.poll() is not None and session.player and session.player.poll() is None and not session.stopping:
            code=session.infer.returncode;session.stop();last_error=f'推論が終了しました (code {code})。下のメッセージを確認してください';state.configure(text=last_error)
        was_running=running
        if pending and not running and not session.stopping:
            c=pending;pending=None
            try:session.start(c);last_error=''
            except Exception as e:messagebox.showerror('再起動できません',str(e))
        def number(kind,key):return f'{statuses[kind][key]:.1f}' if kind in statuses and key in statuses[kind] else '—'
        metrics.configure(text=f'推論 {number("inference","hz")} Hz    描画 {number("player","renderHz")} fps')
        if 'inference' in statuses and not last_error:state.configure(text=f'処理 {number("inference","busyMs")} ms/観測（入力・上限待機を除く）  /  '+('追跡中' if statuses['inference'].get('tracked') else '検出待ち'))
        elif running and not session.stopping and not last_error:state.configure(text='モーション再生中（推論なし）' if session.infer is None else '起動中 / 新しい推論データを待っています')
        lines=[]
        for _ in range(60):
            try:lines.append(session.messages.get_nowait())
            except queue.Empty:break
        if lines:
            messages.configure(state='normal')
            for line in lines:messages.insert('end',line+'\n','warning' if line.startswith('【警告') else 'error' if line.startswith('【エラー') else '')
            if int(messages.index('end-1c').split('.')[0])>100:messages.delete('1.0','end-80l')
            messages.see('end');messages.configure(state='disabled')
        if closing and not running and not session.stopping:session.sock.close();window.destroy();return
        window.after(200,tick)
    if test_hook:test_hook(window,variables,session,{'start':start,'apply':apply,'stop':stop,'close':close})
    tick();window.mainloop()


if __name__=='__main__':main()
