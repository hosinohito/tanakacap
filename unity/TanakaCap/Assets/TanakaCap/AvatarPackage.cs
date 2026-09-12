using System;
using UnityEngine;
namespace TanakaCap {
 [Serializable] public class SecondaryCurve {
  public Key[] keys=new Key[0];public int preWrap=8,postWrap=8;
  [Serializable] public class Key {public float time,value,inSlope,outSlope,inWeight,outWeight;public int weightedMode;}
  public AnimationCurve Build(){var k=new Keyframe[keys.Length];for(int i=0;i<k.Length;i++){var a=keys[i];k[i]=new Keyframe(a.time,a.value,a.inSlope,a.outSlope,a.inWeight,a.outWeight){weightedMode=(WeightedMode)a.weightedMode};}return new AnimationCurve(k){preWrapMode=(WrapMode)preWrap,postWrapMode=(WrapMode)postWrap};}
 }
 [Serializable] public class SecondaryChain {
  public string root,sourceId,sourceMode;public string[] ignored=new string[0];
  public int version,integrationType,multiChildType,immobileType,limitType;
  public float pull,spring,stiffness,gravity,gravityFalloff,immobile,radius,maxAngleX,maxAngleZ;
  public Vector3 endpointPosition,limitRotation;
  public SecondaryCurve pullCurve,springCurve,stiffnessCurve,gravityCurve,gravityFalloffCurve,immobileCurve,radiusCurve,maxAngleXCurve,maxAngleZCurve,limitRotationXCurve,limitRotationYCurve,limitRotationZCurve;
  public int[] colliders=new int[0];
  public bool isAnimated,resetWhenDisabled;
 }
 [Serializable] public class SecondaryCollider {
  public string path,sourceId;public int shapeType;public bool insideBounds,bonesAsSpheres;
  public float radius,height;public Vector3 position;public Quaternion rotation=Quaternion.identity;
 }
 [Serializable] public class SecondaryBone {public string path;public Vector3 tail;public int chain;public float depth;}
 [Serializable] public class SecondaryPhysicsData {public int version=1;public SecondaryChain[] chains;public SecondaryCollider[] colliders;public SecondaryBone[] bones;}
 [Serializable] public class AvatarPackageManifest {
  public int formatVersion=1;
  public string unityVersion,platform="StandaloneWindows64",profile="haolan-1.6",prefab="avatar",displayName,bundleSha256;
  public string[] warnings;
  public SecondaryPhysicsData secondaryPhysics;
  public FaceProfile faceProfile;
 }
}
