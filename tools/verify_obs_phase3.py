"""Verify an already-running isolated OBS and TanakaCap sender; no stream/record."""
import json,time
from pathlib import Path
import cv2,numpy as np
from obs_phase3 import OBS,ROOT

def run():
 p=ROOT/'results/phase3';o=OBS()
 (p/'obs-report.json').write_text(json.dumps({'status':'running'}))
 try:
  o.call('SetVideoSettings',baseWidth=1280,baseHeight=720,outputWidth=1280,outputHeight=720)
  scene=o.call('GetSceneList')['scenes'][0]['sceneName']
  for item in o.call('GetSceneItemList',sceneName=scene)['sceneItems']:
   o.call('SetSceneItemTransform',sceneName=scene,sceneItemId=item['sceneItemId'],sceneItemTransform={'scaleX':1.,'scaleY':1.,'positionX':0.,'positionY':0.})
  o.call('SetInputSettings',inputName='TanakaCap',inputSettings={'spoutsenders':'TanakaCap','compositemode':4},overlay=True)
  time.sleep(1)
  for source,name in [('TanakaCap','obs-source-final.png'),(scene,'obs-composite-final.png')]:
   o.call('SaveSourceScreenshot',sourceName=source,imageFormat='png',imageFilePath=str(p/name),imageWidth=1280,imageHeight=720)
  a=cv2.imread(str(p/'obs-source-final.png'),-1);b=cv2.imread(str(p/'obs-composite-final.png'),-1);background=cv2.imread(str(p/'checker.png'))
  assert a.shape==(720,1280,4)
  alpha=a[:,:,3];counts=dict(transparent=int((alpha==0).sum()),opaque=int((alpha==255).sum()),intermediate=int(((alpha>0)&(alpha<255)).sum()))
  assert counts['transparent']>100000 and counts['opaque']>10000 and counts['intermediate']>100
  assert np.max(np.abs(b[20,20,:3].astype(int)-background[20,20].astype(int)))<=2
  assert np.mean(abs(b[:,:,:3].astype(float)-background))>5
  time.sleep(2)
  o.call('SaveSourceScreenshot',sourceName='TanakaCap',imageFormat='png',imageFilePath=str(p/'obs-source-next.png'),imageWidth=1280,imageHeight=720)
  following=cv2.imread(str(p/'obs-source-next.png'),-1);changed=int(np.any(a!=following,axis=2).sum());assert changed>1000
  assert not o.call('GetStreamStatus')['outputActive'] and not o.call('GetRecordStatus')['outputActive']
  report=dict(status='complete',scope='Actual isolated OBS Spout input and compositing from external avatar. Demo motion, not camera latency or long-run quality.',obs_version=o.call('GetVersion')['obsVersion'],spout_plugin='1.12.0',input_settings=o.call('GetInputSettings',inputName='TanakaCap'),alpha_pixels=counts,changed_pixels_after_2s=changed,background_pixel_verified=True,streaming_started=False,recording_started=False)
  (p/'obs-report.json').write_text(json.dumps(report,indent=2));print(counts,'changed',changed)
 except BaseException as e:
  (p/'obs-report.json').write_text(json.dumps({'status':'failed','error':str(e)}));raise
 finally:o.close()
if __name__=='__main__':run()
