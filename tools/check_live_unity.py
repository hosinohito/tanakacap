"""Bounded camera/GPU/player integration check; saves avatar output, not webcam images."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT/'results'/'unity'/f'live-{time.time_ns()}'
    folder.mkdir(parents=True)
    with (folder/'capture.log').open('w',encoding='utf-8') as log:
        capture = subprocess.Popen([str(ROOT/'.venv/Scripts/python.exe'),'-m','capture_lab','benchmark',
                                   '--source','camera','--camera','1','--frames','300','--unity-port','39540','--body3d'],
                                  cwd=ROOT,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            time.sleep(8)
            result = subprocess.run([str(ROOT/'builds/lab/TanakaCap.exe'),'-batchmode','--snapshot',str(folder/'avatar.png'),
                                     '-logFile',str(folder/'player.log')],cwd=ROOT,timeout=40,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            capture.wait(timeout=45)
            if capture.returncode or result.returncode:
                raise RuntimeError(f'capture={capture.returncode}, player={result.returncode}; see {folder}')
            packet = json.loads((folder/'avatar.png.tracking.json').read_text(encoding='utf-8-sig'))
            assert packet['version'] == 1 and packet['sequence'] > 0, 'No camera packet received by player'
            print(json.dumps({'result':str(folder),'received_sequence':packet['sequence'],'person_tracked':packet['tracked']}))
        finally:
            if capture.poll() is None:
                capture.terminate()


if __name__ == '__main__':
    main()
