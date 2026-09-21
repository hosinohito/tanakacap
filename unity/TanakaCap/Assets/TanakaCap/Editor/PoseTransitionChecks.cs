using System;
using UnityEngine;
namespace TanakaCap.Editor
{
    public static class PoseTransitionChecks
    {
        static Quaternion[] Pose(float angle)=>new[]{Quaternion.Euler(0,0,angle)};
        static void Near(Quaternion q,float angle,string message)
        {if(Quaternion.Angle(q,Pose(angle)[0])>.05f)throw new Exception(message);}
        public static void Run()
        {
            var ease=new PoseTransition();var rest=Pose(0);
            Near(ease.Apply(Pose(90),rest,true,0,0)[0],90,"Initial tracking");
            Near(ease.Apply(Pose(0),rest,false,0,.49f)[0],90,"Hold for 0.5 seconds");
            Near(ease.Apply(Pose(0),rest,false,0,.5f)[0],90,"Rest starts continuously");
            Near(ease.Apply(Pose(0),rest,false,0,.75f)[0],90*(1-.15625f),"Smoothstep quarter");
            Near(ease.Apply(Pose(0),rest,false,0,1)[0],45,"Smoothstep midpoint");
            Near(ease.Apply(Pose(0),rest,false,0,1.5f)[0],0,"Rest completes in one second");
            Near(ease.Apply(Pose(90),rest,true,1.6f,1.6f)[0],0,"Recovery starts continuously");
            Near(ease.Apply(Pose(80),rest,true,1.85f,1.85f)[0],40,"Recovery follows moving target");
            Near(ease.Apply(Pose(80),rest,true,2.1f,2.1f)[0],80,"Recovery completes in half second");
            ease.Apply(Pose(80),rest,false,2.1f,2.6f);
            float before=Quaternion.Angle(rest[0],ease.Apply(Pose(80),rest,false,2.1f,2.9f)[0]);
            Near(ease.Apply(Pose(30),rest,true,2.91f,2.91f)[0],before,"Mid-rest recovery must not jump");
            Debug.Log("TANAKACAP_POSE_TRANSITION_CHECK_OK");
        }
    }
}
