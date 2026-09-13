"""Common-visibility temporal audit; variability is not accuracy ground truth."""
import argparse,json,sys
from collections import Counter,defaultdict
from contextlib import ExitStack
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tanakacap.comparison import dump


def run(folder):
    report=json.loads((folder/'report.json').read_text(encoding='utf-8'))
    if report['status']!='complete' or report.get('partial_test'):raise ValueError('Full completed comparison required')
    names=list(report['variants']);counts={name:Counter() for name in names};samples=defaultdict(lambda:defaultdict(list));last=None;total=0
    with ExitStack() as stack:
        streams=[stack.enter_context((folder/name/'frames.jsonl').open(encoding='utf-8')) for name in names]
        for first in streams[0]:
            lines=[first]+[next(s,None) for s in streams[1:]]
            if any(line is None for line in lines):raise ValueError('Truncated comparison')
            rows=[json.loads(line) for line in lines];r=rows[0];key=(r['frame'],r['time'],r['stage']);total+=1
            if any((v['frame'],v['time'],v['stage'])!=key for v in rows):raise ValueError('Clock mismatch')
            packets=[v['sent_packet'] for v in rows]
            for name,p in zip(names,packets):
                counts[name]['torso']+=bool(p['torsoTracked'])
                for side in ('left','right'):
                    for part in ('Arm','Hand'):
                        counts[name][side+part+'Observed']+=bool(p[side+part+'Tracked'] and not p[side+part+'Held'])
                        counts[name][side+part+'Held']+=bool(p[side+part+'Held'])
                    counts[name][side+'FingerObservations']+=sum(p[side+'FingerTracked'])
            visible=[];depths=[]
            for row in rows:
                s=np.asarray(row['body_diagnostics'].get('joint_xy_scores',[]),float)
                z=None if row['body_depth'] is None else np.asarray(row['body_depth'],float)
                valid=len(s)>=4 and np.isfinite(s[:4]).all() and (s[:4]>=.3).all() and z is not None and np.isfinite(z[[5,6,7,8]]).all()
                visible.append(bool(valid));depths.append(None if not valid else np.array([-(z[7]-z[5]),-(z[8]-z[6])]))
            continuous=last is not None and key[0]==last['key'][0]+1 and key[2]==last['key'][2]
            if continuous and all(visible) and all(last['visible']):
                for name,z,old in zip(names,depths,last['depths']):samples[key[2]][name+':raw_elbow_step_m'].append(abs(z-old).tolist())
            if continuous:
                for side in ('left','right'):
                    if all(p[side+'ArmTracked'] and not p[side+'ArmHeld'] for p in packets+last['packets']):
                        for name,p,old in zip(names,packets,last['packets']):samples[key[2]][name+':'+side+'_sent_elbow_step_m'].append(abs(p[side+'Elbow']['z']-old[side+'Elbow']['z'])*.36)
                if all(p['torsoTracked'] for p in packets+last['packets']):
                    for name,p,old in zip(names,packets,last['packets']):samples[key[2]][name+':yaw_step_degrees'].append(abs(p['torsoYaw']-old['torsoYaw']))
            last=dict(key=key,visible=visible,depths=depths,packets=packets)
        if any(next(s,None) is not None for s in streams[1:]):raise ValueError('Extra comparison frames')
    def stats(values):return dict(pairs=len(values),p50=np.percentile(values,50,axis=0).tolist(),p95=np.percentile(values,95,axis=0).tolist(),maximum=np.max(values,axis=0).tolist())
    result={'scope':'Consecutive recorded pairs within the same guide stage, common visibility across ALL variants. Variability is not accuracy; missing/held pairs excluded. Metres are model/nominal-avatar units, not measured human error. Finger observations count five possible fingers per frame. Stage labels are instructions, not verified action annotations.','frames':total,'counts':counts,'stages':{stage:{k:stats(v) for k,v in data.items()} for stage,data in samples.items()}}
    dump(folder/'temporal-audit.json',result)
    output=['# Common-control body comparison','',result['scope'],'',f'Frames: {total}','', '| Model | Torso tracked | Left arm observed | Right arm observed | Left fingers / 5N | Right fingers / 5N |','|---|---:|---:|---:|---:|---:|']
    for name,c in counts.items():output.append(f"| {name} | {c['torso']} | {c['leftArmObserved']} | {c['rightArmObserved']} | {c['leftFingerObservations']} | {c['rightFingerObservations']} |")
    output+=['','## Raw elbow temporal variation','', 'Absolute frame-to-frame relative-depth change p95; left / right. Same visible pairs for every model. Lower is NOT necessarily better.','']
    for stage,data in result['stages'].items():
        output+=['### '+stage,'','| Model | Common pairs | Left p95 (m) | Right p95 (m) |','|---|---:|---:|---:|']
        for name in names:
            v=data.get(name+':raw_elbow_step_m')
            if v:output.append(f"| {name} | {v['pairs']} | {v['p95'][0]:.5f} | {v['p95'][1]:.5f} |")
        output.append('')
    (folder/'temporal-audit.md').write_text('\n'.join(output),encoding='utf-8');print('audited',total,'frames',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('comparison',type=Path);run(p.parse_args().comparison)
