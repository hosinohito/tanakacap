using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
namespace TanakaCap.Editor {
 // Offline package-only diagnostic. Never opens a camera or edits source assets.
 public static class MaterialColorAudit {
  static string Arg(string key){var a=Environment.GetCommandLineArgs();int i=Array.IndexOf(a,key);if(i<0||i+1>=a.Length)throw new Exception("Missing "+key);return a[i+1];}
  public static void Run(){
   string path=Arg("--audit-avatar"),output=Arg("--audit-output");Directory.CreateDirectory(output);
   if(QualitySettings.activeColorSpace==ColorSpace.Linear)ColorTransferChecks.Run();
   EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
   AssetBundle bundle=null;GameObject avatar=null;
   try {
    using(var z=ZipFile.OpenRead(path))using(var s=z.GetEntry("avatar.bundle").Open())using(var m=new MemoryStream()){s.CopyTo(m);bundle=AssetBundle.LoadFromMemory(m.ToArray());}
    if(!bundle)throw new Exception("Bundle load failed");
    avatar=UnityEngine.Object.Instantiate(bundle.LoadAsset<GameObject>("avatar"));
    var animator=avatar.GetComponent<Animator>();animator.enabled=false;
    var report=new StringBuilder("ColorSpace="+QualitySettings.activeColorSpace+"\n");
    foreach(var r in avatar.GetComponentsInChildren<Renderer>(true))foreach(var m in r.sharedMaterials){
     if(!m)continue;report.AppendLine(AnimationUtility.CalculateTransformPath(r.transform,avatar.transform)+" | "+m.name+" | "+m.shader.name+" | supported="+m.shader.isSupported);
     foreach(string prop in new[]{"_Color","_MainTexHSVG","_EmissionColor","_ShadowColor","_MatCapColor","_ReflectionColor","_ReflectionCubeColor"})if(m.HasProperty(prop))report.AppendLine(prop+"="+m.GetVector(prop).ToString("F5"));
    }
    foreach(var material in bundle.LoadAllAssets<Material>()){
     report.AppendLine("Material asset: "+material.name);
     foreach(string prop in new[]{"_Metallic","_Smoothness","_UseReflection","_ApplySpecular","_UseMatCap","_UseEmission"})if(material.HasProperty(prop))report.AppendLine(prop+"="+material.GetFloat(prop));
     foreach(string prop in material.GetTexturePropertyNames()){var tex=material.GetTexture(prop);if(tex)report.AppendLine(prop+"="+tex.name+" "+tex.width+"x"+tex.height);}
    }
    File.WriteAllText(Path.Combine(output,"materials.txt"),report.ToString());
    var camera=new GameObject("Audit Camera").AddComponent<Camera>();camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;camera.nearClipPlane=.01f;camera.farClipPlane=100;camera.fieldOfView=35;camera.allowHDR=false;
    var light=new GameObject("Key Light").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1;light.transform.rotation=Quaternion.Euler(35,-145,0);
    RenderSettings.ambientLight=new Color(.65f,.65f,.65f);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;
    var head=animator.GetBoneTransform(HumanBodyBones.Head);Vector3 center=head.position;
    foreach(float distance in new[]{1.55f,.65f}){
     camera.transform.position=center+new Vector3(0,0,distance);camera.transform.LookAt(center);
     var rt=new RenderTexture(1280,1280,24,RenderTextureFormat.ARGB32);rt.antiAliasing=4;rt.Create();camera.targetTexture=rt;camera.Render();
     var old=RenderTexture.active;RenderTexture.active=rt;var image=new Texture2D(rt.width,rt.height,TextureFormat.RGBA32,false);image.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0);image.Apply();
     File.WriteAllBytes(Path.Combine(output,"avatar-"+distance.ToString(System.Globalization.CultureInfo.InvariantCulture)+".png"),image.EncodeToPNG());
     RenderTexture.active=old;camera.targetTexture=null;UnityEngine.Object.DestroyImmediate(image);rt.Release();UnityEngine.Object.DestroyImmediate(rt);
    }
    Debug.Log("TANAKACAP_MATERIAL_COLOR_AUDIT_OK "+QualitySettings.activeColorSpace);
   }finally{if(avatar)UnityEngine.Object.DestroyImmediate(avatar);if(bundle)bundle.Unload(true);}
  }
 }
}
