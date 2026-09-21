import json
import socket
import pytest
from tanakacap.partial_tracking import LocalSender, FACE_PARTS, BODY_PARTS, PART_FIELDS, part_state
from tanakacap.control_panel import part_rate_text


def test_groups_are_sent_before_later_work_and_share_frame():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1',0)); receiver.settimeout(.2)
        sender=LocalSender(receiver.getsockname()[1])
        try:
            pose=dict(sequence=12,faceTracked=True,headYaw=0,leftArmTracked=True,leftArmHeld=True)
            sender.send(pose,FACE_PARTS)
            first=json.loads(receiver.recv(4096))
            assert {p['id'] for p in first['parts']}==set(FACE_PARTS)
            assert first['parts'][0]['values']['headYaw']==0
            # No gaze completion is needed for the first receive.
            sender.send(pose,BODY_PARTS)
            body=json.loads(receiver.recv(4096))
            arm=next(p for p in body['parts'] if p['id']=='left_arm')
            assert arm['state']=='held' and arm['values']=={}
            sender.send(pose,('gaze',),disabled=('gaze',))
            gaze=json.loads(receiver.recv(4096))
            assert gaze['parts'][0]['state']=='disabled'
            assert first['frameId']==body['frameId']==gaze['frameId']==12
            assert first['streamId']==gaze['streamId']
            assert first['packetSequence']<body['packetSequence']<gaze['packetSequence']
        finally: sender.close()


def test_oversized_parts_split_and_no_nan_is_sent():
    sender=LocalSender(39549)
    class Socket:
        def __init__(self): self.data=[]
        def sendto(self,data,target): self.data.append(data)
        def close(self): pass
    sender.socket.close(); sender.socket=Socket()
    pose=dict(sequence=1,faceTracked=True,browTracked=True,gazeTracked=True,faceDistanceTracked=True,torsoTracked=True)
    for side in ('left','right'):
        pose.update({side+'ArmTracked':True,side+'HandTracked':True,side+'FingerTracked':[True]*5,side+'FingerFlex':[123.123456789]*15})
    for fields in PART_FIELDS.values():
        for field in fields: pose.setdefault(field,123.123456789)
    sender.send(pose)
    assert all(len(data)<=4096 for data in sender.socket.data)
    assert {p['id'] for data in sender.socket.data for p in json.loads(data)['parts']}==set(PART_FIELDS)
    pose['headYaw']=float('nan')
    with pytest.raises(ValueError):sender.send(pose,('head',))


def test_ui_does_not_show_held_as_a_new_observation():
    assert part_rate_text(dict(state='valid',intervalMs=33.3))=='30.0 fps'
    assert part_rate_text(dict(state='held',intervalMs=33.3))=='保持中'
    assert part_rate_text(dict(state='stale',intervalMs=33.3))=='更新待ち'
    assert part_rate_text({})=='—'


def test_palm_uses_its_own_hold_flag():
    pose=dict(leftArmTracked=True,leftArmHeld=True,leftHandTracked=True,leftHandHeld=False)
    assert part_state(pose,'left_arm',())=='held'
    assert part_state(pose,'left_palm',())=='valid'
    pose.update(leftArmHeld=False,leftHandHeld=True)
    assert part_state(pose,'left_arm',())=='valid'
    assert part_state(pose,'left_palm',())=='held'
