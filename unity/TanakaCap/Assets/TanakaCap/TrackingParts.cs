using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace TanakaCap
{
    [Serializable] public sealed class TrackingUpdate
    {
        public int version;
        public string streamId;
        public double streamStarted, inputReadTime, inputSentTime, observationAge;
        public long packetSequence, frameId;
        public TrackingPart[] parts;
    }
    [Serializable] public sealed class TrackingPart
    {
        public string id, state;
        public long sampleSequence;
        public TrackingPacket values;
    }
    [Serializable] public sealed class PartStatus
    {
        public string id, state;
        public float intervalMs, ageMs;
        public long frameId;
    }

    // Wire updates and the composed render target have deliberately separate types.
    // Only these whitelisted fields can be changed by a part; no global tracking gate.
    public sealed class TrackingParts
    {
        sealed class Slot
        {
            public FieldInfo[] fields;
            public long sequence=-1, frame=-1;
            public string state="disabled";
            public float lastValidReceived, observed=float.NegativeInfinity, interval;
            public double sourceTime=-1;
        }
        readonly Dictionary<string,Slot> slots=new Dictionary<string,Slot>();
        readonly TrackingPacket target=new TrackingPacket();
        string stream;
        double streamStarted=-1;
        public bool Started => stream!=null;
        public bool Owns(TrackingPacket pose)=>ReferenceEquals(pose,target);
        public long Revision {get;private set;}
        public long FrameRevision {get;private set;}
        public long FrameId {get;private set;}=-1;
        public double InputReadTime {get;private set;}
        public double InputSentTime {get;private set;}
        public TrackingParts()
        {
            Add("head","headPitch headYaw headRoll");
            Add("face_distance","faceDistanceRatio");
            Add("mouth","mouth mouthWidth mouthRound mouthSmile mouthContourTracked mouthLeftCorner mouthRightCorner mouthBow mouthShift");
            Add("brows","browLeftInner browLeftOuter browRightInner browRightOuter");
            Add("eyelids","leftBlink rightBlink");
            Add("gaze","gazeYaw gazePitch");
            Add("torso","torsoPitch torsoYaw torsoRoll body3d");
            foreach(string side in new[]{"left","right"})
            {
                Add(side+"_arm",side+"Elbow "+side+"Wrist "+side+"CrossBody "+side+"WristInFront "+side+"UpperInFront");
                Add(side+"_palm",side+"HandForward "+side+"HandNormal");
                Add(side+"_fingers",side+"FingerTracked "+side+"FingerFlex");
            }
        }
        void Add(string id,string fields)
        {
            var names=fields.Split(' ');var found=new FieldInfo[names.Length];
            for(int i=0;i<names.Length;i++)found[i]=typeof(TrackingPacket).GetField(names[i])??throw new InvalidOperationException(names[i]);
            slots.Add(id,new Slot{fields=found});
        }
        static bool Finite(double x)=>!double.IsNaN(x)&&!double.IsInfinity(x);
        static bool ValidValue(object value)
        {
            if(value is float f)return Finite(f)&&Math.Abs(f)<=10000;
            if(value is Vector3 v)return ValidValue(v.x)&&ValidValue(v.y)&&ValidValue(v.z);
            if(value is float[] a){if(a.Length!=15)return false;foreach(float n in a)if(!Finite(n)||n<0||n>180)return false;}
            if(value is bool[] b)return b.Length==5;
            return value!=null;
        }
        public bool Accept(TrackingUpdate update,float now,double sourceClock=double.NaN)
        {
            if(update==null||update.version!=2||string.IsNullOrEmpty(update.streamId)||update.streamId.Length>64||
                !Finite(update.streamStarted)||update.streamStarted<0||!Finite(update.observationAge)||update.observationAge<0||
                !Finite(update.inputReadTime)||!Finite(update.inputSentTime)||update.inputReadTime<0||
                update.inputSentTime<update.inputReadTime||update.packetSequence<1||update.frameId<0||
                update.parts==null||update.parts.Length==0||update.parts.Length>13)return false;
            if(stream!=update.streamId)
            {
                // Both processes use the same host monotonic clock. A delayed old
                // stream can never reclaim ownership after a producer restart.
                if(update.streamStarted<=streamStarted)return false;
                stream=update.streamId;streamStarted=update.streamStarted;FrameId=-1;
                foreach(var slot in slots.Values){slot.sequence=-1;slot.frame=-1;slot.state="disabled";slot.observed=float.NegativeInfinity;slot.sourceTime=-1;slot.interval=0;}
            }
            bool changed=false;
            foreach(var part in update.parts)
            {
                if(part==null||part.id==null||!slots.TryGetValue(part.id,out var slot)||part.sampleSequence<=slot.sequence||update.frameId<slot.frame)continue;
                if(part.state!="valid"&&part.state!="lost"&&part.state!="held"&&part.state!="disabled"&&part.state!="error")continue;
                if(part.state=="valid")
                {
                    if(part.values==null)continue;
                    bool valid=true;foreach(var field in slot.fields)if(!ValidValue(field.GetValue(part.values))){valid=false;break;}
                    if(!valid)continue;
                    // The same source observation does not improve freshness or Hz.
                    if(update.frameId==slot.frame)continue;
                    foreach(var field in slot.fields)field.SetValue(target,field.GetValue(part.values));
                    if(slot.state=="valid"&&slot.sourceTime>=0&&now>slot.lastValidReceived)
                    {
                        float interval=(now-slot.lastValidReceived)*1000;
                        slot.interval=slot.interval==0?interval:Mathf.Lerp(slot.interval,interval,.25f);
                    }
                    else slot.interval=0;
                    slot.sourceTime=update.inputReadTime;slot.lastValidReceived=now;
                    double age=Finite(sourceClock)?Math.Max(update.observationAge,sourceClock-update.inputReadTime):update.observationAge;
                    slot.observed=now-(float)age;
                }
                slot.sequence=part.sampleSequence;slot.frame=update.frameId;slot.state=part.state;changed=true;
            }
            if(changed)
            {
                Revision++;
                if(update.frameId>FrameId)FrameRevision++;
                if(update.frameId>=FrameId){FrameId=update.frameId;InputReadTime=update.inputReadTime;InputSentTime=update.inputSentTime;}
            }
            return changed;
        }
        public bool Active(string id,float now)
        {
            var slot=slots[id];return slot.state=="valid"&&now-slot.observed<.3f;
        }
        public float LastObserved(string id)=>slots[id].observed;
        public TrackingPacket Snapshot(float now)
        {
            // Values persist; only independently fresh parts are applied by the driver.
            target.sequence=FrameId;target.inputReadTime=InputReadTime;target.inputSentTime=InputSentTime;
            target.headTracked=Active("head",now);target.faceTracked=target.headTracked||Active("mouth",now)||Active("eyelids",now)||Active("brows",now);
            target.faceDistanceTracked=Active("face_distance",now);target.gazeTracked=Active("gaze",now);target.browTracked=Active("brows",now);
            target.torsoTracked=Active("torso",now);
            target.leftArmTracked=Active("left_arm",now);target.rightArmTracked=Active("right_arm",now);
            target.leftHandTracked=Active("left_palm",now);target.rightHandTracked=Active("right_palm",now);
            target.tracked=false;foreach(string id in slots.Keys)target.tracked|=Active(id,now);
            return target;
        }
        public PartStatus[] Status(float now)
        {
            var result=new List<PartStatus>();
            foreach(var pair in slots)
            {
                var slot=pair.Value;
                result.Add(new PartStatus{id=pair.Key,state=slot.state=="valid"&&!Active(pair.Key,now)?"stale":slot.state,
                    intervalMs=slot.interval,ageMs=float.IsNegativeInfinity(slot.observed)?-1:(now-slot.observed)*1000,frameId=slot.frame});
            }
            return result.ToArray();
        }
    }
}
