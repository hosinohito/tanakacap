// Development-only Editor comparison. No VRChat SDK shipped with TanakaCap.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using TanakaCap;
[DefaultExecutionOrder(-1000)]
public class PhysReferenceDrive : MonoBehaviour {
 public Transform[] heads,torsos; Quaternion[] rest,torsoRest; int frame;
 void Start(){Time.captureDeltaTime=1f/60;rest=heads.Select(h=>h.localRotation).ToArray();torsoRest=torsos.Select(h=>h.localRotation).ToArray();}
 void Update(){foreach(var solver in FindObjectsOfType<SecondaryMotion>())solver.Restore();float t=frame++/60f;float a=t<3?0:t<9?25*Mathf.Sin((t-3)*Mathf.PI*2*.7f):0;
  for(int i=0;i<heads.Length;i++)heads[i].localRotation=rest[i]*Quaternion.Euler(0,a,0);
  float c=t>=9&&t<15?Mathf.Sin((t-9)*Mathf.PI*2*.45f):0;for(int i=0;i<torsos.Length;i++)torsos[i].localRotation=torsoRest[i]*Quaternion.Euler(15*c,0,10*c);}
}
