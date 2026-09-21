using System;
using System.Collections.Generic;
using UnityEngine;

namespace TanakaCap
{
    public partial class AvatarDriver
    {
        bool wristHeadOnly;
        int handHeadCorrections;
        float maximumHandHeadShift,maximumHandHeadResidual;
        readonly List<Vector3> handContactPoints=new List<Vector3>(100);

        void ConfigureHandContact(string[] args)
        {
            wristHeadOnly=Array.IndexOf(args,"--diagnostic-wrist-head-only")>=0;
            if(wristHeadOnly && Array.IndexOf(args,"--render-replay")<0)
                throw new ArgumentException("Wrist-only comparison requires offline replay");
        }

        void CollectHandContacts(Arm arm,Quaternion inverseFrame,Vector3 center)
        {
            handContactPoints.Clear();
            Action<Vector3> add=p=>handContactPoints.Add(inverseFrame*(p-center));
            add(arm.hand.position);
            if(arm.fingers==null)return;
            // Sample phalanges and wrist-to-knuckle spans so a segment cannot
            // cross the head just because its endpoints are outside.
            foreach(var finger in arm.fingers)
            {
                for(int j=0;j<3;j++)
                {
                    var bone=finger.bones[j];if(!bone)continue;
                    Vector3 end;
                    if(j<2 && finger.bones[j+1])end=finger.bones[j+1].position;
                    else if(j==2)end=bone.TransformPoint(finger.tipLocal);
                    else end=bone.position;
                    SampleContactSegment(bone.position,end,add);
                }
                if(finger.bones[0])SampleContactSegment(arm.hand.position,finger.bones[0].position,add);
            }
            // Palm cross-section (index through little knuckles).
            for(int f=1;f<4;f++)
                if(arm.fingers[f].bones[0] && arm.fingers[f+1].bones[0])
                    SampleContactSegment(arm.fingers[f].bones[0].position,arm.fingers[f+1].bones[0].position,add);
        }

        static void SampleContactSegment(Vector3 start,Vector3 end,Action<Vector3> add)
        {
            int count=Mathf.Clamp(Mathf.CeilToInt(Vector3.Distance(start,end)/.008f),1,32);
            for(int i=0;i<=count;i++)add(Vector3.Lerp(start,end,i/(float)count));
        }

        void ClearHandFromHead(Arm arm)
        {
            if(wristHeadOnly || !ArmCorrection("head"))return;
            var frame=head.rotation*Quaternion.Inverse(headRootRest);
            var inverse=Quaternion.Inverse(frame);var center=head.TransformPoint(headClearance.centerLocal);
            float thickness=Mathf.Clamp(arm.lowerLength*.02f,.002f,.008f);
            var start=arm.hand.position;
            // Recheck after IK: its reach and bend limits may prevent the exact
            // rigid displacement. Never stretch bones or reposition fingers.
            for(int iteration=0;iteration<3;iteration++)
            {
                CollectHandContacts(arm,inverse,center);
                var shift=HeadClearance.HandTranslation(handContactPoints,headClearance.radii,thickness);
                if(shift.sqrMagnitude<1e-10f)break;
                var previous=arm.hand.position;
                HeadClearance.MoveHand(arm.upper,arm.lower,arm.hand,frame*shift);
                if((arm.hand.position-previous).sqrMagnitude<1e-10f)break;
            }
            float moved=Vector3.Distance(start,arm.hand.position);
            if(moved>.00001f)
            {
                handHeadCorrections++;
                maximumHandHeadShift=Mathf.Max(maximumHandHeadShift,moved);
                var axis=(arm.hand.position-arm.lower.position).normalized;
                arm.lowerUntwisted=Quaternion.AngleAxis(-arm.twist,axis)*arm.lower.rotation;
            }
            CollectHandContacts(arm,inverse,center);
            var remainder=HeadClearance.HandTranslation(handContactPoints,headClearance.radii,thickness);
            maximumHandHeadResidual=Mathf.Max(maximumHandHeadResidual,remainder.magnitude);
        }

        static float ElbowAxialTwist(Arm arm)
        {
            var q=Quaternion.Inverse(arm.lowerRest)*arm.lower.localRotation;
            float along=Vector3.Dot(new Vector3(q.x,q.y,q.z),arm.lowerDirection);
            if(along*along+q.w*q.w<1e-10f)return 0;
            return Mathf.DeltaAngle(0,2*Mathf.Atan2(along,q.w)*Mathf.Rad2Deg);
        }
    }
}
