using System;
using System.Linq;
using UnityEditor;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class ShaderCompatibilityChecks {
  public static void Run(){
   const string path="Assets/TanakaCapExport-shadercheck/fixed.shader";
   AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
   var shader=AssetDatabase.LoadAssetAtPath<Shader>(path);
   if(!shader)throw new Exception("Shader fixture not prepared");
   var material=new Material(shader);
   try {
    bool pass=material.SetPass(0);
    var errors=ShaderUtil.GetShaderMessages(shader).Where(m=>m.severity.ToString()=="Error").ToArray();
    foreach(var error in errors)Debug.LogError(error.message+" line="+error.line);
    if(!pass||!shader.isSupported||errors.Length>0)throw new Exception("Corrected shader unsupported: "+SystemInfo.graphicsDeviceType);
    Debug.Log("TANAKACAP_SHADER_COMPAT_OK "+shader.name+" "+SystemInfo.graphicsDeviceType);
   }finally{UnityEngine.Object.DestroyImmediate(material);}
   BuildRelease.BuildExporter();
  }
 }
}
