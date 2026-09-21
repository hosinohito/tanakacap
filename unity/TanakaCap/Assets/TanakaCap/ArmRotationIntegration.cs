using System;
using UnityEngine;

namespace TanakaCap
{
    public partial class AvatarDriver
    {
        bool legacyArmRotation;
        float armTwistLimit=ForearmTwistLimit;

        void ConfigureArmRotation(string[] args)
        {
            int index=Array.IndexOf(args,"--diagnostic-arm-rotation");
            if(index>=0)
            {
                if(Array.IndexOf(args,"--render-replay")<0 || index+1>=args.Length)
                    throw new ArgumentException("Arm rotation comparison requires offline replay");
                string mode=args[index+1];
                if(mode!="legacy" && mode!="hinge" && mode!="hinge-unlimited" && mode!="hinge-90")
                    throw new ArgumentException("Unknown arm rotation comparison");
                legacyArmRotation=mode=="legacy";
                if(mode=="hinge-unlimited")armTwistLimit=float.PositiveInfinity;
                if(mode=="hinge-90")armTwistLimit=90;
            }
            Debug.Log("TANAKACAP_ARM_ROTATION "+(legacyArmRotation?"legacy":"hinge")+" limit="+armTwistLimit);
        }

        float ResolveArmTwist(float displayed,float raw)
        {
            return Mathf.Clamp(UnwrapTwist(displayed,displayed,raw),-armTwistLimit,armTwistLimit);
        }

        void ApplyLegacyArmFrame(Arm arm,Vector3 upperDirection,Vector3 lowerDirection,float t)
        {
            Quaternion upperBase=transform.rotation*arm.upperRootRest,lowerBase=transform.rotation*arm.lowerRootRest;
            var upperTarget=Quaternion.FromToRotation(upperBase*arm.upperDirection,transform.TransformDirection(upperDirection))*upperBase;
            var lowerTarget=Quaternion.FromToRotation(lowerBase*arm.lowerDirection,transform.TransformDirection(lowerDirection))*lowerBase;
            arm.upper.rotation=Quaternion.Slerp(arm.upper.rotation,upperTarget,t);
            arm.lowerUntwisted=Quaternion.Slerp(arm.lowerUntwisted,lowerTarget,t);
            arm.lower.rotation=Quaternion.AngleAxis(arm.twist,arm.lowerUntwisted*arm.lowerDirection)*arm.lowerUntwisted;
        }

        void ApplyArmFrame(Arm arm,Vector3 upperDirection,Vector3 lowerDirection,float t,bool snap=false,bool updateReference=true)
        {
            var u=transform.InverseTransformDirection(arm.lower.position-arm.upper.position).normalized;
            var l=transform.InverseTransformDirection(arm.hand.position-arm.lower.position).normalized;
            if(snap){u=upperDirection;l=lowerDirection;}
            else {u=Vector3.Slerp(u,upperDirection,t).normalized;l=Vector3.Slerp(l,lowerDirection,t).normalized;}
            arm.rotationFrame.Solve(u,l,updateReference?FrameDelta:0,out var upper,out var lower);
            arm.upper.rotation=transform.rotation*upper;
            arm.lowerUntwisted=transform.rotation*lower;
            arm.lower.rotation=Quaternion.AngleAxis(arm.twist,arm.lowerUntwisted*arm.lowerDirection)*arm.lowerUntwisted;
        }
    }
}
