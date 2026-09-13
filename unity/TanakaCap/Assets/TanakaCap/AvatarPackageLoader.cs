using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Collections;
using System.Security.Cryptography;
using UnityEngine;
namespace TanakaCap {
 public class AvatarPackageLoader : MonoBehaviour {
  string path,error="";GameObject avatar;AssetBundle bundle;bool loading;bool show;
  IEnumerator Start(){
   var args=Environment.GetCommandLineArgs();int i=Array.IndexOf(args,"--avatar");
   path=i>=0&&i+1<args.Length?args[i+1]:Path.Combine(Directory.GetParent(Application.dataPath).FullName,"avatars/haolan.tcap");
   yield return Load();
  }
  IEnumerator Load(){
   loading=true;error="";
   if(avatar){Destroy(avatar);yield return null;}
   if(bundle){bundle.Unload(true);bundle=null;}
   try {
    using(var zip=ZipFile.OpenRead(path)) {
     if(zip.Entries.Count!=2||zip.Entries.Count(x=>x.FullName=="manifest.json")!=1||zip.Entries.Count(x=>x.FullName=="avatar.bundle")!=1)throw new Exception("Invalid avatar package entries.");
     var metadata=zip.GetEntry("manifest.json");var entry=zip.GetEntry("avatar.bundle");
     if(metadata.Length>1024*1024||entry.Length>1024L*1024*1024)throw new Exception("Avatar package exceeds supported size.");
     AvatarPackageManifest m;using(var reader=new StreamReader(metadata.Open()))m=JsonUtility.FromJson<AvatarPackageManifest>(reader.ReadToEnd());
     if(m==null||m.formatVersion!=1||m.platform!="StandaloneWindows64"||(m.profile!="haolan-1.6"&&m.profile!="existing-expressions-1")||m.unityVersion!=Application.unityVersion||m.prefab!="avatar")throw new Exception("Unsupported avatar format, profile, platform or Unity version.");
     // Allocate exactly once. MemoryStream growth plus ToArray kept ~64 MB
     // of transient managed buffers alive after loading this ~26 MB package.
     byte[] bytes=new byte[checked((int)entry.Length)];
     using(var input=entry.Open()) {
      int offset=0;
      while(offset<bytes.Length) {
       int read=input.Read(bytes,offset,bytes.Length-offset);
       if(read==0)throw new EndOfStreamException("Truncated avatar bundle.");
       offset+=read;
      }
      if(input.ReadByte()!=-1)throw new Exception("Avatar bundle length mismatch.");
     }
     string hash;using(var sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();
     if(hash!=m.bundleSha256)throw new Exception("Avatar checksum mismatch.");
     bundle=AssetBundle.LoadFromMemory(bytes);bytes=null;if(!bundle)throw new Exception("Cannot load avatar bundle.");
     var prefab=bundle.LoadAsset<GameObject>(m.prefab);if(!prefab)throw new Exception("Avatar prefab missing.");
     avatar=Instantiate(prefab);avatar.name=m.displayName;
     var animator=avatar.GetComponent<Animator>();if(!animator||!animator.isHuman)throw new Exception("Humanoid avatar missing.");
     foreach(var r in avatar.GetComponentsInChildren<Renderer>(true))foreach(var mat in r.sharedMaterials)
      if(!mat||!mat.shader||!mat.shader.isSupported||mat.shader.name=="Hidden/InternalErrorShader")throw new Exception("Unsupported avatar material: renderer="+r.name+", material="+(mat?mat.name:"<missing>")+", shader="+(mat&&mat.shader?mat.shader.name:"<missing>")+", supported="+(mat&&mat.shader&&mat.shader.isSupported)+", graphics="+SystemInfo.graphicsDeviceType);
     animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
     var driver=avatar.AddComponent<AvatarDriver>();driver.animator=animator;driver.faceProfile=m.faceProfile;
     if(m.secondaryPhysics!=null && m.secondaryPhysics.bones.Length>0)avatar.AddComponent<SecondaryMotion>().Initialize(m.secondaryPhysics,animator);
     if(Array.IndexOf(Environment.GetCommandLineArgs(),"--secondary-check")>=0)avatar.AddComponent<SecondaryMotionProbe>();
     Debug.Log("TANAKACAP_PACKAGE_LOADED "+Path.GetFullPath(path)+" sha256="+hash);
     foreach(var warning in m.warnings??new string[0])Debug.LogWarning("Avatar package: "+warning);
    }
   }catch(Exception e){
    error=e.Message;Debug.LogError("TANAKACAP_PACKAGE_ERROR "+e);
    if(avatar)Destroy(avatar);if(bundle){bundle.Unload(true);bundle=null;}
    show=true;if(Application.isBatchMode){var output=FindObjectOfType<AlphaOutput>();if(output)output.exitCode=2;Application.Quit(2);}
   }
   loading=false;
  }
  void Update(){if(Input.GetKeyDown(KeyCode.F5))show=!show;}
  void OnGUI(){if(!show)return;GUILayout.BeginArea(new Rect(12,80,700,140),GUI.skin.box);GUILayout.Label("Avatar file (.tcap) / F5");path=GUILayout.TextField(path??"");GUI.enabled=!loading;if(GUILayout.Button("Load avatar"))StartCoroutine(Load());GUI.enabled=true;GUILayout.Label(error);GUILayout.EndArea();}
 }
}
