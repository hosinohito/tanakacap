"""Conservative 2D diagnostic retargeting, not a solved 3D body/face model."""
import json
import socket

import numpy as np
from .mouth_detail import contour_controls


def clamp(value, low=0., high=1.):
    return float(np.clip(value, low, high))


def packet_from_landmarks(points, scores, sequence, threshold=.3):
    p = np.asarray(points, dtype=float)
    s = np.asarray(scores, dtype=float)
    if p.shape != (133, 2) or s.shape != (133,):
        raise ValueError('Expected COCO WholeBody 133 landmarks')

    def visible(indices):
        return bool(np.isfinite(p[indices]).all() and (s[indices] >= threshold).all())

    result = dict(version=1, sequence=int(sequence), tracked=False, faceTracked=False,
                  leftArmTracked=False, rightArmTracked=False, headPitch=0., headYaw=0.,
                  headRoll=0., mouth=0., mouthWidth=0.,mouthRound=0.,mouthSmile=0.,leftBlink=0., rightBlink=0., torsoRoll=0.)
    # COCO whole-body face indices 23:91 use the 68-point face layout.
    face = p[23:91]
    needed = [30, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 54, 62, 66]
    if visible([23+i for i in needed]):
        right_eye = face[36:42].mean(axis=0)
        left_eye = face[42:48].mean(axis=0)
        axis = left_eye-right_eye
        distance = float(np.linalg.norm(axis))
        if distance >= 15:
            horizontal = axis/distance
            vertical = np.array([-horizontal[1], horizontal[0]])
            center = (right_eye+left_eye)/2
            nose = face[30]-center

            def blink(start):
                q = face[start:start+6]
                width = np.linalg.norm(q[0]-q[3])
                ratio = (np.linalg.norm(q[1]-q[5])+np.linalg.norm(q[2]-q[4])) / max(2*width, 1)
                return clamp((.27-ratio)/.16)

            mouth_width = np.linalg.norm(face[48]-face[54])
            opening = np.linalg.norm(face[62]-face[66])/max(mouth_width, 1)
            result.update(faceTracked=True, headRoll=clamp(np.degrees(np.arctan2(axis[1],axis[0])), -35,35),
                          headYaw=clamp(-np.dot(nose,horizontal)/distance*100,-60,60),
                          headPitch=clamp((np.dot(nose,vertical)/distance-.55)*70,-35,35),
                          mouth=clamp(3.5*(opening-.035)/.45),mouthWidth=clamp(3.5*(mouth_width/distance-.8)/.35,-1,1),
                          mouthRound=clamp((.8-mouth_width/distance)/.22),
                          mouthSmile=clamp((np.dot(face[51]-(face[48]+face[54])/2,vertical)/distance-.01)/.08) if visible([23+51]) else 0.,
                          leftBlink=blink(42),rightBlink=blink(36))
    if visible([5, 6]):
        shoulder_width = float(np.linalg.norm(p[5]-p[6]))
        if shoulder_width >= 25:
            result['torsoRoll'] = clamp(-np.degrees(np.arctan2(p[5,1]-p[6,1],abs(p[5,0]-p[6,0]))),-20,20)
            for side, indices in [('left', [5,7,9]), ('right', [6,8,10])]:
                if not visible(indices):
                    continue
                shoulder, elbow, wrist = p[indices]
                a, b = (elbow-shoulder)/shoulder_width, (wrist-shoulder)/shoulder_width
                # Reject implausible discontinuities. No fabricated depth estimate.
                if not (.08 < np.linalg.norm(a) < 1.3 and .08 < np.linalg.norm(b-a) < 1.3):
                    continue
                result[side+'ArmTracked'] = True
                result[side+'Elbow'] = dict(x=float(-a[0]),y=float(-a[1]),z=0.)
                result[side+'Wrist'] = dict(x=float(-b[0]),y=float(-b[1]),z=0.)
    detail=contour_controls(p,s)
    result.update(mouthContourTracked=detail is not None,mouthLeftCorner=0.,mouthRightCorner=0.,mouthBow=0.)
    if detail is not None:result.update(detail)
    from .brows import observe
    observe(p,s,result)
    result['tracked'] = result['faceTracked'] or result['leftArmTracked'] or result['rightArmTracked']
    return result


class FaceFilter:
    """Two-observation motion confirmation shared by head, eyes and mouth."""
    def __init__(self, block_size=1, stride=None, brow_gain=2.):
        from .motion_gate import DirectionGate
        self.head=DirectionGate(.25,float('inf'),block_size,stride)
        self.expression=DirectionGate(.015,float('inf'),block_size,stride)
        self.contour=DirectionGate(.015,float('inf'),block_size,stride)
        from .brows import BrowFilter
        self.brows=BrowFilter(block_size,stride,brow_gain)
        self.corner_samples=[]
        self.corner_neutral=None
        self.bow_samples=[]
        self.bow_neutral=None
        self.shift_samples=[]
        self.shift_neutral=None

    def update(self,packet,now):
        self.brows.update(packet,now)
        packet.setdefault('mouthWidth',0.)
        packet.setdefault('mouthRound',0.)
        packet.setdefault('mouthSmile',0.)
        packet.setdefault('mouthShift',0.)
        if not packet.get('faceTracked'):
            self.head.reset(); self.expression.reset();self.contour.reset()
            return packet
        for flag,gate,keys in [('mouthContourTracked',self.contour,('mouthLeftCorner','mouthRightCorner','mouthBow','mouthShift'))]:
            if packet.get(flag):
                if self.corner_neutral is None and packet.get('mouth',1)<.3:
                    self.corner_samples.append([packet['mouthLeftCorner'],packet['mouthRightCorner']])
                    self.corner_samples=self.corner_samples[-10:]
                    self.bow_samples.append(packet['mouthBow'])
                    self.bow_samples=self.bow_samples[-10:]
                    self.shift_samples=(self.shift_samples+[packet['mouthShift']])[-10:]
                    if len(self.corner_samples)==10 and np.max(np.ptp(self.corner_samples,axis=0))<.4:
                        self.corner_neutral=np.median(self.corner_samples,axis=0)
                        self.bow_neutral=float(np.median(self.bow_samples))
                        self.shift_neutral=float(np.median(self.shift_samples))
                        gate.reset()
                if self.corner_neutral is not None:
                    for k,neutral in zip(keys[:2],self.corner_neutral):
                        packet[k]=float(np.clip((packet[k]-neutral)*3.,-1,1))
                else:
                    packet['mouthLeftCorner']=packet['mouthRightCorner']=0.
                # The natural Cupid's bow is anatomy, not an expression. Do
                # not continuously drive the avatar's smiling omega shape.
                packet['mouthBow']=0. if self.bow_neutral is None else float(np.clip(packet['mouthBow']-self.bow_neutral,0,1))
                packet['mouthShift']=0. if self.shift_neutral is None else float(np.clip((packet['mouthShift']-self.shift_neutral)*1.5,-1,1))
                values=gate.update([packet[k] for k in keys],now)
                if values is None:packet[flag]=False
                else:packet.update(zip(keys,map(float,values)))
            else:gate.reset()
        for gate,keys in [(self.head,('headPitch','headYaw','headRoll')),
                          (self.expression,('mouth','leftBlink','rightBlink','mouthWidth','mouthRound','mouthSmile'))]:
            values=gate.update([packet[k] for k in keys],now)
            if values is None:
                packet['faceTracked']=False
                continue
            packet.update(zip(keys,map(float,values)))
        return packet


class LocalSender:
    def __init__(self, port):
        if not 1024 <= port <= 65535:
            raise ValueError('Local UDP port must be 1024..65535')
        self.target = ('127.0.0.1',port)
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    def send(self, packet):
        self.socket.sendto(json.dumps(packet,allow_nan=False,separators=(',',':')).encode('utf-8'),self.target)

    def close(self):
        self.socket.close()
