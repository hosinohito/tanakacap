"""Replay identical recorded inputs through three shoulder-yaw policies."""
import argparse,copy,json,sys,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from capture_lab.body3d import BodyRetarget
from capture_lab.comparison import dump,line,fingerprint
from capture_lab.models import sha256
from compare_body_models import difference

def run(output):
    common=ROOT/'results/comparisons/first-take'
    baseline=ROOT/'results/comparisons/front-projection-trial-4/front-projection/frames.jsonl'
    source=json.loads((common/'report.json').read_text())
    assert source['status']=='complete'
    settings=dict(source['controls']['settings'],arm_depth_mode='front_projection')
    frozen=fingerprint(settings)
    output.mkdir(parents=True,exist_ok=False)
    report=dict(status='running',source_video_sha256=source['source_video_sha256'],
        common_sha256=sha256(common/'common.jsonl'),baseline_sha256=sha256(baseline),controls=frozen,
        scope='Same recorded RTMW input and front-projection arms. Only shoulder yaw differs; all other sent fields match. Width and face-shoulder gap use image geometry, not model torso depth. Existing model elbow depth supplies direction only. Offline render, not live speed or ground-truth accuracy.',variants={})
    dump(output/'report.json',report)
    try:
        for name,mode in [('current','legacy'),('shoulder-width','width_only'),('shoulder-face','face_ratio')]:
            folder=output/name;folder.mkdir();controller=BodyRetarget(3,1,'front_projection',mode)
            count=0;maximum=0.;last=None;stages=defaultdict(list);statuses=Counter();timings=[]
            with (common/'common.jsonl').open() as cache,baseline.open() as base,(folder/'frames.jsonl').open('w') as detail,(folder/'replay.jsonl').open('w') as replay:
                for aa,bb in zip(cache,base,strict=True):
                    c,old=json.loads(aa),json.loads(bb)
                    assert (c['frame'],c['time'])==(old['frame'],old['time'])
                    geometry={k:None if c[v] is None else np.asarray(c[v],float) for k,v in [('xy','body_xy'),('scores','body_scores'),('depth','body_depth'),('depth_scores','body_depth_scores')]}
                    start=time.perf_counter()
                    packet=controller.update(copy.deepcopy(c['face']),**geometry,now=c['time'],image_size=old['image_size'],reference_xy=np.asarray(c['points_xy'],float),reference_scores=np.asarray(c['scores'],float))
                    timings.append((time.perf_counter()-start)*1000)
                    for key,value in old['sent_packet'].items():
                        if key=='torsoYaw' and mode!='legacy':continue
                        maximum=max(maximum,difference(packet.get(key),value))
                        if maximum>1e-7:raise AssertionError('Fixed field changed: '+key)
                    diag=copy.deepcopy(controller.diagnostics);projection=diag.get('shoulder_projection',{})
                    statuses[projection.get('status','legacy_or_torso_missing')]+=1
                    if packet.get('torsoTracked'):stages[old['stage']].append(float(packet['torsoYaw']))
                    row={k:old[k] for k in ('frame','time','sequence','stage','image_size')};row.update(body_diagnostics=diag,sent_packet=packet)
                    line(detail,row);line(replay,dict(packet=packet,dt=1/30 if last is None else c['time']-last));last=c['time'];count+=1
            report['variants'][name]=dict(frames=count,fixed_max_difference=maximum,statuses=dict(statuses),control_cpu_ms_p50_p95=np.percentile(timings,[50,95]).tolist(),stages={k:dict(count=len(v),absolute_p50_p95=np.percentile(np.abs(v),[50,95]).tolist(),over_15=int(np.count_nonzero(np.abs(v)>15))) for k,v in stages.items()},replay_sha256=sha256(folder/'replay.jsonl'))
            dump(output/'report.json',report);print(name,dict(statuses),flush=True)
        assert fingerprint(settings)['sha256']==frozen['sha256']
        report['status']='complete';dump(output/'report.json',report)
    except BaseException as exc:
        report.update(status='failed',error=str(exc));dump(output/'report.json',report);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
