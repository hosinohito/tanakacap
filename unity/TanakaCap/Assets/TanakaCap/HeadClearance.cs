using System;
using System.Collections.Generic;
using UnityEngine;

namespace TanakaCap
{
    // A fitted, rotating proxy, not mesh contact or finger collision simulation.
    public sealed class HeadClearance
    {
        public Vector3 centerLocal,radii;
        public string source;

        public static HeadClearance Fit(Transform root,Transform head,Transform leftEye,Transform rightEye,
                                        SkinnedMeshRenderer[] renderers)
        {
            float eyeSpan=leftEye && rightEye?Vector3.Distance(leftEye.position,rightEye.position):.08f;
            eyeSpan=Mathf.Clamp(eyeSpan,.025f,.25f);
            var anchor=leftEye && rightEye?(leftEye.position+rightEye.position)*.5f-root.forward*eyeSpan*.45f:
                head.position+root.up*eyeSpan;
            var best=new List<Vector3>();string selected="eye-scaled fallback";bool expressive=false;
            foreach(var renderer in renderers)
            {
                var mesh=renderer.sharedMesh;
                if(!mesh || !mesh.isReadable)continue;
                int headIndex=Array.IndexOf(renderer.bones,head);
                if(headIndex<0)continue;
                var weights=mesh.boneWeights;if(weights.Length!=mesh.vertexCount)continue;
                var baked=new Mesh();renderer.BakeMesh(baked);var vertices=baked.vertices;
                var points=new List<Vector3>();
                for(int i=0;i<vertices.Length;i++)
                {
                    var w=weights[i];float weight=(w.boneIndex0==headIndex?w.weight0:0)+(w.boneIndex1==headIndex?w.weight1:0)+
                        (w.boneIndex2==headIndex?w.weight2:0)+(w.boneIndex3==headIndex?w.weight3:0);
                    if(weight<.5f)continue;
                    var p=Quaternion.Inverse(root.rotation)*(renderer.transform.TransformPoint(vertices[i])-anchor);
                    // Exclude long hair, hats, neck and large ears from the fit.
                    if(Mathf.Abs(p.x)<eyeSpan*1.8f && Mathf.Abs(p.y)<eyeSpan*2 && Mathf.Abs(p.z)<eyeSpan*2)
                        points.Add(p);
                }
                UnityEngine.Object.Destroy(baked);
                bool hasExpressions=mesh.blendShapeCount>0;
                if(points.Count>=100 && ((!expressive && hasExpressions) || (expressive==hasExpressions && points.Count>best.Count)))
                {best=points;selected=renderer.name;expressive=hasExpressions;}
            }
            Vector3 center=anchor,axes=new Vector3(.95f,1.35f,1.15f)*eyeSpan;
            if(best.Count>=100)
            {
                Vector3 low=Vector3.zero,high=Vector3.zero;
                for(int axis=0;axis<3;axis++)
                {
                    var values=best.ConvertAll(p=>p[axis]);values.Sort();
                    low[axis]=values[(int)((values.Count-1)*.01f)];high[axis]=values[(int)((values.Count-1)*.99f)];
                }
                axes=(high-low)*.5f;
                for(int axis=0;axis<3;axis++)axes[axis]=Mathf.Max(eyeSpan*.45f,axes[axis]);
                center=anchor+root.rotation*((high+low)*.5f);
            }
            return new HeadClearance {centerLocal=head.InverseTransformPoint(center),radii=axes,source=selected};
        }

        public static float Level(Vector3 point,Vector3 axes)
        {return point.x*point.x/(axes.x*axes.x)+point.y*point.y/(axes.y*axes.y)+point.z*point.z/(axes.z*axes.z);}

        public static Vector3 Project(Vector3 point,Vector3 axes,float margin=.002f)
        {
            if(axes.x<=0 || axes.y<=0 || axes.z<=0)throw new ArgumentException("Positive head axes required");
            if(Level(point,axes)>=1)return point;
            // Closest point inside an ellipsoid: solve the Lagrange multiplier.
            // Include the singular solution when the nearest shortest axis is zero.
            double[] a={axes.x*axes.x,axes.y*axes.y,axes.z*axes.z};
            double minimum=Math.Min(a[0],Math.Min(a[1],a[2]));
            double[] p={point.x,point.y,point.z};
            int shortest=Array.IndexOf(a,minimum);bool singular=true;double sum=0;
            var result=Vector3.zero;
            for(int i=0;i<3;i++)
            {
                if(Math.Abs(a[i]-minimum)<1e-12){if(Math.Abs(p[i])>1e-12)singular=false;}
                else {result[i]=(float)(a[i]*p[i]/(a[i]-minimum));sum+=result[i]*result[i]/a[i];}
            }
            if(singular && sum<=1)
                result[shortest]=(float)Math.Sqrt(minimum*(1-sum));
            else
            {
                double lo=-minimum,hi=0;
                for(int n=0;n<60;n++)
                {
                    double lambda=(lo+hi)*.5,total=0;
                    for(int i=0;i<3;i++)total+=a[i]*p[i]*p[i]/((a[i]+lambda)*(a[i]+lambda));
                    if(total>1)lo=lambda;else hi=lambda;
                }
                for(int i=0;i<3;i++)result[i]=(float)(a[i]*p[i]/(a[i]+hi));
            }
            var normal=new Vector3(result.x/axes.x/axes.x,result.y/axes.y/axes.y,result.z/axes.z/axes.z).normalized;
            return result+normal*Mathf.Max(0,margin);
        }
    }
}
