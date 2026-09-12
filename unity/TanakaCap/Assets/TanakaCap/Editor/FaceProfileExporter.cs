using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEditor;
namespace TanakaCap.Editor {
 public static class FaceProfileExporter {
  public static FaceProfile Collect(GameObject avatar,List<string> warnings){
   var descriptor=avatar.GetComponents<Component>().FirstOrDefault(c=>c && c.GetType().FullName=="VRC.SDK3.Avatars.Components.VRCAvatarDescriptor");
   var profile=new FaceProfile();var bindings=new List<FaceBinding>();
   if(descriptor){
    var data=new SerializedObject(descriptor);
    var mesh=data.FindProperty("VisemeSkinnedMesh")?.objectReferenceValue as SkinnedMeshRenderer;
    var visemes=data.FindProperty("VisemeBlendShapes");
    string mode=data.FindProperty("lipSync")?.enumNames.ElementAtOrDefault(data.FindProperty("lipSync").enumValueIndex)??"";
    if(mode=="VisemeBlendShape" && mesh && visemes!=null && visemes.isArray){
     foreach(var pair in new[]{("a",10),("i",12),("o",13),("u",14)})
      if(visemes.arraySize>pair.Item2)Add(bindings,avatar,mesh,pair.Item1,visemes.GetArrayElementAtIndex(pair.Item2).stringValue);
    }
    if(mode=="JawFlapBlendShape" && mesh)Add(bindings,avatar,mesh,"jawFallback",data.FindProperty("MouthOpenBlendShapeName")?.stringValue);
    if(mode=="JawFlapBone")warnings.Add("Jaw bone lip sync is not currently driven; existing facial keys will be used when available.");
    var eye=data.FindProperty("customEyeLookSettings");
    if(eye!=null){
     var left=eye.FindPropertyRelative("leftEye")?.objectReferenceValue as Transform;
     var right=eye.FindPropertyRelative("rightEye")?.objectReferenceValue as Transform;
     if(left && left.IsChildOf(avatar.transform))profile.leftEye=FaceExpressions.PathOf(left,avatar.transform);
     if(right && right.IsChildOf(avatar.transform))profile.rightEye=FaceExpressions.PathOf(right,avatar.transform);
     var lid=eye.FindPropertyRelative("eyelidsSkinnedMesh")?.objectReferenceValue as SkinnedMeshRenderer;
     var indices=eye.FindPropertyRelative("eyelidsBlendshapes");
     var type=eye.FindPropertyRelative("eyelidType");
     bool blendshapes=type!=null&&type.enumNames.ElementAtOrDefault(type.enumValueIndex)=="Blendshapes";
     if(blendshapes && lid && lid.sharedMesh && indices!=null && indices.isArray && indices.arraySize>0){
      int index=indices.GetArrayElementAtIndex(0).intValue;
      if(index>=0 && index<lid.sharedMesh.blendShapeCount)foreach(string side in new[]{"L","R"})Add(bindings,avatar,lid,"blink"+side,lid.sharedMesh.GetBlendShapeName(index));
     }
    }
   }
   profile.bindings=bindings.ToArray();
   var map=new FaceExpressions(avatar.transform,avatar.GetComponentsInChildren<SkinnedMeshRenderer>(true),profile);
   profile.bindings=map.Report.Values.ToArray();
   foreach(string channel in new[]{"smileL","frownL","shiftL","browLI"})if(!map.Has(channel))warnings.Add("Existing expression unavailable: "+channel);
   if(!map.Has("jaw")&&!map.Has("a")&&!map.Has("jawFallback"))warnings.Add("No supported mouth opening expression.");
   return profile;
  }
  static void Add(List<FaceBinding> list,GameObject root,SkinnedMeshRenderer mesh,string channel,string shape){
   if(string.IsNullOrEmpty(shape)||!mesh.sharedMesh||mesh.sharedMesh.GetBlendShapeIndex(shape)<0||!mesh.transform.IsChildOf(root.transform))return;
   list.Add(new FaceBinding{channel=channel,renderer=FaceExpressions.PathOf(mesh.transform,root.transform),shape=shape,source="VRC-descriptor",priority=2});
  }
 }
}
