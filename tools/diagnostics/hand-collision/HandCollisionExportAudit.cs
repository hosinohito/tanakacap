using System;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using TanakaCap;
using TanakaCap.Editor;
public static class HandCollisionExportAudit {
 static void Require(bool ok,string message){if(!ok)throw new Exception(message);}
 public static void Run(){
  foreach(var id in AssetDatabase.FindAssets("t:Prefab",new[]{"Assets/forExports"})){
   var path=AssetDatabase.GUIDToAssetPath(id);var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(path);
   if(!prefab.GetComponent<Animator>())continue;
   var copy=UnityEngine.Object.Instantiate(prefab);
   try{
    var warnings=new List<string>();var data=SecondaryMotionExporter.Collect(copy,copy,warnings);
    Require(data.colliders.Count(c=>c.standardHand)==10,"Expected ten standard hand/finger colliders");
    var pb=copy.GetComponentsInChildren<Component>(true).First(c=>c&&c.GetType().Name=="VRCPhysBone");
    var so=new SerializedObject(pb);var enabled=so.FindProperty("allowCollision");var self=so.FindProperty("collisionFilter.allowSelf");
    string pbId=pb.GetInstanceID().ToString();
    for(int mode=0;mode<3;mode++)foreach(bool allow in new[]{false,true}){
     enabled.intValue=mode;self.boolValue=allow;so.ApplyModifiedPropertiesWithoutUndo();
     var variant=SecondaryMotionExporter.Collect(copy,copy,new List<string>());
     var chain=variant.chains.First(c=>c.sourceId==pbId);
     bool expected=mode==1||(mode==2&&allow);
     Require(chain.collisionAllowSelf==expected,"Collision permission mapping");
     Require(chain.colliders.Count(i=>variant.colliders[i].standardHand)==(expected?10:0),"Permission must gate only standard hands");
     Require(chain.colliders.Count(i=>!variant.colliders[i].standardHand)==data.chains.First(c=>c.sourceId==pbId).colliders.Count(i=>!data.colliders[i].standardHand),"Explicit colliders must remain");
    }
    var descriptor=copy.GetComponents<Component>().First(c=>c&&c.GetType().Name=="VRCAvatarDescriptor");
    var ds=new SerializedObject(descriptor);var state=ds.FindProperty("collider_handL.state");
    var field=descriptor.GetType().GetField("collider_handL");var config=field.GetValue(descriptor);var stateType=config.GetType().GetField("state").FieldType;
    state.intValue=Convert.ToInt32(Enum.Parse(stateType,"Disabled"));ds.ApplyModifiedPropertiesWithoutUndo();
    Require(StandardHandColliderExporter.Collect(copy,new List<string>()).Count==9,"Disabled palm omitted");
    state.intValue=Convert.ToInt32(Enum.Parse(stateType,"Custom"));ds.FindProperty("collider_handL.radius").floatValue=.0123f;ds.FindProperty("collider_handL.height").floatValue=.0678f;ds.ApplyModifiedPropertiesWithoutUndo();
    var custom=StandardHandColliderExporter.Collect(copy,new List<string>()).First(c=>c.sourceId=="collider_handL");
    Require(custom.radius==.0123f&&custom.height==.0678f&&custom.sourceState=="Custom","Custom dimensions preserved");
    UnityEngine.Object.DestroyImmediate(copy);copy=UnityEngine.Object.Instantiate(prefab);
    data=SecondaryMotionExporter.Collect(copy,copy,new List<string>());
    System.IO.File.WriteAllText("../export-audit.json",JsonUtility.ToJson(data,true));
    Debug.Log("HAND_AUDIT_OK hands=10 permissionCases=6 custom=ok disabled=ok");
    AvatarExporter.Export(copy,"../hand-collision.tcap");
   }finally{if(copy)UnityEngine.Object.DestroyImmediate(copy);}
  }
 }
}
