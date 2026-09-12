using System;
using System.IO;
using System.Linq;
using System.Collections;
using UnityEngine;
namespace TanakaCap {
 public class SecondaryMotionProbe : MonoBehaviour {
  [Serializable] class Report {public int bones,frames;public float maxAngle,settledAngle,settledSpeed,maxLocalPositionError,maxPrimaryError,maxStepMs;public bool offRestored;}
  IEnumerator Start() {
   yield return null;
   var args=Environment.GetCommandLineArgs();int index=Array.IndexOf(args,"--secondary-check");if(index<0)yield break;
   var motion=GetComponent<SecondaryMotion>();var driver=GetComponent<AvatarDriver>();var a=GetComponent<Animator>();
   driver.enabled=false;motion.externalClock=true;
   var head=a.GetBoneTransform(HumanBodyBones.Head);var chest=a.GetBoneTransform(HumanBodyBones.Chest);
   var headRest=head.localRotation;var chestRest=chest.localRotation;
   var all=GetComponentsInChildren<Transform>(true);var positions=all.Select(t=>t.localPosition).ToArray();
   var primary=Enumerable.Range(0,(int)HumanBodyBones.LastBone).Select(i=>a.GetBoneTransform((HumanBodyBones)i)).Where(t=>t).ToArray();
   var rotations=primary.Select(t=>t.localRotation).ToArray();
   var report=new Report{bones=motion.BoneCount};string path=args[index+1];Directory.CreateDirectory(Path.GetDirectoryName(path));
   for(int frame=0;frame<960;frame++) {
    float dt=frame%3==0?1f/30:1f/60;float t=frame/60f;
    motion.Restore();head.localRotation=headRest*Quaternion.Euler(0,frame<420?28*Mathf.Sin(t*2):0,0);
    chest.localRotation=chestRest*Quaternion.Euler(0,0,frame<420?9*Mathf.Sin(t*2):0);
    for(int j=0;j<primary.Length;j++)rotations[j]=primary[j].localRotation;
    motion.Step(dt);
    report.maxAngle=Mathf.Max(report.maxAngle,motion.MaxAngle);report.maxStepMs=Mathf.Max(report.maxStepMs,motion.LastStepMilliseconds);
    for(int j=0;j<all.Length;j++)report.maxLocalPositionError=Mathf.Max(report.maxLocalPositionError,Vector3.Distance(positions[j],all[j].localPosition));
    for(int j=0;j<primary.Length;j++)report.maxPrimaryError=Mathf.Max(report.maxPrimaryError,Quaternion.Angle(rotations[j],primary[j].localRotation));
    if(frame==165){yield return null;Snapshot(path+".on.png");motion.Restore();yield return null;Snapshot(path+".off.png");}
    report.frames++;if(frame%60==0)yield return null;
   }
   File.WriteAllText(path+".bones.txt",motion.Diagnostics());report.settledAngle=motion.MaxAngle;report.settledSpeed=motion.MaxTipSpeed;motion.motionEnabled=false;motion.Step(1f/60);report.offRestored=motion.MaxAngle<.1f;
   File.WriteAllText(path,JsonUtility.ToJson(report,true));
   bool ok=report.bones>0&&report.maxAngle>1&&report.maxAngle<=180&&report.settledSpeed<.01f&&report.maxLocalPositionError<1e-6f&&report.maxPrimaryError<.1f&&report.offRestored;
   Debug.Log("TANAKACAP_SECONDARY_CHECK "+ok+" "+JsonUtility.ToJson(report));
   var output=FindObjectOfType<AlphaOutput>();if(output)output.exitCode=ok?0:2;Application.Quit(ok?0:2);
  }
  static void Snapshot(string path){var cam=Camera.main;var old=cam.targetTexture;var rt=new RenderTexture(1280,720,24);var active=RenderTexture.active;
   cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var tex=new Texture2D(1280,720,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,1280,720),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToPNG());cam.targetTexture=old;RenderTexture.active=active;Destroy(tex);rt.Release();Destroy(rt);}
 }
}
