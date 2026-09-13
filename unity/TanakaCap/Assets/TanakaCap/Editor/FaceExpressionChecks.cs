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
    map.Begin();map.ApplyMouth(1,0,0,.5f,0,0,0,0);map.Commit();
    Require(Mathf.Abs(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("mouthSmileLeft"))-50)<.001f,"Untouched normal options must be identity, even with mouth open");
    map.CornerGamma=2;map.OpenSmileSuppression=.9f;
    map.Begin();map.ApplyMouth(1,0,0,.5f,0,0,0,0);map.Commit();
    Require(Mathf.Abs(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("mouthSmileLeft"))-2.5f)<.001f,"Adjustable normal gamma and opening suppression");
    Require(Mathf.Abs(FaceExpressions.ExpressiveCorner(-.5f,1,2,.9f)+.25f)<.00001f,"Opening suppression must not reduce frowns");
    map.Begin();map.ApplyMouth(1,0,0,.5f,0,0,0,1);map.Commit();
    Require(Mathf.Abs(renderer.GetBlendShapeWeight(mesh.GetBlendShapeIndex("mouthSmileLeft"))-5)<.001f,"Normal emphasis remains adjustable");
    map.CornerGamma=1;map.OpenSmileSuppression=0;
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
    vrc.UploadMeshData(true);
    var readOnly=new FaceExpressions(root.transform,new[]{renderer},custom);
    Require(readOnly.Has("a"),"Existing keys must work without CPU mesh readability");
    UnityEngine.Object.DestroyImmediate(vrc);
    var perfect=new Mesh();perfect.vertices=mesh.vertices;perfect.triangles=mesh.triangles;
    try {
     foreach(string key in new[]{"mouthLeft","mouthRight","mouthSmileLeft","mouthSmileRight","mouthFrownLeft","mouthFrownRight"})
      perfect.AddBlendShapeFrame(key,100,new[]{Vector3.up*.01f,Vector3.zero,Vector3.zero},null,null);
     renderer.sharedMesh=perfect;var asymmetric=new FaceExpressions(root.transform,new[]{renderer});
     asymmetric.Begin();asymmetric.ApplyMouth(0,0,0,.8f,-.6f,.7f,0,0);asymmetric.Commit();
     string[] keys={"mouthLeft","mouthRight","mouthSmileLeft","mouthSmileRight","mouthFrownLeft","mouthFrownRight"};
     float[] expected={70,0,80,0,0,60};
     for(int i=0;i<keys.Length;i++)Require(Mathf.Abs(renderer.GetBlendShapeWeight(perfect.GetBlendShapeIndex(keys[i]))-expected[i])<.001f,"ARKit asymmetric / lateral transfer: "+keys[i]);
     asymmetric.Begin();asymmetric.ApplyMouth(0,0,0,-.8f,.6f,-.7f,0,0);asymmetric.Commit();
     float[] reversed={0,70,0,60,80,0};
     for(int i=0;i<keys.Length;i++)Require(Mathf.Abs(renderer.GetBlendShapeWeight(perfect.GetBlendShapeIndex(keys[i]))-reversed[i])<.001f,"ARKit mirrored transfer / no stale weights: "+keys[i]);
     Debug.Log("TANAKACAP_ARKIT_ASYMMETRY_OK left/right shift and opposite smile/frown");
    }finally{UnityEngine.Object.DestroyImmediate(perfect);}
    var browMesh=new Mesh();browMesh.vertices=new[]{Vector3.left*.1f,Vector3.right*.1f,Vector3.zero};browMesh.triangles=new[]{0,1,2};
    var eyeL=new GameObject("left-eye");var eyeR=new GameObject("right-eye");Mesh split=null;
    try{
     eyeL.transform.position=Vector3.left*.05f;eyeR.transform.position=Vector3.right*.05f;
     foreach(string key in new[]{"上","下","困る","怒り"})browMesh.AddBlendShapeFrame(key,100,new[]{Vector3.up*.01f,Vector3.up*.01f,Vector3.zero},null,null);
     renderer.sharedMesh=browMesh;
     BrowShapeSplit.Generate(new[]{renderer},eyeL.transform,eyeR.transform,r=>{if(split==null)split=UnityEngine.Object.Instantiate(browMesh);r.sharedMesh=split;return split;});
     var leftDelta=new Vector3[3];var rightDelta=new Vector3[3];
     split.GetBlendShapeFrameVertices(split.GetBlendShapeIndex("TC_BrowLeftUp"),0,leftDelta,null,null);
     split.GetBlendShapeFrameVertices(split.GetBlendShapeIndex("TC_BrowRightUp"),0,rightDelta,null,null);
     Require(leftDelta[0].y>.009f&&leftDelta[1]==Vector3.zero&&rightDelta[0]==Vector3.zero&&rightDelta[1].y>.009f,"Brow geometry must not deform the opposite side");
     new FaceExpressions(root.transform,new[]{renderer},null,true).CheckBrowSides();
     Require(browMesh.blendShapeCount==4,"Original eyebrow mesh must not change");
     renderer.sharedMesh=browMesh;
     foreach(string key in new[]{"上左","上右","下左","下右"})browMesh.AddBlendShapeFrame(key,100,new[]{Vector3.up*.01f,Vector3.zero,Vector3.zero},null,null);
     int before=browMesh.blendShapeCount;
     new FaceExpressions(root.transform,new[]{renderer}).CheckBrowSides();
     Require(browMesh.blendShapeCount==before,"Existing brow mode must not generate keys");
     Debug.Log("TANAKACAP_BROW_SPLIT_GEOMETRY_OK");
    }finally{if(split)UnityEngine.Object.DestroyImmediate(split);UnityEngine.Object.DestroyImmediate(browMesh);UnityEngine.Object.DestroyImmediate(eyeL);UnityEngine.Object.DestroyImmediate(eyeR);}
    Require(AvatarDriver.FollowBrow(0,.2f,0)==0,"Brow follow zero dt");
    Require(AvatarDriver.FollowBrow(0,.2f,.01f,false)==.2f,"Brow follow reversible direct mode");
    float browSmall=0,browLarge=0,browNoise=0,noiseMax=0;
    for(int i=0;i<120;i++){
     browSmall=AvatarDriver.FollowBrow(browSmall,.02f,1f/60);
     if(i<6)browLarge=AvatarDriver.FollowBrow(browLarge,.8f,1f/60);
     browNoise=AvatarDriver.FollowBrow(browNoise,i%2==0?.02f:-.02f,1f/60);
     noiseMax=Mathf.Max(noiseMax,Mathf.Abs(browNoise));
    }
    Require(Mathf.Abs(browSmall-.02f)<.00001f,"Small brow movement must converge");
    Require(browLarge>.65f&&browLarge<=.8f,"Large brow movement must follow rapidly without overshoot");
    Require(noiseMax<.005f,"Small alternating brow noise must be reduced");
    Require(AvatarDriver.FollowBrow(0,0,1f/60)==0,"Unchanged opposite brow must stay still");
    Debug.Log("TANAKACAP_BROW_FOLLOW_CHECK_OK");
    var normal=FacialExaggeration.Parse(new string[0],false);
    Require(normal.BrowValue(.2f)==.2f&&normal.MouthValue(-.3f)==-.3f&&normal.LidValue(.4f)==.4f&&normal.EyeGain==1,"Zero exaggeration must be identity");
    var demo=FacialExaggeration.Parse(new[]{"--eye-exaggeration","0"},true);
    Require(demo.Brow==1&&demo.Eye==1&&demo.Eyelid==1&&demo.Mouth==1,"Demo must force full exaggeration");
    var onlyLid=FacialExaggeration.Parse(new[]{"--eyelid-exaggeration",".7"},false);
    Require(onlyLid.LidValue(.3f)>.3f&&onlyLid.BrowValue(.2f)==.2f&&onlyLid.MouthValue(.2f)==.2f&&onlyLid.EyeGain==1,"Exaggeration parts must be independent");
    Require(demo.BrowValue(0)==0&&demo.MouthValue(0)==0&&demo.LidValue(0)==0,"Neutral must not move under exaggeration");
    Require(demo.BrowValue(1)==1&&demo.LidValue(1)==1&&demo.MouthValue(-1)==-1,"Exaggeration must respect shape range");
    Debug.Log("TANAKACAP_EXAGGERATION_CHECK_OK");
    Debug.Log("TANAKACAP_EXPRESSION_CHECKS_OK priority/empty/descriptor/grouping/gaze/no-generated-keys");
   }finally{UnityEngine.Object.DestroyImmediate(root);UnityEngine.Object.DestroyImmediate(mesh);}
  }
  static void Require(bool condition,string reason){if(!condition)throw new Exception(reason);}
 }
}
