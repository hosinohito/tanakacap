"""Deterministic recorded-input comparison; shared face, clock, ROI and controls."""
import argparse,copy,hashlib,html,json,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import cv2
import numpy as np
from .models import ROOT,sha256,model_path
from .inference import SimCCModel,PersonDetector,DetectionGate
from .retarget import packet_from_landmarks,FaceFilter
from .head_pose import HeadPose
from .face_distance import FaceDistance
from .body3d import BodyRetarget

CANDIDATES=('baseline','dwpose-l-384','rtmw-x-384')

def clean(value):
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [clean(v) for v in value]
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,np.integer):return int(value)
    return value

def dump(path,value):Path(path).write_text(json.dumps(clean(value),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def line(stream,value):stream.write(json.dumps(clean(value),ensure_ascii=False,allow_nan=False)+'\n')

def fingerprint(settings):
    files=list((ROOT/'capture_lab').glob('*.py'))+list((ROOT/'capture_lab/data').glob('*'))+list((ROOT/'unity/TanakaCap/Assets/TanakaCap').rglob('*.cs'))
    files += [ROOT/'builds/lab/TanakaCap.exe',ROOT/'builds/lab/TanakaCap_Data/Managed/Assembly-CSharp.dll']
    hashes={str(p.relative_to(ROOT)):sha256(p) for p in sorted(files) if p.is_file()}
    payload={'settings':settings,'files':hashes}
    return {'sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),**payload}

def load_take(path):
    path=Path(path);meta=json.loads((path/'take.json').read_text(encoding='utf-8'))
    if meta['status']!='complete':raise ValueError('Only completed takes are accepted')
    video_file=meta.get('video_file','camera.mkv')
    if video_file not in ('camera.avi','camera.mkv'):raise ValueError('Invalid video filename')
    for name,key in [(video_file,'video_sha256'),('frames.jsonl','timeline_sha256')]:
        if sha256(path/name)!=meta[key]:raise ValueError(f'Take checksum mismatch: {name}')
    timeline=[json.loads(l) for l in (path/'frames.jsonl').read_text().splitlines()]
    if not timeline or len(timeline)!=meta['frames']:raise ValueError('Timeline frame count mismatch')
    for i,row in enumerate(timeline):
        if row['frame']!=i or not np.isfinite(row['time']):raise ValueError('Invalid timeline')
        if i and (row['time']<=timeline[i-1]['time'] or row['sequence']<=timeline[i-1]['sequence']):raise ValueError('Timeline order mismatch')
    return meta,timeline

def images(path,timeline,limit=None):
    meta=json.loads((Path(path)/'take.json').read_text(encoding='utf-8'))
    video_file=meta.get('video_file','camera.mkv')
    if video_file not in ('camera.avi','camera.mkv'):raise ValueError('Invalid video filename')
    cap=cv2.VideoCapture(str(Path(path)/video_file),cv2.CAP_FFMPEG)
    if not cap.isOpened():raise RuntimeError('Cannot decode take')
    try:
        for row in timeline[:limit]:
            ok,image=cap.read()
            if not ok:raise ValueError('Video ended before timeline')
            yield row,image
        if limit is None and cap.read()[0]:raise ValueError('Video has more frames than timeline')
    finally:cap.release()

def frame_mask(xy,scores,size):
    w,h=size;inside=np.isfinite(xy).all(axis=1)&(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h)
    return np.where(inside,scores,0)

class SharedFace:
    def __init__(self,settings,output):
        self.s=settings;b=settings['observation_block'];stride=settings['observation_stride']
        self.filter=FaceFilter(b,stride);self.pose=HeadPose(settings['head_pitch_gain'],settings['mouth_lip_depth_scale']) if settings['head_pose_mode']=='pnp' else None
        self.distance=FaceDistance(b,stride,settings.get('face_distance_filter','stable'))
        self.gaze=None
        if settings.get('gaze_enabled'):
            from .gaze import IrisGaze
            self.gaze=IrisGaze(output,b,stride,settings['gaze_reference'])
    def update(self,image,xy,scores,index,now):
        p=packet_from_landmarks(xy,scores,index)
        if self.pose:self.pose.update(xy,scores,p,image.shape[1::-1])
        if self.gaze:self.gaze.update(image,xy,scores,p,now)
        self.filter.update(p,now);self.distance.update(xy,scores,p,now)
        return p

class Metrics:
    def __init__(self):self.stages=defaultdict(lambda: {'frames':0,'flags':Counter(),'finger_reasons':Counter(),'torso_yaw':[],'distance':[],'elbow_depth':{'left':[],'right':[]}})
    def update(self,row):
        stage=self.stages[row['stage']];p=row['sent_packet'];stage['frames']+=1
        for k in ('torsoTracked','leftArmTracked','rightArmTracked','leftHandTracked','rightHandTracked'):
            stage['flags'][k]+=int(bool(p.get(k)))
        for side,ids in [('left',(5,7)),('right',(6,8))]:
            for i,flag in enumerate(p.get(side+'FingerTracked',[])):stage['flags'][f'{side}Finger{i}']+=int(flag)
            reasons=row['body_diagnostics'].get('fingers',{}).get(side,[])
            stage['finger_reasons'].update(f'{side}:{r}' for r in reasons)
            if row.get('body_depth') is not None:
                z=np.asarray(row['body_depth'],float)
                if np.isfinite(z[list(ids)]).all():stage['elbow_depth'][side].append(float(z[ids[1]]-z[ids[0]]))
        if p.get('torsoTracked'):stage['torso_yaw'].append(p['torsoYaw'])
        if p.get('faceDistanceTracked'):stage['distance'].append(p['faceDistanceRatio'])
    def result(self):
        def variation(a):
            return {'count':len(a),'p5_p50_p95':np.percentile(a,[5,50,95]).tolist() if a else [],'step_p95':float(np.percentile(np.abs(np.diff(a)),95)) if len(a)>1 else None}
        return {key:{'frames':s['frames'],'active_frames':dict(s['flags']),'finger_reasons':dict(s['finger_reasons']),'torso_yaw':variation(s['torso_yaw']),'distance':variation(s['distance']),'raw_elbow_relative_z':{side:variation(v) for side,v in s['elbow_depth'].items()}} for key,s in self.stages.items()}

def run(take,output,variants=CANDIDATES,limit=None,fixed_roi=False):
    meta,timeline=load_take(take);settings=meta['settings'];output=Path(output);output.mkdir(parents=True,exist_ok=False)
    if 'baseline' not in variants or variants[0]!='baseline':raise ValueError('Baseline must run first')
    frozen=fingerprint(settings)
    report={'status':'running','take':str(Path(take).resolve()),'source_video_sha256':meta['video_sha256'],'source_timeline_sha256':meta['timeline_sha256'],'controls':frozen,'variants':{},'scope':'Recorded-input quality replay. CUDA timings are inference only, not live or display latency. 2D candidates change body agreement reference only; face and learned 3D stay fixed.','partial_test':limit is not None,'fixed_roi_test':fixed_roi}
    dump(output/'report.json',report)
    try:
        for variant in variants:
            if variant not in CANDIDATES:raise ValueError(f'Unsupported candidate {variant}')
            folder=output/variant;folder.mkdir();models=[];shared=None;metrics=Metrics();timings=[]
            body_control=BodyRetarget(settings['observation_block'],settings['observation_stride'],settings.get('arm_depth_mode','legacy'));cache_reader=None;cache_writer=None
            try:
                if variant=='baseline':
                    model=SimCCModel('rtmw-l-384',folder);body=SimCCModel('rtmw3d-x-384',folder);models=[model,body]
                    detector=None if fixed_roi else PersonDetector(folder)
                    if detector:models.append(detector)
                    gate=DetectionGate();shared=SharedFace(settings,folder)
                    cache_writer=(output/'common.jsonl').open('w',encoding='utf-8')
                else:
                    model=SimCCModel(variant,folder);models=[model];cache_reader=(output/'common.jsonl').open(encoding='utf-8')
                with (folder/'frames.jsonl').open('w',encoding='utf-8') as stream,(folder/'replay.jsonl').open('w',encoding='utf-8') as replay:
                    previous_time=None
                    for clock,image in images(take,timeline,limit):
                        index=clock['frame'];now=clock['time'];size=image.shape[1::-1];start=time.perf_counter()
                        if variant=='baseline':
                            roi=[0,0,*size] if detector is None else gate.update(detector.detect(image)[0])
                            xy=np.full((133,2),np.nan);scores=np.zeros(133);body_xy=depth=depth_scores=body_scores=None
                            if roi is not None:
                                xy,scores,_=model.predict(image,roi)
                                body_xy,body_scores,_=body.predict(image,roi);body_scores=frame_mask(body_xy,body_scores,size)
                                depth=body.depth.copy();depth_scores=body.depth_scores.copy()
                            face=shared.update(image,xy,scores,index,now)
                            common={'frame':index,'time':now,'roi':roi,'face':face,'points_xy':xy,'scores':scores,'body_xy':body_xy,'body_scores':body_scores,'body_depth':depth,'body_depth_scores':depth_scores}
                            line(cache_writer,common)
                        else:
                            common=json.loads(next(cache_reader))
                            if common['frame']!=index or common['time']!=now:raise ValueError('Cached frame/time mismatch')
                            roi=common['roi'];face=common['face'];body_xy=common['body_xy'];body_scores=common['body_scores'];depth=common['body_depth'];depth_scores=common['body_depth_scores']
                            body_xy,body_scores,depth,depth_scores=[None if a is None else np.asarray(a,dtype=float) for a in (body_xy,body_scores,depth,depth_scores)]
                            xy=np.full((133,2),np.nan);scores=np.zeros(133)
                            if roi is not None:xy,scores,_=model.predict(image,roi)
                        inference_ms=(time.perf_counter()-start)*1000
                        p=body_control.update(copy.deepcopy(face),body_xy,body_scores,depth,depth_scores,now=now,image_size=size,reference_xy=xy,reference_scores=scores)
                        row={**clock,'image_size':size,'points_xy':xy,'scores':scores,'body_xy':body_xy,'body_scores':body_scores,'body_depth':depth,'body_depth_scores':depth_scores,'body_diagnostics':copy.deepcopy(body_control.diagnostics),'sent_packet':p,'inference_and_common_ms':inference_ms}
                        line(stream,row);line(replay,{'packet':p,'dt':1/30 if previous_time is None else now-previous_time});previous_time=now
                        metrics.update(row);timings.append(inference_ms)
                        if index%100==0:print(f'{variant}: {index+1}/{min(len(timeline),limit or len(timeline))}',flush=True)
                verification=[m.finish() for m in models]
                if shared and shared.gaze:verification.append(shared.gaze.finish())
                report['variants'][variant]={'status':'complete','model':model.identity,'cuda':verification,'metrics':metrics.result(),'processing_ms_p50_p95':np.percentile(timings,[50,95]).tolist(),'face_source':'common baseline','body_source':'rtmw3d-x-384'}
                dump(folder/'summary.json',report['variants'][variant]);dump(output/'report.json',report)
            finally:
                if cache_reader:cache_reader.close()
                if cache_writer:cache_writer.close()
                for m in models:
                    if hasattr(m,'session'):del m.session
                if shared and shared.gaze:del shared.gaze.session
            if fingerprint(settings)!=frozen:raise RuntimeError('Control source changed during comparison')
        report['status']='complete';dump(output/'report.json',report)
        render_report(output,report)
    except BaseException as exc:
        report.update(status='failed',error=str(exc));dump(output/'report.json',report);raise
    return report

def render_report(output,report):
    rows=[]
    for name,result in report['variants'].items():
        for stage,m in result['metrics'].items():
            active=m['active_frames'];n=m['frames']
            left=sum(active.get(f'leftFinger{i}',0) for i in range(5))/(n*5)
            right=sum(active.get(f'rightFinger{i}',0) for i in range(5))/(n*5)
            rows.append(f'<tr><td>{html.escape(name)}</td><td>{html.escape(stage)}</td><td>{n}</td><td>{left:.1%}</td><td>{right:.1%}</td><td>{html.escape(str(m["finger_reasons"]))}</td></tr>')
    page='<meta charset="utf-8"><title>モデル比較</title><style>body{font:16px sans-serif;padding:24px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:8px}</style><h1>モデル比較</h1><p>指有効率は精度ではありません。生点・棄却理由・アバターを併せて評価してください。2D比較では3Dモデルを固定しています。</p><table><tr><th>候補</th><th>動作</th><th>フレーム</th><th>左指有効率</th><th>右指有効率</th><th>理由</th></tr>'+''.join(rows)+'</table>'
    (Path(output)/'index.html').write_text(page,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('take',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--variants',nargs='+',choices=CANDIDATES,default=list(CANDIDATES));parser.add_argument('--limit',type=int);parser.add_argument('--fixed-roi',action='store_true')
    args=parser.parse_args();out=args.output or ROOT/'results'/'comparisons'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-%fZ')
    run(args.take,out,args.variants,args.limit,args.fixed_roi);print(out)
if __name__=='__main__':main()
