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
    var chainRoot=new GameObject("Chain");chainRoot.transform.SetParent(original.transform);
    var accessory=new GameObject("Accessory");accessory.transform.SetParent(chainRoot.transform);accessory.transform.localPosition=Vector3.up;
    var tip=new GameObject("Tip");tip.transform.SetParent(accessory.transform);tip.transform.localPosition=Vector3.up;
    var roots=new System.Collections.Generic.HashSet<string>{"Chain","Chain/Accessory"};
    var human=new System.Collections.Generic.HashSet<Transform>();
    var outer=new SecondaryChain{root="Chain",endpointPosition=Vector3.up};
    var inner=new SecondaryChain{root="Chain/Accessory",endpointPosition=Vector3.up};
    var outerBones=SecondaryMotionExporter.CollectSegments(chainRoot.transform,original.transform,outer,roots,human,warnings);
    var innerBones=SecondaryMotionExporter.CollectSegments(accessory.transform,original.transform,inner,roots,human,warnings);
    Require(outerBones.Count==1&&outerBones[0].Item1==chainRoot.transform&&outerBones[0].Item2==Vector3.up,"Parent retains its segment to child boundary");
    Require(innerBones.Count==2&&innerBones[0].Item1==accessory.transform&&innerBones[1].Item1==tip.transform,"Accessory retains its complete dedicated chain");
    roots.Remove("Chain/Accessory");
    Require(SecondaryMotionExporter.CollectSegments(chainRoot.transform,original.transform,outer,roots,human,warnings).Count==3,"Disabled/absent child PhysBone must not truncate parent");
    outer.ignored=new[]{"Chain/Accessory"};
    Require(SecondaryMotionExporter.CollectSegments(chainRoot.transform,original.transform,outer,roots,human,warnings).Count==1,"Authored ignore subtree must stay excluded");
    Debug.Log("TANAKACAP_SECONDARY_CONSTRAINT_CHECKS_OK");
   } finally {if(copy)UnityEngine.Object.DestroyImmediate(copy);UnityEngine.Object.DestroyImmediate(original);}
  }
  static void Require(bool value,string message){if(!value)throw new Exception(message);}
 }
}
