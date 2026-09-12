"""Replay body candidates through one frozen controller and verify baseline parity."""
import argparse,copy,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.body3d import BodyRetarget
from capture_lab.comparison import dump,line,fingerprint,Metrics
from capture_lab.models import sha256
from sam_body_adapter import adapt


def difference(a,b):
    if isinstance(a,dict):
        if set(a)!=set(b):return float('inf')
        return max((difference(a[k],b[k]) for k in a),default=0.)
    if isinstance(a,list):
        if len(a)!=len(b):return float('inf')
        return max((difference(x,y) for x,y in zip(a,b)),default=0.)
    if isinstance(a,bool) or isinstance(b,bool) or a is None or b is None:return 0. if a==b else float('inf')
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return abs(a-b)
    return 0. if a==b else float('inf')


def run(common,candidates,output,limit=None):
    if limit is not None and limit<1:raise ValueError("Positive smoke limit required")
    parent=json.loads((common/'report.json').read_text(encoding='utf-8'))
    if parent['status']!='complete' or parent['partial_test']:raise ValueError('Complete common run required')
    settings=parent['controls']['settings'];frozen=fingerprint(settings)
    inputs={'current':None,**candidates};reports={}
    for name,folder in candidates.items():
        r=json.loads((folder/'report.json').read_text(encoding='utf-8'))
        if (r['status']!='complete' or (r.get('partial_test',False) and limit is None) or r['video_sha256']!=parent['source_video_sha256'] or r['controls_sha256']!=parent['controls']['sha256'] or r['stride']!=1 or r['start_frame']!=0):raise ValueError('Complete consecutive aligned candidate required: '+name)
        reports[name]=r
    output.mkdir(parents=True,exist_ok=False)
    report={'status':'running','partial_test':limit is not None,'source_video_sha256':parent['source_video_sha256'],'source_timeline_sha256':parent['source_timeline_sha256'],'common_sha256':sha256(common/'common.jsonl'),'historical_controls_sha256':parent['controls']['sha256'],'controls':frozen,'candidates':reports,'scope':'Native metric XYZ and projected body/hand joints changed. Face/gaze/mouth/distance packets, RTMW3D visibility evidence and correction algorithms held common. SAM has no per-joint confidence; generated hidden joints are not counted as observations. Default FOV, no ground truth. Offline replay is not realtime performance.','variants':{}}
    dump(output/'report.json',report)
    try:
        for name,candidate in inputs.items():
            folder=output/name;folder.mkdir();control=BodyRetarget(settings['observation_block'],settings['observation_stride'])
            metrics=Metrics();maximum=0.;projection_max=0.;total=0;last=None;missing=0;raw=None
            if candidate:raw=(candidate/'raw.jsonl').open(encoding='utf-8')
            try:
                with (common/'common.jsonl').open(encoding='utf-8') as cache,(common/'baseline/frames.jsonl').open(encoding='utf-8') as baseline,(folder/'replay.jsonl').open('w',encoding='utf-8') as replay,(folder/'frames.jsonl').open('w',encoding='utf-8') as details:
                    for cl in cache:
                        if limit is not None and total>=limit:break
                        c=json.loads(cl);original=json.loads(next(baseline));clock={k:original[k] for k in ('frame','time','sequence','stage')};size=original['image_size']
                        if c['frame']!=clock['frame'] or c['time']!=clock['time']:raise ValueError('Common clock mismatch')
                        total+=1;prediction=None
                        if raw:
                            candidate_line=next(raw,None)
                            if candidate_line is None:raise ValueError('Truncated candidate')
                            r=json.loads(candidate_line)
                            if r['frame']!=c['frame'] or r['time']!=c['time']:raise ValueError('Candidate clock mismatch')
                            if len(r['predictions'])>1:raise ValueError('Single-person recording expected')
                            prediction=r['predictions'][0] if r['predictions'] else None
                        geometry={k:None if c[v] is None else np.asarray(c[v],float) for k,v in [('xy','body_xy'),('scores','body_scores'),('depth','body_depth'),('depth_scores','body_depth_scores')]}
                        if candidate:
                            converted=adapt(c,prediction,size)
                            if converted is None:
                                geometry=dict(xy=None,scores=None,depth=None,depth_scores=None);missing+=1
                            else:
                                geometry,error=converted;projection_max=max(projection_max,error)
                        packet=control.update(copy.deepcopy(c['face']),**geometry,now=c['time'],image_size=size,reference_xy=np.asarray(c['points_xy'],float),reference_scores=np.asarray(c['scores'],float))
                        # BodyRetarget updates 'tracked'; every actual face output is fixed.
                        for k,v in c['face'].items():
                            if (k.startswith(('head','mouth','gaze','face')) or k in {'leftBlink','rightBlink','version','sequence'}) and difference(packet.get(k),v)>1e-9:raise AssertionError('Shared face field changed: '+k)
                        if not candidate:
                            maximum=max(maximum,difference(packet,original['sent_packet']))
                            if maximum>1e-7:raise AssertionError(f'Baseline packet mismatch frame {c["frame"]}: {maximum}')
                        row={**clock,'image_size':size,'body_depth':geometry['depth'],'body_diagnostics':copy.deepcopy(control.diagnostics),'sent_packet':packet}
                        line(details,row);line(replay,{'packet':packet,'dt':1/30 if last is None else c['time']-last});last=c['time'];metrics.update(row)
                    if limit is None and (next(baseline,None) is not None or (raw and next(raw,None) is not None)):raise ValueError('Extra frames')
                if candidate and (reports[name]['frames'] if limit is None else min(limit,reports[name]['frames']))!=total:raise ValueError('Candidate report count mismatch')
                result={'frames':total,'baseline_max_difference':maximum if not candidate else None,'projection_max_pixels':projection_max if candidate else None,'missing_predictions':missing,'metrics':metrics.result(),'replay_sha256':sha256(folder/'replay.jsonl')}
                dump(folder/'summary.json',result);report['variants'][name]=result;dump(output/'report.json',report);print(name,total,'baseline error',maximum,'projection error',projection_max,flush=True)
            finally:
                if raw:raw.close()
        if fingerprint(settings)['sha256']!=frozen['sha256']:raise RuntimeError('Controls changed during comparison')
        report['status']='complete';dump(output/'report.json',report)
    except BaseException as exc:
        report.update(status='failed',error=str(exc));dump(output/'report.json',report);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--common',type=Path,required=True);p.add_argument('--candidate',action='append',default=[],help='name=raw_folder');p.add_argument('--output',type=Path,required=True);p.add_argument('--limit',type=int,help='Explicit partial integration test only');a=p.parse_args()
    candidates={}
    for item in a.candidate:
        name,path=item.split('=',1)
        if name=='current' or not name.replace('-','').isalnum() or name in candidates:raise ValueError('Invalid/duplicate variant name')
        candidates[name]=Path(path)
    run(a.common,candidates,a.output,a.limit)
