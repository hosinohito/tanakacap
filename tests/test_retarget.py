import json
import socket
import numpy as np
from tanakacap.retarget import LocalSender, packet_from_landmarks


def test_missing_landmarks_produce_safe_inactive_packet():
    packet = packet_from_landmarks(np.full((133,2),np.nan),np.zeros(133),17)
    assert not packet['tracked'] and not packet['faceTracked']
    assert packet['sequence'] == 17
    json.dumps(packet, allow_nan=False)


def test_occluded_arm_does_not_disable_other_arm():
    points = np.zeros((133,2))
    scores = np.zeros(133)
    points[[5,6,7,9]] = [[300,100],[100,100],[320,200],[330,290]]
    scores[[5,6,7,9]] = 1
    packet = packet_from_landmarks(points,scores,0)
    assert packet['leftArmTracked'] and not packet['rightArmTracked']
    assert packet['leftWrist']['x'] < 0 and packet['leftWrist']['y'] < 0
    scores[9] = 0
    assert not packet_from_landmarks(points,scores,1)['leftArmTracked']


def test_loopback_transport_sends_json_without_image():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1',0))
        receiver.settimeout(1)
        sender = LocalSender(receiver.getsockname()[1])
        try:
            sender.send(packet_from_landmarks(np.full((133,2),np.nan),np.zeros(133),2))
            data, address = receiver.recvfrom(4096)
            assert address[0] == '127.0.0.1'
            assert json.loads(data)['sequence'] == 2
        finally:
            sender.close()
