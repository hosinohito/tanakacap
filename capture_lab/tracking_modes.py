"""Independent output switches; OFF preserves the Player's last pose."""
def suppress_body(packet):
    for flag in ("body3d", "torsoTracked", "leftArmTracked", "rightArmTracked",
                 "leftHandTracked", "rightHandTracked", "leftUpperArmTracked",
                 "rightUpperArmTracked", "faceDistanceTracked"):
        packet[flag] = False
    packet["leftFingerTracked"] = [False] * 5
    packet["rightFingerTracked"] = [False] * 5
    packet["tracked"] = bool(packet.get("faceTracked") or packet.get("headTracked"))
    return packet
