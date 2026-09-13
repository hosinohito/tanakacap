using System;
using UnityEngine;
using UnityEngine.Animations;
namespace TanakaCap.Editor {
 public static class SecondaryConstraintChecks {
  public static void Run(){
   var original=new GameObject("ConstraintFixture");GameObject copy=null;
   try {
    var anchor=new GameObject("Anchor");anchor.transform.SetParent(original.transform);
    var bone=new GameObject("Bone");bone.transform.SetParent(original.transform);
    var position=bone.AddComponent<PositionConstraint>();
    position.AddSource(new ConstraintSource{sourceTransform=anchor.transform,weight=1});
    position.constraintActive=true;position.locked=true;position.weight=1;
    var warnings=new System.Collections.Generic.List<string>();
    Require(!SecondaryMotionExporter.ShouldSimulate(bone.transform,Vector3.up,"Bone",warnings)&&warnings.Count==1,"Constraint priority must be reported");
    copy=UnityEngine.Object.Instantiate(original);
    var cloned=copy.transform.Find("Bone").GetComponent<PositionConstraint>();
    Require(cloned.GetSource(0).sourceTransform==copy.transform.Find("Anchor"),"Source references must point into export copy");
    var rotation=bone.AddComponent<RotationConstraint>();
    Require(!SecondaryMotionExporter.ShouldSimulate(bone.transform,Vector3.up,"Bone",warnings),"Rotation conflict must not enter solver");
    int warningCount=warnings.Count;
    Require(!SecondaryMotionExporter.ShouldSimulate(bone.transform,Vector3.zero,"Bone",warnings)&&warnings.Count==warningCount,"Unsimulated endpoint must not produce a false overlap warning");
    UnityEngine.Object.DestroyImmediate(rotation);
    var parent=bone.AddComponent<ParentConstraint>();
    Require(!SecondaryMotionExporter.ShouldSimulate(bone.transform,Vector3.up,"Bone",warnings)&&warnings[warnings.Count-1].Contains("ParentConstraint"),"Parent constraint must be preserved and reported");
    var child=new GameObject("UnconstrainedChild");child.transform.SetParent(bone.transform);
    Require(SecondaryMotionExporter.ShouldSimulate(child.transform,Vector3.up,"Bone/UnconstrainedChild",warnings),"Descendant must remain eligible for secondary motion");
    Require(position.sourceCount==1&&position.GetSource(0).sourceTransform==anchor.transform&&position.constraintActive,"Original constraint must stay intact");
    Debug.Log("TANAKACAP_SECONDARY_CONSTRAINT_CHECKS_OK");
   } finally {if(copy)UnityEngine.Object.DestroyImmediate(copy);UnityEngine.Object.DestroyImmediate(original);}
  }
  static void Require(bool value,string message){if(!value)throw new Exception(message);}
 }
}
