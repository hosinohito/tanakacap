using UnityEngine;

namespace TanakaCap
{
    // Joint angle transitions must stay inside their allowed interval; quaternion
    // slerp could cross the excluded +/-180 boundary between opposite limits.
    public sealed class ScalarPoseTransition
    {
        enum Phase { Tracking,Waiting,Resting,Recovering }
        Phase phase;
        bool initialized;
        float displayed,origin,started,first;
        public float Apply(float target,float rest,bool valid,float lastObserved,float now)
        {
            if(!initialized){initialized=true;displayed=target;first=now;}
            float age=now-(float.IsNegativeInfinity(lastObserved)?first:lastObserved);
            if(valid)
            {
                if(phase==Phase.Resting || phase==Phase.Waiting)
                {phase=Phase.Recovering;started=now;origin=displayed;}
            }
            else
            {
                if(phase==Phase.Tracking || phase==Phase.Recovering)phase=Phase.Waiting;
                if(phase==Phase.Waiting && age>=.5f){phase=Phase.Resting;started=now;origin=displayed;}
            }
            if(phase==Phase.Tracking)displayed=target;
            else if(phase==Phase.Resting || phase==Phase.Recovering)
            {
                float t=Mathf.Clamp01((now-started)/(phase==Phase.Resting?1f:.5f));
                displayed=Mathf.Lerp(origin,phase==Phase.Resting?rest:target,t*t*(3-2*t));
                if(t>=1 && phase==Phase.Recovering)phase=Phase.Tracking;
            }
            return displayed;
        }
    }
}
