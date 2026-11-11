using System;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class SecondaryStabilityChecks {
  static void Require(bool value,string message){if(!value)throw new Exception(message);}
  public static void Run(){
   foreach(float length in new[]{.001f,.01f,.1f})foreach(int fps in new[]{30,60,120}){
    var root=new GameObject("SecondaryStabilityFixture");
    try {
     var anchor=new GameObject("anchor").transform;anchor.SetParent(root.transform);
     var bone=new GameObject("bone").transform;bone.SetParent(anchor);
     var motion=root.AddComponent<SecondaryMotion>();motion.externalClock=true;
     var chain=new SecondaryChain{root="anchor/bone",pull=.2f,spring=.2f,gravity=.1f,limitType=1,maxAngleX=30};
     motion.Initialize(new SecondaryPhysicsData{chains=new[]{chain},colliders=new SecondaryCollider[0],bones=new[]{new SecondaryBone{path="anchor/bone",tail=Vector3.down*length}}},null);
     var previous=bone.localRotation;float largest=0;
     for(int i=0;i<fps*6;i++){
      float time=i/(float)fps;motion.Restore();
      anchor.localPosition=i<fps*2?new Vector3(.02f*Mathf.Sin(time*4),0,0):Vector3.zero;
      motion.Step(1f/fps);
      largest=Mathf.Max(largest,Quaternion.Angle(previous,bone.localRotation));previous=bone.localRotation;
      Require(!float.IsNaN(motion.MaxTipSpeed)&&motion.MaxAngle<=30.01f,"Secondary finite/angle constraint");
      Require(bone.localPosition==Vector3.zero,"Secondary must preserve authored bone positions");
     }
     Require(largest<45,"Secondary short segment angular jump: "+length+" / "+fps+" = "+largest);
     Require(motion.MaxTipSpeed<.001f,"Secondary must settle after motion: "+motion.MaxTipSpeed);
     motion.motionEnabled=false;motion.Step(1f/fps);Require(motion.MaxAngle<.01f,"Secondary reset");
    }finally{UnityEngine.Object.DestroyImmediate(root);}
   }
   var contactRoot=new GameObject("SecondaryContactFixture");
   try {
    var bone=new GameObject("bone").transform;bone.SetParent(contactRoot.transform);
    var hand=new GameObject("hand").transform;hand.SetParent(contactRoot.transform);hand.localPosition=new Vector3(.02f,-.08f,0);
    var motion=contactRoot.AddComponent<SecondaryMotion>();motion.externalClock=true;
    motion.Initialize(new SecondaryPhysicsData{version=2,
     chains=new[]{new SecondaryChain{root="bone",pull=.2f,spring=.2f,radius=.005f,colliders=new[]{0}}},
     bones=new[]{new SecondaryBone{path="bone",tail=Vector3.down*.1f}},
     colliders=new[]{new SecondaryCollider{path="hand",standardHand=true,shapeType=0,radius=.03f,maxWorldSize=.3f}}},null);
    Quaternion previous=bone.localRotation;float lateStep=0;
    for(int i=0;i<240;i++){motion.Restore();motion.Step(1f/60);if(i>180)lateStep=Mathf.Max(lateStep,Quaternion.Angle(previous,bone.localRotation));previous=bone.localRotation;}
    Require(motion.MaxAngle>2,"Standard hand contact must still deflect a bone");
    Require(lateStep<.2f,"Persistent hand contact must not chatter: "+lateStep);
    hand.localPosition=Vector3.right;
    for(int i=0;i<240;i++){motion.Restore();motion.Step(1f/60);}
    Require(motion.MaxAngle<.2f,"Bone must recover after hand leaves");
   }finally{UnityEngine.Object.DestroyImmediate(contactRoot);}
   Debug.Log("TANAKACAP_SECONDARY_STABILITY_CHECKS_OK lengths=1,10,100mm fps=30,60,120 contact/recovery");
  }
 }
}
