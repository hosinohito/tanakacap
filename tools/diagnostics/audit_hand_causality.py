"""Audit saved camera hands: geometry sensitivity, signed curls, and unilateral Player controls."""
import argparse,copy,json,subprocess,sys
from pathlib import Path
from collections import Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.hand_orientation import palm_basis

def run(folder,output):
    output.mkdir(parents=True,exist_ok=False)
    session=json.loads((folder/'session.json').read_text(encoding='utf-8'))
    rows=[json.loads(x) for x in (Path(session['inference_results'])/'frames.jsonl').read_text().splitlines()]
    useful=[r for r in rows if 'geometry' in r['body_diagnostics']]
    scale=np.array([r['body_diagnostics']['geometry']['model_scale'] for r in useful])
    xy=np.array([r['body_xy'] for r in useful]);z=np.array([r['body_depth'] for r in useful])
    report=dict(source=str(folder),observations=len(rows),hands={},
                note='Screen-space shortening is a proxy, not ground truth. Fixed-scale test isolates scale math without changing model observations.')
    for side,k in [('left',91),('right',112)]:
        dy=-(xy[:,k+9,1]-xy[:,k,1]);dz=z[:,k+9]-z[:,k]
        pitch=np.degrees(np.arctan2(-dz,dy*scale))
        fixed=np.degrees(np.arctan2(-dz,dy*np.median(scale)))
        error=np.abs((pitch-fixed+180)%360-180)
        h=dict(valid=np.sum([r['sent_packet'][side+'FingerTracked'] for r in rows],axis=0).tolist(),
               reasons=dict(Counter(v for r in rows for v in r['body_diagnostics'].get('fingers',{}).get(side,[]))),
               fixed_scale_pitch_error_p95_max=np.percentile(error,[95,100]).tolist(),shortened={})
        for finger,start in enumerate((5,9,13,17),1):
            length=np.linalg.norm(xy[:,k+start]-xy[:,k],axis=1)
            reach=np.linalg.norm(xy[:,k+start+3]-xy[:,k+start],axis=1)/length
            signed=[];selected=[]
            for i,r in enumerate(useful):
                if reach[i]>=.45 or not r['sent_packet'][side+'FingerTracked'][finger]:continue
                xyz=np.column_stack((-xy[i]*scale[i],-z[i]))
                basis=palm_basis(xyz,r['body_scores'],r['body_depth_scores'],k)
                if basis is None:continue
                normal=basis[1];inward=normal*(1 if side=='left' else -1)
                segments=np.diff(xyz[np.array([0,start,start+1,start+2,start+3])+k],axis=0)
                segments/=np.linalg.norm(segments,axis=1)[:,None]
                along=segments[1]-normal*(segments[1]@normal)
                reference=segments[0]-normal*(segments[0]@normal)
                if np.linalg.norm(along)<.2:along=reference
                elif along@reference<0:along=-along
                along/=max(1e-5,np.linalg.norm(along))
                projected=segments[1:]@np.array([along,inward]).T
                directions=np.arctan2(projected[:,1],projected[:,0])
                signed.append(np.degrees(np.r_[directions[0],(np.diff(directions)+np.pi)%(2*np.pi)-np.pi]))
                selected.append(r['sent_packet'][side+'FingerFlex'][finger*3:finger*3+3])
            h['shortened'][str(finger)]=dict(valid_samples=len(selected),
                sent_median=np.median(selected,axis=0).tolist() if selected else [],
                signed_before_filter_median=np.median(signed,axis=0).tolist() if signed else [])
        report['hands'][side]=h
    # Keep the entire target constant except one side's fields; real recorded changes on that side.
    base=next(r['sent_packet'] for r in rows[60:] if all(r['sent_packet'].get(s+'HandTracked') for s in ('left','right')))
    base=dict(base,gazeTracked=False)  # Isolate hands from gaze-only snapshot assertions.
    fixture=output/'baseline.json';fixture.write_text(json.dumps(base))
    report['unilateral']={}
    for moving,still in [('right','left'),('left','right')]:
        replay=output/(moving+'-only.jsonl')
        with replay.open('w') as f:
            for r in rows:
                pose=copy.deepcopy(base)
                pose.update({k:v for k,v in r['sent_packet'].items() if k.startswith(moving)})
                pose['sequence']=r['frame']
                f.write(json.dumps(dict(packet=pose,dt=1/30))+'\n')
        trace=output/(moving+'-trace.jsonl')
        subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/smoke_unity.py'),
            '--avatar',session['settings']['avatar'],'--packet-file',str(fixture),
            '--replay-file',str(replay),'--hand-trace',str(trace),'--output',str(output/(moving+'.png'))],
            cwd=ROOT,check=True,timeout=90)
        actual=[json.loads(x) for x in trace.read_text().splitlines()]
        actual=[r for r in actual if r['target'] and r['target']['sequence']>=200]
        n=np.array([list(r[still+'Normal'].values()) for r in actual]);n/=np.linalg.norm(n,axis=1)[:,None]
        delta=np.degrees(np.arccos(np.clip(n@n[0],-1,1)))
        f=np.array([r[still+'Fingers'] for r in actual])
        report['unilateral'][moving]=dict(still_side=still,normal_change_max=float(delta.max()),
            finger_change_max=float(np.abs(f-f[0]).max()),samples=len(actual))
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.folder.resolve(),a.output.resolve())
