"""Finish the authorized offline comparison after existing raw workers complete."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=[ROOT/'results/comparisons'/('first-take-sam-'+name) for name in ('dinov3','vith')]
OUT=ROOT/'results/comparisons/body-three-models'
VIDEO=ROOT/'results/avatar-videos/body-three-models'


def report(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError):return None


def run():
    deadline=time.monotonic()+10800
    while True:
        statuses=[report(folder/'report.json') for folder in RAW]
        for folder,r in zip(RAW,statuses):
            if r and r.get('status')=='failed':raise RuntimeError(str(folder)+': '+r.get('error','failed'))
        if all(r and r.get('status')=='complete' for r in statuses):break
        if time.monotonic()>deadline:raise TimeoutError('Raw inference not complete; no partial video published')
        time.sleep(5)
    if any(r.get('frames')!=5187 or r.get('stride')!=1 or r.get('start_frame')!=0 for r in statuses):raise ValueError('Full 5187-frame candidates required')
    if not OUT.exists():
        subprocess.run([sys.executable,'tools/compare_body_models.py','--common','results/comparisons/first-take','--candidate','sam-dinov3='+str(RAW[0]),'--candidate','sam-vith='+str(RAW[1]),'--output',str(OUT)],cwd=ROOT,check=True)
    r=report(OUT/'report.json')
    if not r or r.get('status')!='complete' or r.get('partial_test'):raise ValueError('Complete common-control comparison required')
    if not VIDEO.exists():
        subprocess.run([sys.executable,'tools/render_comparison_videos.py','--comparison',str(OUT),'--output',str(VIDEO)],cwd=ROOT,check=True)
    r=report(VIDEO/'report.json')
    if not r or r.get('status')!='complete':raise ValueError('Complete decoded videos required')
    print('READY_FOR_VISUAL_REVIEW',VIDEO,flush=True)

if __name__=='__main__':run()
