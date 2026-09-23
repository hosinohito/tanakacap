"""Run the normal inference/UDP/Player path with opt-in numeric hand diagnostics."""
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.control_panel import commands, load_settings, close_player

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',choices=('video','camera'),required=True)
    parser.add_argument('--frames',type=int,default=901)
    parser.add_argument('--headless',action='store_true')
    args=parser.parse_args()
    if args.frames<2:parser.error('frames must be >=2')
    config=load_settings()
    config.update(source=args.source,mode='full',body=True,expression='auto-custom')
    if args.source=='video':
        import cv2
        video=cv2.VideoCapture(config['video'])
        fps=video.get(cv2.CAP_PROP_FPS);video.release()
        if not 1<=fps<=240:raise ValueError('Cannot read recording FPS')
    folder=ROOT/'results/hand-realtime'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-%fZ')
    folder.mkdir(parents=True,exist_ok=False)
    stop=threading.Event()
    def udp():
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1',0));sock.settimeout(.1)
        return sock
    relay,status,probe=udp(),udp(),udp()
    port=probe.getsockname()[1];probe.close()
    player_args,_=commands(config,port,status.getsockname()[1])
    player_args.remove('-nolog')
    player_args+=['-logFile',str(folder/'player.log'),'--hand-trace',str(folder/'player-hands.jsonl')]
    if args.headless:player_args+=['-batchmode']
    meta=dict(status='running',source=args.source,settings=config,started_utc=datetime.now(timezone.utc).isoformat(),
              scope='Normal inference, part-wise UDP and Player. Numeric diagnostics add overhead; no raw images are recorded or displayed.',
              timing='Video capped at source FPS, may run slower under load; camera uses selected capture settings.')
    (folder/'session.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    failures=[]
    def receive(sock,path,forward=False):
        try:
            with path.open('w',encoding='utf-8') as log:
                while not stop.is_set():
                    try:data,_=sock.recvfrom(65535)
                    except socket.timeout:continue
                    stamp=time.perf_counter()
                    if forward:sock.sendto(data,('127.0.0.1',port))
                    log.write(json.dumps(dict(time=stamp,packet=json.loads(data)))+'\n')
        except BaseException as error:failures.append(repr(error))
    threads=[threading.Thread(target=receive,args=(relay,folder/'wire.jsonl',True)),
             threading.Thread(target=receive,args=(status,folder/'status.jsonl'))]
    player=infer=None
    try:
        for thread in threads:thread.start()
        player=subprocess.Popen(player_args,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
        _,infer_args=commands(config,relay.getsockname()[1],status.getsockname()[1],player.pid)
        infer_args.remove('--no-log')
        if '--loop-video' in infer_args:infer_args.remove('--loop-video')
        infer_args[infer_args.index('--frames')+1]=str(args.frames)
        infer_args+=['--landmarks','--no-ort-profile']
        if args.source=='video':infer_args[infer_args.index('--inference-limit')+1]=str(fps)
        env=dict(os.environ,TANAKACAP_UI_PRECISION=config['precision'],PYTHONIOENCODING='utf-8',PYTHONUTF8='1')
        infer=subprocess.Popen(infer_args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                               encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
        meta.update(player_command=player_args,inference_command=infer_args)
        def console():
            with (folder/'inference.log').open('w',encoding='utf-8') as log:
                for line in infer.stdout:
                    line=re.sub(r'\x1b\[[0-9;]*m','',line.replace('\x00','')).rstrip()
                    log.write(line+'\n')
                    if line.startswith('Results: '):meta['inference_results']=line[9:]
                    if 'frames processed' in line:print(line,flush=True)
        reader=threading.Thread(target=console);reader.start()
        print('ログ: '+str(folder),flush=True)
        print('SPACE: 症状の時刻を記録 / Q: 終了。実写は表示しません。',flush=True)
        start=time.perf_counter()
        with (folder/'markers.jsonl').open('w',encoding='utf-8') as markers:
            while infer.poll() is None:
                if time.perf_counter()-start>max(120,args.frames/5):raise TimeoutError('Inference timeout')
                if failures:raise RuntimeError(str(failures))
                if not args.headless:
                    import msvcrt
                    if msvcrt.kbhit():
                        key=msvcrt.getwch()
                        if key==' ':
                            markers.write(json.dumps(dict(time=time.perf_counter()))+'\n');markers.flush()
                            print('時刻を記録しました。',flush=True)
                        if key.lower()=='q':close_player(player)
                time.sleep(.05)
        reader.join(timeout=5)
        if infer.returncode:raise RuntimeError('Inference failed; see inference.log')
        meta['status']='complete'
    except BaseException as error:
        meta.update(status='failed',error=repr(error));raise
    finally:
        close_player(player)
        if infer and infer.poll() is None:
            try:infer.wait(timeout=5)
            except subprocess.TimeoutExpired:infer.terminate();infer.wait(timeout=5)
        stop.set()
        for thread in threads:
            if thread.ident:thread.join(timeout=3)
        relay.close();status.close()
        if failures:meta.update(status='failed',errors=failures)
        if not (folder/'player-hands.jsonl').is_file() or (folder/'player-hands.jsonl').stat().st_size==0:meta.update(status='failed',error='Player hand trace missing; rebuild Player')
        (folder/'session.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
        print('結果: '+str(folder),flush=True)
    if meta['status']!='complete':raise RuntimeError(meta.get('error',str(failures)))

if __name__=='__main__':main()
