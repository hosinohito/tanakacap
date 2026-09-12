using System;
using UnityEngine;
namespace TanakaCap {
 public static class BrowShapeSplit {
  public static void Generate(SkinnedMeshRenderer[] meshes,Transform leftEye,Transform rightEye,Func<SkinnedMeshRenderer,Mesh> clone){
   if(!leftEye||!rightEye){Debug.LogWarning("Brow split skipped: eye bones required for anatomical sides");return;}
   Vector3 axis=leftEye.position-rightEye.position,center=(leftEye.position+rightEye.position)*.5f;
   float span=axis.magnitude;if(span<.001f)return;axis/=span;
   foreach(var renderer in meshes){
    var original=renderer.sharedMesh;if(!original||!original.isReadable)continue;
    // Avoid interpreting unrelated one-character shapes as eyebrows.
    bool mmd=original.GetBlendShapeIndex("困る")>=0||original.GetBlendShapeIndex("真面目")>=0;
    if(!mmd&&original.GetBlendShapeIndex("browInnerUp")<0)continue;
    var vertices=original.vertices;
    string[] sources={original.GetBlendShapeIndex("browInnerUp")>=0?"browInnerUp":"上",mmd?"下":"",mmd?"困る":"",mmd?"怒り":""},labels={"Up","Down","Sad","Angry"};
    for(int kind=0;kind<sources.Length;kind++){
     int source=original.GetBlendShapeIndex(sources[kind]);if(source<0)continue;
     var mesh=clone(renderer);
     for(int side=0;side<2;side++){
      string name="TC_Brow"+(side==0?"Left":"Right")+labels[kind];
      if(mesh.GetBlendShapeIndex(name)>=0)continue;
      for(int frame=0;frame<original.GetBlendShapeFrameCount(source);frame++){
       var d=new Vector3[vertices.Length];var n=new Vector3[vertices.Length];var t=new Vector3[vertices.Length];
       original.GetBlendShapeFrameVertices(source,frame,d,n,t);
       float movement=0;
       for(int i=0;i<d.Length;i++){
        float coordinate=Vector3.Dot(renderer.transform.TransformPoint(vertices[i])-center,axis);
        float left=Mathf.SmoothStep(0,1,Mathf.Clamp01(.5f+coordinate/(span*.2f)));
        float weight=side==0?left:1-left;d[i]*=weight;n[i]*=weight;t[i]*=weight;movement+=d[i].sqrMagnitude;
       }
       if(movement>1e-14f)mesh.AddBlendShapeFrame(name,original.GetBlendShapeFrameWeight(source,frame),d,n,t);
      }
     }
    }
   }
  }
 }
}
