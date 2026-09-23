"""Quantify mirror consistency on saved paired hand predictions, not accuracy."""
import argparse,json
from pathlib import Path
import numpy as np

def run(output):
    variants={n:[json.loads(x) for x in (output/n/"frames.jsonl").read_text().splitlines()] for n in ("original","mirrored","mirror-z-only","mirror-xy-only")}
    report={"scope":"All sides restored to original identities; no ground truth. Percentiles are responsiveness/consistency, not accuracy.","hands":{}}
    for side,k in [("left",0),("right",21)]:
        h={};report["hands"][side]=h
        paired=[(a,b) for a,b in zip(variants["original"],variants["mirrored"]) if "xy" in a and "xy" in b]
        xy=[];depth=[];angles=[];zonly=[];xyonly=[]
        for a,b in paired:
            x,y=[np.array(r["xy"],float)[k:k+21] for r in (a,b)]
            z,w=[np.array(r["z"],float)[k:k+21] for r in (a,b)]
            valid=(np.array(a["scores"])[k:k+21]>=.3)&(np.array(b["scores"])[k:k+21]>=.3)
            xy.extend(np.linalg.norm(x-y,axis=1)[valid]);depth.extend(abs((z-z[0])-(w-w[0]))[valid]*1000)
            i=a["frame"]
            def angle(r,s):
                u=r["normal"][side];v=s["normal"][side]
                return None if u is None or v is None else float(np.degrees(np.arccos(np.clip(np.dot(u,v),-1,1))))
            for values,r,s in [(angles,a,b),(zonly,b,variants["mirror-z-only"][i]),(xyonly,a,variants["mirror-xy-only"][i])]:
                value=angle(r,s)
                if value is not None:values.append(value)
        h["xy_difference_px_p50_p95"]=np.percentile(xy,[50,95]).tolist()
        h["relative_z_difference_mm_p50_p95"]=np.percentile(depth,[50,95]).tolist()
        h["palm_original_vs_mirror_deg_p50_p95"]=np.percentile(angles,[50,95]).tolist()
        h["palm_mirror_vs_zonly_deg_p50_p95"]=np.percentile(zonly,[50,95]).tolist()
        h["palm_original_vs_xyonly_deg_p50_p95"]=np.percentile(xyonly,[50,95]).tolist()
        h["variants"]={}
        for name,rows in variants.items():
            f=np.array([r["packet"][side+"FingerFlex"] for r in rows]);valid=np.array([r["packet"][side+"FingerTracked"] for r in rows])
            p95=[float(np.percentile(f[valid[:,j//3],j],95)) if valid[:,j//3].any() else None for j in range(15)]
            h["variants"][name]=dict(valid=valid.sum(axis=0).tolist(),valid_angle_p95=p95)
    report["palm_triangle_at_7_seconds"]={}
    for name,rows in variants.items():
        a=[]
        for i in (225,228,231,234):
            r=rows[i];p=np.array(r["xy"])[[0,5,17]];z=np.array(r["z"])[[0,5,17]]
            u,v=p[1]-p[0],p[2]-p[0];area=float(u[0]*v[1]-u[1]*v[0])
            a.append(dict(frame=i,time=i/30,xy_triangle_signed_area=area,relative_z_mm=((z-z[0])*1000).tolist(),normal=r["normal"]["left"]))
        report["palm_triangle_at_7_seconds"][name]=a
    (output/"summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("output",type=Path);run(p.parse_args().output)
