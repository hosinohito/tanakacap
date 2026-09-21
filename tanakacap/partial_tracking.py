"""Part-wise absolute targets. Internal pose dictionaries are not wire packets."""
import json
import socket
import time
import uuid

FACE_PARTS = ('head', 'face_distance', 'mouth', 'brows', 'eyelids')
BODY_PARTS = ('torso', 'left_arm', 'right_arm', 'left_palm', 'right_palm', 'left_fingers', 'right_fingers')
PART_FIELDS = {
    'head': ('headPitch', 'headYaw', 'headRoll'),
    'face_distance': ('faceDistanceRatio',),
    'mouth': ('mouth', 'mouthWidth', 'mouthRound', 'mouthSmile', 'mouthContourTracked',
              'mouthLeftCorner', 'mouthRightCorner', 'mouthBow', 'mouthShift'),
    'brows': ('browLeftInner', 'browLeftOuter', 'browRightInner', 'browRightOuter'),
    'eyelids': ('leftBlink', 'rightBlink'),
    'gaze': ('gazeYaw', 'gazePitch'),
    'torso': ('torsoPitch', 'torsoYaw', 'torsoRoll', 'body3d'),
}
for _side in ('left', 'right'):
    PART_FIELDS[_side+'_arm'] = tuple(_side+k for k in ('Elbow', 'Wrist', 'CrossBody', 'WristInFront', 'UpperInFront'))
    PART_FIELDS[_side+'_palm'] = tuple(_side+k for k in ('HandForward', 'HandNormal'))
    PART_FIELDS[_side+'_fingers'] = tuple(_side+k for k in ('FingerTracked', 'FingerFlex'))


def part_state(pose, part, disabled):
    if part in disabled:
        return 'disabled'
    if part == 'head':
        valid = pose.get('headTracked', pose.get('faceTracked', False))
    elif part in ('mouth', 'eyelids'):
        valid = pose.get('faceTracked', False)
    elif part in ('brows', 'face_distance', 'gaze', 'torso'):
        flag = dict(brows='browTracked', face_distance='faceDistanceTracked', gaze='gazeTracked', torso='torsoTracked')[part]
        valid = pose.get(flag, False)
    else:
        side, kind = part.split('_')
        valid = any(pose.get(side+'FingerTracked', [])) if kind == 'fingers' else pose.get(side+('ArmTracked' if kind == 'arm' else 'HandTracked'), False)
        held_flag=side+('ArmHeld' if kind=='arm' else 'HandHeld')
        if valid and kind in ('arm', 'palm') and pose.get(held_flag, False):
            return 'held'
    return 'valid' if valid else 'lost'


class LocalSender:
    """Only protocol v2 is sent; rollback is a source revision, not a runtime mode."""
    def __init__(self, port, *, clock=time.perf_counter):
        if not 1024 <= port <= 65535:
            raise ValueError('Local UDP port must be 1024..65535')
        self.target = ('127.0.0.1', port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clock = clock
        self.stream_id = uuid.uuid4().hex
        self.stream_started = clock()
        self.sequence = 0
        self.part_sequences = dict.fromkeys(PART_FIELDS, 0)

    def send(self, pose, parts=None, *, disabled=()):
        now = self.clock()
        acquired = pose.get('inputReadTime', now)
        header = dict(version=2, streamId=self.stream_id, streamStarted=self.stream_started,
                      frameId=int(pose['sequence']), inputReadTime=acquired, inputSentTime=now,
                      observationAge=max(0., now-acquired))
        batch = []
        for name in PART_FIELDS if parts is None else parts:
            self.part_sequences[name] += 1
            state = part_state(pose, name, disabled)
            values = {key: pose[key] for key in PART_FIELDS[name] if key in pose} if state == 'valid' else {}
            part = dict(id=name, sampleSequence=self.part_sequences[name], state=state, values=values)
            candidate = dict(header, packetSequence=self.sequence+1, parts=batch+[part])
            if len(self._encode(candidate)) > 4096:
                if not batch:
                    raise ValueError('Tracking part exceeds UDP size limit: '+name)
                self._send(header, batch)
                batch = []
            batch.append(part)
        if batch:
            self._send(header, batch)

    @staticmethod
    def _encode(packet):
        return json.dumps(packet, allow_nan=False, separators=(',', ':')).encode('utf-8')

    def _send(self, header, parts):
        self.sequence += 1
        data = self._encode(dict(header, packetSequence=self.sequence, parts=parts))
        if len(data) > 4096:
            raise ValueError('Tracking datagram exceeds UDP size limit')
        self.socket.sendto(data, self.target)

    def close(self):
        self.socket.close()
