using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class AvatarShaderCompatibility {
  public const string LegacyAudioLink="Assets/AudioLink/Shaders/AudioLink.cginc";
  public const string PackageAudioLink="Packages/com.llealloo.audiolink/Runtime/Shaders/AudioLink.cginc";
  public static void Prepare(GameObject copy,string scratch,List<string> warnings){
   var shaders=new Dictionary<Shader,Shader>();var materials=new Dictionary<Material,Material>();
   foreach(var renderer in copy.GetComponentsInChildren<Renderer>(true)){
    var slots=renderer.sharedMaterials;
    for(int i=0;i<slots.Length;i++){
     var original=slots[i];if(!original||!original.shader)continue;
     if(materials.TryGetValue(original,out var reused)){slots[i]=reused;continue;}
     var shader=original.shader;
     if(!shaders.TryGetValue(shader,out var replacement)){
      replacement=shader;string path=AssetDatabase.GetAssetPath(shader);
      if(path.EndsWith(".shader",StringComparison.OrdinalIgnoreCase)&&!File.Exists(LegacyAudioLink)&&File.Exists(PackageAudioLink)){
       string text=File.ReadAllText(path);string corrected=Rewrite(text,PackageAudioLink);
       if(corrected!=text){
        string generated=scratch+"/AudioLinkCompat-"+Guid.NewGuid().ToString("N")+".shader";
        File.WriteAllText(generated,corrected);AssetDatabase.ImportAsset(generated,ImportAssetOptions.ForceSynchronousImport);
        replacement=AssetDatabase.LoadAssetAtPath<Shader>(generated);
        if(!replacement||ShaderUtil.ShaderHasError(replacement)){
         replacement=shader;warnings.Add("AudioLink compatibility shader failed to compile: "+path+". Original preserved; unsupported renderer may be disabled by the Player.");
        }else warnings.Add("Export-only AudioLink include migration: "+path+" : "+LegacyAudioLink+" -> "+PackageAudioLink+". Original shader/material preserved; AudioLink audio input is not supplied by TanakaCap.");
       }
      }
      shaders.Add(shader,replacement);
     }
     if(replacement!=shader){var material=new Material(original);material.shader=replacement;AssetDatabase.CreateAsset(material,scratch+"/Material-"+Guid.NewGuid().ToString("N")+".mat");materials.Add(original,material);slots[i]=material;}
    }
    renderer.sharedMaterials=slots;
   }
  }
  internal static string Rewrite(string text,string include)=>text.Replace("\""+LegacyAudioLink+"\"","\""+include+"\"");
 }
}
