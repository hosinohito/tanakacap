from capture_lab.tracking_modes import suppress_body
def test_disabled_body_cannot_drive_fallback_arms_fingers_or_distance():
    packet = dict(faceTracked=True, headYaw=23, mouth=.8, torsoTracked=True,
                  leftArmTracked=True, rightArmTracked=True, body3d=True,
                  faceDistanceTracked=True, leftFingerTracked=[True]*5,
                  rightFingerTracked=[True]*5)
    suppress_body(packet)
    assert packet["tracked"] and packet["headYaw"] == 23 and packet["mouth"] == .8
    assert not any(packet[k] for k in ("torsoTracked","leftArmTracked","rightArmTracked","body3d","faceDistanceTracked"))
    assert not any(packet["leftFingerTracked"] + packet["rightFingerTracked"])
