"""Audit one-sided palm/finger targets through the real Player; no camera."""
import argparse, copy, hashlib, json, math, socket, subprocess, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.partial_tracking import LocalSender

def run(player,avatar,output):
    output.mkdir(parents=True,exist_ok=False)
    base=dict(faceTracked=True,headTracked=True,body3d=True,torsoTracked=True,
              headPitch=0,headYaw=0,headRoll=0,torsoPitch=0,torsoYaw=0,torsoRoll=0)
    for side,sign in [('left',-1),('right',1)]:
        base.update({side+'ArmTracked':True,side+'HandTracked':True,
                     side+'Elbow':dict(x=sign*.5,y=-.2,z=.3),side+'Wrist':dict(x=sign*.45,y=.6,z=.9),
                     side+'HandForward':dict(x=0,y=1,z=0),side+'HandNormal':dict(x=0,y=0,z=-1),
                     side+'FingerTracked':[True]*5,side+'FingerFlex':[0.]*15})
    report=dict(avatar=str(avatar),player=str(player),
        avatar_sha256=hashlib.sha256(avatar.read_bytes()).hexdigest(),
        assembly_sha256=hashlib.sha256((player.parent/(player.stem+'_Data')/'Managed/Assembly-CSharp.dll').read_bytes()).hexdigest(),cases={})
    for name in ['baseline','right-roll','left-roll','left-curl','right-curl']:
        p=copy.deepcopy(base)
        if name!='baseline':
            side,kind=name.split('-')
            if kind=='roll':p[side+'HandNormal']=dict(x=-math.sin(math.pi/3),y=0,z=-math.cos(math.pi/3))
            else:p[side+'FingerFlex']=[0,25,30]+[35,65,45]*4
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        image=(output/(name+'.png')).resolve()
        process=subprocess.Popen([str(player),'--avatar',str(avatar),'--expression-mode','auto-custom',
            '-batchmode','--snapshot',str(image),'--port',str(port),'-logFile',str(image.with_suffix('.log'))],
            cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
        sender=LocalSender(port);start=time.monotonic();seq=0
        try:
            while process.poll() is None and time.monotonic()-start<40:
                # Initial common pose followed by unilateral change tests history as well as mapping.
                pose=copy.deepcopy(base if time.monotonic()-start<1 else p)
                pose.update(sequence=seq,inputReadTime=time.perf_counter());sender.send(pose)
                seq+=1;time.sleep(1/30)
            if process.poll() is None:raise RuntimeError('Snapshot timeout: '+name)
            if process.returncode:raise RuntimeError('Player failed: '+name)
            bones=json.loads(Path(str(image)+'.bones.json').read_text(encoding='utf-8-sig'))
            packet=json.loads(Path(str(image)+'.tracking.json').read_text(encoding='utf-8-sig'))
            report['cases'][name]=dict(bones=bones,received=packet)
            print('completed '+name,flush=True)
        finally:
            sender.close()
            if process.poll() is None:process.terminate();process.wait(timeout=10)
    reference=report['cases']['baseline']['bones'];changes={}
    for name,case in report['cases'].items():
        changes[name]={}
        for side in ['left','right']:
            def angle(field):
                a=np.array(list(reference[side+field].values()));b=np.array(list(case['bones'][side+field].values()))
                return float(np.degrees(np.arccos(np.clip(a@b/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1))))
            changes[name][side]=dict(normal_degrees=angle('HandNormal'),forward_degrees=angle('HandForward'),
                finger_max_delta=float(np.max(np.abs(np.array(case['bones'][side+'FingerAngles'])-reference[side+'FingerAngles']))))
    report['changes']=changes
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(changes,indent=2))
    for name in ['right-roll','left-roll','left-curl','right-curl']:
        moving,kind=name.split('-');still='left' if moving=='right' else 'right'
        assert max(changes[name][still].values())<.2,(name,'opposite hand changed',changes[name][still])
        field='normal_degrees' if kind=='roll' else 'finger_max_delta'
        assert changes[name][moving][field]>10,(name,'requested hand did not move')
    return report

def audit_recording(source, output, size):
    from tanakacap.body3d import BodyRetarget
    tracker=BodyRetarget(3,1,arm_depth_mode='front_projection',shoulder_yaw_mode='face_ratio')
    sides=('left','right')
    reasons={s:Counter() for s in sides};valid={s:np.zeros(5,int) for s in sides}
    angles={s:[] for s in sides};pairs={s:[0,0] for s in sides};count=0;missing_depth_amplitude=0
    with source.open(encoding='utf-8-sig') as stream:
        for line in stream:
            row=json.loads(line)
            def array(key,fallback):
                v=row.get(key,row.get(fallback))
                return None if v is None else np.asarray(v,float)
            xy=array('body_xy','xy');scores=array('body_scores','scores');depth=array('body_depth','depth')
            ds=array('body_depth_scores','depth_scores')
            if ds is None and scores is not None:
                ds=np.ones(len(scores));missing_depth_amplitude+=1
            pose=tracker.update(copy.deepcopy(row['sent_packet']),xy,scores,depth,ds,
                now=row['time'],image_size=row.get('image_size',size))
            count+=1
            for side,start,own,other in [('left',91,9,10),('right',112,10,9)]:
                reasons[side].update(tracker.diagnostics.get('fingers',{}).get(side,['body_early_return']*5))
                valid[side]+=pose[side+'FingerTracked'];angles[side].append(pose[side+'FingerFlex'])
                if xy is not None and scores is not None and np.isfinite(xy[[start,own,other]]).all() and min(scores[[start,own,other]])>=.3:
                    pairs[side][0]+=1
                    pairs[side][1]+=int(np.linalg.norm(xy[start]-xy[other])+10<np.linalg.norm(xy[start]-xy[own]))
    report=dict(source=str(source),observations=count,missing_depth_amplitude=missing_depth_amplitude,
        scope='Retarget saved model output, not new inference or ground truth. Missing depth peak amplitudes use finite ones; XY confidence unchanged. Opposite-wrist proximity is a proxy, not proof.',
        hands={s:dict(reasons=dict(reasons[s]),valid=valid[s].tolist(),wrist_pairs=pairs[s][0],opposite_wrist_nearer=pairs[s][1],
               flex_p95=np.percentile(angles[s],95,axis=0).tolist() if count else []) for s in sides})
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--avatar',type=Path)
    parser.add_argument('--recorded',type=Path)
    parser.add_argument('--image-size',type=int,nargs=2,default=[1280,720])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--player',type=Path,default=ROOT/'builds/player/TanakaCap.exe')
    a=parser.parse_args()
    if bool(a.avatar)==bool(a.recorded):parser.error('Choose exactly one of --avatar or --recorded')
    if a.recorded:audit_recording(a.recorded,a.output,a.image_size)
    else:run(a.player.resolve(),a.avatar.resolve(),a.output.resolve())
