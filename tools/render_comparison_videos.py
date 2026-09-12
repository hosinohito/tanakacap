"""Render both existing controls through the real Unity avatar at the same clock."""
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def run(output):
 output=output.resolve();output.mkdir(parents=True,exist_ok=False)
 ff=ROOT/'tools/bin/ffmpeg.exe';player=ROOT/'builds/lab/TanakaCap.exe'
 inputs={'current':ROOT/'results/comparisons/first-take/baseline/replay.jsonl','hamer-fingers':ROOT/'results/comparisons/first-take-hamer/fingers/replay.jsonl'}
 report={'status':'running','scope':'Same original capture and camera; only finger geometry differs. Offline rendering, not live latency. Opaque MP4 preview; OBS RGBA output unchanged.','sources':{k:{'path':str(p),'sha256':sha(p)} for k,p in inputs.items()},'assembly_sha256':sha(ROOT/'builds/lab/TanakaCap_Data/Managed/Assembly-CSharp.dll'),'ffmpeg_sha256':sha(ff)}
 (output/'report.json').write_text(json.dumps(report,indent=2))
 videos=[]
 for name,source in inputs.items():
  video=output/(name+'.mp4');log=output/(name+'.log')
  subprocess.run([str(player),'-batchmode','--render-replay',str(source),'--video-output',str(video),'--ffmpeg',str(ff),'-logFile',str(log)],cwd=ROOT,check=True,timeout=900,creationflags=subprocess.CREATE_NO_WINDOW)
  meta=json.loads(Path(str(video)+'.json').read_text());assert meta['status']=='complete' and meta['packets']==5187
  videos.append(video);report[name]=meta;print(name,meta['frames'],meta['duration'],flush=True)
 if report['current']['frames']!=report['hamer-fingers']['frames']:raise ValueError('Video clocks differ')
 font='C\\:/Windows/Fonts/arial.ttf'
 labels=[f"[{i}:v]pad=iw:ih+48:0:48:color=0x161c26,drawtext=fontfile='{font}':text='{text}':fontcolor=white:fontsize=25:x=20:y=10[v{i}]" for i,text in enumerate(['Current - RTMW3D','HaMeR fingers - same body and corrections'])]
 filt=';'.join(labels)+';[v0][v1]hstack=inputs=2[out]'
 combined=output/'side-by-side.mp4'
 subprocess.run([str(ff),'-hide_banner','-loglevel','error','-n','-i',str(videos[0]),'-i',str(videos[1]),'-filter_complex',filt,'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(combined)],check=True,timeout=900,creationflags=subprocess.CREATE_NO_WINDOW)
 for video in videos+[combined]:
  subprocess.run([str(ff),'-hide_banner','-loglevel','error','-xerror','-i',str(video),'-f','null','-'],check=True,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
 report['status']='complete';report['videos']={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in videos+[combined]}
 (output/'report.json').write_text(json.dumps(report,indent=2));print(combined,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
