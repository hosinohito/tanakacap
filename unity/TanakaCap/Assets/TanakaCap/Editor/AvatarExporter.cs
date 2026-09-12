using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
namespace TanakaCap.Editor {
 public static class AvatarExporter {
  [MenuItem("TanakaCap/Export selected avatar (HAOLAN profile)")]
  public static void ExportSelected() {
   var source=Selection.activeGameObject;
   if(!source)throw new Exception("Select the avatar root first.");
   var path=EditorUtility.SaveFilePanel("Export local avatar","","avatar","tcap");
   if(!string.IsNullOrEmpty(path))Export(source,path);
  }
  public static void Export(GameObject source,string destination) {
   if(File.Exists(destination))throw new Exception("Choose a new file name; existing package is preserved.");
   string scratch="Assets/TanakaCapExport-"+Guid.NewGuid().ToString("N");
   string build=Path.Combine("Temp",Guid.NewGuid().ToString("N"));
   GameObject copy=null;
   var warnings=new List<string>{"HAOLAN 1.6 expression profile only.","VRChat behaviours and animator controllers are not reproduced.","Modular Avatar and other build-time modifications must not be silently omitted; unsupported scripts stop this exporter."};
   try {
    Directory.CreateDirectory(scratch);Directory.CreateDirectory(build);AssetDatabase.Refresh();
    copy=UnityEngine.Object.Instantiate(source);copy.name="avatar";
    copy.transform.SetParent(null);copy.transform.SetPositionAndRotation(Vector3.zero,Quaternion.identity);
    var animator=copy.GetComponent<Animator>();
    if(!animator||!animator.isHuman||!animator.avatar.isValid)throw new Exception("A valid Humanoid Animator is required on the selected root.");
    foreach(var bone in new[]{HumanBodyBones.Hips,HumanBodyBones.Spine,HumanBodyBones.Head,HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm,HumanBodyBones.LeftHand,HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm,HumanBodyBones.RightHand})
     if(!animator.GetBoneTransform(bone))throw new Exception("Missing required bone: "+bone);
    var body=copy.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(x=>x.name=="Body"&&x.sharedMesh&&x.sharedMesh.GetBlendShapeIndex("vrc.v_aa")>=0);
    if(!body)throw new Exception("This first exporter requires the HAOLAN Body/viseme profile.");
    var secondary=SecondaryMotionExporter.Collect(source,copy,warnings);
    foreach(var t in copy.GetComponentsInChildren<Transform>(true)) {
     int count=GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject);
     if(count>0)warnings.Add("Missing components omitted: "+AnimationUtility.CalculateTransformPath(t,copy.transform)+" : "+count);
     GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
    }
    foreach(var component in copy.GetComponentsInChildren<Component>(true)) {
     if(component is Transform||component is Animator||component is SkinnedMeshRenderer||component is MeshRenderer||component is MeshFilter||component is UnityEngine.Animations.IConstraint)continue;
     string type=component.GetType().FullName;
     if(type=="TanakaCap.AvatarDriver"||type.StartsWith("VRC.")) {
      warnings.Add("Omitted: "+type+" at "+AnimationUtility.CalculateTransformPath(component.transform,copy.transform));
      UnityEngine.Object.DestroyImmediate(component);
     } else throw new Exception("Unsupported component: "+type+" on "+component.name);
    }
    foreach(var a in copy.GetComponentsInChildren<Animator>(true)){a.runtimeAnimatorController=null;a.applyRootMotion=false;}
    foreach(var r in copy.GetComponentsInChildren<Renderer>(true))foreach(var m in r.sharedMaterials)
     if(!m||!m.shader||m.shader.name=="Hidden/InternalErrorShader")throw new Exception("Missing material/shader: "+r.name);
    string prefab=scratch+"/avatar.prefab";
    PrefabUtility.SaveAsPrefabAsset(copy,prefab);AssetDatabase.SaveAssets();
    var result=BuildPipeline.BuildAssetBundles(build,new[]{new AssetBundleBuild{assetBundleName="avatar.bundle",assetNames=new[]{prefab},addressableNames=new[]{"avatar"}}},BuildAssetBundleOptions.ChunkBasedCompression|BuildAssetBundleOptions.StrictMode,BuildTarget.StandaloneWindows64);
    if(!result)throw new Exception("AssetBundle build failed");
    string bundle=Path.Combine(build,"avatar.bundle");
    string hash;using(var sha=SHA256.Create())using(var f=File.OpenRead(bundle))hash=BitConverter.ToString(sha.ComputeHash(f)).Replace("-","").ToLowerInvariant();
    var manifest=new AvatarPackageManifest{unityVersion=Application.unityVersion,displayName=source.name,bundleSha256=hash,warnings=warnings.ToArray(),secondaryPhysics=secondary};
    Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(destination)));
    string temp=destination+".partial";
    try {
     using(var zip=ZipFile.Open(temp,ZipArchiveMode.Create)) {
      using(var writer=new StreamWriter(zip.CreateEntry("manifest.json").Open()))writer.Write(JsonUtility.ToJson(manifest,true));
      zip.CreateEntryFromFile(bundle,"avatar.bundle",System.IO.Compression.CompressionLevel.NoCompression);
     }
     File.Move(temp,destination);
    } finally {if(File.Exists(temp))File.Delete(temp);}
    File.WriteAllText(destination+".report.json",JsonUtility.ToJson(manifest,true));
    Debug.Log("TANAKACAP_EXPORT_OK "+destination+" warnings="+warnings.Count);
   } finally {
    if(copy)UnityEngine.Object.DestroyImmediate(copy);
    if(AssetDatabase.IsValidFolder(scratch))AssetDatabase.DeleteAsset(scratch);
    // Build cache remains under Temp for diagnostics; no source assets are edited.
   }
  }
 }
}
