"""Re-infer every completed local take with common settings, then audit old finger signs."""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.comparison import load_take, images, frame_mask, line, dump
from tanakacap.inference import SimCCModel, PersonDetector, DetectionGate
from tanakacap.body3d import BodyRetarget

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--takes',type=Path,default=ROOT/'results/comparison-takes')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--revision',default='66d08f2')
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 settings=json.loads((ROOT/'tracking-settings.json').read_text())
 source=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','show',f'{a.revision}:tanakacap/fingers.py'],text=True)
 ns=dict(__name__='tanakacap.old_fingers',__package__='tanakacap');exec(compile(source,'old_fingers.py','exec'),ns)
 model=SimCCModel('rtmw3d-x-384',None,'graph-fp16',preprocess_mode=settings['preprocess_mode'])
 detector=PersonDetector(None,'graph',detector_graph=True)
 report=dict(status='running',revision=a.revision,settings=settings,model=model.identity,takes={})
 dump(a.output/'report.json',report)
 try:
  for take in sorted(a.takes.iterdir()):
   if not (take/'take.json').is_file():continue
   meta,timeline=load_take(take)
   folder=a.output/take.name;folder.mkdir()
   body=BodyRetarget(settings['observation_block'],settings['observation_stride'],'front_projection','face_ratio')
   old=ns['FingerTracker'](settings['observation_block'],settings['observation_stride'])
   gate=DetectionGate();roi=None;valid=0
   with (folder/'frames.jsonl').open('w') as stream:
    for clock,image in images(take,timeline):
     i=clock['frame'];now=clock['time'];size=image.shape[1::-1]
     if i%settings['detector_interval']==0:roi=gate.update(detector.detect(image)[0])
     packet={};detail={}
     if roi is not None:
      xy,s,_=model.predict(image,roi);s=frame_mask(xy,s,size);z=model.depth.copy();ds=model.depth_scores.copy()
      body.update(dict(faceTracked=False),xy,s,z,ds,now=now,image_size=size,reference_xy=xy,reference_scores=s)
      scale=body.diagnostics.get('geometry',{}).get('model_scale')
      if scale is not None:
       xyz=np.column_stack((-xy[:,0]*scale,-xy[:,1]*scale,-z))
       old.update(packet,xyz,s,ds,now)
       detail=dict(xy=xy[91:],z=z[91:],scores=s[91:],depth_scores=ds[91:],scale=scale)
       valid+=1
     else:body.update(dict(faceTracked=False),None,None,None,None,now=now,image_size=size)
     line(stream,dict(frame=i,time=now,**detail,packet=packet))
     if (i+1)%500==0:print(take.name,i+1,'/',len(timeline),flush=True)
   dump(folder/'reference.json',dict(settings=settings))
   subprocess.run([sys.executable,str(ROOT/'tools/diagnostics/audit_finger_signs.py'),'--records',str(folder/'frames.jsonl'),'--reference-report',str(folder/'reference.json'),'--revision',a.revision,'--output',str(folder/'audit')],stdout=subprocess.DEVNULL,check=True)
   report['takes'][take.name]=dict(video=str(take/meta['video_file']),video_sha256=meta['video_sha256'],frames=len(timeline),geometry_frames=valid,seconds=timeline[-1]['time']-timeline[0]['time'],audit=json.loads((folder/'audit/report.json').read_text()))
   dump(a.output/'report.json',report);print('Completed',take.name,flush=True)
  report.update(status='complete',execution=model.finish(),detector_execution=detector.finish())
 except BaseException as e:
  report.update(status='failed',error=repr(e));raise
 finally:dump(a.output/'report.json',report)
if __name__=='__main__':main()