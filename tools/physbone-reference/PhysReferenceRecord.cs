// Development-only Editor comparison. No VRChat SDK shipped with TanakaCap.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using TanakaCap;
[DefaultExecutionOrder(20000)]
public class PhysReferenceRecord : MonoBehaviour {
 public Transform original,independent; public string dataJson;
 SecondaryMotion solver; SecondaryPhysicsData data; StreamWriter writer; int frame;
 Quaternion[] rest; Transform[] a,b;
 [Serializable] class Row {public int frame;public float dt;public float[] referenceAngle,independentAngle,errorDegrees;}
 void Start(){data=JsonUtility.FromJson<SecondaryPhysicsData>(dataJson);
  solver=independent.GetComponent<SecondaryMotion>();solver.Initialize(data,independent.GetComponent<Animator>());solver.externalClock=true;
  a=data.bones.Select(n=>original.Find(n.path)).ToArray();b=data.bones.Select(n=>independent.Find(n.path)).ToArray();
  rest=a.Select(n=>n.localRotation).ToArray();
  writer=new StreamWriter(Path.GetFullPath("../frames.jsonl"),false);}
 void LateUpdate(){if(writer==null)return;solver.Step(Time.deltaTime);
  var row=new Row{frame=frame++,dt=Time.deltaTime,referenceAngle=new float[a.Length],independentAngle=new float[a.Length],errorDegrees=new float[a.Length]};
  for(int i=0;i<a.Length;i++){row.referenceAngle[i]=Quaternion.Angle(rest[i],a[i].localRotation);row.independentAngle[i]=Quaternion.Angle(rest[i],b[i].localRotation);row.errorDegrees[i]=Quaternion.Angle(a[i].localRotation,b[i].localRotation);}
  writer.WriteLine(JsonUtility.ToJson(row));
  if(frame>=1260){writer.Dispose();writer=null;Debug.Log("TANAKACAP_PHYS_REFERENCE_COMPLETE");EditorApplication.Exit(0);}
 }
 void OnDestroy(){writer?.Dispose();}
}
