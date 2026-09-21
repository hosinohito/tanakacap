using System;
using UnityEngine;
namespace TanakaCap.Editor
{
    public static class FingerFollowChecks
    {
        static float Follow(float value,float target,float dt) =>
            Mathf.Lerp(value,target,AvatarDriver.FingerFollowAmount(target-value,dt));
        public static void Run()
        {
            float old=0,current=0,oldPower=0,newPower=0;
            for(int i=0;i<600;i++)
            {
                float target=(i/2%2==0?1:-1)*2f;
                current=Follow(current,target,1f/60);
                old=Mathf.Lerp(old,target,1-Mathf.Exp(-1));
                if(i>60){oldPower+=old*old;newPower+=current*current;}
            }
            if(newPower>=oldPower*.25f)throw new Exception("Finger jitter attenuation");
            foreach(int fps in new[]{30,60,120})
            {
                current=0;
                for(int i=0;i<fps/5;i++)current=Follow(current,60,1f/fps);
                if(current<57 || current>60)throw new Exception("Large finger bend response");
                current=0;
                for(int i=0;i<fps;i++)current=Follow(current,2,1f/fps);
                if(current<1.99f || current>2)throw new Exception("Small deliberate bend must converge");
            }
            if(AvatarDriver.FingerFollowAmount(60,0)!=0)throw new Exception("Zero delta");
            Debug.Log("TANAKACAP_FINGER_FOLLOW_CHECK_OK jitterPowerRatio="+newPower/oldPower);
        }
    }
}
