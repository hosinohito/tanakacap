"""Read-only coverage and discontinuity audit of the adopted recorded controls."""
import argparse,json
from collections import defaultdict
from pathlib import Path
import numpy as np

def summarize(path,output):
    groups=defaultdict(list)
    for line in path.open(encoding="utf-8"):
        row=json.loads(line);groups[row["stage"]].append(row)
    report={"source":str(path),"scope":"Recorded controls, not human ground truth. Availability is not accuracy; nominal .36 scale is not measured anatomical metres.","stages":{}}
    for stage,rows in groups.items():
        packets=[r["sent_packet"] for r in rows];entry={"frames":len(rows)}
        yaw=[p["torsoYaw"] for p in packets if p.get("torsoTracked")]
        if yaw:entry["absolute_yaw_p50_p95"]=np.percentile(np.abs(yaw),[50,95]).tolist()
        for side in ("left","right"):
            tracked=[p for p in packets if p.get(side+"ArmTracked") and not p.get(side+"ArmHeld")]
            hand=[p for p in packets if p.get(side+"HandTracked")]
            fingers=[p for p in packets if any(p.get(side+"FingerTracked",[]))]
            jumps=[];recoveries=[];previous=None;last_good=None;gap=0
            for p in packets:
                good=p.get(side+"ArmTracked") and not p.get(side+"ArmHeld") and side+"Wrist" in p
                if good:
                    v=np.array([p[side+"Wrist"][k] for k in "xyz"])*.36
                    if previous is not None:jumps.append(float(np.linalg.norm(v-previous)))
                    if gap and last_good is not None:recoveries.append(dict(gap_frames=gap,nominal_wrist_step=float(np.linalg.norm(v-last_good))))
                    previous=last_good=v;gap=0
                else:previous=None;gap+=1
            flex=[p[side+"FingerFlex"] for p in fingers]
            entry[side]={"observed_arm_frames":len(tracked),"palm_frames":len(hand),"any_finger_frames":len(fingers),
                "offscreen_frames":sum(bool(p.get(side+"OutOfView")) for p in packets),
                "nominal_wrist_steps_over_0_10":sum(x>.1 for x in jumps),
                "nominal_wrist_step_p50_p95_max":np.percentile(jumps,[50,95,100]).tolist() if jumps else None,
                "recovery_count":len(recoveries),"largest_recoveries":sorted(recoveries,key=lambda r:r["nominal_wrist_step"],reverse=True)[:3],
                "finger_angle_span_by_joint":np.ptp(flex,axis=0).tolist() if flex else None}
        report["stages"][stage]=entry
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:{"frames":v["frames"],"yaw":v.get("absolute_yaw_p50_p95"),
        **{s:{"arm":v[s]["observed_arm_frames"],"finger":v[s]["any_finger_frames"],"large_steps":v[s]["nominal_wrist_steps_over_0_10"]} for s in ("left","right")}} for k,v in report["stages"].items()},indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args();summarize(a.source,a.output)
