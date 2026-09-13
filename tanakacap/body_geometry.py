"""Conservative online geometry cues; never treat projected lengths as ground truth."""
from collections import deque
import numpy as np


def visible_hand_inward(xy,scores,side):
    """User's seated prior: observed wrist medial to its own shoulder is front.

    No upper/lower image-height limit, and no palm-facing requirement. Visibility
    is already censored at the frame boundary by BodyRetarget.
    """
    shoulder,wrist,other=(5,9,6) if side=='left' else (6,10,5)
    ids=[shoulder,wrist,other]
    p=np.asarray(xy)[ids];s=np.asarray(scores)[ids]
    if not np.isfinite(p).all() or not np.isfinite(s).all() or (s<.3).any():return False
    inward=p[2,0]-p[0,0]
    if abs(inward)<30:return False
    return bool((p[1,0]-p[0,0])*np.sign(inward)>=0)


def cross_body_amount(xy,scores,side):
    if not visible_hand_inward(xy,scores,side):return 0.
    shoulder,wrist,other=(5,9,6) if side=='left' else (6,10,5)
    p=np.asarray(xy)
    fraction=(p[wrist,0]-p[shoulder,0])/(p[other,0]-p[shoulder,0])
    return float(np.clip((fraction-.35)/.30,0,1))


def visible_in_front_of_torso(xy,scores,side,nominal_width=None):
    """Visible-hand/torso overlap cue, not a segmentation or occlusion proof."""
    xy=np.asarray(xy); scores=np.asarray(scores)
    # A widened torso rectangle is not evidence that an outward wrist is in
    # front. It used to swallow the valid elbow-back / hand-outside posture.
    if not visible_hand_inward(xy,scores,side): return False
    offset=91 if side=='left' else 112
    wrist=9 if side=='left' else 10
    ids=[5,6,wrist,offset,offset+9]
    if nominal_width is None:
        ids += [offset+5,offset+17]
    if not np.isfinite(xy[ids]).all() or not np.isfinite(scores[ids]).all() or not (scores[ids]>=.3).all():
        return False
    left,right=sorted(xy[[5,6]],key=lambda p:p[0])
    span=right[0]-left[0]
    top=(left[1]+right[1])/2
    if span<60: return False
    width=span if nominal_width is None else max(span,min(float(nominal_width),span*3))
    bottom=top+1.5*width
    if np.isfinite(xy[[11,12]]).all() and (scores[[11,12]]>=.5).all():
        bottom=min(bottom,float(np.mean(xy[[11,12],1])))
    points=xy[[wrist,offset+9]]
    if np.linalg.norm(xy[wrist]-xy[offset])>.35*width:
        return False
    center=(left[0]+right[0])/2
    radius=.60*width if nominal_width is None else 1.25*width
    return bool(((abs(points[:,0]-center)<radius)
                 &(points[:,1]>top-.85*width)&(points[:,1]<bottom)).all())


def constrain_front_arm(bones, upper_forward=False):
    """Keep an observed front wrist on the camera side of its shoulder.

    This seated overlap prior is not an occlusion detector. Preserve segment
    lengths and the posterior elbow branch; never stretch a forearm to satisfy
    contradictory monocular cues. upper_forward is a legacy ignored argument.
    """
    result=np.asarray(bones,dtype=float).copy()
    if result[:,2].sum()<.015:
        lengths=np.linalg.norm(result,axis=1)
        if (lengths<1e-8).any(): return result
        def set_depth(i,z):
            z=float(np.clip(z,-lengths[i],lengths[i]))
            xy=np.linalg.norm(result[i,:2])
            radius=np.sqrt(max(0,lengths[i]**2-z*z))
            result[i,:2]=result[i,:2]*radius/xy if xy>1e-8 else [0,-radius]
            result[i,2]=z
        # If necessary reduce posterior depth toward zero, without reflecting
        # the humerus. This is a cue compromise, not measured elbow motion.
        if .015-result[0,2]>lengths[1]:
            set_depth(0,min(0.,lengths[1]-.015))
        set_depth(1,max(abs(result[1,2]),.015-result[0,2]))
    return result


class SupportedLengths:
    """Largest per-segment lower bound supported by >=10 samples in 5 seconds."""
    def __init__(self):
        self.samples=[deque(),deque()]
        self.value=np.zeros(2)

    def update(self,projected,now):
        for i,length in enumerate(projected):
            history=self.samples[i]
            while history and now-history[0][0]>5:
                history.popleft()
            if np.isfinite(length) and .04<length<.5:
                history.append((now,float(length)))
            if len(history)>=10:
                candidate=sorted(v for _,v in history)[-10]
                self.value[i]=max(self.value[i],candidate)
        return self.value.copy()


class DepthAssist:
    def __init__(self):
        self.previous=None
        self.time=None
        self.front_count=0
        self.last_front=None
        self.front_active=False
        self.upper_forward=False
        self.lengths=SupportedLengths()

    def update(self, a, b, now, front_visible=False,learn_lengths=True):
        bones=np.stack([a,b]); projected=np.linalg.norm(bones[:,:2],axis=1)
        if self.time is None or now-self.time>.3:
            self.previous=None; self.front_count=0; self.last_front=None
        self.time=now
        self.front_count=self.front_count+1 if front_visible else 0
        if self.front_count>=2: self.last_front=now
        # A single lost palm point must not switch the depth branch to the back.
        # Expire from the last CONFIRMED cue, never extend on missing evidence.
        self.front_active=self.last_front is not None and now-self.last_front<=.2
        # A fallback distance scale must neither calibrate permanent lengths nor
        # interpret its shorter projection as a new length-based depth cue.
        # Keep stored session maxima intact; use model geometry + front cue.
        lengths=self.lengths.update(projected,now) if learn_lengths else np.zeros(2)
        # Wrist visibility does not determine the humerus depth branch. An
        # elbow behind its shoulder can reach a visible wrist by flexion.
        self.upper_forward=False
        if (lengths<=0).any():
            return (constrain_front_arm(bones,self.upper_forward),'front_learning') if self.front_active else (bones,'learning')
        if self.front_active:
            # Enumerate depth branches at the supported length. Keep observed XY;
            # a fully extended projection still uses model depth. The visible
            # front wrist constrains the ENDPOINT, not both segment signs.
            magnitudes=np.abs(bones[:,2]).copy()
            shortened=projected<.85*lengths
            magnitudes[shortened]=np.sqrt(np.maximum(0,lengths[shortened]**2-projected[shortened]**2))
            candidates=[]
            for s0 in (-1,1):
                for s1 in (-1,1):
                    z=magnitudes*np.array([s0,s1])
                    if abs(bones[0,2])>=.035 and z[0]*bones[0,2]<0: continue
                    if z.sum()<.015: continue
                    cost=float(np.sum((z-bones[:,2])**2))
                    if self.previous is not None:
                        cost+=.5*float(np.sum((z-self.previous)**2))
                    candidates.append((cost,z))
            if candidates:
                result=bones.copy()
                result[:,2]=min(candidates,key=lambda item:item[0])[1]
                self.previous=result[:,2].copy()
                return result,'front_length_fit'
        # A supported maximum is only a lower-bound length estimate. Use a soft
        # depth supplement, not the old hard length constraint or arm rejection.
        result=bones.copy()
        used_front=False
        for i in range(2):
            ratio=projected[i]/lengths[i]
            # Outward hands no longer receive the front prior. A collapsed
            # segment still has the same supported length: recover its depth
            # in the observed/previous hemisphere, without inventing +Z.
            if np.linalg.norm(bones[i])<.07 and lengths[i]>=.07 and projected[i]<lengths[i]:
                sign=np.sign(bones[i,2]) if abs(bones[i,2])>=.005 else np.sign(self.previous[i]) if self.previous is not None else 0
                if sign:
                    result[i,2]=sign*np.sqrt(max(0,lengths[i]**2-projected[i]**2))
                    continue
            # Recover a gross model-depth outlier without discarding valid XY.
            if np.linalg.norm(bones[i])>=.65 and projected[i]<lengths[i]*1.05:
                sign=np.sign(bones[i,2])
                result[i,2]=sign*np.sqrt(max(0,lengths[i]**2-projected[i]**2))
            if ratio>=.85 or (ratio<.15 and not (i==0 and self.front_count>=2)):
                continue
            magnitude=np.sqrt(max(0,lengths[i]**2-projected[i]**2))
            z=bones[i,2]
            # Only supplement a direction supported by the model; no guessed
            # camera-facing sign when model depth is ambiguous.
            if abs(z)<.035 or abs(z)>=magnitude:
                continue
            if self.previous is None or self.previous[i]*z<=0:
                continue
            result[i,2]=np.sign(z)*(.5*abs(z)+.5*magnitude)
        if self.front_active:
            if projected[1]<lengths[1]*.85 and result[:,2].sum()<.04:
                # A clearly foreshortened forearm must not remain flat merely
                # because the model provided almost zero depth.
                result[1,2]=max(result[1,2],.7*np.sqrt(max(0,lengths[1]**2-projected[1]**2)))
            result=constrain_front_arm(result,self.upper_forward)
            used_front=True
        self.previous=result[:,2].copy()
        return result,'front_prior' if used_front else ('assisted' if not np.allclose(result,bones) else 'model')

