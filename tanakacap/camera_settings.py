"""Session-local camera controls with a recovery journal for abnormal termination."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
from .windows_camera_controls import WindowsPowerline, identity_key

POWERLINE={'keep':None,'off':0,'50hz':1,'60hz':2}


def process_alive(pid):
    if pid==os.getpid():return True
    if os.name!='nt':
        try:os.kill(pid,0);return True
        except ProcessLookupError:return False
        except PermissionError:return True
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:return ctypes.get_last_error()!=87 # Missing PID vs denied/unknown.
    try:
        code=ctypes.c_ulong()
        return not kernel.GetExitCodeProcess(handle,ctypes.byref(code)) or code.value==259
    finally:kernel.CloseHandle(handle)


class PowerlineSession:
    def __init__(self, device_id, mode='keep', *, directory=None, provider=None, warn=print, kind='powerline'):
        if kind not in ('powerline','lowlight'):raise ValueError('Invalid camera control')
        self.choices=POWERLINE if kind=='powerline' else {'keep':None,'fixed':0,'variable':1}
        if mode not in self.choices:raise ValueError('Invalid camera control mode')
        self.device_id=device_id;self.mode=mode
        self.warn=warn if kind=='powerline' else lambda message:warn(message.replace('ちらつき防止','暗所補正'))
        self.provider=provider or WindowsPowerline(device_id,kind)
        directory=directory or Path(__file__).resolve().parents[1]/'logs/camera-settings'
        self.path=Path(directory)/(hashlib.sha256(identity_key(device_id).encode()).hexdigest()+('' if kind=='powerline' else '-lowlight')+'.json')
        self.original=None
        self.status={'requested':mode,'applied':False}

    def restore_record(self, record):
        if identity_key(record.get('device_id',''))!=identity_key(self.device_id):raise RuntimeError('Camera recovery identity mismatch')
        expected=tuple(record['original'])
        if tuple(self.provider.write(*expected))!=expected:raise RuntimeError('カメラのちらつき防止設定を復元できません。')
        self.path.unlink()

    def start(self):
        if self.path.exists():
            record=json.loads(self.path.read_text(encoding='utf-8'))
            if process_alive(record['pid']):raise RuntimeError('同じカメラの設定を別の実行が使用中です。先に停止してください。')
            self.restore_record(record)
            self.warn('【カメラ】前回中断したちらつき防止設定を復元しました。')
        if self.mode=='keep':return self.status
        if not self.device_id:
            self.warn('【警告・継続中】カメラを一意に識別できないため、ちらつき防止は変更していません。')
            return self.status
        try:
            original=tuple(self.provider.read())
            valid_values=(0,1,2,3) if self.choices is POWERLINE else (0,1)
            if len(original)!=2 or original[0] not in valid_values or original[1] not in (0,1,2,3):
                raise OSError('Camera returned an unknown control value or flags')
        except OSError as error:
            self.warn('【警告・継続中】ちらつき防止の取得が未対応または失敗しました。元設定で継続します。 '+str(error))
            return self.status
        self.status['original']=original
        target=self.choices[self.mode]
        if original[0]==target:
            self.status.update(applied=True,actual=original[0]);return self.status
        # Exclusive durable write before changing the device. Failure leaves it unchanged.
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('x',encoding='utf-8') as stream:
            json.dump(dict(device_id=self.device_id,pid=os.getpid(),original=original),stream)
            stream.flush();os.fsync(stream.fileno())
        self.original=original
        try:
            actual=self.provider.write(target,2) # KS manual; some drivers read flags back as 0.
            if actual[0]!=target:raise OSError('Requested setting was not applied')
            self.status.update(applied=True,actual=actual[0])
            self.warn('【カメラ】ちらつき防止: '+self.mode+'（適用確認済み）')
        except OSError as error:
            self.close() # If this fails, abort rather than claim unchanged state.
            self.warn('【警告・継続中】ちらつき防止の変更に失敗したため元設定へ戻しました。 '+str(error))
        return self.status

    def verify(self):
        if not self.status['applied']:return
        try:
            actual=self.provider.read()[0]
            if actual!=self.choices[self.mode]:
                self.status.update(applied=False,actual=actual)
                self.warn('【警告・継続中】撮影開始時にちらつき防止設定が変わりました。要求値は現在適用されていません。')
        except OSError as error:
            self.status['verification_error']=str(error)
            self.warn('【警告・継続中】撮影開始後のちらつき防止設定は読み戻せませんでした。 '+str(error))

    def close(self):
        if self.original is None:return
        self.restore_record(dict(device_id=self.device_id,original=self.original))
        self.original=None
        self.warn('【カメラ】ちらつき防止を起動前の設定へ復元しました。')
