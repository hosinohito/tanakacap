"""Render real PhysBone and the current independent solver together in the Editor."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"results/physbone-reference"
OUT=ROOT/"results/avatar-videos/physbone-vs-independent"
FF=ROOT/"tools/bin/ffmpeg.exe"
def run(command,timeout=900):
    subprocess.run(list(map(str,command)),cwd=ROOT,check=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--encode-existing",action="store_true");args=parser.parse_args()
    if not args.encode_existing:OUT.mkdir(parents=True,exist_ok=False)
    unity=Path(r"C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe")
    if not args.encode_existing:run([unity,"-batchmode","-force-d3d11","-projectPath",BASE/"project","-executeMethod",
         "PhysReferenceSetup.Run","--phys-video",OUT,"-logFile",OUT/"editor.log"],timeout=900)
    log=(OUT/"editor.log").read_text(encoding="utf-8",errors="replace")
    if "TANAKACAP_PHYS_VIDEO_COMPLETE frames=1260" not in log or "Exception:" in log:
        raise RuntimeError("Editor video capture incomplete")
    if not args.encode_existing:
        for name in ("frames.jsonl","manifest.json","warnings.txt"):shutil.copy2(BASE/name,OUT/name)
    rows=[json.loads(s) for s in (OUT/"frames.jsonl").open(encoding="utf-8")]
    if len(rows)!=1260 or not all(abs(r["dt"]-1/60)<1e-6 for r in rows[1:]):raise RuntimeError("Video clocks invalid")
    for key in ("referenceAngle","independentAngle"):
        a=np.asarray([r[key] for r in rows])
        if not np.isfinite(a).all() or np.ptp(a[180:540],axis=0).max()<1:raise RuntimeError("A solver is not moving")
    (OUT/"report.json").write_text(json.dumps(dict(status="encoding",frames=len(rows))),encoding="utf-8")
    labels={"left":"本家 PhysBone  /  SDK 3.10.5","right":"独自実装  /  現在の減衰設定",
            "rest":"静止・初期のなじみ","head":"頭を左右に振る（同じ入力）",
            "body":"体を前後・左右に傾ける（同じ入力）","settle":"動作停止後の揺れ・収束"}
    for name,value in labels.items():(OUT/(name+".txt")).write_text(value,encoding="utf-8")
    def quote(path):return path.as_posix().replace(":","\\:")
    font="C\\:/Windows/Fonts/meiryo.ttc"
    def text(name,x,y,enable=None):
        f=f"drawtext=fontfile='{font}':textfile='{quote(OUT/(name+'.txt'))}':fontcolor=white:fontsize=26:x={x}:y={y}"
        if enable:f+=f":enable='{enable}'"
        return f
    filt="scale=1728:972,pad=1920:1080:96:54:color=0x121821,"
    filt+=",".join([text("left",90,9),text("right",1030,9),
                   text("rest",90,1044,"lt(t,3)"),text("head",90,1044,"between(t,3,8.9999)"),
                   text("body",90,1044,"between(t,9,14.9999)"),text("settle",90,1044,"gte(t,15)")])
    videos=[]
    for name in ("front","hair-closeup"):
        raw=OUT/(name+"-raw.mp4");target=OUT/(name+".mp4")
        run([FF,"-hide_banner","-loglevel","error","-y","-i",raw,"-vf",filt,"-an","-c:v","libx264",
             "-preset","fast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",target])
        slow=OUT/(name+"-half-speed.mp4")
        run([FF,"-hide_banner","-loglevel","error","-y","-i",target,"-vf","setpts=2*PTS","-r","60",
             "-an","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",slow])
        for video in (target,slow):
            run([FF,"-hide_banner","-loglevel","error","-xerror","-i",video,"-f","null","-"])
            cap=cv2.VideoCapture(str(video));frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS)
            if fps!=60 or abs(frames-(1260 if video==target else 2520))>1:raise RuntimeError("Unexpected video duration")
            cap.set(cv2.CAP_PROP_POS_FRAMES,360 if video==target else 720);ok,im=cap.read();cap.release()
            if not ok:raise RuntimeError("No video pixels")
            videos.append(dict(path=video.name,frames=frames,fps=fps,bytes=video.stat().st_size))
            if video==target:cv2.imwrite(str(OUT/(name+"-preview.jpg")),im,[cv2.IMWRITE_JPEG_QUALITY,70])
    error=np.asarray([r["errorDegrees"] for r in rows])
    report=dict(status="complete",sdk="3.10.5",independent_damping=1.5,frames=1260,simulation_fps=60,
                initial_dt=rows[0]["dt"],mean_rotation_error=float(error.mean()),videos=videos,
                scope="Actual isolated Editor SDK vs independent solver, same authored motion. Not camera capture or realtime performance. Original prefab T-pose; no animation controllers.")
    (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(OUT,flush=True)
if __name__=="__main__":main()
