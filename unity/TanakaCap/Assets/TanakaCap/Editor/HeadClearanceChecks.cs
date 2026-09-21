using System;
using UnityEngine;
namespace TanakaCap.Editor
{
    public static class HeadClearanceChecks
    {
        public static void Run()
        {
            var axes=new Vector3(.09f,.13f,.11f);
            foreach(var point in new[]{Vector3.zero,new Vector3(.08f,0,0),new Vector3(-.08f,0,0),
                new Vector3(0,0,-.1f),new Vector3(0,.12f,0),new Vector3(.04f,.02f,-.05f),new Vector3(0,.02f,.04f)})
            {
                var nearest=HeadClearance.Project(point,axes,0);
                if(Mathf.Abs(HeadClearance.Level(nearest,axes)-1)>.0001f)throw new Exception("Head proxy boundary");
                // Compare with dense independent surface samples; exact solution
                // must be at least as close, including interior singular cases.
                float distance=(nearest-point).sqrMagnitude;
                for(int y=0;y<=90;y++)for(int x=0;x<180;x++)
                {
                    float latitude=y*Mathf.PI/90,longitude=x*Mathf.PI/90;
                    var sample=Vector3.Scale(axes,new Vector3(Mathf.Sin(latitude)*Mathf.Cos(longitude),
                        Mathf.Cos(latitude),Mathf.Sin(latitude)*Mathf.Sin(longitude)));
                    if(distance>(sample-point).sqrMagnitude+1e-7f)throw new Exception("Not nearest head surface");
                }
                var clear=HeadClearance.Project(point,axes);
                if(HeadClearance.Level(clear,axes)<1 || HeadClearance.Project(clear,axes)!=clear)
                    throw new Exception("Head clearance drift");
            }
            if(HeadClearance.Project(new Vector3(0,0,-.1f),axes).z>=0)throw new Exception("Back pushed forward");
            if(HeadClearance.Project(new Vector3(.08f,0,0),axes).x<.09f)throw new Exception("Side contact");
            Debug.Log("TANAKACAP_HEAD_CLEARANCE_CHECK_OK nearest/side/back/top/center");
            foreach(float sign in new[]{-1f,1f})
            {
                var points=new[]{new Vector3(sign*.08f,0,0),new Vector3(sign*.075f,.025f,0),new Vector3(sign*.10f,-.02f,.01f)};
                var shift=HeadClearance.HandTranslation(points,axes,.004f);
                if(shift.x*sign<=0 || shift.magnitude>.04f)throw new Exception("Hand contact direction/distance");
                foreach(var p in points)if(HeadClearance.Level(p+shift,axes+Vector3.one*.004f)<.9999f)
                    throw new Exception("Hand contact left a sample inside");
                if(HeadClearance.HandTranslation(Array.ConvertAll(points,p=>p+shift),axes,.004f).sqrMagnitude>1e-10f)
                    throw new Exception("Hand contact drift");
            }
            var root=new GameObject("ContactCheck");
            try
            {
                var upper=new GameObject("upper").transform;upper.SetParent(root.transform);
                var lower=new GameObject("lower").transform;lower.SetParent(upper);lower.localPosition=new Vector3(.1f,-.2f,0);
                var hand=new GameObject("hand").transform;hand.SetParent(lower);hand.localPosition=new Vector3(0,.05f,.2f);
                var finger=new GameObject("finger").transform;finger.SetParent(hand);finger.localPosition=new Vector3(.02f,0,.05f);
                finger.localRotation=Quaternion.Euler(20,10,0);
                var worldRotation=hand.rotation;var localRotation=finger.localRotation;var localPosition=finger.localPosition;
                float a=Vector3.Distance(upper.position,lower.position),b=Vector3.Distance(lower.position,hand.position);
                var target=hand.position+new Vector3(.015f,.01f,0);
                HeadClearance.MoveHand(upper,lower,hand,target-hand.position);
                if(Vector3.Distance(target,hand.position)>.0001f || Quaternion.Angle(hand.rotation,worldRotation)>.01f ||
                   Quaternion.Angle(finger.localRotation,localRotation)>.01f || finger.localPosition!=localPosition ||
                   Mathf.Abs(Vector3.Distance(upper.position,lower.position)-a)>.00001f ||
                   Mathf.Abs(Vector3.Distance(lower.position,hand.position)-b)>.00001f)
                    throw new Exception("Hand contact changed grasp/orientation/length or missed reachable target");
                HeadClearance.MoveHand(upper,lower,hand,Vector3.one*10);
                if(Mathf.Abs(Vector3.Distance(lower.position,hand.position)-b)>.00001f)
                    throw new Exception("Unreachable contact stretched arm");
            }
            finally {UnityEngine.Object.DestroyImmediate(root);}
            Debug.Log("TANAKACAP_HAND_CONTACT_CHECK_OK rigid/nearest/side/reach/length/grasp");
        }
    }
}
