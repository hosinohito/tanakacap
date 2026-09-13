"""Independent output switches; OFF preserves the Player's last pose."""
def suppress_body(packet):
    for flag in ("body3d", "torsoTracked", "leftArmTracked", "rightArmTracked",
                 "leftHandTracked", "rightHandTracked", "leftUpperArmTracked",
                 "rightUpperArmTracked", "faceDistanceTracked"):
        packet[flag] = False
    packet["leftFingerTracked"] = [False] * 5
    packet["rightFingerTracked"] = [False] * 5
    # Unity validates flags and angles together, even for disabled fingers.
    # The face-only source has no body retargeter to populate these arrays.
    packet.setdefault("leftFingerFlex", [0.] * 15)
    packet.setdefault("rightFingerFlex", [0.] * 15)
    packet["tracked"] = bool(packet.get("faceTracked") or packet.get("headTracked"))
    return packet
