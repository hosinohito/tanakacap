using System;
using UnityEngine;

namespace TanakaCap
{
    public partial class AvatarDriver
    {
        void CheckImagePosition()
        {
            var camera=Camera.main;var savedRoot=transform.position;
            bool enabled=followImagePosition,established=imagePositionEstablished;
            var savedImage=imagePosition;
            try
            {
                foreach(float fps in new[]{30f,60f,120f})
                foreach(float depthOffset in new[]{-.2f,0,.2f})
                {
                    transform.position=savedRoot+camera.transform.forward*depthOffset;
                    imagePositionEstablished=false;followImagePosition=true;
                    float depth=camera.WorldToViewportPoint(head.position).z;
                    var packet=new TrackingPacket{faceImagePositionTracked=true,faceImagePosition=new Vector3(.65f,.55f,0)};
                    for(int i=0;i<fps;i++)ApplyImagePosition(packet,true,1/fps);
                    var actual=camera.WorldToViewportPoint(head.position);
                    if(Mathf.Abs(actual.x-.65f)>.001f || Mathf.Abs(actual.y-.55f)>.001f || Mathf.Abs(actual.z-depth)>1e-4f)
                        throw new Exception("Image position changed depth or missed target");
                    var before=transform.position;
                    ApplyImagePosition(new TrackingPacket(),true,1);
                    if(Vector3.Distance(before,transform.position)>1e-5f)throw new Exception("Lost image position snapped");
                    followImagePosition=false;packet.faceImagePosition=Vector3.zero;
                    ApplyImagePosition(packet,true,1);
                    if(Vector3.Distance(before,transform.position)>1e-5f)throw new Exception("Disabled image position moved avatar");
                }
                Debug.Log("TANAKACAP_IMAGE_POSITION_CHECK_OK");
            }
            finally{transform.position=savedRoot;followImagePosition=enabled;imagePositionEstablished=established;imagePosition=savedImage;}
        }

        void CheckDistributedTwist()
        {
            if(legacyArmRotation)return;
            foreach(var arm in new[]{left,right})
            {
                RestoreDistributedTwist(arm);
                var upper=arm.upper.localRotation;var lower=arm.lower.rotation;var hand=arm.hand.rotation;
                float twist=arm.twist,share=arm.upperTwistShare;
                var elbow=arm.lower.position;var wrist=arm.hand.position;
                try
                {
                    arm.twist=150;
                    for(int i=0;i<120;i++)
                    {
                        DistributeArmTwist(arm);
                        if(Vector3.Distance(elbow,arm.lower.position)>1e-4f || Vector3.Distance(wrist,arm.hand.position)>1e-4f || Quaternion.Angle(hand,arm.hand.rotation)>.05f)
                            throw new Exception("Twist distribution changed solved endpoints or palm");
                        RestoreDistributedTwist(arm);
                        if(Quaternion.Angle(upper,arm.upper.localRotation)>.05f)throw new Exception("Twist distribution accumulated");
                    }
                }
                finally{arm.upper.localRotation=upper;arm.lower.rotation=lower;arm.hand.rotation=hand;arm.twist=twist;arm.upperTwistShare=share;arm.twistDistributed=false;}
            }
            if(Mathf.Abs(UpperTwistShare(5,160)-104)>.001f || UpperTwistShare(90,160)!=0)
                throw new Exception("Twist distribution bend weighting failed");
            Debug.Log("TANAKACAP_TWIST_DISTRIBUTION_CHECK_OK");
        }
    }
}
