using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
namespace TanakaCap {
 // Independent solver from documented parameter meanings, not SDK implementation.
 [DefaultExecutionOrder(500)]
 public class SecondaryMotion : MonoBehaviour {
  class Node {
   public Transform bone;public SecondaryBone settings;public SecondaryChain chain;public Quaternion rest,previousRest;
   public Vector3 tip,velocity,anchor,initialGravityLocal;public float pull,spring,stiffness,gravity,falloff,immobile,radius,maxX,maxZ;
   public Quaternion limitRotation;
  }
  class Collider {public Transform transform;public SecondaryCollider settings;}
  class RootState {public Transform parent;public Matrix4x4 previousInverse;}
  readonly List<Node> nodes=new List<Node>();readonly List<Collider> colliders=new List<Collider>();
  RootState[] roots;Vector3 previousRoot;
  public bool motionEnabled=true,externalClock;
  public int BoneCount=>nodes.Count;
  public float MaxAngle=>nodes.Count==0?0:nodes.Max(n=>Quaternion.Angle(n.rest,n.bone.localRotation));
  public float MaxTipSpeed=>nodes.Count==0?0:nodes.Max(n=>n.velocity.magnitude);
  public float LastStepMilliseconds {get;private set;}
  public string Diagnostics(){return string.Join("\n",nodes.Select(n=>n.settings.path+" angle="+Quaternion.Angle(n.rest,n.bone.localRotation)+" radius="+(n.radius*Scale(n.bone))+" tip="+n.tip+" colliders="+string.Join(";",n.chain.colliders.Select(i=>colliders[i].settings.path+" center="+colliders[i].transform.TransformPoint(colliders[i].settings.position)+" radius="+(colliders[i].settings.radius*Scale(colliders[i].transform))))));}
  static float Curve(float value,SecondaryCurve curve,float t)=>value*(curve==null||curve.keys.Length==0?1:curve.Build().Evaluate(t));
  public void Initialize(SecondaryPhysicsData data,Animator animator) {
   if(data.version!=1||data.bones.Length>4096||data.chains.Length>512||data.colliders.Length>1024)throw new Exception("Unsupported secondary physics data");
   var human=new HashSet<Transform>();for(int i=0;i<(int)HumanBodyBones.LastBone;i++){var b=animator.GetBoneTransform((HumanBodyBones)i);if(b)human.Add(b);}
   roots=new RootState[data.chains.Length];for(int i=0;i<roots.Length;i++){var t=Find(data.chains[i].root);roots[i]=new RootState{parent=t.parent?t.parent:transform};}
   foreach(var c in data.colliders){if(!Finite(c.radius)||c.radius<0||!Finite(c.height)||c.height<0||!Finite(c.position)||!Finite(c.rotation)||c.shapeType<0||c.shapeType>2)throw new Exception("Invalid secondary collider");colliders.Add(new Collider{transform=Find(c.path),settings=c});}
   var seen=new HashSet<Transform>();
   foreach(var s in data.bones) {
    var b=Find(s.path);
    if(human.Contains(b)||!seen.Add(b)||b.GetComponents<Component>().Any(c=>c is UnityEngine.Animations.IConstraint)||!Finite(s.tail)||s.tail.sqrMagnitude<1e-10f||s.chain<0||s.chain>=data.chains.Length||!Finite(s.depth)||s.depth<0||s.depth>1)throw new Exception("Invalid secondary bone: "+s.path);
    var c=data.chains[s.chain];
    if(c.version<0||c.version>1||c.integrationType<0||c.integrationType>1||c.limitType<0||c.limitType>3||c.immobileType<0||c.immobileType>1||c.colliders.Any(i=>i<0||i>=colliders.Count))throw new Exception("Invalid secondary chain");
    Func<float,SecondaryCurve,float> value=(v,curve)=>Curve(v,curve,s.depth);
    var n=new Node{bone=b,settings=s,chain=c,rest=b.localRotation,previousRest=b.localRotation,
     pull=value(c.pull,c.pullCurve),spring=value(c.spring,c.springCurve),stiffness=value(c.stiffness,c.stiffnessCurve),
     gravity=value(c.gravity,c.gravityCurve),falloff=value(c.gravityFalloff,c.gravityFalloffCurve),immobile=value(c.immobile,c.immobileCurve),radius=value(c.radius,c.radiusCurve),
     maxX=value(c.maxAngleX,c.maxAngleXCurve),maxZ=value(c.maxAngleZ,c.maxAngleZCurve),
     initialGravityLocal=Quaternion.Inverse(b.rotation)*Vector3.down,
     limitRotation=Quaternion.Euler(value(c.limitRotation.x,c.limitRotationXCurve),value(c.limitRotation.y,c.limitRotationYCurve),value(c.limitRotation.z,c.limitRotationZCurve))};
    foreach(float f in new[]{n.pull,n.spring,n.stiffness,n.gravity,n.falloff,n.immobile,n.radius,n.maxX,n.maxZ})if(!Finite(f))throw new Exception("Non-finite secondary parameter");
    if(n.pull<0||n.pull>1||n.spring<0||n.spring>1||n.stiffness<0||n.stiffness>1||Mathf.Abs(n.gravity)>1||n.falloff<0||n.falloff>1||n.immobile<0||n.immobile>1||n.radius<0||n.maxX<0||n.maxX>180||n.maxZ<0||n.maxZ>180||!Finite(n.limitRotation))throw new Exception("Secondary parameter outside supported range");
    nodes.Add(n);
   }
   nodes.Sort((a,b)=>Depth(a.bone).CompareTo(Depth(b.bone)));ResetState();
   motionEnabled=Array.IndexOf(Environment.GetCommandLineArgs(),"--no-secondary-motion")<0;
   Debug.Log("TANAKACAP_SECONDARY_READY bones="+nodes.Count+" chains="+roots.Length+" colliders="+colliders.Count+" enabled="+motionEnabled);
  }
  Transform Find(string path){var t=string.IsNullOrEmpty(path)?transform:transform.Find(path);if(!t)throw new Exception("Missing secondary transform: "+path);return t;}
  static int Depth(Transform t){int d=0;while(t.parent){d++;t=t.parent;}return d;}
  static bool Finite(float v)=>!float.IsNaN(v)&&!float.IsInfinity(v);
  static bool Finite(Vector3 v)=>Finite(v.x)&&Finite(v.y)&&Finite(v.z);
  static bool Finite(Quaternion q)=>Finite(q.x)&&Finite(q.y)&&Finite(q.z)&&Finite(q.w);
  static float Scale(Transform t){var s=t.lossyScale;return Mathf.Max(Mathf.Abs(s.x),Mathf.Abs(s.y),Mathf.Abs(s.z));}
  public void Restore(){foreach(var n in nodes)if(n.bone)n.bone.localRotation=n.rest;}
  public void ResetState(){Restore();foreach(var n in nodes){n.tip=n.bone.TransformPoint(n.settings.tail);n.velocity=Vector3.zero;n.anchor=n.bone.position;n.previousRest=n.bone.rotation;}if(roots!=null)foreach(var r in roots)r.previousInverse=r.parent.worldToLocalMatrix;previousRoot=transform.position;}
  void Update(){if(Input.GetKeyDown(KeyCode.F6)){motionEnabled=!motionEnabled;ResetState();}if(!externalClock)Restore();}
  void OnDisable(){Restore();}
  void LateUpdate(){if(!externalClock)Step(Time.unscaledDeltaTime);}
  static Vector3 Limit(Node n,Vector3 direction,Quaternion restWorld){
   if(direction.sqrMagnitude<1e-12f)direction=restWorld*n.settings.tail;
   if(n.chain.limitType==0)return direction.normalized;
   var frame=restWorld*Quaternion.FromToRotation(Vector3.up,n.settings.tail.normalized)*n.limitRotation;
   var local=Quaternion.Inverse(frame)*direction.normalized;
   if(n.chain.limitType==1)local=Vector3.RotateTowards(Vector3.up,local,n.maxX*Mathf.Deg2Rad,0);
   else if(n.chain.limitType==2){float angle=Mathf.Clamp(Mathf.Atan2(local.z,local.y)*Mathf.Rad2Deg,-n.maxX,n.maxX)*Mathf.Deg2Rad;local=new Vector3(0,Mathf.Cos(angle),Mathf.Sin(angle));}
   else {float pitch=Mathf.Clamp(Mathf.Atan2(local.z,local.y)*Mathf.Rad2Deg,-n.maxX,n.maxX)*Mathf.Deg2Rad;float yaw=Mathf.Clamp(Mathf.Asin(Mathf.Clamp(local.x,-1,1))*Mathf.Rad2Deg,-n.maxZ,n.maxZ)*Mathf.Deg2Rad;local=new Vector3(Mathf.Sin(yaw),Mathf.Cos(yaw)*Mathf.Cos(pitch),Mathf.Cos(yaw)*Mathf.Sin(pitch));}
   return (frame*local).normalized;
  }
  static Vector3 PointCorrection(Vector3 point,float boneRadius,Collider collider){
   var c=collider.settings;var t=collider.transform;float scale=Scale(t);var center=t.TransformPoint(c.position);var rotation=t.rotation*c.rotation;
   if(c.shapeType==2){var normal=rotation*Vector3.up;float d=Vector3.Dot(point-center,normal);return d<boneRadius?normal*(boneRadius-d):Vector3.zero;}
   float radius=c.radius*scale;float half=c.shapeType==1?Mathf.Max(0,c.height*scale*.5f-radius):0;
   var axis=rotation*Vector3.up;var closest=center+axis*Mathf.Clamp(Vector3.Dot(point-center,axis),-half,half);
   var away=point-closest;float length=away.magnitude;float target=c.insideBounds?Mathf.Max(0,radius-boneRadius):radius+boneRadius;
   if(c.insideBounds?length>target:length<target)return (length>1e-8f?away/length:rotation*Vector3.right)*(target-length);
   return Vector3.zero;
  }
  public void Step(float delta) {
   long start=System.Diagnostics.Stopwatch.GetTimestamp();
   if(!motionEnabled||!Finite(delta)||delta<=0||delta>.15f){ResetState();return;}
   delta=Mathf.Min(delta,1f/15);int steps=Mathf.CeilToInt(delta*120);float dt=delta/steps;
   var worldMovement=transform.position-previousRoot;
   foreach(var n in nodes){
    if(!n.bone.gameObject.activeInHierarchy){if(n.chain.resetWhenDisabled){n.tip=n.bone.TransformPoint(n.settings.tail);n.velocity=Vector3.zero;n.anchor=n.bone.position;}continue;}
    if(n.chain.isAnimated)n.rest=n.bone.localRotation;
    n.bone.localRotation=n.rest;var restWorld=n.bone.rotation;
    Vector3 anchor=n.bone.position,restTip=n.bone.TransformPoint(n.settings.tail),restDirection=restTip-anchor;float length=restDirection.magnitude;if(length<1e-5f)continue;
    var root=roots[n.settings.chain];
    Vector3 transported=n.chain.immobileType==0?root.parent.localToWorldMatrix.MultiplyPoint3x4(root.previousInverse.MultiplyPoint3x4(n.tip)):n.tip+worldMovement;
    n.tip=Vector3.Lerp(n.tip,transported,n.immobile);
    if((anchor-n.anchor).magnitude>.4f){n.tip=restTip;n.velocity=Vector3.zero;}
    float frequency=n.pull<=0?0:.5f+8*Mathf.Sqrt(n.pull);float w=2*Mathf.PI*frequency;
    float damping=n.chain.integrationType==0?Mathf.Lerp(1.1f,.12f,n.spring):Mathf.Lerp(1,.055f,n.spring);
    float radius=n.radius*Scale(n.bone);
    for(int j=0;j<steps;j++){
     Vector3 before=n.tip;Vector3 targetDirection=restDirection.normalized;
     if(n.chain.integrationType==1){var previousDirection=n.chain.version>=1?n.previousRest*n.settings.tail:restDirection;targetDirection=Vector3.Slerp(targetDirection,previousDirection.normalized,n.stiffness);}
     if(n.chain.version>=1){var gravity=Vector3.down-(restWorld*n.initialGravityLocal)*n.falloff;if(gravity.sqrMagnitude>1e-10f)targetDirection=Vector3.Slerp(targetDirection,(n.gravity>=0?gravity:-gravity).normalized,Mathf.Clamp01(Mathf.Abs(n.gravity)*gravity.magnitude));}
     n.velocity+=(anchor+targetDirection*length-n.tip)*(w*w*dt);
     if(n.chain.version==0){var gravity=Vector3.down-(restWorld*n.initialGravityLocal)*n.falloff;n.velocity+=gravity*(n.gravity*9.81f*dt);}
     n.velocity*=Mathf.Exp(-Mathf.Max(1,2*damping*w)*dt);n.tip+=n.velocity*dt;
     n.tip=anchor+Limit(n,n.tip-anchor,restWorld)*length;
     // Explicit original colliders, with sampled segment capsules (not mesh collisions).
     for(int iteration=0;iteration<2;iteration++){
      foreach(int ci in n.chain.colliders){var c=colliders[ci];// An immovable anchor outside an inside volume cannot be projected by rotating its child.
       int samples=c.settings.bonesAsSpheres||c.settings.insideBounds?1:4;for(int sample=1;sample<=samples;sample++){float u=sample/(float)samples;var p=Vector3.Lerp(anchor,n.tip,u);var correction=PointCorrection(p,radius,c);n.tip+=correction/u;}}
      n.tip=anchor+Limit(n,n.tip-anchor,restWorld)*length;
     }
     n.velocity=(n.tip-before)/dt;
    }
    if(!Finite(n.tip)||!Finite(n.velocity)){n.tip=restTip;n.velocity=Vector3.zero;}
    n.bone.rotation=Quaternion.FromToRotation(restDirection,n.tip-anchor)*restWorld;n.anchor=anchor;n.previousRest=n.bone.rotation;
   }
   foreach(var r in roots)r.previousInverse=r.parent.worldToLocalMatrix;previousRoot=transform.position;
   LastStepMilliseconds=(float)((System.Diagnostics.Stopwatch.GetTimestamp()-start)*1000.0/System.Diagnostics.Stopwatch.Frequency);
  }
 }
}
