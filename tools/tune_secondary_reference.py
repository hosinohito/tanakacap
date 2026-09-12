"""Measure independent damping candidates against real SDK behavior in the isolated Editor."""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"results/physbone-reference"
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--values",nargs="+",type=float,default=[1.,1.5])
    args=parser.parse_args()
    if any(not .1<=x<=4 for x in args.values): parser.error("damping values must be 0.1..4")
    project=BASE/"project"
    source=(ROOT/"unity/TanakaCap/Assets/TanakaCap/SecondaryMotion.cs").read_text(encoding="utf-8")
    target=project/"Assets/Comparison/SecondaryMotion.cs"
    marker="(referenceDamping?1.5f:1f)"
    if marker not in source: raise RuntimeError("Update candidate substitution for the current solver")
    output=BASE/("sweep-"+str(time.time_ns()));output.mkdir()
    summaries=[]
    try:
        for value in args.values:
            out=output/str(value);out.mkdir()
            target.write_text(source.replace(marker,f"{value}f"),encoding="utf-8")
            run=subprocess.run([r"C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe",
                "-batchmode","-projectPath",str(project),"-executeMethod","PhysReferenceSetup.Run",
                "-logFile",str(out/"editor.log")],timeout=240)
            log=(out/"editor.log").read_text(encoding="utf-8",errors="replace")
            if run.returncode or "TANAKACAP_PHYS_REFERENCE_COMPLETE" not in log or "Exception:" in log:
                raise RuntimeError("Invalid comparison run: "+str(out))
            for name in ("frames.jsonl","manifest.json","warnings.txt"):shutil.copy2(BASE/name,out/name)
            rows=[json.loads(line) for line in (out/"frames.jsonl").open(encoding="utf-8")]
            if len(rows)!=1260: raise RuntimeError("Incomplete comparison")
            error=np.array([r["errorDegrees"] for r in rows])
            ref=np.array([r["referenceAngle"] for r in rows]);ours=np.array([r["independentAngle"] for r in rows])
            if np.ptp(ref[180:540],axis=0).max()<1 or np.ptp(ours[180:540],axis=0).max()<1:
                raise RuntimeError("A solver did not actually move")
            summary=dict(damping=value,mean=float(error.mean()),head_mean=float(error[180:540].mean()),
                         chest_mean=float(error[540:900].mean()),rest_mean=float(error[1200:].mean()))
            summaries.append(summary);print(json.dumps(summary),flush=True)
    finally:
        target.write_text(source,encoding="utf-8")
        (output/"summary.json").write_text(json.dumps(summaries,indent=2),encoding="utf-8")
if __name__=="__main__":main()
