"""Sequential user-launched camera diagnosis; numeric logs only, restores controls."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tanakacap.camera_devices import enumerate_cameras

NATIVE = ROOT / 'builds/diagnostics/camera_native.exe'
PENDING = ROOT / 'results/camera-diagnostic-pending-restore.json'


def parse_events(content):
    events = []
    for line in content.splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except ValueError:
            pass
    return events


def exposure_trials(controls):
    if not controls.get('exposure_available'):
        return []
    low, high = controls['minimum'], controls['maximum']
    step = max(1, controls['step'])
    trials = []
    if controls['caps'] & 1:
        trials.append(('auto', controls['exposure'], 1))
    if controls['caps'] & 2:
        # IAMCameraControl exposure is log2(seconds): -6 / -7 target short exposures.
        values = sorted({low + ((max(low, min(high, target))-low)//step)*step
                         for target in (-6, -7)}, reverse=True)
        trials.extend(('manual'+str(value), value, 2) for value in values if value <= -6)
    return trials


def run_logged(command, log, timeout=40):
    interrupted = False
    with log.open('w', encoding='utf-8') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform=='win32' else 0)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(); code = 'timeout'
        except KeyboardInterrupt:
            process.kill(); process.wait(); code = 'interrupted'; interrupted = True
    content = log.read_text(encoding='utf-8', errors='replace')
    if interrupted:
        raise KeyboardInterrupt
    return {'exit_code': code, 'events': parse_events(content), 'log': str(log)}, content


def restore_controls(snapshot, output):
    controls = snapshot['controls']
    args = [str(NATIVE), 'restore',
            str(controls['power']) if controls.get('power_available') else 'skip', str(controls['power_flags']),
            str(controls['exposure']) if controls.get('exposure_available') else 'skip', str(controls['exposure_flags'])]
    restore_log = output/f'restore-{time.time_ns()}.txt'
    result, _ = run_logged(args, restore_log)
    ok = result['exit_code'] == 0
    for key, needed in [('restore_power', controls.get('power_available')),
                        ('restore_exposure', controls.get('exposure_available'))]:
        if needed:
            ok = ok and any(event.get(key) == 1 for event in result['events'])
    if not ok:
        raise RuntimeError('カメラ設定の復元を確認できません。復元記録を残して停止します: '+str(restore_log))
    if PENDING.exists():
        PENDING.unlink()


def main():
    if not NATIVE.is_file():
        raise RuntimeError('tools/diagnostics/build-native.cmd を実行して診断ツールをビルドしてください。')
    devices = enumerate_cameras()
    matches = [d for d in devices if 'CMS-V43BK' in d['name'].upper()]
    if len(matches) != 1:
        raise RuntimeError('CMS-V43BKを一意に選べません: '+str(devices))
    device = matches[0]
    output = ROOT/'results'/f'camera-diagnostic-{time.time_ns()}'
    output.mkdir(parents=True)
    print('対象: '+device['name']+'。他のカメラ利用を停止してください。映像の表示・保存はしません。', flush=True)
    print('保存先: '+str(output), flush=True)
    if PENDING.exists():
        print('前回中断した設定を先に復元します。', flush=True)
        restore_controls(json.loads(PENDING.read_text(encoding='utf-8')), output)
    reports = []

    def save(item):
        reports.append(item)
        (output/'summary.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')

    def native(label, *args):
        print(label+'...', flush=True)
        item, _ = run_logged([str(NATIVE), *map(str,args)], output/(label+'.txt'))
        item['case'] = label
        save(item)
        captured = next((event['capture'] for event in item['events'] if 'capture' in event), None)
        print(f"取得 {captured['fps']:.1f}fps" if captured else '設定・対応情報を記録（未対応・失敗理由は個別ログ）。', flush=True)
        return item

    inventory = native('00-inspect', 'inspect')
    snapshot = next((event for event in inventory['events'] if 'controls' in event), None)
    mf_index = next((event['mf_index'] for event in inventory['events'] if 'mf_index' in event), None)
    if snapshot:
        (output/'original-controls.json').write_text(json.dumps(snapshot, indent=2), encoding='utf-8')

    def changed_trial(label, *args):
        # Persist before mutation; recovery also runs after timeout or Ctrl+C.
        PENDING.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
        try:
            return native(label, *args)
        finally:
            restore_controls(snapshot, output)

    try:
        native('01-power-baseline', 'capture')
        if snapshot and snapshot['controls'].get('power_available'):
            for label, value in [('off',0), ('50hz',1), ('60hz',2)]:
                changed_trial('01-power-'+label, 'power', value)
        else:
            save({'case':'01-power', 'skipped':'ちらつき防止の元設定を取得できないため変更しません。'})
        native('02-exposure-baseline', 'capture')
        for label, value, flags in exposure_trials(snapshot['controls'] if snapshot else {}):
            changed_trial('02-exposure-'+label, 'exposure', value, flags)
        if not snapshot or not exposure_trials(snapshot['controls']):
            save({'case':'02-exposure', 'skipped':'露出設定または短い固定露出が未対応。'})
        # Native probe enumerates modes and selects a returned type without synthesizing a substitute.
        native('03-native-mode', 'capture')
        print('04: OpenCVの取得経路を比較します。', flush=True)
        for backend, index in [('dshow', device['index']), ('msmf', mf_index)]:
            if index is None:
                save({'case':'04-'+backend, 'skipped':'同じカメラの番号を照合できません。'})
                continue
            label = '04-opencv-'+backend
            cmd = [sys.executable,'-X','utf8','-m','tanakacap','probe-camera',
                   '--camera',str(index),'--backend',backend,'--width','1280','--height','720',
                   '--fps','30','--frames','150','--pixel-format','MJPG']
            item, content = run_logged(cmd, output/(label+'.txt'), timeout=45)
            item['case'] = label
            for line in content.splitlines():
                if line.startswith('Results: '):
                    path = Path(line[9:])/'report.json'
                    if path.is_file(): item['result'] = json.loads(path.read_text(encoding='utf-8'))
            save(item)
            if 'result' in item:
                print(f"{backend}: {item['result']['effective_read_fps']:.1f}fps", flush=True)
        native('04-native-repeat', 'capture')
    finally:
        if PENDING.exists():
            restore_controls(json.loads(PENDING.read_text(encoding='utf-8')), output)
    print('完了: '+str(output/'summary.json'), flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('中断しました。復元失敗の場合は診断batを再実行してください。')
        sys.exit(130)
