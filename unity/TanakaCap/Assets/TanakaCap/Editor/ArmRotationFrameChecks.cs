using System;
using UnityEngine;

namespace TanakaCap.Editor
{
    public static class ArmRotationFrameChecks
    {
        public static void Run()
        {
            foreach(float sign in new[]{-1f,1f})
            {
                var axis=Vector3.right*sign;var hinge=Vector3.forward*sign;
                var solver=new ArmRotationFrame(axis,axis,hinge,hinge,Quaternion.identity,"test");
                var root=Quaternion.Euler(20,30,10);
                var u=root*axis;var l=root*(Quaternion.AngleAxis(80,hinge)*axis);
                Quaternion upper=Quaternion.identity,lower=Quaternion.identity;
                for(int i=0;i<120;i++)solver.Solve(u,l,1f/60,out upper,out lower);
                if(Vector3.Angle(upper*axis,u)>.03f || Vector3.Angle(lower*axis,l)>.03f)
                    throw new Exception("Coupled arm missed solved directions");
                if(Quaternion.Angle(Quaternion.Inverse(upper)*lower,Quaternion.AngleAxis(80,hinge))>.03f)
                    throw new Exception("Elbow accumulated non-hinge rotation");
                var previous=upper;
                for(int i=0;i<120;i++)
                {
                    // Alternating tiny flexion across extension must not flip roll.
                    l=Quaternion.AngleAxis(i%2==0?.1f:-.1f,root*hinge)*u;
                    solver.Solve(u,l,1f/60,out upper,out lower);
                    if(Quaternion.Angle(previous,upper)>.1f)throw new Exception("Extended arm roll flipped");
                    if(Vector3.Angle(lower*axis,l)>.03f)throw new Exception("Straight arm endpoint changed");
                    previous=upper;
                }
                l=Quaternion.AngleAxis(-80,root*hinge)*u;
                solver.Solve(u,l,1f/60,out upper,out lower);
                if(Quaternion.Angle(previous,upper)>9.1f)throw new Exception("Bend plane switched abruptly");
                if(Vector3.Angle(lower*axis,l)>.03f)throw new Exception("Transported elbow moved endpoint");
            }
            var scalar=new ScalarPoseTransition();
            scalar.Apply(160,0,true,0,0);
            scalar.Apply(160,0,false,0,.1f);
            float before=scalar.Apply(-160,0,true,.2f,.2f);
            if(before!=160)throw new Exception("Twist recovery jumped");
            for(int i=1;i<=30;i++)
            {
                float value=scalar.Apply(-160,0,true,.2f+i/60f,.2f+i/60f);
                if(value>before+.001f || Mathf.Abs(value)>160.001f)throw new Exception("Twist recovery crossed excluded interval");
                before=value;
            }
            if(Mathf.Abs(before+160)>.01f)throw new Exception("Twist recovery incomplete");
            if(AvatarDriver.SelectForearmTwist(160,-170)!=160 || AvatarDriver.SelectForearmTwist(-160,170)!=-160)
                throw new Exception("Twist wrap took opposite limit");
            Debug.Log("TANAKACAP_ARM_FRAME_CHECK_OK mirrored/hinge/extension/continuous/directions/twist_transition");
        }
    }
}
