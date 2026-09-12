using UnityEngine;
namespace TanakaCap {
 // Existing authored morphs only. No generated meshes or additional inference.
 public sealed class BrowExpressions {
  readonly SkinnedMeshRenderer[] meshes;
  public BrowExpressions(SkinnedMeshRenderer[] renderers){meshes=renderers;}
  bool Set(string name,float value){
   bool found=false;
   foreach(var r in meshes){int i=r.sharedMesh.GetBlendShapeIndex(name);if(i>=0){r.SetBlendShapeWeight(i,Mathf.Clamp01(value)*100);found=true;}}
   return found;
  }
  bool Has(string name){foreach(var r in meshes)if(r.sharedMesh.GetBlendShapeIndex(name)>=0)return true;return false;}
  public void CheckMotion(){
   float[][] saved=new float[meshes.Length][];
   for(int m=0;m<meshes.Length;m++){saved[m]=new float[meshes[m].sharedMesh.blendShapeCount];for(int i=0;i<saved[m].Length;i++)saved[m][i]=meshes[m].GetBlendShapeWeight(i);}
   float change=0;
   try{
    Apply(0,0,0,0);var baseline=new Vector3[meshes.Length][];
    for(int m=0;m<meshes.Length;m++){var mesh=new Mesh();meshes[m].BakeMesh(mesh);baseline[m]=mesh.vertices;Object.Destroy(mesh);}
    Apply(.8f,.8f,.8f,.8f);
    for(int m=0;m<meshes.Length;m++){var mesh=new Mesh();meshes[m].BakeMesh(mesh);var p=mesh.vertices;for(int i=0;i<p.Length;i++)change=Mathf.Max(change,(p[i]-baseline[m][i]).magnitude);Object.Destroy(mesh);}
    if(change<1e-5f)throw new System.Exception("Eyebrow morph did not deform the avatar");
    Debug.Log("TANAKACAP_BROWS_VERIFIED displacement="+change);
   }finally{for(int m=0;m<meshes.Length;m++)for(int i=0;i<saved[m].Length;i++)meshes[m].SetBlendShapeWeight(i,saved[m][i]);}
  }
  public void Apply(float li,float lo,float ri,float ro){
   float up=Mathf.Max(0,(li+lo+ri+ro)*.25f),down=Mathf.Max(0,-(li+lo+ri+ro)*.25f);
   bool inner=Set("browInnerUp",Mathf.Max(0,(li+ri)*.5f));
   bool outerL=Set("browOuterUpLeft",Mathf.Max(0,lo)),outerR=Set("browOuterUpRight",Mathf.Max(0,ro));
   bool downL=Set("browDownLeft",Mathf.Max(0,-(li+lo)*.5f)),downR=Set("browDownRight",Mathf.Max(0,-(ri+ro)*.5f));
   // Bilateral MMD morphs cannot recreate one-sided movements. Use the mean.
   // Do not stack a bilateral fallback over a partly supported ARKit group.
   if(!inner&&!outerL&&!outerR){Set("上",up);Set("困る",Mathf.Max(0,(li-lo+ri-ro)*.25f));}
   if(!downL&&!downR){Set("下",down);Set("怒り",Mathf.Max(0,(lo-li+ro-ri)*.25f));}
  }
 }
}
