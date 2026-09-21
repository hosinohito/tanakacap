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
        }
    }
}
