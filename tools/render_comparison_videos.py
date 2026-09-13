"""Render synchronized candidate controls through the real Unity avatar at the same clock."""
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def run(output,comparison=None):
 output=output.resolve();output.mkdir(parents=True,exist_ok=False)
 ff=ROOT/'tools/bin/ffmpeg.exe';player=ROOT/'builds/lab/TanakaCap.exe'
 variants={}
 inputs={'current':ROOT/'results/comparisons/first-take/baseline/replay.jsonl','hamer-fingers':ROOT/'results/comparisons/first-take-hamer/fingers/replay.jsonl'}
 scope='Same original capture and camera; only finger geometry differs. Offline rendering, not live latency. Opaque MP4 preview; OBS RGBA output unchanged.'
 if comparison is not None:
  comparison=comparison.resolve();result=json.loads((comparison/'report.json').read_text(encoding='utf-8'))
  if result['status']!='complete':raise ValueError('Completed body comparison required')
  inputs={name:comparison/name/'replay.jsonl' for name in result['variants']}
  variants=result['variants']
  scope=result['scope']+' Opaque MP4 preview; OBS RGBA output unchanged.'
  if result.get('partial_test'):scope='PARTIAL INTEGRATION TEST. '+scope
 if len(inputs)<2:raise ValueError('At least two variants required')
 clocks=[]
 for source in inputs.values():
  rows=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
  clocks.append([row['dt'] for row in rows])
 if not clocks[0] or any(clock[1:]!=clocks[0][1:] or len(clock)!=len(clocks[0]) for clock in clocks[1:]):raise ValueError('Replay clocks differ')
 expected=len(clocks[0])
 report={'status':'running','scope':scope,'sources':{k:{'path':str(p),'sha256':sha(p)} for k,p in inputs.items()},'assembly_sha256':sha(ROOT/'builds/lab/TanakaCap_Data/Managed/Assembly-CSharp.dll'),'ffmpeg_sha256':sha(ff)}
 (output/'report.json').write_text(json.dumps(report,indent=2))
 videos=[]
 for name,source in inputs.items():
  video=output/(name+'.mp4');log=output/(name+'.log')
  variant=variants.get(name,{})
  selected=Path(variant.get('player',player))
  extra=variant.get('player_args',[])
  if not isinstance(extra,list) or any(not isinstance(a,str) for a in extra):raise ValueError('player_args must be a string list')
  subprocess.run([str(selected),'-batchmode',*extra,'--render-replay',str(source),'--video-output',str(video),'--ffmpeg',str(ff),'-logFile',str(log)],cwd=ROOT,check=True,timeout=900,creationflags=subprocess.CREATE_NO_WINDOW)
  for marker in variant.get('expected_log',[]):
   if marker not in log.read_text(encoding='utf-8',errors='replace'):raise ValueError('Missing Player verification: '+marker)
  meta=json.loads(Path(str(video)+'.json').read_text());assert meta['status']=='complete' and meta['packets']==expected
  meta['player']=str(selected);meta['player_args']=extra
  meta['assembly_sha256']=sha(selected.parent/'TanakaCap_Data/Managed/Assembly-CSharp.dll')
  avatar=Path(extra[extra.index('--avatar')+1]) if '--avatar' in extra else selected.parent/'avatars/haolan.tcap'
  meta['avatar_path']=str(avatar.resolve());meta['avatar_sha256']=sha(avatar)
  videos.append(video);report[name]=meta;print(name,meta['frames'],meta['duration'],flush=True)
 if len({report[name]['frames'] for name in inputs})!=1:raise ValueError('Video clocks differ')
 font='C\\:/Windows/Fonts/arial.ttf'
 labels=[f"[{i}:v]pad=iw:ih+48:0:48:color=0x161c26,drawtext=fontfile='{font}':text='{text}':fontcolor=white:fontsize=25:x=20:y=10[v{i}]" for i,text in enumerate([{'separate':'Face - RTMW-L (original)','body3d':'Face - RTMW3D-X / PnP','depth3d':'Face - RTMW3D-X / learned Z','current':'Current - RTMW3D-X','shoulder-width':'Shoulder width - monotonic reference','shoulder-face':'Shoulder width + face ratio guard','front-projection':'RTMW3D - front projection trial','hamer-fingers':'HaMeR fingers - same body and corrections','sam-dinov3':'SAM 3D Body - DINOv3','sam-vith':'SAM 3D Body - ViT-H'}.get(name,name) for name in inputs])]
 filt=';'.join(labels)+';'+''.join(f'[v{i}]' for i in range(len(videos)))+f'hstack=inputs={len(videos)}[out]'
 combined=output/'side-by-side.mp4'
 subprocess.run([str(ff),'-hide_banner','-loglevel','error','-n',*[v for path in videos for v in ['-i',str(path)]],'-filter_complex',filt,'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(combined)],check=True,timeout=900,creationflags=subprocess.CREATE_NO_WINDOW)
 rendered=videos+[combined]
 if list(inputs) in (['shift-4mm','shift-8mm'], ['range-off','range-on'], ['gaze-legacy','gaze-soft'], ['normal','exaggerated'], ['brow-direct','brow-adaptive'], ['brow-1x','brow-2x'], ['fixed','adaptive'], ['pnp','size2d'], ['separate','body3d'], ['body3d','depth3d'], ['mouth-z','mouth-no-z'], ['CUDA-FP32','CUDA-FP16'],['custom-demo','existing','auto-custom']):
  closeup=output/'face-closeup.mp4'
  close_labels=[label.replace('pad=iw:', 'crop=640:480:320:0,scale=960:720,pad=iw:') for label in labels]
  close_filter=';'.join(close_labels)+';'+''.join(f'[v{i}]' for i in range(len(videos)))+f'hstack=inputs={len(videos)}[out]'
  subprocess.run([str(ff),'-hide_banner','-loglevel','error','-n',*[v for path in videos for v in ['-i',str(path)]],'-filter_complex',close_filter,'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(closeup)],check=True,timeout=900,creationflags=subprocess.CREATE_NO_WINDOW)
  rendered.append(closeup)
 for video in rendered:
  subprocess.run([str(ff),'-hide_banner','-loglevel','error','-xerror','-i',str(video),'-f','null','-'],check=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
 report['status']='complete';report['videos']={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in rendered}
 (output/'report.json').write_text(json.dumps(report,indent=2));print(combined,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--comparison',type=Path);a=p.parse_args();run(a.output,a.comparison)
