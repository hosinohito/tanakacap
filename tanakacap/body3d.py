"""RTMW3D relative depth -> avatar-space directions, with explicit weak-perspective scale.

XY pixels and Z metres are different units. A nominal .36 m shoulder span anchors
initial scale; rigid upper-face image size tracks relative camera distance.
This is an approximation, not calibrated metric reconstruction.
"""
import time
import numpy as np
from .hand_orientation import add_hands, PalmFilter
from .fingers import FingerTracker
from .arm_constraints import ArmCalibration, constrain_arm, smooth_fixed_bones
from .arm_filter import filter_arm
from .front_projection import FrontProjection
from .shoulder_projection import ShoulderProjection
from .motion_gate import DirectionGate
from .visibility import screen_visibility
from .face_scale import FaceScale
from .torso_yaw import elbow_yaw, elbow_agreement, shoulder_yaw_magnitude, ShoulderWidthReference
from .body_geometry import DepthAssist, visible_in_front_of_torso, constrain_front_arm, visible_hand_inward, cross_body_amount


class BodyRetarget:
    def __init__(self, block_size=1, stride=None, arm_depth_mode="legacy", shoulder_yaw_mode="legacy"):
        if arm_depth_mode not in ("legacy", "front_projection"): raise ValueError("Unknown arm depth mode")
        if shoulder_yaw_mode not in ("legacy", "width_only", "face_ratio"): raise ValueError("Unknown shoulder yaw mode")
        self.shoulder_yaw_mode = shoulder_yaw_mode
        self.shoulder_projection = ShoulderProjection()
        self.arm_depth_mode = arm_depth_mode
        self.projector = {side:FrontProjection() for side in ("left", "right")}
        self.block_size=block_size
        self.stride=stride
        self.previous = {}
        self.last_time = None
        self.diagnostics = {}
        self.scale = None
        self.face_scale = FaceScale()
        self.scale_time = -float('inf')
        self.shoulder_scale_ratio=1.
        self.calibration = ArmCalibration()
        self.calibration.status='AUTO lengths: collecting 10 observations within 5s'
        self.palms = PalmFilter(self.block_size,self.stride)
        self.fingers = FingerTracker(self.block_size,self.stride)
        self.arm_modes = {}
        self.motion={side:DirectionGate(.006,float('inf'),block_size,stride) for side in ('left','right')}
        self.cross_motion={side:DirectionGate(.02,float('inf'),block_size,stride) for side in ('left','right')}
        self.depth_assist={side:DepthAssist() for side in ('left','right')}
        self.torso_motion=DirectionGate(.35,float('inf'),block_size,stride)
        self.held={}
        self.yaw_direction=0.
        self.shoulder_width_reference=ShoulderWidthReference()

    def update(self, packet, xy, scores, depth, depth_scores, now=None, image_size=None,
               reference_xy=None, reference_scores=None, camera_xyz=None):
        now = time.perf_counter() if now is None else now
        dt = .033 if self.last_time is None else max(.001,min(.1,now-self.last_time))
        if self.last_time is not None and now-self.last_time > .3:
            self.previous.clear()
            for projector in self.projector.values(): projector.reset()
        self.last_time = now
        self.diagnostics = {'torso':'no_person','left':'no_person','right':'no_person'}
        packet.update(body3d=True,torsoTracked=False,torsoPitch=0.,torsoYaw=0.,torsoRoll=0.,
                      leftArmTracked=False,rightArmTracked=False,leftHandTracked=False,rightHandTracked=False,
                      leftArmHeld=False,rightArmHeld=False,leftHandHeld=False,rightHandHeld=False,
                      tracked=bool(packet['faceTracked']))
        for side in ('left','right'):
            packet[side+'FingerTracked']=[False]*5
            packet[side+'FingerFlex']=[0.]*15
            packet[side+'WristInFront']=False
            packet[side+'UpperInFront']=False
            packet[side+'OutOfView']=False
            packet[side+'UpperArmTracked']=False
            packet[side+'CrossBody']=0.
        if xy is None or depth is None:
            self.calibration.observe(None,None,now)
            self.previous.clear()
            self.held.clear()
            for projector in self.projector.values(): projector.reset()
            for gate in self.motion.values(): gate.reset()
            for gate in self.cross_motion.values():gate.reset()
            self.torso_motion.reset()
            # Accepted lengths are session maxima: never shorten on detection loss.
            for assist in self.depth_assist.values():
                assist.previous=None; assist.front_count=0; assist.time=None
            self.palms=PalmFilter(self.block_size,self.stride)
            self.fingers=FingerTracker(self.block_size,self.stride)
            return packet
        xy, scores, depth, depth_scores = map(np.asarray,(xy,scores,depth,depth_scores))
        scores,edge_states=screen_visibility(xy,scores,image_size)
        self.diagnostics['screen_boundary']=edge_states
        for side,invalid in edge_states.items():
            packet[side+'OutOfView']=invalid
            if invalid:
                self.held.pop(side+'Arm',None);self.held.pop(side+'Hand',None)
        if self.calibration.observe(xy,scores,now):
            self.previous.clear()
        self.calibration.check_consistency(xy,scores)
        calibrated=self.calibration.value
        self.diagnostics['calibration']=calibrated
        self.diagnostics['calibration_status']=self.calibration.status
        self.diagnostics['calibration_rejection']=self.calibration.rejection

        def visible(ids):
            # RTMW3D confidence is min(max(X), max(Y)), as in MMPose's
            # rtmpose3d/utils.py. Z peak amplitude is not a visibility score:
            # valid recorded joints commonly have peaks below 0.1.
            return (np.isfinite(xy[ids]).all() and np.isfinite(depth[ids]).all()
                    and np.isfinite(scores[ids]).all() and (scores[ids]>=.3).all()
                    and np.isfinite(depth_scores[ids]).all())

        self.diagnostics['joint_xy_scores'] = [float(v) for v in scores[5:13]]
        self.diagnostics['joint_z_scores'] = [float(v) for v in depth_scores[5:13]]

        shoulders_visible = visible([5,6])
        span = np.linalg.norm(xy[6]-xy[5]) if np.isfinite(xy[[5,6]]).all() else 0.
        dz = float(depth[6]-depth[5]) if np.isfinite(depth[[5,6]]).all() else float('inf')
        shoulder_scale=None
        if shoulders_visible and span>=30 and abs(dz)<=.5:
            shoulder_scale=np.sqrt(max(.36**2-min(abs(dz),.33)**2,.13**2))/span
        face_scale=self.face_scale.update(xy,scores,shoulder_scale,now)
        scale_source='cached'
        if face_scale is not None:
            self.scale=face_scale
            self.scale_time=now
            scale_source='face'
            if shoulder_scale is not None:self.shoulder_scale_ratio=face_scale/shoulder_scale
        elif shoulder_scale is not None:
            # Distance calibration is optional evidence, not a whole-body gate.
            # Preserve the last agreed face/shoulder ratio while continuing to
            # observe shoulders. Do NOT learn arm lengths from this fallback.
            self.scale=shoulder_scale*self.shoulder_scale_ratio
            self.scale_time=now
            scale_source='shoulder_fallback'
        self.diagnostics['distance_source']=self.face_scale.status
        self.diagnostics['face_scale']=self.face_scale.details
        self.diagnostics['geometry_scale_source']=scale_source
        learn_lengths=face_scale is not None or (image_size is None and self.face_scale.reference is None)
        self.diagnostics['arm_length_learning']=learn_lengths
        if self.scale is None or now-self.scale_time>.5:
            self.diagnostics['geometry_scale_source']='unavailable'
            self.diagnostics.update(torso='scale_unavailable',left='scale_unavailable',right='scale_unavailable')
            self.previous.clear()
            return packet
        # Only differences are used below; no dependence on a missing opposite shoulder.
        xyz = np.column_stack((-xy[:,0]*self.scale,-xy[:,1]*self.scale,-depth))
        if camera_xyz is not None:
            # Optional native metric geometry. Image landmarks still supply
            # visibility/face scale/overlap evidence; do not flatten true 3D XY.
            native=np.asarray(camera_xyz,dtype=float)
            if native.shape!=(len(xy),3):raise ValueError('camera_xyz must match joint layout')
            mask=np.isfinite(native).all(axis=1)
            if not mask[[5,6]].all():raise ValueError('Native geometry requires finite shoulders')
            anchor=xyz[[5,6]].mean(axis=0)
            xyz[mask]=-(native[mask]-native[[5,6]].mean(axis=0))+anchor
            self.diagnostics['native_metric_geometry']=True
        self.diagnostics['geometry']={'model_scale':float(self.scale),
                                      'shoulder_pixels':float(span),
                                      'shoulder_depth_difference':float(dz) if np.isfinite(dz) else None}
        # Unity avatar faces +Z, camera depth increases away: invert Z.
        self.diagnostics['torso']='shoulder_confidence'
        if shoulders_visible and span>=30 and abs(dz)<=.5:
            right = xyz[6]-xyz[5]
            right /= np.linalg.norm(right)
            up = np.array([0.,1.,0.])
            pitch_observed=False
            if visible([11,12]):
                hips = (xyz[11]+xyz[12]-xyz[5]-xyz[6])/2
                if .12 < -hips[1] < .8 and np.linalg.norm(hips) < 1.:
                    up = -hips/np.linalg.norm(hips)
                    pitch_observed=True
            forward = np.cross(right,up)
            norm = np.linalg.norm(forward)
            self.diagnostics['torso']='torso_basis'
            # In a side view projected shoulders can cross. Strong shoulder
            # depth still supplies a yaw cue; do not drop the entire torso.
            if norm>=.2 and (forward[2]>.1 or abs(dz)>.08):
                forward /= norm
                self.diagnostics['torso']='ok'
                packet.update(torsoTracked=True,
                              torsoYaw=0.,
                              torsoPitch=float(np.clip(np.degrees(np.arctan2(-forward[1],np.hypot(forward[0],forward[2]))),-50,50)),
                              torsoRoll=float(np.clip(np.degrees(np.arctan2(right[1],right[0])),-25,25)))
                if not pitch_observed:
                    # A visible shoulder line still supplies yaw/roll. Missing
                    # pelvis supplies no new pitch; retain its accepted angle.
                    packet['torsoPitch']=float(self.torso_motion.accepted[0]) if self.torso_motion.accepted is not None else 0.
                self.diagnostics['torso_pitch_source']='hips' if pitch_observed else 'held_missing_hips'
                elbow_direction=elbow_yaw(xyz,scores) if visible([7,8]) else None
                agreement,detail=elbow_agreement(xy,scores,reference_xy,reference_scores,image_size)
                self.diagnostics['elbow_agreement']=detail
                yaw_source='shoulder_width_elbow_sign'
                if elbow_direction is None:
                    yaw_source='held_missing_elbows'
                elif not agreement:
                    yaw_source='held_elbow_'+detail['status']
                elif abs(xyz[7,2]-xyz[8,2])>=.015:
                    self.yaw_direction=float(np.sign(elbow_direction))
                else:
                    yaw_source='held_ambiguous_elbow_sign'
                if self.shoulder_yaw_mode == 'legacy':
                    magnitude,magnitude_source=shoulder_yaw_magnitude(xy,face_scale,dz)
                    if face_scale is not None or self.shoulder_width_reference.width is not None:
                        self.diagnostics['shoulder_frontal_reference_updated']=self.shoulder_width_reference.observe_frontal(span,face_scale,dz,agreement,now)
                        magnitude=self.shoulder_width_reference.update(span,face_scale,now)
                        magnitude_source='observed_shoulder_reference' if face_scale is not None else 'held_shoulder_scale'
                    self.diagnostics['shoulder_reference_width']=self.shoulder_width_reference.width
                    reference_width=self.shoulder_width_reference.width
                    self.diagnostics['shoulder_face_relative_ratio']=(span*face_scale/reference_width) if face_scale is not None and reference_width else None
                    self.diagnostics['shoulder_reference_pixels']=(reference_width/face_scale) if face_scale is not None and reference_width else None
                    packet['torsoYaw']=self.yaw_direction*magnitude
                    # Width shrink alone also occurs when the shoulder detector
                    # moves on clothing. Require compatible shoulder-depth evidence;
                    # elbows still choose the sign and width still supplies amount.
                    yaw_consistent=abs(dz)>=.025
                    if not yaw_consistent:packet['torsoYaw']=0.
                else:
                    magnitude=self.shoulder_projection.update(xy,scores,self.face_scale.details,
                        face_scale is not None,packet,now,guard=self.shoulder_yaw_mode=='face_ratio')
                    projection=self.shoulder_projection.details.copy()
                    self.diagnostics['shoulder_projection']=projection
                    magnitude_source='image_shoulder_face_ratio'
                    yaw_source=self.shoulder_yaw_mode
                    if projection['status']!='width_observed':
                        # Hold the signed accepted yaw, not only its magnitude;
                        # a noisy model elbow must not flip a missing observation.
                        packet['torsoYaw']=float(self.torso_motion.accepted[1]) if self.torso_motion.accepted is not None else 0.
                    else:
                        packet['torsoYaw']=self.yaw_direction*magnitude
                    yaw_consistent=None  # Legacy shoulder-Z veto is not used.
                self.diagnostics['torso_yaw_evidence_consistent']=yaw_consistent
                self.diagnostics['torso_yaw_source']=yaw_source
                self.diagnostics['torso_yaw_magnitude']=magnitude
                self.diagnostics['torso_yaw_magnitude_source']=magnitude_source
                self.diagnostics['torso_yaw_direction']=self.yaw_direction
                self.diagnostics['torso_elbow_depths']=xyz[[7,8],2].tolist() if elbow_direction is not None else None
                raw_angles=[packet['torsoPitch'],packet['torsoYaw'],packet['torsoRoll']]
                self.diagnostics['torso_raw_angles']=raw_angles
                self.diagnostics['torso_shoulder_direction']=right.tolist()
                angles=self.torso_motion.update(raw_angles,now)
                if angles is None:
                    packet['torsoTracked']=False
                else:
                    packet.update(torsoPitch=float(angles[0]),torsoYaw=float(angles[1]),torsoRoll=float(angles[2]))
                self.diagnostics['torso_mode']='shoulder_width_elbow_sign_roll_hip_pitch'
        for side, ids in [('left',[5,7,9]),('right',[6,8,10])]:
            if not visible(ids):
                self.motion[side].reset()
                self.diagnostics[side]='screen_boundary' if edge_states[side] else 'joint_confidence'
                self.previous.pop(side,None)
                continue
            shoulder, elbow, wrist = xyz[ids]
            a,b = elbow-shoulder,wrist-elbow
            self.diagnostics[side+'_lengths'] = [float(np.linalg.norm(a)),float(np.linalg.norm(b))]
            prior=self.previous.get(side)
            mode='model'
            if calibrated:
                confirmed=self.motion[side].update(np.stack([a,a+b])/.36,now)
                if confirmed is None:
                    self.diagnostics[side]='observation_warmup'
                    continue
                confirmed=confirmed*.36
                a,b=confirmed[0],confirmed[1]-confirmed[0]
                # Calibration changes arm geometry only, never torso/palm scale.
                ca,cb=a.copy(),b.copy()
                ca[:2]*=calibrated['scale']/self.scale
                cb[:2]*=calibrated['scale']/self.scale
                prior_bones=None if prior is None or self.arm_modes.get(side)!='calibrated' else np.stack([prior[0],prior[1]-prior[0]])*.36
                # Do not clamp a visibly longer projection to a shorter bone and
                # flatten its depth. Use model tracking when calibration conflicts.
                compatible=(np.linalg.norm([ca[:2],cb[:2]],axis=1)<=np.asarray(calibrated[side])*1.05).all()
                solved=constrain_arm(ca,cb,calibrated[side],prior_bones,
                                     forward if packet['torsoTracked'] else None)
                if solved is not None and compatible:
                    if prior_bones is not None:
                        solved=smooth_fixed_bones(prior_bones,solved,calibrated[side],dt)
                    a,b=solved
                    mode='calibrated'
                    self.diagnostics[side+'_constrained_lengths']=[float(np.linalg.norm(a)),float(np.linalg.norm(b))]
                else:
                    self.diagnostics[side+'_fallback']='calibration_inconsistent'
            if mode=='model' and self.arm_depth_mode=='front_projection' and camera_xyz is None:
                assist=self.depth_assist[side]
                if learn_lengths:
                    assist.lengths.update(np.linalg.norm(np.stack([a,b])[:,:2],axis=1),now)
                self.diagnostics[side+'_automatic_lengths']=assist.lengths.value.tolist()
                if not learn_lengths:
                    self.diagnostics[side]='projection_scale_unavailable'
                    self.projector[side].reset()
                    continue
                values=self.motion[side].update(np.stack([a,a+b])/.36,now)
                if values is None:
                    self.diagnostics[side]='observation_warmup'
                    continue
                observed_depth=values[:,2].copy()
                if side in self.previous:
                    values=filter_arm(self.previous[side],values,dt)
                # XY is smoothed for rendering. Depth evidence comes only from
                # confirmed model observations, not our previous reconstructed Z.
                values[:,2]=observed_depth
                filtered=np.stack([values[0],values[1]-values[0]])*.36
                fitted=self.projector[side].solve(filtered,assist.lengths.value,now)
                self.diagnostics[side+'_projection']=self.projector[side].details.copy()
                if fitted is None:
                    self.diagnostics[side]='projection_unavailable'
                    continue
                a,b=fitted
                mode='front_projection'
                packet[side+'WristInFront']=True
                self.diagnostics[side+'_depth_mode']=mode
            self.arm_modes[side]=mode
            self.diagnostics[side+'_mode']=mode
            if mode=='model':
                inward=visible_hand_inward(xy,scores,side)
                if not inward:
                    assist=self.depth_assist[side]
                    assist.front_count=0;assist.last_front=None;assist.front_active=False
                front=inward or visible_in_front_of_torso(xy,scores,side,nominal_width=.36/self.scale)
                self.diagnostics[side+'_inward_front']=inward
                self.diagnostics[side+'_front_overlap']=front
                bones,cue=self.depth_assist[side].update(a,b,now,front_visible=front,learn_lengths=learn_lengths)
                a,b=bones
                self.diagnostics[side+'_depth_mode']=cue
                self.diagnostics[side+'_automatic_lengths']=self.depth_assist[side].lengths.value.tolist()
                if not (.07<np.linalg.norm(a)<.65 and .07<np.linalg.norm(b)<.65):
                    self.diagnostics[side]='bone_length'
                    self.previous.pop(side,None)
                    continue
            values = np.stack([a,a+b])/.36
            if mode=='model' and not calibrated:
                values=self.motion[side].update(values,now)
                if values is None:
                    self.diagnostics[side]='observation_warmup'
                    continue
            if side in self.previous and mode=='model':
                values = filter_arm(self.previous[side],values,dt)
            # The temporal filter must not reintroduce a forbidden depth branch.
            if mode=='model' and (self.depth_assist[side].front_active or visible_hand_inward(xy,scores,side)):
                assist=self.depth_assist[side]
                bones=constrain_front_arm(np.stack([values[0],values[1]-values[0]])*.36,assist.upper_forward)/.36
                values=np.stack([bones[0],bones.sum(axis=0)])
                packet[side+'WristInFront']=True
                packet[side+'UpperInFront']=assist.upper_forward
                self.diagnostics[side+'_front_constraint']=True
            self.previous[side] = values
            self.diagnostics[side]='ok'
            packet[side+'ArmTracked'] = True
            if not visible_hand_inward(xy,scores,side):self.cross_motion[side].reset()
            crossing=self.cross_motion[side].update([cross_body_amount(xy,scores,side)],now)
            packet[side+'CrossBody']=0. if crossing is None else float(crossing[0])
            for label,value in zip(('Elbow','Wrist'),values):
                packet[side+label] = dict(zip(('x','y','z'),map(float,value)))
        packet['tracked'] = bool(packet['faceTracked'] or packet['torsoTracked'] or packet['leftArmTracked'] or packet['rightArmTracked'])
        add_hands(packet,xyz,scores,depth_scores)
        self.diagnostics['palm_observation']={side:bool(packet.get(side+'HandTracked')) for side in ('left','right')}
        self.palms.update(packet,now)
        self.fingers.update(packet,xyz,scores,depth_scores,now)
        self.diagnostics['fingers']={side:list(reasons) for side,reasons in self.fingers.diagnostics.items()}
        self.hold_brief_loss(packet,now)
        self.calibration.status='AUTO lengths (10 samples / 5s, never decrease)'
        return packet

    def automatic_lengths(self):
        return {side:assist.lengths.value.tolist() for side,assist in self.depth_assist.items()}

    def hold_brief_loss(self,packet,now):
        # Bounded last-observation hold, explicitly logged as held, never a new
        # detection. No-person returns above clear this cache immediately.
        for side in ('left','right'):
            for part,fields in [('Arm',('Elbow','Wrist','WristInFront','UpperInFront','CrossBody')),('Hand',('HandForward','HandNormal'))]:
                key=side+part
                packet[key+'Held']=False
                if packet.get(key+'Tracked'):
                    self.held[key]=(now,{side+field:packet[side+field].copy() if isinstance(packet[side+field],dict) else packet[side+field] for field in fields})
                elif key in self.held and now-self.held[key][0]<=.12 and (part=='Arm' or packet.get(side+'ArmTracked')):
                    packet.update(self.held[key][1])
                    packet[key+'Tracked']=True
                    packet[key+'Held']=True
                    self.diagnostics[key+'_state']='held'
        packet['tracked']=bool(packet['faceTracked'] or packet['torsoTracked'] or packet['leftArmTracked'] or packet['rightArmTracked'])
