"""Reprocess a -Diagnose numeric recording without opening the camera.

Compare recorded tracking flags with current retargeting, not ground-truth accuracy.
Writes a separate report and packet stream; never modifies the source recording.
"""
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture_lab.body3d import BodyRetarget
from capture_lab.retarget import FaceFilter,packet_from_landmarks

FLAGS = ('torsoTracked', 'leftArmTracked', 'rightArmTracked',
         'leftHandTracked', 'rightHandTracked')


def summarize(packets):
    return {flag: {
        'active_frames': sum(bool(p.get(flag)) for p in packets),
        'transitions': sum(bool(a.get(flag)) != bool(b.get(flag))
                           for a,b in zip(packets,packets[1:]))
    } for flag in FLAGS}


def replay(source, output, observation_block=1, observation_stride=None):
    rows = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    if not rows or not all('sent_packet' in row for row in rows):
        raise ValueError('Recording requires -Diagnose and Unity packet output')
    if not any(row.get('body_xy') is not None for row in rows):
        raise ValueError('No recorded 3D body landmarks')
    old, new, stream = [], [], []
    reasons = {key: Counter() for key in ('torso','left','right')}
    retarget = BodyRetarget(observation_block,observation_stride)
    face_filter=FaceFilter(observation_block,observation_stride)
    now = 0.
    metadata=source.parent/'report.json'
    arguments=json.loads(metadata.read_text(encoding='utf-8')).get('arguments',{}) if metadata.exists() else {}
    image_size=[arguments['width'],arguments['height']] if 'width' in arguments and 'height' in arguments else None
    recorded_calibration=None
    for row in rows:
        interval = row.get('result_interval_ms', 1000/30)
        now += (interval if interval is not None else 1000/30)/1000
        original = row['sent_packet']
        calibration=row.get('body_diagnostics',{}).get('calibration')
        if calibration != recorded_calibration:
            retarget.calibration.value=calibration
            retarget.calibration.consistency.clear()
            retarget.previous.clear()
            recorded_calibration=deepcopy(calibration)
        base=deepcopy(original)
        base['mouthShift']=0.
        if row.get('points_xy') is not None:
            raw_face=packet_from_landmarks(row['points_xy'],row['scores'],original['sequence'])
            base['mouthShift']=raw_face.get('mouthShift',0.)
            for key in ('faceTracked','headPitch','headYaw','headRoll','mouth','mouthWidth','mouthRound','mouthSmile','leftBlink','rightBlink','mouthContourTracked','mouthLeftCorner','mouthRightCorner','mouthBow'):
                base[key]=raw_face[key]
        base.pop('tongueTracked',None);base.pop('tongueOut',None)
        face_filter.update(base,now)
        current = retarget.update(base, row.get('body_xy'),
                                  row.get('body_scores'), row.get('body_depth'),
                                  row.get('body_depth_scores'), now=now,image_size=row.get('image_size',image_size),
                                  reference_xy=row.get('points_xy'),reference_scores=row.get('scores'))
        old.append(original)
        new.append(current)
        stream.append({'frame': row['frame'], 'time_seconds':now, 'packet':current,
                       'body_diagnostics':deepcopy(retarget.diagnostics)})
        for key in reasons:
            reasons[key][retarget.diagnostics[key]] += 1
    report = dict(source=str(source.resolve()), frames=len(rows), observation_block=observation_block, observation_stride=observation_stride,
                  body_frames=sum(row.get('body_xy') is not None for row in rows),
                  limitation='Activation continuity only; no ground-truth motion or accuracy measurement. Replay starts without pre-recording warmup state.',
                  recorded=summarize(old), replay=summarize(new),
                  held_frames={key:sum(p.get(key,False) for p in new)
                               for key in ('leftArmHeld','rightArmHeld','leftHandHeld','rightHandHeld')},
                  rejection_counts=reasons)
    output.mkdir(parents=True,exist_ok=False)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (output/'packets.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in stream),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation-stride',type=int,choices=(1,3))
    parser.add_argument('--observation-block',type=int,choices=(1,3),default=1)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    replay(args.source,args.output,args.observation_block,args.observation_stride)
