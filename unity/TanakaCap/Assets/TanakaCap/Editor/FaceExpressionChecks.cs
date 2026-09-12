using System;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class FaceExpressionChecks {
  public static void Run(){
   var root=new GameObject("ExpressionFixture");var renderer=root.AddComponent<SkinnedMeshRenderer>();var mesh=new Mesh();
   try {
    mesh.vertices=new[]{Vector3.zero,Vector3.right,Vector3.up};mesh.triangles=new[]{0,1,2};
    foreach(string key in new[]{"jawOpen","mouthSmileLeft","口角上げ","口角下げ","あ","い","お","う","vrc.v_aa","renamed-vowel","eyeBlinkLeft","ウィンク２右","困る","上","下","browInnerUp","eyeLookInLeft","eyeLookOutLeft"})
     mesh.AddBlendShapeFrame(key,100,new[]{Vector3.up*.01f,Vector3.zero,Vector3.zero},null,null);
    // A named but empty ARKit key must not mask a functioning MMD fallback.
    mesh.AddBlendShapeFrame("mouthSmileRight",100,new Vector3[3],null,null);
    renderer.sharedMesh=mesh;int count=mesh.blendShapeCount;
    var custom=new FaceProfile{bindings=new[]{new FaceBinding{channel="a",renderer="",shape="renamed-vowel",source="VRC-descriptor",priority=2}}};
    var map=new FaceExpressions(root.transform,new[]{renderer},custom);
    Require(map.Report["jaw"].source=="ARKit"&&map.Report["a"].shape=="あ","MMD must beat VRC descriptor");
    Require(map.Report["smileL"].shape=="mouthSmileLeft"&&map.Report["smileR"].shape=="口角上げ","Per-side priority / empty key fallback");
    Require(map.Report["blinkL"].priority==0&&map.Report["blinkR"].priority==1,"Per-feature fallback");
    map.Begin();map.ApplyMouth(.8f,0,0,1,0,0,0,0);map.Commit();
    Require(Mathf.Abs(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("jawOpen"))-80)<.001f,"ARKit opening");
    Require(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("あ"))==0,"Do not stack MMD vowels over ARKit jaw");
    map.Begin();map.ApplyBrows(1,0,0,0);map.Commit();
    Require(Mathf.Abs(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("browInnerUp"))-50)<.001f,"Bilateral brow averages instead of sum/max");
    map.Begin();var residual=map.Eye("L",new Vector2(10,5));map.Commit();
    Require(residual==new Vector2(0,5),"Bone fallback per gaze axis");
    map.Eye("L",new Vector2(-10,5));map.Commit();
    Require(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("eyeLookInLeft"))==0,"No stale opposite gaze weight");
    Require(renderer.sharedMesh==mesh&&mesh.blendShapeCount==count,"Existing mode must never generate/clone keys");
    var vrc=new Mesh();vrc.vertices=mesh.vertices;vrc.triangles=mesh.triangles;
    foreach(string key in new[]{"vrc.v_aa","renamed-vowel"})vrc.AddBlendShapeFrame(key,100,new[]{Vector3.up*.01f,Vector3.zero,Vector3.zero},null,null);
    renderer.sharedMesh=vrc;
    var fallback=new FaceExpressions(root.transform,new[]{renderer},custom);
    Require(fallback.Report["a"].shape=="renamed-vowel","Explicit VRC descriptor must beat guessed VRC name");
    UnityEngine.Object.DestroyImmediate(vrc);
    Debug.Log("TANAKACAP_EXPRESSION_CHECKS_OK priority/empty/descriptor/grouping/gaze/no-generated-keys");
   }finally{UnityEngine.Object.DestroyImmediate(root);UnityEngine.Object.DestroyImmediate(mesh);}
  }
  static void Require(bool condition,string reason){if(!condition)throw new Exception(reason);}
 }
}
