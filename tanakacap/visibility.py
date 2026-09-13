"""Reject image-boundary observations before geometry/calibration, not after IK."""
import numpy as np


def screen_visibility(xy, scores, image_size):
    scores=np.asarray(scores,dtype=float).copy()
    states={side:False for side in ('left','right')}
    if image_size is None: return scores,states
    width,height=map(float,image_size)
    if width<=0 or height<=0: raise ValueError('Positive image dimensions required')
    xy=np.asarray(xy,dtype=float)
    margin=max(8.,min(width,height)*.025)
    edge=(~np.isfinite(xy).all(axis=1)) | (xy[:,0]<margin) | (xy[:,0]>width-1-margin) | (xy[:,1]<margin) | (xy[:,1]>height-1-margin)
    scores[7:9][edge[7:9]]=0
    # Seated hips often collapse onto the bottom border too. They must not
    # manufacture forward lean from a plausible confidence score.
    shoulder_span=float(np.linalg.norm(xy[6]-xy[5]))
    pelvis_margin=max(margin,.25*shoulder_span) if np.isfinite(shoulder_span) else margin
    hips=xy[11:13]
    # A hip center barely inside the frame still has no visible lower context.
    # Require a quarter shoulder-width of image below/around the pelvis.
    hip_edge=(~np.isfinite(hips).all(axis=1)) | (hips[:,0]<pelvis_margin) | (hips[:,0]>width-1-pelvis_margin) | (hips[:,1]>height-1-pelvis_margin) | (hips[:,1]<margin)
    scores[11:13][hip_edge]=0
    for side,offset,wrist in [('left',91,9),('right',112,10)]:
        palm=np.array([0,5,9,17])+offset
        # One clipped fingertip invalidates that finger, not an entire hand.
        # Body wrist or a collapsed palm at the border cannot identify an arm.
        censored=bool(edge[wrist] or (edge[palm[0]] and scores[palm[0]]>=.3) or np.count_nonzero(edge[palm] & (scores[palm]>=.3))>=3)
        states[side]=censored
        scores[offset:offset+21][edge[offset:offset+21]]=0
        if censored:
            scores[wrist]=0
            scores[offset:offset+21]=0
    return scores,states
