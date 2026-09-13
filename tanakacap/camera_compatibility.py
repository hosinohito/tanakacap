"""Source-backed camera quirks. Hints are not claims about untested hardware."""
import math
import re


def fourcc_name(value):
    if value is None or not math.isfinite(value) or value<0 or value>0xffffffff:return None
    raw=int(value).to_bytes(4,'little')
    return raw.decode('ascii') if all(32<=v<127 for v in raw) else None


def choose_format(requested, backend, modes, width, height, fps):
    if requested=='native':return None
    if requested not in (None,'auto'):return requested
    matching=[m for m in modes if m['width']==width and m['height']==height and abs(m['fps']-fps)<.2]
    if matching:
        available={fourcc_name(m['fourcc']) for m in matching}
        # Original Facecam and some uncompressed-only devices have no MJPEG mode.
        for value in ('MJPG','NV12','YUY2'):
            if value in available:return value
        return None
    return 'MJPG' if backend=='dshow' else None


def hints(name, width, height, fps, *, slow=False, failed=False):
    name=name.casefold();messages=[]
    if re.search(r'\bc922\b',name):
        if fps>30 and (width>1280 or height>720):
            messages.append('C922の60fpsは720p向けです。カメラ解像度を1280×720にして比較してください。')
        if slow:messages.append('C922ではLow Light Compensationがfpsを下げる場合があります。照明とLogitech側の設定を確認してください。ChromaCam経由は720p/30fpsの制限があります。')
    if name in ('elgato facecam','facecam'):
        if fps<=30:messages.append('初代Facecamは30fps要求時に15〜30fpsの可変動作になります。一定速度を優先するならカメラfpsを60にして比較できます。')
        if failed or slow:messages.append('初代FacecamはUSB 3.0が必要です。付属ケーブル・直結・USB帯域の競合を確認してください。')
    if 'facecam' in name:
        if 'mk.2' in name or 'mk2' in name or 'mk 2' in name:
            if failed or slow:messages.append('Facecam MK.2はUSB 2.0接続時にMJPEGのみ対応します。形式をMJPEGにするかUSB 3.0接続を確認してください。')
        if slow:messages.append('Facecamはシャッター速度でもfpsが変わります。Camera Hubの露出とちらつき防止を確認してください。')
    if 'brio' in name and (failed or slow):
        messages.append('BRIOはUSB帯域や接続条件で高解像度モードが使えない場合があります。4K Stream Editionの4KにはUSB 3.0が必要です。他のBRIO製品へ同じ制限を一律適用はしていません。')
    if 'obs virtual camera' in name and (failed or slow):
        messages.append('OBS仮想カメラはOBS側の仮想カメラ開始・出力設定を確認してください。物理カメラの露出設定は適用しません。')
    if 'cms-v43bk' in name and slow:
        messages.append('CMS-V43BKでは50Hzのちらつき防止で約25fps、無効/60Hzで約30fpsを実測しています。照明の縞を確認しながら設定を比較してください。')
    return messages
