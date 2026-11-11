using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using TanakaCap;
using TanakaCap.Editor;
public static class HandCollisionRuntimeAudit {
 public static void Run(){
  HandCollisionChecks.Run();
  var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/forExports/Phys_Haolan.prefab");
  var source=JsonUtility.FromJson<SecondaryPhysicsData>(File.ReadAllText("../export-audit.json"));
  foreach(string hand in new[]{"collider_handL","collider_handR"})foreach(bool enabled in new[]{false,true}){
   var avatar=UnityEngine.Object.Instantiate(prefab);
   try{
    var a=avatar.GetComponent<Animator>();a.enabled=false;
    var bone=new GameObject("ContactFixture").transform;bone.SetParent(avatar.transform);bone.position=new Vector3(0,1,0);
    var c=source.colliders.First(x=>x.sourceId==hand);var t=avatar.transform.Find(c.path);
    t.rotation=Quaternion.Inverse(c.rotation);var target=bone.position+Vector3.up*.1f;
    t.position+=target+Vector3.right*.005f-t.TransformPoint(c.position);
    var data=new SecondaryPhysicsData{version=2,chains=new[]{new SecondaryChain{root="ContactFixture",pull=.2f,spring=.2f,maxAngleX=180,maxAngleZ=180,colliders=enabled?new[]{0}:new int[0]}},colliders=new[]{c},bones=new[]{new SecondaryBone{path="ContactFixture",tail=Vector3.up*.1f}}};
    var motion=avatar.AddComponent<SecondaryMotion>();motion.externalClock=true;motion.Initialize(data,a);
    for(int i=0;i<120;i++){motion.Restore();motion.Step(1f/60);}
    float angle=motion.MaxAngle;
    if(enabled?angle<1:angle>.1f)throw new Exception("Hand contact did not match permission "+hand+" "+enabled+" angle="+angle);
    Debug.Log("HAND_CONTACT "+hand+" enabled="+enabled+" angle="+angle);
   }finally{UnityEngine.Object.DestroyImmediate(avatar);}
  }
  foreach(bool hands in new[]{false,true}){
   var avatar=UnityEngine.Object.Instantiate(prefab);
   try{
    var a=avatar.GetComponent<Animator>();a.enabled=false;
    var data=JsonUtility.FromJson<SecondaryPhysicsData>(JsonUtility.ToJson(source));
    if(!hands)foreach(var chain in data.chains)chain.colliders=chain.colliders.Where(i=>!data.colliders[i].standardHand).ToArray();
    var motion=avatar.AddComponent<SecondaryMotion>();motion.externalClock=true;motion.Initialize(data,a);
    var left=a.GetBoneTransform(HumanBodyBones.LeftHand);var right=a.GetBoneTransform(HumanBodyBones.RightHand);
    var lp=left.position;var rp=right.position;var lr=left.localRotation;var rr=right.localRotation;
    double total=0;float max=0;var positions=avatar.GetComponentsInChildren<Transform>(true).ToDictionary(t=>t,t=>t.localPosition);
    for(int frame=0;frame<900;frame++){
     motion.Restore();float phase=frame*.08f;
     left.position=lp+new Vector3(.12f*Mathf.Sin(phase),.08f*Mathf.Cos(phase),0);right.position=rp+new Vector3(0,.1f*Mathf.Sin(phase),.1f*Mathf.Cos(phase));
     left.localRotation=lr*Quaternion.Euler(30*Mathf.Sin(phase),0,50*Mathf.Sin(phase));right.localRotation=rr*Quaternion.Euler(0,40*Mathf.Cos(phase),0);
     if(frame==200)left.position+=Vector3.one;
     if(frame==400)left.gameObject.SetActive(false);if(frame==420)left.gameObject.SetActive(true);
     motion.Step(frame==600?.5f:frame%2==0?1f/30:1f/60);
     if(float.IsNaN(motion.MaxAngle)||float.IsNaN(motion.MaxTipSpeed)||motion.MaxAngle>180)throw new Exception("Unstable hand collision");
     foreach(var p in positions)if(p.Key!=left&&p.Key!=right&&Vector3.Distance(p.Key.localPosition,p.Value)>1e-5f)throw new Exception("Bone length changed");
     total+=motion.LastStepMilliseconds;max=Mathf.Max(max,motion.LastStepMilliseconds);
    }
    motion.ResetState();if(motion.MaxAngle>.1f)throw new Exception("Reset failed");
    Debug.Log("HAND_PERF hands="+hands+" frames=900 averageMs="+(total/900)+" maxMs="+max+" boneLengths=unchanged reset=ok");
   }finally{UnityEngine.Object.DestroyImmediate(avatar);}
  }
  Debug.Log("HAND_RUNTIME_AUDIT_OK");
 }
}
