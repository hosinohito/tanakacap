// Development-only Editor comparison. No VRChat SDK shipped with TanakaCap.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using TanakaCap;
using TanakaCap.Editor;
public static class PhysReferenceSetup {
 public static void Run(){
  EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
  var source=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/HAOLAN/Phys_Haolan.prefab");
  if(!source)throw new Exception("Missing source prefab");
  var reference=UnityEngine.Object.Instantiate(source);reference.name="Reference";reference.SetActive(false);
  var independent=UnityEngine.Object.Instantiate(source);independent.name="Independent";independent.SetActive(false);
  var warnings=new List<string>();
  var data=SecondaryMotionExporter.Collect(source,independent,warnings);
  int phys=reference.GetComponentsInChildren<Component>(true).Count(c=>c&&c.GetType().Name=="VRCPhysBone");
  if(phys==0)throw new Exception("Reference has no real SDK PhysBones");
  foreach(var root in new[]{reference,independent}){
   foreach(var c in root.GetComponentsInChildren<Animator>(true))c.enabled=false;
   foreach(var c in root.GetComponentsInChildren<Renderer>(true))c.enabled=false;
  }
  foreach(var c in independent.GetComponentsInChildren<Component>(true))
   if(c && c.GetType().Namespace!=null && c.GetType().Namespace.StartsWith("VRC"))UnityEngine.Object.DestroyImmediate(c);
  var solver=independent.AddComponent<SecondaryMotion>();solver.Initialize(data,independent.GetComponent<Animator>());
  var driver=new GameObject("Comparison").AddComponent<PhysReferenceDrive>();
  driver.heads=new[]{reference.GetComponent<Animator>().GetBoneTransform(HumanBodyBones.Head),independent.GetComponent<Animator>().GetBoneTransform(HumanBodyBones.Head)};
  driver.torsos=new[]{reference.GetComponent<Animator>().GetBoneTransform(HumanBodyBones.Chest),independent.GetComponent<Animator>().GetBoneTransform(HumanBodyBones.Chest)};
  var record=driver.gameObject.AddComponent<PhysReferenceRecord>();record.original=reference.transform;record.independent=independent.transform;record.dataJson=JsonUtility.ToJson(data);
  File.WriteAllText(Path.GetFullPath("../manifest.json"),JsonUtility.ToJson(data,true));
  File.WriteAllLines(Path.GetFullPath("../warnings.txt"),warnings);
  reference.SetActive(true);independent.SetActive(true);
  EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(),"Assets/Comparison/Compare.unity");
  Debug.Log("TANAKACAP_PHYS_REFERENCE_READY sdkPhysBones="+phys);
  EditorApplication.isPlaying=true;
 }
}
