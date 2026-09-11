"""Replay the same landmark stream through both distance filters, not ground truth."""
import argparse,json,time
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.face_distance import FaceDistance

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    models={mode:FaceDistance(3,1,mode) for mode in ('legacy','stable')}
    records=[];now=0.;elapsed=[]
    for line in args.source.read_text().splitlines():
        row=json.loads(line);now+=(row.get('result_interval_ms') or 1000/30)/1000
        item={'frame':row['frame'],'time':now}
        for mode,model in models.items():
            packet=row['sent_packet'].copy();start=time.perf_counter()
            model.update(row['points_xy'],row['scores'],packet,now)
            if mode=='stable':elapsed.append((time.perf_counter()-start)*1000)
            item[mode]=packet['faceDistanceRatio'] if packet['faceDistanceTracked'] else None
        records.append(item)
    report={'source':str(args.source),'frames':len(records),'scope':'Mixed real movement, not labelled stationary footage. Less variation is not accuracy proof.'}
    for mode in models:
        values=[r[mode] for r in records if r[mode] is not None]
        steps=[abs(b[mode]-a[mode]) for a,b in zip(records,records[1:]) if a[mode] is not None and b[mode] is not None]
        report[mode]={'valid':len(values),'ratio_p5_p50_p95':np.percentile(values,[5,50,95]).tolist() if values else [],'step_p95':float(np.percentile(steps,95)) if steps else None}
    report['stable_ms_p50_p95']=np.percentile(elapsed,[50,95]).tolist()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    args.output.with_suffix('.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
