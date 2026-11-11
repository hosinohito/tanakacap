using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
namespace TanakaCap.Editor {
 // Public SDK data/API is used only in the authoring Editor; no SDK code is shipped in the Player.
 public static class StandardHandColliderExporter {
  static object Field(object obj,string name){var f=obj.GetType().GetField(name);if(f==null)throw new Exception("Descriptor collider field unavailable: "+name);return f.GetValue(obj);}
  public static List<SecondaryCollider> Collect(GameObject copy,List<string> warnings){
   var result=new List<SecondaryCollider>();
   var descriptor=copy.GetComponents<Component>().FirstOrDefault(c=>c&&c.GetType().FullName=="VRC.SDK3.Avatars.Components.VRCAvatarDescriptor");
   if(!descriptor){warnings.Add("Standard hand collision unavailable: Avatar Descriptor missing. Restore the SDK and re-export to preserve hand settings.");return result;}
   var type=descriptor.GetType();var animator=copy.GetComponent<Animator>();
   foreach(bool left in new[]{true,false})for(int slot=-1;slot<4;slot++){
    string name="collider_"+(slot<0?"hand":new[]{"fingerIndex","fingerMiddle","fingerRing","fingerLittle"}[slot])+(left?"L":"R");
    try {
     object stored=Field(descriptor,name);string state=Field(stored,"state").ToString();
     if(state=="Disabled")continue;
     if(state!="Automatic"&&state!="Custom")throw new Exception("Unknown collider state "+state);
     // Resolve the SDK's automatic geometry on the clone. Custom dimensions remain author supplied.
     string method=slot<0?"CalcPalmCollider":"CalcFingerCollider";
     var api=type.GetMethod(method,BindingFlags.Public|BindingFlags.Static);
     if(api==null)throw new Exception("SDK public collider calculation unavailable: "+method);
     var automatic=api.Invoke(null,slot<0?new object[]{animator,left}:new object[]{animator,slot,left});
     object config=state=="Automatic"?automatic:stored;
     var bone=(Transform)Field(automatic,"transform");
     if(!bone)throw new Exception("Required hand/finger bone missing");
     if(bone!=copy.transform&&!bone.IsChildOf(copy.transform))throw new Exception("Hand collider transform outside avatar");
     var maxField=type.GetField("COLLIDER_MAX_SIZE",BindingFlags.Public|BindingFlags.Static);
     if(maxField==null)throw new Exception("SDK collider size bound unavailable");
     var c=new SecondaryCollider{path=AnimationUtility.CalculateTransformPath(bone,copy.transform),sourceId=name,sourceState=state,standardHand=true,finger=slot>=0,shapeType=1,
      radius=Convert.ToSingle(Field(config,"radius")),height=Convert.ToSingle(Field(config,"height")),position=(Vector3)Field(config,"position"),rotation=(Quaternion)Field(config,"rotation"),maxWorldSize=Convert.ToSingle(maxField.GetValue(null))};
     if(float.IsNaN(c.radius)||float.IsInfinity(c.radius)||c.radius<0||float.IsNaN(c.height)||float.IsInfinity(c.height)||c.height<0||c.maxWorldSize<=0)throw new Exception("Invalid standard collider dimensions");
     result.Add(c);
    }catch(Exception e){warnings.Add("Standard hand collider omitted: "+name+"; "+(e.InnerException??e).Message);}
   }
   warnings.Add("Standard hand/finger colliders: "+result.Count+". Automatic geometry resolved by authoring SDK; Custom/Disabled and PhysBone self-collision permission preserved.");
   return result;
  }
 }
}
