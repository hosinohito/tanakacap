"""Same recorded RTMW inputs: legacy versus front-projection, with SAM reference."""
import argparse,copy,json,shutil,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tanakacap.body3d import BodyRetarget
from tanakacap.comparison import dump,line,fingerprint
from tanakacap.models import sha256
from compare_body_models import difference


def run(output):
    common=ROOT/'results/comparisons/first-take'
    source=json.loads((common/'report.json').read_text())
    if source['status']!='complete':raise ValueError('Complete source required')
    settings=source['controls']['settings'];frozen=fingerprint(settings)
    output.mkdir(parents=True,exist_ok=False)
    report=dict(status='running',partial_test=False,source_video_sha256=source['source_video_sha256'],
        common_sha256=sha256(common/'common.jsonl'),controls=frozen,
        scope='Same recorded RTMW3D input, face/gaze/mouth/torso outputs fixed; palm/finger algorithms fixed but arm availability can change their gating. Only arm reconstruction changed. SAM ViT-H full replay is an existing quality reference, not ground truth. Front projection restricts the wrist workspace; backward tracking is not recovered. Offline rendering does not measure inference FPS.',variants={})
    dump(output/'report.json',report)
    try:
        for name,mode in [('current','legacy'),('front-projection','front_projection')]:
            folder=output/name;folder.mkdir();controller=BodyRetarget(settings['observation_block'],settings['observation_stride'],mode)
            count=0;maximum=0.;last=None;statuses=Counter();timings=[];max_length_error=0.;min_wrist_z=0.;examples=[]
            with (common/'common.jsonl').open() as cache,(common/'baseline/frames.jsonl').open() as base,(folder/'replay.jsonl').open('w') as replay,(folder/'frames.jsonl').open('w') as detail:
                for a,b in zip(cache,base,strict=True):
                    c,old=json.loads(a),json.loads(b)
                    if (c['frame'],c['time'])!=(old['frame'],old['time']):raise ValueError('Frame mismatch')
                    geometry={k:None if c[v] is None else np.asarray(c[v],float) for k,v in [('xy','body_xy'),('scores','body_scores'),('depth','body_depth'),('depth_scores','body_depth_scores')]}
                    started=time.perf_counter()
                    packet=controller.update(copy.deepcopy(c['face']),**geometry,now=c['time'],image_size=old['image_size'],reference_xy=np.asarray(c['points_xy'],float),reference_scores=np.asarray(c['scores'],float))
                    timings.append((time.perf_counter()-started)*1000)
                    if mode=='legacy':
                        maximum=max(maximum,difference(packet,old['sent_packet']))
                        if maximum>1e-7:raise AssertionError('Legacy changed')
                    for key,value in old['sent_packet'].items():
                        if key.startswith(('head','mouth','gaze','face','torso')) or key.endswith('Blink'):
                            if difference(packet.get(key),value)>1e-8:raise AssertionError('Fixed field changed: '+key)
                    diag=copy.deepcopy(controller.diagnostics)
                    for side in ('left','right'):
                        statuses[side+':'+diag.get(side,'missing')]+=1
                        fit=diag.get(side+'_projection',{})
                        if fit.get('reason')=='fit':
                            max_length_error=max(max_length_error,fit['length_error'])
                            z=packet[side+'Wrist']['z']*.36;min_wrist_z=min(min_wrist_z,z)
                            if z < -1e-7:raise AssertionError('Back wrist escaped front mode')
                        if c['frame'] in (4150,4240,4246,4251,4277):
                            examples.append(dict(frame=c['frame'],side=side,old_elbow=old['sent_packet'][side+'Elbow'],old_wrist=old['sent_packet'][side+'Wrist'],new_elbow=packet[side+'Elbow'],new_wrist=packet[side+'Wrist'],fit=fit))
                    row={k:old[k] for k in ('frame','time','sequence','stage','image_size')};row.update(body_depth=geometry['depth'],body_diagnostics=diag,sent_packet=packet)
                    line(detail,row);line(replay,dict(packet=packet,dt=1/30 if last is None else c['time']-last));last=c['time'];count+=1
            report['variants'][name]=dict(frames=count,legacy_max_difference=maximum if mode=='legacy' else None,statuses=dict(statuses),length_error_max=max_length_error,wrist_z_min=min_wrist_z,control_cpu_ms_p50_p95=np.percentile(timings,[50,95]).tolist(),examples=examples,replay_sha256=sha256(folder/'replay.jsonl'))
            dump(output/'report.json',report);print(name,count,dict(statuses),flush=True)
        reference=ROOT/'results/comparisons/body-three-models/sam-vith'
        ref_report=json.loads((reference.parent/'report.json').read_text())
        if ref_report['status']!='complete' or ref_report['source_video_sha256']!=source['source_video_sha256']:raise ValueError('Wrong SAM reference')
        target=output/'sam-vith';target.mkdir()
        shutil.copyfile(reference/'replay.jsonl',target/'replay.jsonl')
        report['variants']['sam-vith']=dict(frames=report['variants']['current']['frames'],reference=str(reference),replay_sha256=sha256(target/'replay.jsonl'))
        if fingerprint(settings)['sha256']!=frozen['sha256']:raise RuntimeError('Controls changed during run')
        report['status']='complete';dump(output/'report.json',report)
    except BaseException as exc:
        report.update(status='failed',error=str(exc));dump(output/'report.json',report);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.output)
