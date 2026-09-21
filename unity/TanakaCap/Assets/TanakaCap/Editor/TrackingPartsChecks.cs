using System;
using UnityEngine;
namespace TanakaCap.Editor
{
    public static class TrackingPartsChecks
    {
        static void Check(bool result,string description){if(!result)throw new Exception("Partial tracking: "+description);}
        static TrackingUpdate Update(long frame,string id,string state="valid",float yaw=0,string stream="first",double started=1)
        {
            return new TrackingUpdate{version=2,streamId=stream,streamStarted=started,packetSequence=frame+1,frameId=frame,
                inputReadTime=frame*.03,inputSentTime=frame*.03,
                parts=new[]{new TrackingPart{id=id,state=state,sampleSequence=frame+1,values=new TrackingPacket{headYaw=yaw}}}};
        }
        public static void Run()
        {
            var store=new TrackingParts();
            Check(store.Accept(Update(1,"head",yaw:20),1),"first head");
            Check(store.Accept(Update(2,"left_arm"),1.03f),"independent arm");
            Check(store.Snapshot(1.03f).headYaw==20&&store.Active("head",1.03f),"omitted head survives");
            Check(store.Accept(Update(3,"head",yaw:0),1.06f)&&store.Snapshot(1.06f).headYaw==0,"valid zero");
            Check(!store.Accept(Update(2,"head",yaw:40),1.07f),"reordered head");
            Check(!store.Accept(Update(3,"head",yaw:50),1.08f),"duplicate head");
            Check(store.Accept(Update(2,"gaze"),1.09f),"late different part accepted");
            Check(store.Snapshot(1.09f).sequence==3,"frame does not rewind");
            Check(store.Accept(Update(4,"left_arm","held"),1.1f),"held state");
            Check(!store.Active("left_arm",1.1f)&&store.Active("head",1.1f),"held arm does not block head");
            var held=Array.Find(store.Status(1.2f),p=>p.id=="left_arm");
            Check(Math.Abs(held.ageMs-170)<1,"held does not refresh observation");
            Check(store.Accept(Update(5,"head","lost"),1.2f)&&!store.Active("head",1.2f),"explicit loss");
            Check(store.Accept(Update(6,"left_palm"),1.21f)&&store.Snapshot(1.21f).leftHandTracked,"palm independent from arm");
            Check(!store.Active("left_palm",1.6f),"per-part timeout");
            var delayed=Update(7,"head");delayed.observationAge=.4;
            Check(store.Accept(delayed,1.6f)&&!store.Active("head",1.6f),"delayed observation stale on arrival");
            var mixed=Update(8,"head");mixed.parts[0].values.headYaw=float.NaN;
            mixed.parts=new[]{mixed.parts[0],new TrackingPart{id="mouth",sampleSequence=9,state="valid",values=new TrackingPacket{mouth=.8f}}};
            Check(store.Accept(mixed,1.7f)&&store.Active("mouth",1.7f)&&!store.Active("head",1.7f),"bad part isolated");
            Check(!store.Accept(Update(9,"left_fingers"),1.8f),"missing finger masks rejected");
            var fingers=Update(9,"left_fingers");fingers.parts[0].values.leftFingerTracked=new[]{true,false,false,false,false};fingers.parts[0].values.leftFingerFlex=new float[15];
            Check(store.Accept(fingers,1.8f)&&store.Snapshot(1.8f).leftFingerTracked[0],"finger mask accepted");
            Check(store.Accept(Update(0,"head",stream:"second",started:2),2),"producer restart");
            Check(!store.Active("mouth",2),"old targets disabled on restart");
            Check(!store.Accept(Update(99,"head"),2.1f),"old stream cannot return");
            var legacy=Update(1,"head");legacy.version=1;
            Check(!store.Accept(legacy,2.2f),"no old wire protocol");
            Console.WriteLine("TANAKACAP_PARTIAL_TRACKING_CHECKS_OK");
        }
    }
}
