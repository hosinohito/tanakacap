using System;
using UnityEditor;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class ColorTransferChecks {
  public static void Run(){
   if(QualitySettings.activeColorSpace!=ColorSpace.Linear)throw new Exception("Color transfer checks require Linear");
   var source=new Texture2D(16,16,TextureFormat.RGBA32,false,false);
   var target=new RenderTexture(16,16,0,RenderTextureFormat.ARGB32);target.Create();
   var sample=new Color32(192,96,32,128);var pixels=new Color32[256];for(int i=0;i<pixels.Length;i++)pixels[i]=sample;source.SetPixels32(pixels);source.Apply();
   var previous=RenderTexture.active;bool srgb=GL.sRGBWrite;
   try {
    if(!target.sRGB)throw new Exception("Output must encode sRGB in Linear rendering");
    Check(source,target,"Assets/TanakaCap/EdgeAntialiasing.shader",0,sample);
    Check(source,target,"Assets/TanakaCap/PreviewComposite.shader",0,new Color32(192,96,32,255));
    Check(source,target,"Packages/jp.keijiro.klak.spout/Runtime/Internal/Blit.shader",0,sample);
    Debug.Log("TANAKACAP_COLOR_TRANSFER_CHECKS_OK edge/preview/spout RGB and alpha");
   }finally{GL.sRGBWrite=srgb;RenderTexture.active=previous;target.Release();UnityEngine.Object.DestroyImmediate(target);UnityEngine.Object.DestroyImmediate(source);}
  }
  static void Check(Texture source,RenderTexture target,string path,int pass,Color32 expected){
   var shader=AssetDatabase.LoadAssetAtPath<Shader>(path);if(!shader||!shader.isSupported)throw new Exception("Color check shader missing: "+path);
   var material=new Material(shader);var read=new Texture2D(16,16,TextureFormat.RGBA32,false);
   try {
    if(path.Contains("PreviewComposite")){material.SetColor("_Background",Color.black);material.SetFloat("_OutputAspect",1);material.SetFloat("_ViewAspect",1);}
    GL.sRGBWrite=true;Graphics.Blit(source,target,material,pass);RenderTexture.active=target;read.ReadPixels(new Rect(0,0,16,16),0,0);read.Apply();var actual=(Color32)read.GetPixel(8,8);
    if(Math.Abs(actual.r-expected.r)>2||Math.Abs(actual.g-expected.g)>2||Math.Abs(actual.b-expected.b)>2||Math.Abs(actual.a-expected.a)>1)throw new Exception("Color transfer mismatch "+path+" expected="+expected+" actual="+actual);
   }finally{UnityEngine.Object.DestroyImmediate(read);UnityEngine.Object.DestroyImmediate(material);}
  }
 }
}
