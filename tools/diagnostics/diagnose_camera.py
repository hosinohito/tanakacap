"""User-launched CMS-V43BK acquisition checks; no inference or image display/save."""
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.camera_devices import enumerate_cameras

def main():
    devices=enumerate_cameras()
    matches=[d for d in devices if 'CMS-V43BK' in d['name'].upper()]
    if len(matches)!=1:raise RuntimeError('CMS-V43BKを一意に選べません: '+str(devices))
    device=matches[0]
    output=ROOT/'results'/f'camera-diagnostic-{time.time_ns()}';output.mkdir(parents=True)
    print('カメラを使うアプリの撮影を停止してください。映像の表示・保存はしません。',flush=True)
    print('対象: '+device['name']+' / 最大30fps',flush=True)
    print('保存先: '+str(output),flush=True)
    reports=[]
    for width,height,fmt in [(1280,720,'MJPG'),(640,480,'MJPG'),(1280,720,'YUY2'),(640,480,'YUY2')]:
        label=f'{width}x{height}-{fmt}'
        print(label+' / 30fps要求を検査中...',flush=True)
        cmd=[sys.executable,'-X','utf8','-m','tanakacap','probe-camera','--camera',str(device['index']),'--backend','dshow','--width',str(width),'--height',str(height),'--fps','30','--frames','120','--pixel-format',fmt]
        log=output/(label+'.txt')
        item=dict(case=label,requested_fps=30,device=device)
        with log.open('w',encoding='utf-8') as stream:
            try:
                done=subprocess.run(cmd,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=45)
                item['exit_code']=done.returncode
            except subprocess.TimeoutExpired:item['error']='45秒でタイムアウト'
        content=log.read_text(encoding='utf-8')
        for line in content.splitlines():
            if line.startswith('Results: '):
                report=Path(line[9:])/'report.json'
                if report.is_file():item['result']=json.loads(report.read_text(encoding='utf-8'))
        if 'result' in item:
            result=item['result'];code=result['camera']['fourcc'];fourcc=''.join(chr((code>>(8*i))&255) for i in range(4))
            print(f"実取得 {result['effective_read_fps']:.1f}fps / 報告値 {result['camera']['reported']} / 形式 {fourcc}",flush=True)
        else:print('取得失敗。詳細: '+str(log),flush=True)
        reports.append(item)
        (output/'summary.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    print('完了: '+str(output/'summary.json'),flush=True)

if __name__=='__main__':main()
