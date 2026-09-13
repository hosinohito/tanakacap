"""Independent three-joint finger flexion from existing 21-point hands."""
import numpy as np
from .hand_orientation import palm_basis
from .motion_gate import DirectionGate


class FingerTracker:
    def __init__(self, block_size=1, stride=None):
        self.block_size=block_size
        self.stride=stride
        self.gates = {}
        self.diagnostics = {}

    def update(self, packet, xyz, scores, depth_scores, now):
        for side, offset in [('left', 91), ('right', 112)]:
            reasons=['palm_basis']*5
            self.diagnostics[side]=reasons
            valid, angles = [False]*5, [0.]*15
            packet[side+'FingerTracked'] = valid
            packet[side+'FingerFlex'] = angles
            basis = palm_basis(xyz, scores, depth_scores, offset)
            if basis is None:
                for key,gate in self.gates.items():
                    if key[0]==side: gate.reset()
                continue
            normal = basis[1]
            inward=normal*(1 if side=='left' else -1)
            for finger, start in enumerate((1, 5, 9, 13, 17)):
                reasons[finger]='joint_confidence'
                ids = np.array([0, start, start+1, start+2, start+3])+offset
                points = np.asarray(xyz)[ids]
                confidence = np.asarray(scores)[ids]
                if (not np.isfinite(points).all() or not np.isfinite(confidence).all()
                        or (confidence < .3).any()
                        or not np.isfinite(np.asarray(depth_scores)[ids]).all()):
                    gate=self.gates.get((side,finger))
                    if gate: gate.reset()
                    continue
                segments = np.diff(points, axis=0)
                reasons[finger]='segment_length'
                lengths = np.linalg.norm(segments, axis=1)
                if (lengths < .003).any() or (lengths > .2).any():
                    gate=self.gates.get((side,finger))
                    if gate: gate.reset()
                    continue
                segments /= lengths[:, None]
                reasons[finger]='flexion_plane'
                # Signed hinge-plane angles: lateral errors and extension must
                # not be rectified into positive curl before temporal averaging.
                along=segments[1]-normal*(segments[1]@normal)
                reference=segments[0]-normal*(segments[0]@normal)
                # A closing MCP can point through the palm plane and its
                # projection can reverse. Anchor the longitudinal hemisphere
                # to the metacarpal, which does not fold with the finger.
                if finger!=0:
                    if np.linalg.norm(along)<.2:
                        along=reference
                    elif along@reference<0:
                        along=-along
                    if np.linalg.norm(along)<1e-5: continue
                along/=max(1e-5,np.linalg.norm(along))
                plane=np.array([along,inward])
                projected=segments[1:]@plane.T
                if (np.linalg.norm(projected,axis=1)<.2).any() and finger!=0: continue
                directions=np.arctan2(projected[:,1],projected[:,0])
                flex=np.degrees(np.r_[directions[0],(np.diff(directions)+np.pi)%(2*np.pi)-np.pi])
                if finger==0:
                    # Thumb CMC opposition is not the same DOF as finger MCP
                    # curl. Preserve the authored base instead of folding it
                    # from its angle to the palm; use a thumb-specific plane.
                    if not np.isfinite(scores[offset+5]) or scores[offset+5]<.3:
                        gate=self.gates.get((side,finger))
                        if gate: gate.reset()
                        continue
                    toward_index=np.asarray(xyz)[offset+5]-points[2]
                    axis=np.cross(segments[1],toward_index)
                    if not np.isfinite(axis).all() or np.linalg.norm(axis)<1e-5:
                        gate=self.gates.get((side,finger))
                        if gate: gate.reset()
                        continue
                    axis/=np.linalg.norm(axis)
                    flex=[0.]+[max(0,float(np.degrees(np.arctan2(axis@np.cross(a,b),a@b)))-5)
                               for a,b in zip(segments[1:3],segments[2:4])]
                    flex=np.clip(flex,0,[0,50,65])
                reasons[finger]='observation_warmup'
                flex = self.gates.setdefault((side, finger), DirectionGate(2.5, float('inf'),self.block_size,self.stride)).update(flex, now)
                if flex is None:
                    continue
                if finger!=0:
                    # 7-degree uncertainty band after signed averaging. Preserve
                    # the range endpoint; do not add another temporal filter.
                    limits=np.array([80.,110.,90.])
                    flex=np.maximum(0,np.asarray(flex)-7)*limits/(limits-7)
                flex=np.clip(flex,0,[80,110,90])
                angles[finger*3:finger*3+3] = [round(float(v), 3) for v in flex]
                valid[finger] = True
                reasons[finger]='ok'
