"""Lip-contour controls from observed facial landmarks."""
import numpy as np

KEYS=('mouthLeftCorner','mouthRightCorner','mouthBow','mouthShift')


def contour_controls(points,scores):
    p=np.asarray(points,dtype=float)[23:91];s=np.asarray(scores)[23:91]
    ids=[31,35,36,39,42,45,*range(48,68)]
    if not np.isfinite(p[ids]).all() or not np.isfinite(s[ids]).all() or (s[ids]<.3).any():
        return None
    axis=(p[42]+p[45]-p[36]-p[39])/2
    distance=np.linalg.norm(axis)
    if distance<15:return None
    down=np.array([-axis[1],axis[0]])/distance
    # Upper and lower lip shoulder points give each corner its own reference.
    # 54 is the person's LEFT corner; raw camera images are not mirrored.
    center=(p[51]+p[57])/2
    left=float((center-p[54])@down/distance)
    right=float((center-p[48])@down/distance)
    # Upper central bow relative to its flanking contour; size alone cannot
    # create this signal. The avatar uses its authored omega mouth as a basis.
    bow=float(((p[50]+p[52])/2-p[51])@down/distance)
    shift=float(((p[48]+p[54]-p[31]-p[35])/2)@(axis/distance)/distance)
    return dict(mouthLeftCorner=float(np.clip(left/.10,-1,1)),
                mouthRightCorner=float(np.clip(right/.10,-1,1)),
                mouthBow=float(np.clip((bow-.01)/.06,0,1)),
                mouthShift=float(shift/.12))

