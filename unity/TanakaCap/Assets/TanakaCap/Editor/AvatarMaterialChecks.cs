using System;
using UnityEngine;
namespace TanakaCap.Editor {
 public static class AvatarMaterialChecks {
  public static void Run(){
   var root=new GameObject("MaterialFixture");Material material=null;
   try {
    var valid=new GameObject("Valid");valid.transform.SetParent(root.transform);
    var good=valid.AddComponent<MeshRenderer>();material=new Material(Shader.Find("Unlit/Color"));good.sharedMaterial=material;
    var invalid=new GameObject("Invalid");invalid.transform.SetParent(root.transform);
    var bad=invalid.AddComponent<MeshRenderer>();bad.sharedMaterials=new Material[]{null};
    if(AvatarPackageLoader.DisableUnsupportedRenderers(root)!=1||bad.enabled||!good.enabled||!root.activeSelf)throw new Exception("Material failure must be confined to its renderer");
    if(AvatarPackageLoader.TryInitializeSecondary(root,new SecondaryPhysicsData{version=99},null)||root.GetComponent<SecondaryMotion>()||!good.enabled||!root.activeSelf)throw new Exception("Invalid secondary data must leave avatar usable and remove the incomplete solver");
    var curve=new SecondaryCurve{keys=new[]{
     new SecondaryCurve.Key{time=.0669441223f,value=0},
     new SecondaryCurve.Key{time=.80940938f,value=.26564848f,inSlope=1.2977928f,outSlope=1.2977928f},
     new SecondaryCurve.Key{time=1,value=.41273498f}}};
    float raw=.01f*curve.Build().Evaluate(1f/3);
    if(raw>=0||SecondaryMotion.SampleParameter(.01f,curve,1f/3,0,float.MaxValue,"fixture radius")!=0)throw new Exception("Negative radius interpolation must become zero without rejecting the chain");
    float positive=.01f*curve.Build().Evaluate(2f/3);
    if(SecondaryMotion.SampleParameter(.01f,curve,2f/3,0,float.MaxValue,"fixture radius")!=positive)throw new Exception("Valid curve evaluation must remain unchanged");
    if(!float.IsNaN(SecondaryMotion.SampleParameter(float.NaN,null,0,0,1,"invalid")))throw new Exception("Non-finite input must not be hidden");
    Debug.Log("TANAKACAP_CURVE_BOUND_CHECKS_OK rawRadius="+raw);
    Debug.Log("TANAKACAP_MATERIAL_FALLBACK_CHECKS_OK");
   }finally{UnityEngine.Object.DestroyImmediate(root);if(material)UnityEngine.Object.DestroyImmediate(material);}
  }
 }
}
