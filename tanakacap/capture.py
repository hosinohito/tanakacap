"""Bounded latest-frame camera reader. No image or audio recording by default."""
import threading
import time
import math
from dataclasses import dataclass

import cv2
from .camera_compatibility import choose_format, fourcc_name, hints
from .camera_devices import resolve_camera
from .camera_settings import PowerlineSession
from .windows_camera_controls import enumerate_mf_cameras, identity_key, native_modes


def safe_get(cap, key):
    try:
        value=float(cap.get(key))
        return value if math.isfinite(value) else None
    except (cv2.error,ValueError,TypeError):return None


def safe_set(cap, key, value):
    try:return bool(cap.set(key,value))
    except cv2.error:return False


def camera_from_args(args):
    return Camera(args.camera,args.width,args.height,args.fps,args.backend,
                  getattr(args,'pixel_format',None),device_id=getattr(args,'camera_id',''),
                  powerline=getattr(args,'camera_powerline','keep'),lowlight=getattr(args,'camera_lowlight','keep'))


@dataclass
class Frame:
    sequence: int
    acquired: float
    image: object


class LatestFrame:
    def __init__(self):
        self.condition = threading.Condition()
        self.latest = None
        self.error = None
        self.closed = False

    def publish(self, frame):
        with self.condition:
            self.latest = frame
            self.condition.notify_all()

    def fail(self, error):
        with self.condition:
            self.error = error
            self.closed = True
            self.condition.notify_all()

    def next(self, after=-1, timeout=5):
        with self.condition:
            ok = self.condition.wait_for(lambda: self.error or self.closed or
                                         (self.latest is not None and self.latest.sequence > after), timeout)
            if self.error:
                raise RuntimeError(self.error)
            if not ok or self.closed:
                raise TimeoutError('Camera did not deliver a new frame')
            return self.latest


class Camera:
    def __init__(self, index=0, width=1280, height=720, fps=30, backend='msmf', pixel_format=None, *, device_id='', powerline='keep', lowlight='keep'):
        if backend not in ('dshow','msmf'):raise ValueError('Invalid camera backend')
        if pixel_format not in (None,'auto','native','MJPG','YUY2','NV12'):raise ValueError('Invalid camera format')
        if not all(math.isfinite(v) and v>0 for v in (width,height,fps)):raise ValueError('Invalid camera dimensions/rate')
        self.mailbox = LatestFrame()
        self.stop = threading.Event()
        self.metadata = {}
        self.args = index, width, height, fps, backend, pixel_format
        self.device_id=device_id;self.powerline=powerline;self.lowlight=lowlight
        self.thread = threading.Thread(target=self._read, daemon=True)

    def _read(self):
        index, width, height, fps, backend, pixel_format = self.args
        cap = None
        control=None;lowlight_control=None;name='';modes=[]
        try:
            # Stable identity is resolved in the selected backend immediately before open.
            # Never reuse a DSHOW index for MSMF or silently open a replacement device.
            if self.device_id or self.powerline!='keep' or self.lowlight!='keep':
                devices=enumerate_mf_cameras() if backend=='msmf' else None
                if backend=='msmf' and self.device_id:
                    matches=[d for d in devices if identity_key(d['device_id'])==identity_key(self.device_id)]
                    if len(matches)!=1:raise RuntimeError('選択したカメラはこの取得方式では見つかりません。別のカメラへ切り替えず停止しました。')
                    device=matches[0]
                else:device=resolve_camera(index,self.device_id,devices)
                index=device['index'];name=device['name'];self.device_id=device.get('device_id','')
                if self.device_id:
                    try:modes=native_modes(self.device_id)
                    except OSError as error:print('【カメラ】対応モードを取得できません。通常の形式交渉で継続します。 '+str(error),flush=True)
                control=PowerlineSession(self.device_id,self.powerline,warn=lambda message:print(message,flush=True))
                control.start()
                lowlight_control=PowerlineSession(self.device_id,self.lowlight,kind='lowlight',warn=lambda message:print(message,flush=True))
                lowlight_control.start()
            requested_format=choose_format(pixel_format,backend,modes,width,height,fps)
            if modes and not any(m['width']==width and m['height']==height and abs(m['fps']-fps)<.2 and
                                 (not requested_format or fourcc_name(m['fourcc'])==requested_format) for m in modes):
                print('【警告・継続中】要求した解像度・fps・形式の組み合わせが対応モード一覧にありません。実際の取得設定を確認してください。',flush=True)
            for message in hints(name,width,height,fps):print('【カメラ】'+message,flush=True)
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW if backend == 'dshow' else cv2.CAP_MSMF)
            if not cap.isOpened():
                raise RuntimeError(f'カメラ {index} ({backend}) を開けません。他アプリの使用、Windowsのカメラ許可、接続を確認してください。')
            accepted = {'width': safe_set(cap,cv2.CAP_PROP_FRAME_WIDTH, width),
                        'height': safe_set(cap,cv2.CAP_PROP_FRAME_HEIGHT, height),
                        'fps': safe_set(cap,cv2.CAP_PROP_FPS, fps)}
            # Size/rate negotiation can reset the subtype; select the format last.
            format_accepted=safe_set(cap,cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*requested_format)) if requested_format else None
            self.metadata = {'index': index, 'backend': cap.getBackendName(),
                             'requested': [width, height, fps],
                             'reported': [safe_get(cap,cv2.CAP_PROP_FRAME_WIDTH), safe_get(cap,cv2.CAP_PROP_FRAME_HEIGHT),
                                          safe_get(cap,cv2.CAP_PROP_FPS)],
                             'fourcc': safe_get(cap,cv2.CAP_PROP_FOURCC), 'requested_format':requested_format,
                             'format_accepted':format_accepted, 'exposure':safe_get(cap,cv2.CAP_PROP_EXPOSURE),
                             'auto_exposure':safe_get(cap,cv2.CAP_PROP_AUTO_EXPOSURE), 'settings_accepted': accepted,
                             'device_name':name,'native_modes':modes,
                             'powerline':control.status if control else {'requested':'keep'},
                             'lowlight':lowlight_control.status if lowlight_control else {'requested':'keep'}}
            actual_format=fourcc_name(self.metadata['fourcc'])
            self.metadata['actual_format']=actual_format
            self.metadata['format_matches_request']=actual_format==requested_format if requested_format and actual_format else None
            if requested_format and actual_format!=requested_format:
                print(f'【警告・継続中】カメラ形式の要求={requested_format}、報告={actual_format or "不明（API固有値）"}。同じ形式で取得できたとは確認できません。', flush=True)
            if self.metadata['reported'][:2] != [width, height]:
                print(f'WARNING: requested {width}x{height}, received {self.metadata["reported"][:2]}. Check camera index.', flush=True)
            sequence = 0
            rate_start=None;rate_sequence=0;slow_warned=False;rate_reported=False;shape_checked=False
            while not self.stop.is_set():
                ok, image = cap.read()
                acquired = time.perf_counter()
                if not ok or image is None or not getattr(image,'size',0):
                    raise RuntimeError('カメラの画像取得が停止しました。切断・他アプリの使用・USB帯域・対応形式を確認してください。')
                if image.ndim==2:image=cv2.cvtColor(image,cv2.COLOR_GRAY2BGR)
                elif image.ndim==3 and image.shape[2]==4:image=cv2.cvtColor(image,cv2.COLOR_BGRA2BGR)
                elif image.ndim!=3 or image.shape[2]!=3:raise RuntimeError('カメラが未対応の画像配列を返しました。形式を自動または機器既定へ変更してください。')
                if not shape_checked:
                    shape_checked=True;self.metadata['frame_shape']=list(image.shape)
                    if list(image.shape[:2])!=[height,width]:print(f'【警告・継続中】実画像は{image.shape[1]}×{image.shape[0]}です。要求した{width}×{height}とは異なります。',flush=True)
                    if control:control.verify()
                    if lowlight_control:lowlight_control.verify()
                if sequence==30:rate_start=acquired;rate_sequence=sequence
                if rate_start is not None and acquired-rate_start>=3:
                    measured=(sequence-rate_sequence)/(acquired-rate_start)
                    self.metadata['measured_capture_fps']=measured
                    if not rate_reported:
                        print(f'【カメラ】実取得 {measured:.1f}fps / 要求 {fps:g}fps（推論速度とは別）',flush=True)
                        rate_reported=True
                    if not slow_warned and measured<fps*.9:
                        print('【警告・継続中】カメラ取得が要求fpsを下回っています。ちらつき防止・暗所補正・露出・USB接続を確認してください。',flush=True)
                        for message in hints(name,width,height,fps,slow=True):print('【カメラ】'+message,flush=True)
                        slow_warned=True
                    rate_start=acquired;rate_sequence=sequence
                self.mailbox.publish(Frame(sequence, acquired, image))
                sequence += 1
        except Exception as exc:
            for message in hints(name,width,height,fps,failed=True):print('【カメラ】'+message,flush=True)
            self.mailbox.fail(str(exc))
        finally:
            if cap is not None:
                cap.release()
            if lowlight_control:
                try:lowlight_control.close()
                except Exception as error:print('【エラー】暗所補正を復元できません。同じカメラで再起動すると復元を再試行します。 '+str(error),flush=True)
            if control:
                try:control.close()
                except Exception as error:print('【エラー】カメラ設定を復元できません。再接続後に同じカメラで再起動すると復元を再試行します。 '+str(error),flush=True)

    def __enter__(self):
        self.thread.start()
        try:
            self.mailbox.next(timeout=15)
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(timeout=3)
        if self.thread.is_alive():
            print('WARNING: camera driver did not stop within 3 seconds; process exit will release it.')
