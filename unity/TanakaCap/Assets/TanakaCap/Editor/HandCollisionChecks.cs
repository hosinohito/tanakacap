using System;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class HandCollisionChecks {
  static void Require(bool value,string message){if(!value)throw new Exception(message);}
  public static void Run(){
   var root=new GameObject("HandCollisionFixture");
   try{
    var palm=new GameObject("Palm").transform;palm.SetParent(root.transform);
    var c=new SecondaryCollider{standardHand=true,shapeType=1,radius=.02f,height=.1f,maxWorldSize=.3f};
    var hit=SecondaryMotion.CollisionCorrection(new Vector3(.01f,0,0),.005f,c,palm);
    Require(Mathf.Abs(hit.x-.015f)<1e-6f,"Palm capsule contact");
    palm.position=Vector3.right;
    Require(SecondaryMotion.CollisionCorrection(Vector3.zero,0,c,palm)==Vector3.zero,"Hand translation must move contact");
    palm.position=Vector3.zero;palm.rotation=Quaternion.Euler(0,0,90);
    Require(SecondaryMotion.CollisionCorrection(new Vector3(.04f,0,0),0,c,palm).magnitude>.009f,"Palm rotation must move capsule axis");
    palm.rotation=Quaternion.identity;palm.localScale=Vector3.one*100;
    Require(SecondaryMotion.CollisionCorrection(new Vector3(.16f,0,0),0,c,palm)==Vector3.zero,"SDK maximum palm size");
    palm.localScale=Vector3.one;
    var finger=new GameObject("FingerEnd").transform;finger.SetParent(palm);finger.localPosition=Vector3.up*.1f;
    c.finger=true;
    Require(SecondaryMotion.CollisionCorrection(new Vector3(.01f,.05f,0),0,c,finger).x>.009f,"Finger capsule between parent and endpoint");
    finger.localPosition=Vector3.right*.1f;
    Require(SecondaryMotion.CollisionCorrection(new Vector3(.01f,.05f,0),0,c,finger)==Vector3.zero,"Finger bend must update capsule direction");
    Require(SecondaryMotion.CollisionCorrection(new Vector3(.05f,.01f,0),0,c,finger).y>.009f,"Bent finger capsule contact");
    palm.gameObject.SetActive(false);
    Require(SecondaryMotion.CollisionCorrection(new Vector3(.05f,.01f,0),0,c,finger)==Vector3.zero,"Inactive hand must not collide");
    Debug.Log("TANAKACAP_HAND_COLLISION_CHECKS_OK");
   }finally{UnityEngine.Object.DestroyImmediate(root);}
  }
 }
}
