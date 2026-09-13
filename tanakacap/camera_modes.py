"""Device-advertised camera mode choices; no network or frame capture."""
import json
import math
import subprocess
import sys


def supported_modes(raw):
    from .camera_compatibility import fourcc_name
    result=set()
    for m in raw:
        try:
            w,h,f=int(m['width']),int(m['height']),float(m['fps'])
            fmt=fourcc_name(m['fourcc'])
            if 64<=w<=8192 and 64<=h<=8192 and math.isfinite(f) and 1<=f<=240 and fmt in ('MJPG','NV12','YUY2'):
                result.add((w,h,f,fmt))
        except (KeyError,ValueError,TypeError,OverflowError):continue
    return sorted(result)


def default_fps(modes):
    rates=sorted({m[2] for m in modes})
    if not rates:raise ValueError('利用できる対応モードが取得できませんでした')
    near=[f for f in rates if abs(f-60)<.1]
    if near:return min(near,key=lambda f:abs(f-60))
    below=[f for f in rates if f<=60]
    return max(below) if below else min(rates)


def resolutions(modes,fps):
    return sorted({(w,h) for w,h,f,fmt in modes if abs(f-fps)<.00001},key=lambda wh:wh[0]*wh[1],reverse=True)


def query_modes(device_id):
    # A driver can hang during activation; isolate it from the Tk process.
    python=sys.executable
    if python.lower().endswith('pythonw.exe'):python=python[:-11]+'python.exe'
    r=subprocess.run([python,'-X','utf8','-m','tanakacap.camera_modes',device_id],
                     capture_output=True,text=True,encoding='utf-8',errors='replace',
                     timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if r.returncode:raise OSError(r.stderr.strip()[-500:] or '対応モード取得に失敗しました')
    return supported_modes(json.loads(r.stdout))


if __name__=='__main__':
    from .windows_camera_controls import native_modes
    print(json.dumps(native_modes(sys.argv[1])))
