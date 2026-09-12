"""Summarize measured windows without calling their p95 a whole-run percentile."""
import argparse,json
from pathlib import Path
import numpy as np

def read(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8-sig").splitlines()]
def summarize(folder):
    report=json.loads((folder/"report.json").read_text(encoding="utf-8"))
    if report["status"]!="complete":raise ValueError("Incomplete test: "+str(folder))
    rows=[r for r in read(folder/"player.jsonl") if 30<=r["seconds"]<=report["seconds_requested"]]
    if not rows:raise ValueError("No steady windows")
    result={"condition":{k:report.get(k) for k in ("resolution","edge_aa","demo","obs_fps_requested","obs_video")},
        "sampled_seconds":sum(r["windowSeconds"] for r in rows),
        "player_fps_median":float(np.median([r["fps"] for r in rows])),
        "received_hz":sum(r["receivedPackets"] for r in rows)/sum(r["windowSeconds"] for r in rows),
        "one_second_frame_p95_ms_median":float(np.median([r["frameP95Ms"] for r in rows])),
        "worst_frame_ms":max(r["frameMaxMs"] for r in rows),
        "render_submit_ms_median":float(np.median([r["renderSubmitMeanMs"] for r in rows])),
        "gpu_frame_ms_median":None,"latest_input_read_to_render_ms_median":None}
    gpu=[r["gpuFrameMeanMs"] for r in rows if r.get("gpuSamples",0)>0]
    if gpu:result["gpu_frame_ms_median"]=float(np.median(gpu))
    timed=[r for r in rows if r.get("timedPackets",0)>0]
    if timed:
        result["latest_input_read_to_render_ms_median"]=float(np.median([r["latestInputReadToRenderSubmitP50Ms"] for r in timed]))
        result["one_second_input_read_p95_ms_median"]=float(np.median([r["latestInputReadToRenderSubmitP95Ms"] for r in timed]))
        result["send_to_render_ms_median"]=float(np.median([r["sendToRenderSubmitP50Ms"] for r in timed]))
    system=[r for r in read(folder/"system.jsonl") if r["seconds"]>=30]
    result["memory"]={}
    for process in ("player","obs","capture"):
        samples=[r[process] for r in system if process in r]
        if process=="capture" and (folder/"capture-memory.jsonl").exists():
            supplemental=read(folder/"capture-memory.jsonl")
            samples=[r["memory"] for r in supplemental]
            result["capture_memory_supplement_duration_seconds"]=supplemental[-1]["seconds"]-supplemental[0]["seconds"]
        if samples:
            result["memory"][process]={key:dict(first_window_median=float(np.median([r[key] for r in samples[:6]])),
                last_window_median=float(np.median([r[key] for r in samples[-6:]])),peak=max(r[key] for r in samples))
                for key in ("private_mb","working_mb")}
    obs=[r["obs_stats"] for r in system]
    if obs:
        result["obs_fps_median"]=float(np.median([r["activeFps"] for r in obs]))
        result["obs_render_skipped_delta"]=obs[-1]["renderSkippedFrames"]-obs[0]["renderSkippedFrames"]
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("folders",nargs="+",type=Path);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    result={"scope":"Window summaries. GPU diagnostics incur overhead. Existing-video processing is not motion-to-display latency or accuracy.",
            "runs":{str(f):summarize(f) for f in a.folders}}
    a.output.write_text(json.dumps(result,indent=2),encoding="utf-8");print(json.dumps(result,indent=2))
