"""Palm orientation from the whole-body model's hand landmarks; no finger articulation."""
import numpy as np
from .motion_gate import RotationGate


class PalmFilter:
    """Confirm large orientation changes briefly and filter whole orthogonal frames."""
    def __init__(self, block_size=1, stride=None):
        self.block_size=block_size
        self.stride=stride
        self.states={}
        self.pending={}
        self.motion={}

    def update(self,packet,now):
        for side in ('left','right'):
            if not packet.get(side+'HandTracked'):
                self.pending.pop(side,None)
                if side in self.motion:
                    gate=self.motion[side]
                    gate.missing()
                continue
            f,n=[np.array([packet[side+suffix][axis] for axis in 'xyz'])
                 for suffix in ('HandForward','HandNormal')]
            frame=np.column_stack((np.cross(n,f),n,f))
            frame=self.motion.setdefault(side,RotationGate(self.block_size,self.stride)).update(frame,now)
            if frame is None:
                packet[side+'HandTracked']=False
                continue
            state=self.states.get(side)
            if state and now-state[0]<.2:
                dt=max(.001,now-state[0]); old=state[1]
                angle=np.arccos(np.clip((np.trace(old.T@frame)-1)/2,-1,1))
                # RotationGate already confirms all rotations in two observations.
                # Do not add another reversal gate (which would wait twice).
                # Interpolate rotations, including an exact 180-degree change.
                relative=old.T@frame
                angle=np.arccos(np.clip((np.trace(relative)-1)/2,-1,1))
                gain=48
                alpha=min(1-np.exp(-gain*dt),np.radians(720)*dt/max(angle,1e-8))
                if angle>1e-6:
                    if np.pi-angle<1e-4:
                        _,vectors=np.linalg.eigh((relative+relative.T)/2)
                        axis=vectors[:,-1]
                        direction=self.motion[side].direction
                        if direction is not None and axis@(old.T@direction)<0:
                            axis=-axis
                    else:
                        axis=np.array([relative[2,1]-relative[1,2],relative[0,2]-relative[2,0],relative[1,0]-relative[0,1]])
                        axis/=np.linalg.norm(axis)
                    x,y,z=axis
                    cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
                    theta=angle*alpha
                    frame=old@(np.eye(3)+np.sin(theta)*cross+(1-np.cos(theta))*(cross@cross))
            else:
                self.pending.pop(side,None)
            self.states[side]=(now,frame)
            for suffix,vector in [('HandForward',frame[:,2]),('HandNormal',frame[:,1])]:
                packet[side+suffix]=dict(zip('xyz',map(float,vector)))


def palm_basis(xyz, scores, depth_scores, offset):
    # Each 21-point hand: wrist=0, index MCP=5, middle MCP=9, little MCP=17.
    ids = np.array([0,5,9,17])+offset
    p = np.asarray(xyz)[ids]
    confidence = np.asarray(scores)[ids]
    # Depth peak amplitude is diagnostic only, not calibrated confidence.
    if (not np.isfinite(p).all() or not np.isfinite(confidence).all()
            or (confidence<.3).any() or not np.isfinite(np.asarray(depth_scores)[ids]).all()):
        return None
    wrist,index,middle,little = p
    forward = middle-wrist
    across = little-index
    if not (.015<np.linalg.norm(forward)<.25 and .01<np.linalg.norm(across)<.2):
        return None
    normal = np.cross(index-wrist,little-wrist)
    area = np.linalg.norm(normal)
    denominator = np.linalg.norm(index-wrist)*np.linalg.norm(little-wrist)
    if denominator<1e-6 or area/denominator<.15:
        # Keep the original basis whenever valid. Only recover a collapsed
        # wrist triangle if independent middle/across axes still define a plane.
        middle_fraction=float(np.dot(middle-index,across)/np.dot(across,across))
        if not -.2<=middle_fraction<=1.2:return None
        normal=np.cross(forward,across)
        if np.linalg.norm(normal)/(np.linalg.norm(forward)*np.linalg.norm(across))<.15:return None
    forward /= np.linalg.norm(forward)
    normal -= forward*np.dot(normal,forward)
    if np.linalg.norm(normal)<1e-6:
        return None
    normal /= np.linalg.norm(normal)
    return forward,normal


def add_hands(packet, xyz, scores, depth_scores):
    for side,offset in [('left',91),('right',112)]:
        packet[side+'HandTracked'] = False
        basis = palm_basis(xyz,scores,depth_scores,offset)
        if basis is None or not packet.get(side+'ArmTracked'):
            continue
        packet[side+'HandTracked'] = True
        for label,vector in zip(('HandForward','HandNormal'),basis):
            packet[side+label] = dict(zip(('x','y','z'),map(float,vector)))
