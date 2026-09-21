"""Check native Player window sizing and decoration recovery using demo motion only."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
U=c.WinDLL('user32',use_last_error=True)
VISITOR=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
U.EnumWindows.argtypes=[VISITOR,w.LPARAM]
U.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
U.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
U.GetClientRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
U.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
U.GetWindowLongPtrW.argtypes=[w.HWND,c.c_int];U.GetWindowLongPtrW.restype=c.c_ssize_t
U.SetWindowLongPtrW.argtypes=[w.HWND,c.c_int,c.c_ssize_t];U.SetWindowLongPtrW.restype=c.c_ssize_t
U.SetWindowPos.argtypes=[w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT]

def find(pid):
    handles=[]
    @VISITOR
    def visit(h,_):
        owner=w.DWORD();U.GetWindowThreadProcessId(h,c.byref(owner))
        name=c.create_unicode_buffer(128);U.GetClassNameW(h,name,128)
        if owner.value==pid and name.value=='UnityWndClass':handles.append(h)
        return True
    U.EnumWindows(visit,0)
    return handles[0] if handles else None

def state(h):
    client=w.RECT();outer=w.RECT()
    assert U.GetClientRect(h,c.byref(client)) and U.GetWindowRect(h,c.byref(outer))
    return dict(style=U.GetWindowLongPtrW(h,-16),client=[client.right-client.left,client.bottom-client.top],outer=[outer.right-outer.left,outer.bottom-outer.top])

def main():
    output=ROOT/'results/window-sizing';output.mkdir(parents=True,exist_ok=True)
    avatar=ROOT/'builds/player/avatars/haolan.tcap'
    assert avatar.is_file()
    reports=[]
    for width,height in [(960,540),(1920,1080)]:
        p=subprocess.Popen([str(ROOT/'builds/release-player/TanakaCap.exe'),'-nolog','--avatar',str(avatar),'--expression-mode','auto-custom','--motion-demo','--output-width',str(width),'--output-height',str(height),'--render-fps','60','--error-log',str(output/f'{width}-errors.log')])
        try:
            deadline=time.monotonic()+30;h=None
            while time.monotonic()<deadline:
                assert p.poll() is None,'Player exited'
                h=find(p.pid)
                if h and state(h)['client']==[width,height] and not state(h)['style']&0x00C40000:break
                time.sleep(.2)
            assert h
            time.sleep(2)
            before=state(h)
            assert before['client']==before['outer']==[width,height] and not before['style']&0x00C40000,before
            U.SetWindowLongPtrW(h,-16,before['style']|0x00C40000)
            U.SetWindowPos(h,None,0,0,800,450,0x0036)
            time.sleep(2)
            after=state(h)
            assert after['client']==after['outer']==[width,height] and not after['style']&0x00C40000,after
            reports.append(dict(width=width,height=height,before=before,recovered=after))
        finally:
            p.terminate();p.wait(timeout=15)
    (output/'report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('Native window size, border removal and recovery passed for 960x540 and 1920x1080')

if __name__=='__main__':main()
