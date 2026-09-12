import json
from tools.summarize_body_comparison import run


def test_temporal_audit_uses_common_consecutive_visible_pairs(tmp_path):
    (tmp_path/'report.json').write_text(json.dumps({'status':'complete','partial_test':False,'variants':{'current':{},'sam':{}}}))
    for name,factor in [('current',1),('sam',2)]:
        folder=tmp_path/name;folder.mkdir();rows=[]
        for frame in range(6):
            z=[0.]*133;z[7]=-(100 if frame==2 else frame)*factor
            scores=[.9]*8
            if name=='sam' and frame==2:scores[2]=0
            p={'torsoTracked':True,'torsoYaw':0.}
            for side in ('left','right'):
                p.update({side+'ArmTracked':True,side+'ArmHeld':frame==2,side+'HandTracked':True,side+'HandHeld':False,side+'FingerTracked':[True]*5,side+'Elbow':{'z':frame*factor}})
            rows.append({'frame':frame,'time':frame/30,'stage':'a' if frame<4 else 'b','body_depth':z,'body_diagnostics':{'joint_xy_scores':scores},'sent_packet':p})
        (folder/'frames.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
    run(tmp_path)
    r=json.loads((tmp_path/'temporal-audit.json').read_text())
    assert r['frames']==6
    for stage in ('a','b'):
        a=r['stages'][stage]['current:raw_elbow_step_m'];b=r['stages'][stage]['sam:raw_elbow_step_m']
        assert a['pairs']==b['pairs']==1
        assert a['p95']==[1.,0.] and b['p95']==[2.,0.]
    assert r['counts']['current']['leftArmObserved']==5
    assert r['counts']['sam']['leftFingerObservations']==30
    assert len((tmp_path/'temporal-audit.md').read_text().splitlines())>10
