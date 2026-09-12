"""Isolated OBS + actual Player + GPU inference on existing video. Never streams/records."""
import argparse, ctypes, json, socket, subprocess, sys, time
from pathlib import Path
import numpy as np
import cv2
from obs_phase3 import OBS, ROOT

class Memory(ctypes.Structure):
    _fields_=[("cb",ctypes.c_ulong),("faults",ctypes.c_ulong)]+[(k,ctypes.c_size_t) for k in
       ("peak_working","working","peak_pool","pool","peak_nonpaged","nonpaged","pagefile","peak_pagefile","private")]
def memory(pid):
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.OpenProcess.restype=ctypes.c_void_p
    k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    p=ctypes.WinDLL("psapi")
    p.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Memory),ctypes.c_ulong]
    h=k.OpenProcess(0x410,False,pid)
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    try:
        m=Memory();m.cb=ctypes.sizeof(m)
        if not p.GetProcessMemoryInfo(h,ctypes.byref(m),m.cb):raise ctypes.WinError(ctypes.get_last_error())
        return dict(working_mb=m.working/1048576,private_mb=m.private/1048576)
    finally:k.CloseHandle(h)
class ProcessEntry(ctypes.Structure):
    _fields_=[("size",ctypes.c_ulong),("usage",ctypes.c_ulong),("pid",ctypes.c_ulong),
        ("heap",ctypes.c_size_t),("module",ctypes.c_ulong),("threads",ctypes.c_ulong),
        ("parent",ctypes.c_ulong),("priority",ctypes.c_long),("flags",ctypes.c_ulong),("exe",ctypes.c_wchar*260)]
def memory_tree(pid):
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes=[ctypes.c_ulong,ctypes.c_ulong];k.CreateToolhelp32Snapshot.restype=ctypes.c_void_p
    k.Process32FirstW.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessEntry)]
    k.Process32NextW.argtypes=[ctypes.c_void_p,ctypes.POINTER(ProcessEntry)]
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    snapshot=k.CreateToolhelp32Snapshot(2,0)
    if snapshot==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    parents={}
    try:
        entry=ProcessEntry();entry.size=ctypes.sizeof(entry)
        ok=k.Process32FirstW(snapshot,ctypes.byref(entry))
        while ok:
            parents[entry.pid]=entry.parent
            ok=k.Process32NextW(snapshot,ctypes.byref(entry))
    finally:k.CloseHandle(snapshot)
    ids={pid}
    while True:
        expanded=ids|{child for child,parent in parents.items() if parent in ids}
        if ids==expanded:break
        ids=expanded
    members={str(i):memory(i) for i in ids}
    return {**{key:sum(m[key] for m in members.values()) for key in ("working_mb","private_mb")},"members":members}

def stop(process):
    if process is None or process.poll() is not None:return
    # Request normal teardown on windows owned by this exact child process.
    user=ctypes.WinDLL("user32")
    callback=ctypes.WINFUNCTYPE(ctypes.c_int,ctypes.c_void_p,ctypes.c_ssize_t)
    user.GetWindowThreadProcessId.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    user.PostMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t]
    found=[]
    @callback
    def close(hwnd,param):
        owner=ctypes.c_ulong()
        user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value==process.pid:
            user.PostMessageW(hwnd,0x10,0,0);found.append(hwnd)
        return 1
    user.EnumWindows.argtypes=[callback,ctypes.c_ssize_t]
    user.EnumWindows(close,0)
    if found:
        try:process.wait(10);return
        except subprocess.TimeoutExpired:pass
    process.terminate()
    try:process.wait(10)
    except subprocess.TimeoutExpired:process.kill();process.wait()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds",type=int,default=1800)
    parser.add_argument("--video",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--no-edge-aa",action="store_true")
    parser.add_argument("--gpu-timing",action="store_true",help="Adds profiling overhead; compare with same flag on both sides")
    parser.add_argument("--output-height",type=int,choices=(720,1080),default=720)
    parser.add_argument("--obs-fps",type=int,choices=(30,60),default=60)
    parser.add_argument("--demo",action="store_true",help="Render-only A/B test instead of inference")
    args=parser.parse_args()
    if args.seconds<10:parser.error("At least 10 seconds")
    if not args.demo and (args.video is None or not args.video.is_file()):parser.error("Video not found")
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    # Refuse to take over an already-running isolated server.
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1",4456))==0:raise RuntimeError("Isolated OBS already running")
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1",0));port=probe.getsockname()[1]
    player=obs_process=capture=None;o=None
    report={"status":"running","seconds_requested":args.seconds,"scope":"Existing video stress loop, not sensor/display latency; OBS preview/composite, no encoding/stream/record",
            "edge_aa":not args.no_edge_aa,"demo":args.demo,"resolution":[args.output_height*16//9,args.output_height],"obs_fps_requested":args.obs_fps}
    (out/"report.json").write_text(json.dumps(report,indent=2))
    try:
        obs_path=ROOT/"results/phase3-obs/app/bin/64bit/obs64.exe"
        obs_process=subprocess.Popen([str(obs_path),"--portable","--multi","--minimize-to-tray"],cwd=obs_path.parent,creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(40):
            if obs_process.poll() is not None:raise RuntimeError("Isolated OBS exited")
            try:o=OBS();break
            except OSError:time.sleep(.5)
        if o is None:raise RuntimeError("Isolated OBS not ready")
        if o.call("GetStreamStatus")["outputActive"] or o.call("GetRecordStatus")["outputActive"]:raise RuntimeError("Unexpected active output in test OBS")
        width,height=args.output_height*16//9,args.output_height
        o.call("SetVideoSettings",baseWidth=width,baseHeight=height,outputWidth=width,outputHeight=height,
               fpsNumerator=args.obs_fps,fpsDenominator=1)
        cmd=[str(ROOT/"builds/lab/TanakaCap.exe"),"--port",str(port),"--obs","--output-height",str(height),
             "--performance-log",str(out/"player.jsonl"),"--performance-seconds",str(args.seconds+15),
             "-logFile",str(out/"player.log")]
        if args.gpu_timing:cmd+=["--performance-gpu"]
        if args.no_edge_aa:cmd+=["--no-edge-aa"]
        if args.demo:cmd+=["--motion-demo"]
        player=subprocess.Popen(cmd,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
        if not args.demo:
            settings=json.loads((ROOT/"tracking-settings.json").read_text())
            cmd=[sys.executable,"-m","capture_lab","benchmark","--source","video","--video",str(args.video.resolve()),
                 "--loop-video","--no-log","--frames","0","--parent-pid",str(player.pid),"--unity-port",str(port),"--body3d",
                 "--model","rtmw-l-384","--gaze"]
            for key in ("observation_block","observation_stride","head_pose_mode","head_pitch_gain","mouth_lip_depth_scale",
                        "face_distance_filter","arm_depth_mode","shoulder_yaw_mode","gaze_reference"):
                cmd+=["--"+key.replace("_","-"),str(settings[key])]
            with (out/"capture-console.log").open("w") as console:
                capture=subprocess.Popen(cmd,cwd=ROOT,stdout=console,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        start=time.monotonic();samples=[]
        o.call("SetInputSettings",inputName="TanakaCap",inputSettings={"spoutsenders":"TanakaCap","compositemode":4},overlay=True)
        scene=o.call("GetSceneList")["scenes"][0]["sceneName"]
        screenshots=False
        normalized=False
        report["obs_video"]=o.call("GetVideoSettings")
        with (out/"system.jsonl").open("w") as stream:
            while time.monotonic()-start<args.seconds:
                if player.poll() is not None:raise RuntimeError("Player exited early")
                if capture and capture.poll() is not None:raise RuntimeError("Capture exited early; inspect capture-console.log")
                row={"seconds":time.monotonic()-start,"player":memory(player.pid),"obs":memory(obs_process.pid),"obs_stats":o.call("GetStats")}
                if capture:row["capture"]=memory_tree(capture.pid)
                query=subprocess.run(["nvidia-smi","--query-gpu=utilization.gpu,memory.used,temperature.gpu,power.draw","--format=csv,noheader,nounits"],
                                     capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
                row["gpu_csv"]=query.stdout.strip() if query.returncode==0 else None
                samples.append(row);stream.write(json.dumps(row)+"\n");stream.flush()
                if not normalized and row["seconds"]>10:
                    for item in o.call("GetSceneItemList",sceneName=scene)["sceneItems"]:
                        transform=o.call("GetSceneItemTransform",sceneName=scene,sceneItemId=item["sceneItemId"])["sceneItemTransform"]
                        sw,sh=transform["sourceWidth"],transform["sourceHeight"]
                        if sw<=0 or sh<=0:raise AssertionError("OBS source dimensions not ready")
                        o.call("SetSceneItemTransform",sceneName=scene,sceneItemId=item["sceneItemId"],
                               sceneItemTransform={"scaleX":width/sw,"scaleY":height/sh,"positionX":0.,"positionY":0.,"rotation":0.,
                                                   "cropTop":0,"cropBottom":0,"cropLeft":0,"cropRight":0,"boundsType":"OBS_BOUNDS_NONE"})
                    normalized=True
                if not screenshots and row["seconds"]>30:
                    for source,name in [("TanakaCap","source-start.png"),(scene,"composite-start.png")]:
                        o.call("SaveSourceScreenshot",sourceName=source,imageFormat="png",imageFilePath=str(out/name),imageWidth=width,imageHeight=height)
                    screenshots=True
                time.sleep(min(10,max(0,args.seconds-(time.monotonic()-start))))
        for source,name in [("TanakaCap","source-end.png"),(scene,"composite-end.png")]:
            o.call("SaveSourceScreenshot",sourceName=source,imageFormat="png",imageFilePath=str(out/name),imageWidth=width,imageHeight=height)
        source=cv2.imread(str(out/"source-end.png"),cv2.IMREAD_UNCHANGED)
        if source is None or source.shape!=(height,width,4):raise AssertionError("OBS did not receive RGBA")
        alpha=source[:,:,3]
        report["alpha_pixels"]={key:int(mask.sum()) for key,mask in
            [("transparent",alpha==0),("opaque",alpha==255),("intermediate",(alpha>0)&(alpha<255))]}
        if report["alpha_pixels"]["transparent"]<10000 or report["alpha_pixels"]["opaque"]<10000:
            raise AssertionError("OBS received empty or opaque-only output")
        composite=cv2.imread(str(out/"composite-end.png"),cv2.IMREAD_UNCHANGED)
        background=cv2.resize(cv2.imread(str(ROOT/"results/phase3/checker.png")),(width,height),interpolation=cv2.INTER_LINEAR)
        corner_errors=[]
        for x,y in ((20,20),(width-20,20),(20,height-20),(width-20,height-20)):
            if alpha[y,x]==0:
                corner_errors.append(int(np.max(np.abs(composite[y,x,:3].astype(int)-background[y,x].astype(int)))))
        report["background_corner_errors"]=corner_errors
        if len(corner_errors)<2 or max(corner_errors)>3:raise AssertionError("OBS background or source placement mismatch")
        if screenshots:
            first=cv2.imread(str(out/"source-start.png"),cv2.IMREAD_UNCHANGED)
            report["changed_source_pixels"]=int(np.any(first!=source,axis=2).sum())
            if report["changed_source_pixels"]<1000:raise AssertionError("OBS output did not move")
        if o.call("GetStreamStatus")["outputActive"] or o.call("GetRecordStatus")["outputActive"]:
            raise AssertionError("Unexpected stream/record output")
        # Player owns a graceful Spout shutdown a few seconds after the test window.
        player.wait(timeout=35)
        if player.returncode!=0:raise RuntimeError("Player exit code "+str(player.returncode))
        if capture:
            capture.wait(timeout=20)
            if capture.returncode!=0:raise RuntimeError("Capture exit code "+str(capture.returncode))
        rows=[json.loads(x) for x in (out/"player.jsonl").read_text().splitlines()]
        stable=[r for r in rows if 30<=r["seconds"]<=args.seconds]
        if not stable:stable=rows[3:-1]
        report.update(status="complete",elapsed_seconds=time.monotonic()-start,player_exit=player.returncode,
            player_fps_median=float(np.median([r["fps"] for r in stable])),
            player_frame_p95_ms_median=float(np.median([r["frameP95Ms"] for r in stable])),
            render_submit_ms_median=float(np.median([r["renderSubmitMeanMs"] for r in stable])),
            received_hz=sum(r["receivedPackets"] for r in stable)/sum(r["windowSeconds"] for r in stable),
            memory_first=samples[min(3,len(samples)-1)],memory_last=samples[-1],
            obs_version=o.call("GetVersion")["obsVersion"],recording=False,streaming=False)
    except BaseException as e:
        report.update(status="failed",error=repr(e));raise
    finally:
        stop(capture);stop(player)
        if o:o.close()
        stop(obs_process)
        (out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in report.items() if not k.startswith("memory_")},indent=2),flush=True)
if __name__=="__main__":main()
