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
    Debug.Log("TANAKACAP_MATERIAL_FALLBACK_CHECKS_OK");
   }finally{UnityEngine.Object.DestroyImmediate(root);if(material)UnityEngine.Object.DestroyImmediate(material);}
  }
 }
}
