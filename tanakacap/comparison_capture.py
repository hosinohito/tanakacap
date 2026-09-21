"""User-started lossless camera take. No inference, audio, or network transfer."""
from . import camera_display
import argparse,json,time,shutil
from datetime import datetime,timezone
from pathlib import Path
import cv2
import numpy as np
from .capture import Camera
from .models import ROOT,sha256

STAGES=[
 ('neutral',10,'正面で静止','口を閉じ、顔と両肩を映してください。'),
 ('arm_calibration',10,'両腕をゆっくり伸ばす','画面内で左右に広げ、肘を伸ばしてください。'),
 ('distance_still',15,'動かず静止','顔の前後位置のガタつきを測ります。'),
 ('distance_move',15,'接近して戻る','ゆっくり前に寄って戻る。最後に少し素早く1回。'),
 ('head_only',15,'頭だけ上下・左右','体の位置を保ち、うなずいてから左右を向いてください。'),
 ('left_fingers_face',15,'左手：顔の横でグー・パー','肘の位置をなるべく固定して、5回ゆっくり開閉。'),
 ('right_fingers_face',15,'右手：顔の横でグー・パー','肘の位置をなるべく固定して、5回ゆっくり開閉。'),
 ('hands_chest',15,'胸の前で両手をグー・パー','両手が重ならないように開閉してください。'),
 ('palms',15,'手のひら・手の甲','両手をゆっくり裏返して戻してください。'),
 ('torso_yaw',15,'胴体を左右にひねる','顔はできるだけカメラへ。左右2回ずつ。'),
 ('arm_depth',20,'腕を前へ・交差・外へ引く','順に行い、各姿勢で少し止まってください。'),
 ('loss_return',15,'片手ずつ画面外へ・戻す','最後に顔を手で一瞬隠して戻してください。'),
 ('end_still',10,'最後に正面で静止','姿勢を戻して、そのまま終了を待ってください。')]

FACE_STAGES=[('free',30,'録画中','')]
PROFILES={'body':STAGES,'face-head':FACE_STAGES}

def stage_at(seconds,stages=None):
    elapsed=0.
    for key,duration,title,instruction in (STAGES if stages is None else stages):
        if seconds<elapsed+duration:return key,title,instruction,elapsed+duration-seconds
        elapsed+=duration
    return None

class TakeWriter:
    def __init__(self,path,size,fps,settings,camera,profile='body'):
        stages=PROFILES[profile]
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=False)
        self.size=tuple(size);self.fps=fps;self.count=0;self.last_time=None;self.last_sequence=None;self.skipped=0
        self.writer=cv2.VideoWriter(str(self.path/'camera.avi'),cv2.CAP_FFMPEG,cv2.VideoWriter_fourcc(*'HFYU'),fps,self.size)
        if not self.writer.isOpened():raise RuntimeError('Lossless HuffYUV writer unavailable')
        self.log=(self.path/'frames.jsonl').open('w',encoding='utf-8')
        self.meta={'version':1,'status':'recording','codec':'HuffYUV','video_file':'camera.avi','size':size,'nominal_fps':fps,'settings':settings,'camera':camera,'stages':STAGES,'audio':False,'mirrored_file':False,'timestamp_note':'After camera read, not exposure. AVI/MKV nominal timestamps are not used for replay.'}
        self.meta.update(profile=profile,stages=stages)
        self.save()
    def save(self):
        (self.path/'take.json').write_text(json.dumps(self.meta,ensure_ascii=False,indent=2),encoding='utf-8')
    def append(self,image,timestamp,sequence,stage):
        if image.shape[:2]!=self.size[::-1]:raise ValueError('Camera resolution changed')
        if not np.isfinite(timestamp) or (self.last_time is not None and timestamp<=self.last_time):raise ValueError('Non-monotonic capture timestamp')
        if self.last_sequence is not None:
            if sequence<=self.last_sequence:raise ValueError("Non-monotonic camera sequence")
            self.skipped+=sequence-self.last_sequence-1
        self.last_sequence=sequence
        self.writer.write(image)
        self.log.write(json.dumps({'frame':self.count,'time':timestamp,'sequence':sequence,'stage':stage})+'\n')
        self.last_time=timestamp;self.count+=1
    def finish(self,status='complete',error=None):
        self.writer.release();self.log.close()
        self.meta.update(status=status,frames=self.count,error=error,skipped_camera_frames=self.skipped,duration_seconds=self.last_time)
        if self.count:
            self.meta['video_sha256']=sha256(self.path/'camera.avi')
            self.meta['timeline_sha256']=sha256(self.path/'frames.jsonl')
        self.save()

def camera_options(camera_index=None):
    """Reuse the UI's selected device without opening or enumerating cameras."""
    path=ROOT/'ui-settings.json'
    saved=json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else {}
    device_id=saved.get('camera_id','') if camera_index is None else ''
    index=int(saved.get('camera',0)) if camera_index is None else camera_index
    if index<0 and not device_id:
        raise ValueError('通常UIで録画に使うカメラを選択して保存してください。')
    return dict(index=index,device_id=device_id,width=int(saved.get('camera_width',1280)),
                height=int(saved.get('camera_height',720)),fps=float(saved.get('camera_fps',30)),
                backend=saved.get('camera_backend','dshow'),pixel_format=saved.get('camera_format','auto'),
                powerline=saved.get('camera_powerline','keep') if camera_index is None else 'keep',
                lowlight=saved.get('camera_lowlight','keep') if camera_index is None else 'keep')


def record(camera_index=None,profile='body'):
    import tkinter as tk
    from tkinter import messagebox
    settings=json.loads((ROOT/'tracking-settings.json').read_text())
    stages=PROFILES[profile];duration=sum(stage[1] for stage in stages)
    options=camera_options(camera_index)
    window=tk.Tk();window.title('TanakaCap モデル比較用 撮影');window.geometry('960x730')
    title=tk.StringVar(value='カメラを準備しています');hint=tk.StringVar(value='開始ボタンを押すまでは映像を保存しません。音声は録音しません。')
    tk.Label(window,textvariable=title,font=('Yu Gothic UI',21,'bold')).pack(pady=8)
    tk.Label(window,textvariable=hint,font=('Yu Gothic UI',13),wraplength=930).pack()
    preview=tk.Label(window,text='カメラ映像は非表示です。' if not camera_display.allowed() else '');preview.pack(pady=5)
    status=tk.StringVar();tk.Label(window,textvariable=status,wraplength=930).pack()
    take=None;started=None;countdown=None;last_sequence=-1;camera=None
    def finish(result='interrupted',error=None):
        nonlocal take,started,countdown
        if countdown is not None:
            countdown=None;button.config(state='normal');title.set('撮影待機')
        if take:
            path=take.path;take.finish(result,error);take=None;started=None
            title.set('撮影完了' if result=='complete' else '撮影を中断しました')
            hint.set('画面を閉じて「撮影した」と伝えてください。' if result=='complete' else '最初から撮り直せます。中断分は比較に使いません。')
            status.set(str(path));button.config(state='normal')
    def start():
        nonlocal countdown
        countdown=time.perf_counter()+3;button.config(state='disabled')
    def close():
        finish();window.destroy()
    button=tk.Button(window,text=f'撮影開始（{duration}秒）',font=('Yu Gothic UI',15),command=start);button.pack(pady=10)
    tk.Button(window,text='中断',command=lambda:finish()).pack()
    window.protocol('WM_DELETE_WINDOW',close)
    try:
        camera=Camera(**options);camera.__enter__()
        title.set('撮影待機' if profile=='face-head' else 'おなか〜頭、左右の手が映る位置へ')
        def tick():
            nonlocal take,started,countdown,last_sequence
            try:
                frame=camera.mailbox.latest
                if camera.mailbox.error:raise RuntimeError(camera.mailbox.error)
                clock=time.perf_counter()
                if frame is not None and clock-frame.acquired>5:raise RuntimeError("カメラ映像が5秒以上停止しています")
                if countdown is not None:
                    title.set(f'撮影まで {max(1,int(countdown-clock)+1)}')
                    if clock>=countdown:
                        if frame is None:raise RuntimeError('カメラから画像が届いていません。')
                        if shutil.disk_usage(ROOT).free<30*1024**3:raise RuntimeError('撮影には30GB以上の空きが必要です')
                        path=ROOT/'results'/'comparison-takes'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-%fZ')
                        take=TakeWriter(path,list(frame.image.shape[1::-1]),options['fps'],settings,camera.metadata,profile)
                        started=frame.acquired;countdown=None;last_sequence=-1
                if frame is not None and frame.sequence!=last_sequence:
                    if take:
                        elapsed=frame.acquired-started;stage=stage_at(elapsed,stages)
                        if stage is None:finish('complete')
                        else:
                            key,label,instruction,remaining=stage
                            title.set(f'{label}  残り{int(remaining)+1}秒');hint.set(instruction)
                            take.append(frame.image,elapsed,frame.sequence,key)
                            status.set(f'録画中 {take.count}フレーム / {elapsed:.1f}秒  |  ローカル保存・音声なし')
                    last_sequence=frame.sequence
                    camera_display.update_tk_preview(preview, frame.image)
                window.after(10,tick)
            except Exception as exc:
                countdown=None;finish('failed',str(exc));messagebox.showerror('撮影エラー',str(exc));window.destroy()
        tick();window.mainloop()
    finally:
        if take:take.finish('interrupted')
        if camera:camera.__exit__()

def main():
    parser=argparse.ArgumentParser(allow_abbrev=False);camera_display.add_argument(parser);parser.add_argument('--camera',type=int)
    parser.add_argument('--profile',choices=list(PROFILES),default='body')
    args=parser.parse_args();record(args.camera,args.profile)
if __name__=='__main__':main()
