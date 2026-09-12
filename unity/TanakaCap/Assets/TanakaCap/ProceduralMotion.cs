// SPDX-License-Identifier: 0BSD
// Original analytic motion, no external animation clip or recorded performer.
using UnityEngine;
namespace TanakaCap {
 public static class ProceduralMotion {
  public static TrackingPacket Sample(float seconds) {
   float t=seconds%24f,w=2*Mathf.PI/24f;
   float left=.5f+.5f*Mathf.Sin(w*t*2),right=.5f+.5f*Mathf.Sin(w*t*2+Mathf.PI);
   return new TrackingPacket {
    version=1,tracked=true,faceTracked=true,body3d=true,torsoTracked=true,
    headYaw=28*Mathf.Sin(w*t*3),headPitch=10*Mathf.Sin(w*t*2),headRoll=9*Mathf.Sin(w*t*4),
    torsoYaw=18*Mathf.Sin(w*t),torsoRoll=7*Mathf.Sin(w*t*2),torsoPitch=5*Mathf.Sin(w*t*2),
    mouth=.15f+.2f*(1+Mathf.Sin(w*t*6)),leftBlink=Blink(t),rightBlink=Blink(t),
    gazeTracked=true,gazeYaw=4*Mathf.Sin(w*t*3),gazePitch=1.5f*Mathf.Sin(w*t*2),
    leftArmTracked=true,rightArmTracked=true,leftHandTracked=true,rightHandTracked=true,
    leftElbow=new Vector3(-.14f,-.22f+.12f*left,.10f),rightElbow=new Vector3(.14f,-.22f+.12f*right,.10f),
    leftWrist=new Vector3(-.20f,-.26f+.52f*left,.26f),rightWrist=new Vector3(.20f,-.26f+.52f*right,.26f),
    leftWristInFront=true,rightWristInFront=true,
    leftHandForward=new Vector3(-.12f,1,.12f),rightHandForward=new Vector3(.12f,1,.12f),
    leftHandNormal=Vector3.forward,rightHandNormal=Vector3.forward,
    leftFingerTracked=new[]{true,true,true,true,true},rightFingerTracked=new[]{true,true,true,true,true},
    leftFingerFlex=Fingers(left),rightFingerFlex=Fingers(right)
   };
  }
  static float Blink(float t){float d=(t%4)-3.7f;return Mathf.Exp(-d*d/.004f);}
  static float[] Fingers(float amount){float f=35*(1-amount);return new[]{5f,10f,10f,f,f*1.4f,f,f,f*1.4f,f,f,f*1.4f,f,f,f*1.4f,f};}
 }
}
