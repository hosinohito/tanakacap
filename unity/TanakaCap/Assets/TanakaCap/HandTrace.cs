using System;
using System.IO;
using UnityEngine;

namespace TanakaCap
{
    public partial class AvatarDriver
    {
        StreamWriter handTrace;
        [Serializable] sealed class HandTraceRow
        {
            public int renderFrame;
            public float time, dt;
            public double inputReadTime;
            public bool live;
            public TrackingPacket target;
            public PartStatus[] parts;
            public Vector3 leftNormal,rightNormal,leftForward,rightForward;
            public float leftTwist,rightTwist,leftRequestedTwist,rightRequestedTwist;
            public float[] leftFingers,rightFingers;
        }
        void InitializeHandTrace(string[] args)
        {
            int index=Array.IndexOf(args,"--hand-trace");
            if(index<0)return;
            if(index+1>=args.Length)throw new ArgumentException("Missing --hand-trace path");
            string path=Path.GetFullPath(args[index+1]);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            handTrace=new StreamWriter(new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read));
        }
        void TraceHands(bool live)
        {
            if(handTrace==null)return;
            var lf=Quaternion.Inverse(transform.rotation)*left.hand.rotation*Quaternion.Inverse(left.handFrameCorrection);
            var rf=Quaternion.Inverse(transform.rotation)*right.hand.rotation*Quaternion.Inverse(right.handFrameCorrection);
            handTrace.WriteLine(JsonUtility.ToJson(new HandTraceRow {
                renderFrame=Time.frameCount,time=Time.unscaledTime,dt=FrameDelta,
                inputReadTime=InputReadTime,live=live,target=current,parts=parts.Status(Time.unscaledTime),
                leftNormal=lf*Vector3.up,rightNormal=rf*Vector3.up,
                leftForward=lf*Vector3.forward,rightForward=rf*Vector3.forward,
                leftTwist=left.twist,rightTwist=right.twist,
                leftRequestedTwist=left.requestedTwist,rightRequestedTwist=right.requestedTwist,
                leftFingers=FingerAngles(left),rightFingers=FingerAngles(right)}));
            if(Time.frameCount%60==0)handTrace.Flush();
        }
    }
}
