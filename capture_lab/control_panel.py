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

ROOT=Path(__file__).resolve().parents[1]
SETTINGS=ROOT/'ui-settings.json'
MODES={'full':'全部 ON','face_head':'顔・頭（目線なし）','head_only':'頭のみ'}
DEFAULT=dict(source='camera',camera=1,video='',avatar=str(ROOT/'builds/lab/avatars/haolan.tcap'),
             mode='full',body=True,gaze=True,detector=True,rate='60',fps=60,width=1920,height=1080,
             aa=True,preview=True,expression='existing',gamma=None,suppression=None,emphasis=0.,gaze_gain=4.,head_pose_mode='pnp',
             brow_exaggeration=0.,eye_exaggeration=0.,eyelid_exaggeration=0.,mouth_exaggeration=0.)


def validate(values):
    data={k:values.get(k,v) for k,v in DEFAULT.items()}
    for key,choices in dict(source=('camera','video','motion'),mode=tuple(MODES),rate=('60','sync','30','custom'),expression=('existing','auto-custom')).items():
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
    cap=c['fps'] if c['rate'] in ('sync','custom') else int(c['rate'])
    player=[str(ROOT/'builds/lab/TanakaCap.exe'),'-nolog','--port',str(port),'--ui-status-port',str(status_port),
            '--avatar',str(Path(c['avatar']).resolve()),'--render-fps',str(cap),'--output-width',str(c['width']),
            '--output-height',str(c['height']),'--expression-mode',c['expression'],'--mouth-corner-emphasis',str(c['emphasis']),
            '--gaze-gain',str(c['gaze_gain'])]
    for key in ('brow_exaggeration','eye_exaggeration','eyelid_exaggeration','mouth_exaggeration'):
        player+=['--'+key.replace('_','-'),str(c[key])]
    if Path(c['avatar']).resolve()==(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap').resolve():player+=['--use-demo-shape-keys']
    if c['rate']=='sync':player+=['--render-sync']
    if not c['aa']:player+=['--no-edge-aa']
    if not c['preview']:player+=['--no-preview']
    for key,flag in [('gamma','--mouth-corner-gamma'),('suppression','--mouth-open-smile-suppression')]:
        if c[key] is not None:player += [flag,str(c[key])]
    if c['source']=='motion':return player+['--motion-demo'],None
    infer=[str(ROOT/'.venv/Scripts/python.exe'),'-m','capture_lab','benchmark','--source',c['source'],'--no-log',
           '--frames','0','--warmup','0','--unity-port',str(port),'--parent-pid',str(player_pid),
           '--status-port',str(status_port),'--inference-limit',str(cap)]
    if c['source']=='video':infer+=['--video',str(Path(c['video']).resolve()),'--loop-video']
    else:infer+=['--camera',str(c['camera'])]
    body=c['mode']=='full' and c['body']
    infer+=['--face-source',tracking.get('face_source','body3d') if body else 'separate']
    for key,default in [('observation_block',3),('observation_stride',1),('head_pose_mode','pnp'),('head_pitch_gain',1.8),
                        ('brow_gain',2.),('mouth_lip_depth_scale',1.5),('face_distance_filter','stable'),('arm_depth_mode','front_projection'),
                        ('shoulder_yaw_mode','face_ratio'),('gaze_reference','contour'),('preprocess_mode','crop'),
                        ('detector_interval',3),('detector_model','yolox-m-human')]:
        value=tracking.get(key,default)
        if key=='head_pose_mode':value=c['head_pose_mode']
        if key=='head_pose_mode' and not body and value in ('depth3d','pnp_depthmouth'):value='pnp'
        infer+=['--'+key.replace('_','-'),str(value)]
    for key in ('batch_eyes','detector_graph'):
        if tracking.get(key,True):infer+=['--'+key.replace('_','-')]
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
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.sock.bind(('127.0.0.1',0));self.sock.setblocking(False)
    @property
    def running(self):return any(p is not None and p.poll() is None for p in (self.player,self.infer))
    def start(self,config, *, frames=0):
        if self.running:raise ValueError('停止が完了してから開始してください')
        c=validate(config)
        if not Path(c['avatar']).is_file():raise ValueError('アバターファイルが見つかりません')
        if c['source']=='video' and not Path(c['video']).is_file():raise ValueError('録画ファイルが見つかりません')
        exe=ROOT/'builds/lab/TanakaCap.exe'
        if not exe.is_file():raise ValueError('Playerをビルドしてください（build-unity-lab.ps1）')
        self.poll();self.status={};self.last={}
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        player,_=commands(c,port,self.sock.getsockname()[1])
        self.player=subprocess.Popen(player,cwd=ROOT)
        try:
            _,infer=commands(c,port,self.sock.getsockname()[1],self.player.pid)
            if infer and frames:infer[infer.index('--frames')+1]=str(frames)
            self.infer=None
            if infer:
                self.infer=subprocess.Popen(infer,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
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
    style=ttk.Style();style.theme_use('clam');style.configure('.',font=('Yu Gothic UI',10))
    style.configure('TLabel',wraplength=610)
    style.configure('Title.TLabel',font=('Yu Gothic UI',19,'bold'));style.configure('Metric.TLabel',font=('Yu Gothic UI',13,'bold'))
    session=Session();pending=None;closing=False;was_running=False;last_error=''
    try:settings=load_settings()
    except Exception as error:settings=DEFAULT.copy();messagebox.showerror('設定を読み込めません',str(error))
    variables={k:(tk.BooleanVar(value=v) if type(v) is bool else tk.StringVar(value='' if v is None else str(v))) for k,v in settings.items()}
    outer=ttk.Frame(window,padding=20);outer.pack(fill='both',expand=True)
    ttk.Label(outer,text='TanakaCap',style='Title.TLabel').pack(anchor='w')
    ttk.Label(outer,text='操作と設定  •  実写カメラ映像は表示しません').pack(anchor='w',pady=(0,12))
    metrics=ttk.Label(outer,text='停止中',style='Metric.TLabel');metrics.pack(anchor='w',pady=8)
    state=ttk.Label(outer,text='設定を確認して開始してください');state.pack(anchor='w')
    tabs=ttk.Notebook(outer);tabs.pack(fill='both',expand=True,pady=12)
    frames={}
    for name in ('入力・推論','描画・OBS','表情'):
        pane=ttk.Frame(tabs);tabs.add(pane,text=name)
        canvas=tk.Canvas(pane,highlightthickness=0,background=style.lookup('TFrame','background'))
        scroll=ttk.Scrollbar(pane,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y')
        canvas.configure(yscrollcommand=scroll.set);canvas.pack(fill='both',expand=True)
        frame=ttk.Frame(canvas,padding=15);frame.columnconfigure(1,weight=1)
        item=canvas.create_window((0,0),window=frame,anchor='nw')
        frame.bind('<Configure>',lambda event,c=canvas:c.configure(scrollregion=c.bbox('all')))
        canvas.bind('<Configure>',lambda event,c=canvas,i=item:c.itemconfigure(i,width=event.width))
        canvas.bind('<MouseWheel>',lambda event,c=canvas:c.yview_scroll(-int(event.delta/120),'units'))
        frames[name]=frame
    display_names={'source':{'camera':'カメラ','video':'保存済み録画','motion':'自作モーション'},
                   'mode':MODES,'rate':{'60':'60 fps','sync':'推論同期','30':'30 fps','custom':'自由入力'},
                   'expression':{'existing':'既存キー優先','auto-custom':'自動独自キー（実験用）'}}
    def row(frame,index,label,key,choices=None):
        ttk.Label(frame,text=label).grid(row=index,column=0,sticky='w',padx=(0,15),pady=9)
        if choices and key in display_names:
            names=display_names[key];shown=tk.StringVar(value=names[variables[key].get()])
            widget=ttk.Combobox(frame,textvariable=shown,values=list(names.values()),state='readonly')
            widget.bind('<<ComboboxSelected>>',lambda event:variables[key].set(next(k for k,v in names.items() if v==shown.get())))
            variables[key].trace_add('write',lambda *args:shown.set(names[variables[key].get()]))
        else:widget=ttk.Combobox(frame,textvariable=variables[key],values=choices,state='readonly') if choices else ttk.Entry(frame,textvariable=variables[key])
        widget.grid(row=index,column=1,sticky='ew');return widget
    f=frames['入力・推論']
    row(f,0,'入力','source',['camera','video','motion'])
    row(f,1,'カメラ番号','camera')
    row(f,2,'録画のパス（映像非表示）','video')
    takes=sorted((ROOT/'results/comparison-takes').glob('*/camera.avi'))
    def choose_take():
        picker=tk.Toplevel(window);picker.title('録画を選択');picker.geometry('650x280')
        box=tk.Listbox(picker,font=('Yu Gothic UI',10));box.pack(fill='both',expand=True)
        for path in takes:box.insert('end',path.parent.name)
        def choose():
            if box.curselection():variables['video'].set(str(takes[box.curselection()[0]]));variables['source'].set('video');picker.destroy()
        ttk.Button(picker,text='この録画を使う',command=choose).pack(pady=8)
    ttk.Button(f,text='保存済み録画から選択',command=choose_take).grid(row=3,column=1,sticky='w')
    row(f,4,'アバター (.tcap)','avatar')
    def avatar():
        path=filedialog.askopenfilename(filetypes=[('TanakaCap avatar','*.tcap')])
        if path:variables['avatar'].set(path)
    ttk.Button(f,text='アバターを選択',command=avatar).grid(row=5,column=1,sticky='w')
    row(f,6,'推論モード','mode',list(MODES))
    ttk.Label(f,text='頭のみは顔ランドマークも省略する軽量構成です').grid(row=7,column=0,columnspan=2,sticky='w')
    parts=ttk.Frame(f);parts.grid(row=8,column=0,columnspan=2,sticky='w',pady=12)
    for key,text in [('body','体・腕・指'),('gaze','目線'),('detector','人物検出')]:ttk.Checkbutton(parts,text=text,variable=variables[key]).pack(side='left',padx=7)
    def parts_state(*args):
        for child in parts.winfo_children():child.configure(state='normal' if variables['mode'].get()=='full' else 'disabled')
    variables['mode'].trace_add('write',parts_state);parts_state()
    ttk.Label(f,text='部位設定は「全部 ON」で使用。体・腕・指は一緒に切り替わります。\n頭のみでは表情と指は動かしません。音声口パクは未対応。').grid(row=9,column=0,columnspan=2,sticky='w')
    cost=ttk.Label(f,text='負荷目安：未計測');cost.grid(row=10,column=0,columnspan=2,sticky='w',pady=14)
    head_choice=row(f,11,'頭角度（size2d=比率試行 / pnp=従来）','head_pose_mode',['size2d','pnp','legacy','depth3d','pnp_depthmouth'])
    def head_choice_state(*args):
        head_choice.configure(state='disabled' if variables['mode'].get()=='head_only' else 'readonly')
    variables['mode'].trace_add('write',head_choice_state);head_choice_state()
    ttk.Label(f,text='比率試行は起動後に正面で短く静止。頭のみモードは別モデルです。').grid(row=12,column=0,columnspan=2,sticky='w')
    f=frames['描画・OBS']
    row(f,0,'描画レート','rate',['60','sync','30','custom'])
    ttk.Label(f,text='推論同期では新しい結果が届いたときにアバター画像を更新').grid(row=1,column=0,columnspan=2,sticky='w')
    row(f,2,'自由入力 fps / 同期時の上限','fps')
    row(f,3,'出力の幅','width');row(f,4,'出力の高さ','height')
    ttk.Button(f,text='Full HD に戻す',command=lambda:(variables['width'].set('1920'),variables['height'].set('1080'))).grid(row=5,column=1,sticky='w')
    ttk.Checkbutton(f,text='軽量アンチエイリアス',variable=variables['aa']).grid(row=6,column=0,columnspan=2,sticky='w',pady=12)
    ttk.Checkbutton(f,text='アバターをウインドウにも表示',variable=variables['preview']).grid(row=7,column=0,columnspan=2,sticky='w')
    ttk.Label(f,text='OBS: Spout ソース名 TanakaCap（透過）\n操作画面はOBS出力に入りません。\n推論は描画の指定上限まで、処理を始める前に待機します。\n推論同期でも通信停止中は10Hz以下で表示を更新します。',wraplength=610).grid(row=8,column=0,columnspan=2,sticky='w',pady=20)
    f=frames['表情']
    row(f,0,'表情方式','expression',['existing','auto-custom'])
    ttk.Label(f,text='既存キーは Perfect Sync → MMD → VRC の順に使用').grid(row=1,column=0,columnspan=2,sticky='w')
    exaggeration_widgets=[]
    for index,key,label,lo,hi in [(2,'brow_exaggeration','眉の大げさ度',0,1),(4,'eye_exaggeration','目（目線）の大げさ度',0,1),
                                 (6,'eyelid_exaggeration','まぶた（閉じ）の大げさ度',0,1),(8,'mouth_exaggeration','口の大げさ度',0,1),
                                 (10,'gamma','口角ガンマ',.25,4),(12,'suppression','開口時の口角上げ抑制',0,1),(14,'emphasis','口角の追加強調',0,1),(16,'gaze_gain','目線の基準感度',.5,6)]:
        entry=row(f,index,label,key)
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
    ttk.Button(f,text='口角をモード既定へ戻す',command=lambda:(variables['gamma'].set(''),variables['suppression'].set(''),variables['emphasis'].set('0'))).grid(row=18,column=1,sticky='w',pady=12)
    ttk.Label(f,text='大げさ度: 0は追加強調なし、1は最大。適用すると再起動します。\n保存デモアバターは4項目とも常に最大です。\n口角の空欄はモード既定。対応キーがない動きは追加されません。').grid(row=19,column=0,columnspan=2,sticky='w')
    def demo_strength_state(*args):
        try:is_demo=Path(variables['avatar'].get()).resolve()==(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap').resolve()
        except (OSError,ValueError):is_demo=False
        for key,entry,scale in exaggeration_widgets:
            if is_demo:variables[key].set('1')
            entry.configure(state='disabled' if is_demo else 'normal');scale.configure(state='disabled' if is_demo else 'normal')
    variables['avatar'].trace_add('write',demo_strength_state);demo_strength_state()
    messages=tk.Text(outer,height=3,font=('Yu Gothic UI',9),state='disabled');messages.pack(fill='x')
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
    start_button=ttk.Button(buttons,text='開始',command=start);start_button.pack(side='left',padx=(0,8))
    ttk.Button(buttons,text='停止',command=lambda:stop()).pack(side='left',padx=8)
    ttk.Button(buttons,text='保存して適用（実行中は再起動）',command=apply).pack(side='right')
    def stop():
        nonlocal pending
        pending=None;session.stop()
    def close():
        nonlocal closing
        closing=True;stop()
    window.protocol('WM_DELETE_WINDOW',close)
    def tick():
        nonlocal pending,was_running,last_error
        statuses=session.poll();running=session.running
        start_button.configure(state='disabled' if running or session.stopping else 'normal')
        if was_running and not running:state.configure(text=last_error or '停止しました')
        if session.infer is not None and session.infer.poll() is not None and session.player and session.player.poll() is None and not session.stopping:
            code=session.infer.returncode;session.stop();last_error=f'推論が終了しました (code {code})。下のメッセージを確認してください';state.configure(text=last_error)
        was_running=running
        if pending and not running and not session.stopping:
            c=pending;pending=None
            try:session.start(c);last_error=''
            except Exception as e:messagebox.showerror('再起動できません',str(e))
        def number(kind,key):return f'{statuses[kind][key]:.1f}' if kind in statuses and key in statuses[kind] else '—'
        metrics.configure(text=f'推論 {number("inference","hz")} Hz    描画 {number("player","renderHz")} fps    受信 {number("player","receiveHz")} Hz')
        if 'inference' in statuses and not last_error:state.configure(text=f'処理 {number("inference","busyMs")} ms/観測（入力・上限待機を除く）  /  '+('追跡中' if statuses['inference'].get('tracked') else '検出待ち'))
        elif running and not session.stopping and not last_error:state.configure(text='モーション再生中（推論なし）' if session.infer is None else '起動中 / 新しい推論データを待っています')
        try:
            costs=json.loads((ROOT/'docs/ui-costs.json').read_text(encoding='utf-8'))
            m=variables['mode'].get()
            if variables['source'].get()=='motion' or (m=='full' and not all(variables[k].get() for k in ('body','gaze','detector'))):raise ValueError()
            ratio=costs['modes'][m]['ratio'];cost.configure(text=f'負荷目安：約{ratio}倍（頭のみ=1、推論1回の処理時間）\n録画での参考値。描画・待機を除く。')
        except (OSError,ValueError,KeyError):cost.configure(text='モーション再生は推論なし' if variables['source'].get()=='motion' else '負荷目安：この構成は未計測')
        lines=[]
        for _ in range(60):
            try:lines.append(session.messages.get_nowait())
            except queue.Empty:break
        if lines:
            messages.configure(state='normal');messages.insert('end','\n'.join(lines)+'\n')
            if int(messages.index('end-1c').split('.')[0])>100:messages.delete('1.0','end-80l')
            messages.see('end');messages.configure(state='disabled')
        if closing and not running and not session.stopping:session.sock.close();window.destroy();return
        window.after(200,tick)
    if test_hook:test_hook(window,variables,session,{'start':start,'apply':apply,'stop':stop,'close':close})
    tick();window.mainloop()


if __name__=='__main__':main()
