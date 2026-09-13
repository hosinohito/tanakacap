"""Repeatable stage timing on the same existing recording, sequential GPU runs."""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video",type=Path,default=ROOT/"results/comparison-takes/20260911T235327-031115Z/camera.avi")
    p.add_argument("--frames",type=int,default=900)
    args=p.parse_args()
    output=ROOT/"results"/("inference-stages-"+str(time.time_ns()));output.mkdir()
    modes={"full":["--body3d","--gaze"],"without-body":["--no-body","--gaze"],
           "face-head":["--no-body"],"face-head-fixed":["--no-body","--fixed-roi"],
           "head-only-fixed":["--head-only","--head-roi-mode","fixed","--roi","618","246","170","165"],
           "head-only-auto":["--head-only"]}
    reports={}
    for name,extra in modes.items():
        command=[sys.executable,"-m","tanakacap","benchmark","--source","video","--video",str(args.video),
                 "--frames",str(args.frames),"--warmup","30","--unity-port","39549","--no-ort-profile",
                 "--arm-depth-mode","front_projection","--shoulder-yaw-mode","face_ratio",*extra]
        with (output/(name+".log")).open("wb") as stream:
            run=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
        log=(output/(name+".log")).read_text(encoding="utf-8",errors="replace")
        if run.returncode: raise RuntimeError("Failed "+name+": "+str(output))
        match=re.search(r"Results: ([^\r\n]+)",log)
        if not match: raise RuntimeError("Missing result path")
        result=Path(match[1])/"report.json"
        report=json.loads(result.read_text(encoding="utf-8"))
        if report["status"]!="completed": raise RuntimeError("Incomplete result")
        reports[name]=dict(report=str(result.relative_to(ROOT)),timings=report["timings"])
        print(name,{k:round(v["p50"],3) for k,v in report["timings"].items() if v and k in
                    ("face_model_ms","body3d_ms","gaze_ms","detector_inference_call_ms","head_model_ms","iteration_ms")},flush=True)
        (output/"summary.json").write_text(json.dumps(reports,indent=2),encoding="utf-8")
    print(output)
if __name__=="__main__":main()
