using System;
using System.Collections.Generic;
using UnityEngine;

namespace TanakaCap
{
    // Parent-relative elbow swing with a transported upper-arm bend reference.
    public sealed class ArmRotationFrame
    {
        readonly Vector3 upperAxis,lowerAxis,hinge;
        readonly Quaternion upperFrameInverse,straightElbow;
        Vector3 previousUpper,normal;
        public string source;

        public ArmRotationFrame(Vector3 upperAxis,Vector3 lowerAxis,Vector3 upperHinge,Vector3 lowerHinge,
                                Quaternion initialUpper,string source)
        {
            this.upperAxis=upperAxis.normalized;this.lowerAxis=lowerAxis.normalized;
            hinge=Vector3.ProjectOnPlane(upperHinge,this.upperAxis).normalized;
            var lowerNormal=Vector3.ProjectOnPlane(lowerHinge,this.lowerAxis).normalized;
            if(hinge.sqrMagnitude<.5f || lowerNormal.sqrMagnitude<.5f)throw new ArgumentException("Invalid elbow axes");
            var upperFrame=Quaternion.LookRotation(this.upperAxis,hinge);
            upperFrameInverse=Quaternion.Inverse(upperFrame);
            straightElbow=upperFrame*Quaternion.Inverse(Quaternion.LookRotation(this.lowerAxis,lowerNormal));
            previousUpper=initialUpper*this.upperAxis;normal=initialUpper*hinge;this.source=source;
        }

        public void Solve(Vector3 upperDirection,Vector3 lowerDirection,float dt,out Quaternion upper,out Quaternion lower)
        {
            var u=upperDirection.normalized;var l=lowerDirection.normalized;
            var transported=Quaternion.FromToRotation(previousUpper,u)*normal;
            transported=Vector3.ProjectOnPlane(transported,u).normalized;
            var observed=Vector3.Cross(u,l);
            float bend=Vector3.Angle(u,l);
            // Near extension the cross product carries little directional evidence.
            float confidence=Mathf.SmoothStep(0,1,Mathf.InverseLerp(5,20,bend));
            if(observed.sqrMagnitude>1e-8f)
            {
                float angle=Vector3.SignedAngle(transported,observed.normalized,u);
                float step=Mathf.Clamp(angle*confidence,-540*Mathf.Max(0,dt),540*Mathf.Max(0,dt));
                transported=Quaternion.AngleAxis(step,u)*transported;
            }
            normal=transported;previousUpper=u;
            upper=Quaternion.LookRotation(u,normal)*upperFrameInverse;
            // The lower arm inherits the upper reference; never independently
            // swing it from a fixed world T-pose. Preserve the solved endpoint.
            lower=Quaternion.FromToRotation(u,l)*upper*straightElbow;
        }

        public void Rest(Vector3 u,Vector3 l,out Quaternion upper,out Quaternion lower)
        {
            u.Normalize();l.Normalize();var n=Vector3.Cross(u,l).normalized;
            if(n.sqrMagnitude<.5f)n=Vector3.ProjectOnPlane(normal,u).normalized;
            upper=Quaternion.LookRotation(u,n)*upperFrameInverse;
            lower=Quaternion.FromToRotation(u,l)*upper*straightElbow;
        }

        public static ArmRotationFrame Fit(Animator animator,Transform root,Transform upper,Transform lower,Transform hand,
                                          Vector3 upperAxis,Vector3 lowerAxis,bool isLeft)
        {
            var a=(lower.position-upper.position).normalized;var b=(hand.position-lower.position).normalized;
            var n=Vector3.Cross(a,b);
            if(n.magnitude>.09f)
                return new ArmRotationFrame(upperAxis,lowerAxis,upper.InverseTransformDirection(n),lower.InverseTransformDirection(n),
                    Quaternion.Inverse(root.rotation)*upper.rotation,"authored bent bones");
            // Sample a transform-only temporary copy: no scripts, renderers,
            // animation controllers, or writes to the original skeleton/assets.
            var mapping=new Dictionary<Transform,Transform>();
            Transform Copy(Transform original,Transform parent)
            {
                var copy=new GameObject(original.name).transform;copy.SetParent(parent,false);
                copy.localPosition=original.localPosition;copy.localRotation=original.localRotation;copy.localScale=original.localScale;
                mapping.Add(original,copy);
                foreach(Transform child in original)Copy(child,copy);
                return copy;
            }
            var skeleton=Copy(animator.transform,null);skeleton.gameObject.hideFlags=HideFlags.HideAndDontSave;
            skeleton.position=Vector3.zero;skeleton.rotation=Quaternion.identity;
            try
            {
                using(var handler=new HumanPoseHandler(animator.avatar,skeleton))
                {
                    var pose=new HumanPose();handler.GetHumanPose(ref pose);
                    int muscle=Array.IndexOf(HumanTrait.MuscleName,(isLeft?"Left":"Right")+" Forearm Stretch");
                    if(muscle<0)throw new Exception("Humanoid forearm stretch muscle unavailable");
                    pose.muscles[muscle]=-.5f;handler.SetHumanPose(ref pose);
                    var u=mapping[upper];var l=mapping[lower];var h=mapping[hand];
                    n=Vector3.Cross((l.position-u.position).normalized,(h.position-l.position).normalized);
                    if(n.magnitude<.05f)throw new Exception("Humanoid elbow calibration remained straight");
                    return new ArmRotationFrame(upperAxis,lowerAxis,u.InverseTransformDirection(n),l.InverseTransformDirection(n),
                        Quaternion.Inverse(root.rotation)*upper.rotation,"Humanoid temporary skeleton");
                }
            }
            finally {UnityEngine.Object.DestroyImmediate(skeleton.gameObject);}
        }
    }
}
