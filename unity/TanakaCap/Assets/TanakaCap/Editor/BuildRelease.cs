using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class BuildRelease {
  public static void Build(){
   FaceExpressionChecks.Run();
   var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
   var camera=new GameObject("Output Camera").AddComponent<Camera>();camera.tag="MainCamera";
   camera.transform.position=new Vector3(0,1.05f,1.55f);camera.transform.LookAt(new Vector3(0,1.05f,0));
   camera.fieldOfView=35;camera.nearClipPlane=.01f;camera.farClipPlane=30;
   camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.06f,.07f,.09f);
   var output=camera.gameObject.AddComponent<AlphaOutput>();
   output.edgeShader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/TanakaCap/EdgeAntialiasing.shader");
   output.previewShader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/TanakaCap/PreviewComposite.shader");
   output.resources=AssetDatabase.LoadAssetAtPath<Klak.Spout.SpoutResources>("Packages/jp.keijiro.klak.spout/Editor/SpoutResources.asset");
   if(!output.edgeShader||!output.previewShader||!output.resources)throw new Exception("Release rendering resources missing");
   new GameObject("Avatar Loader").AddComponent<AvatarPackageLoader>();
   var light=new GameObject("Key Light").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1;light.transform.rotation=Quaternion.Euler(35,-145,0);
   RenderSettings.ambientLight=new Color(.65f,.65f,.65f);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;
   QualitySettings.vSyncCount=0;PlayerSettings.enableFrameTimingStats=true;
   PlayerSettings.companyName="tanakacap";PlayerSettings.productName="TanakaCap";PlayerSettings.defaultScreenWidth=1280;PlayerSettings.defaultScreenHeight=720;
   PlayerSettings.fullScreenMode=FullScreenMode.Windowed;PlayerSettings.runInBackground=true;
   Directory.CreateDirectory("Assets/TanakaCap/Scenes");
   const string scenePath="Assets/TanakaCap/Scenes/Release.unity";EditorSceneManager.SaveScene(scene,scenePath);
   Directory.CreateDirectory("../../builds/release-player");
   AssetDatabase.ExportPackage(new[]{"Assets/TanakaCap/LICENSE.txt","Assets/TanakaCap/AvatarPackage.cs","Assets/TanakaCap/FaceExpressions.cs","Assets/TanakaCap/Editor/FaceProfileExporter.cs","Assets/TanakaCap/Editor/AvatarExporter.cs","Assets/TanakaCap/Editor/SecondaryMotionExporter.cs"},"../../builds/release-player/TanakaCapExporter.unitypackage",ExportPackageOptions.Default);
   var result=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{scenePath},locationPathName="../../builds/release-player/TanakaCap.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});
   if(result.summary.result!=UnityEditor.Build.Reporting.BuildResult.Succeeded)throw new Exception("Release Player build failed");
   Debug.Log("TANAKACAP_RELEASE_BUILD_OK no embedded avatar");
  }
 }
}
