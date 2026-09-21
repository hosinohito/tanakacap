using UnityEngine;

namespace TanakaCap
{
    // Fixed transition origins avoid exponential easing. Targets can keep moving
    // during recovery; interrupted transitions start from the displayed pose.
    public sealed class PoseTransition
    {
        enum Phase { Tracking, Waiting, Resting, Recovering }
        Phase phase=Phase.Tracking;
        Quaternion[] displayed, origin;
        float started, initialized;
        public bool Moving {get;private set;}
        public Quaternion[] Apply(Quaternion[] target,Quaternion[] rest,bool valid,float lastObserved,float now)
        {
            if(displayed==null){displayed=(Quaternion[])target.Clone();initialized=now;}
            float age=now-(float.IsNegativeInfinity(lastObserved)?initialized:lastObserved);
            if(valid)
            {
                if(phase==Phase.Resting || phase==Phase.Waiting)
                {phase=Phase.Recovering;started=now;origin=(Quaternion[])displayed.Clone();}
            }
            else
            {
                if(phase==Phase.Tracking || phase==Phase.Recovering)phase=Phase.Waiting;
                if(phase==Phase.Waiting && age>=.5f)
                {phase=Phase.Resting;started=now;origin=(Quaternion[])displayed.Clone();}
            }
            Moving=false;
            if(phase==Phase.Tracking)displayed=(Quaternion[])target.Clone();
            else if(phase==Phase.Resting || phase==Phase.Recovering)
            {
                float duration=phase==Phase.Resting?1f:.5f;
                float t=Mathf.Clamp01((now-started)/duration);
                float weight=t*t*(3-2*t);
                var destination=phase==Phase.Resting?rest:target;
                for(int i=0;i<displayed.Length;i++)displayed[i]=Quaternion.Slerp(origin[i],destination[i],weight);
                Moving=t<1;
                if(t>=1 && phase==Phase.Recovering)phase=Phase.Tracking;
            }
            return displayed;
        }
    }
}
