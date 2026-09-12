using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace TanakaCap {
 [Serializable] public class FaceBinding {public string channel,renderer,shape,source;public int priority;}
 [Serializable] public class FaceProfile {public FaceBinding[] bindings=new FaceBinding[0];public string leftEye,rightEye;}
 public sealed class FaceExpressions {
  public readonly Dictionary<string,FaceBinding> Report=new Dictionary<string,FaceBinding>();
  readonly Dictionary<string,Slot> slots=new Dictionary<string,Slot>();
  readonly Dictionary<(SkinnedMeshRenderer,int),float> weights=new Dictionary<(SkinnedMeshRenderer,int),float>();
  readonly Transform root; readonly SkinnedMeshRenderer[] meshes;
  readonly Dictionary<(SkinnedMeshRenderer,string),float> cornerGains;
  readonly Dictionary<(Mesh,int),bool> usable=new Dictionary<(Mesh,int),bool>();
  (SkinnedMeshRenderer,int)[] owned;
  static readonly Dictionary<string,string> AutoChannels=new Dictionary<string,string>{
   {"smileL","TC_LeftCornerUp"},{"smileR","TC_RightCornerUp"},{"frownL","TC_LeftCornerDown"},{"frownR","TC_RightCornerDown"},
   {"shiftL","TC_MouthShiftLeft"},{"shiftR","TC_MouthShiftRight"},
   {"eyeLPos","TC_GazeRight"},{"eyeRPos","TC_GazeRight"},{"eyeLNeg","TC_GazeLeft"},{"eyeRNeg","TC_GazeLeft"},
   {"eyeLUp","TC_GazeUp"},{"eyeRUp","TC_GazeUp"},{"eyeLDown","TC_GazeDown"},{"eyeRDown","TC_GazeDown"}};
  class Slot {public SkinnedMeshRenderer renderer;public int index;public FaceBinding info;}
  public static string Normalize(string name){return new string((name??"").Normalize().Where(char.IsLetterOrDigit).ToArray()).ToLowerInvariant();}
  public static string PathOf(Transform t,Transform root){if(t==root)return "";return t.parent==root?t.name:PathOf(t.parent,root)+"/"+t.name;}
  public FaceExpressions(Transform root,SkinnedMeshRenderer[] meshes,FaceProfile profile=null,bool auto=false,Dictionary<(SkinnedMeshRenderer,string),float> cornerGains=null){
   this.root=root;this.meshes=meshes;
   this.cornerGains=cornerGains;
   Add("jaw",new[]{"jawOpen"});
   Add("a",null,new[]{"あ"},new[]{"vrc.v_aa"});Add("i",null,new[]{"い"},new[]{"vrc.v_ih","vrc.v_E"});
   Add("o",null,new[]{"お"},new[]{"vrc.v_oh"});Add("u",null,new[]{"う"},new[]{"vrc.v_ou"});
   Add("funnel",new[]{"mouthFunnel"});Add("pucker",new[]{"mouthPucker"});
   Add("wideL",new[]{"mouthStretchLeft"},new[]{"口横広げ"});Add("wideR",new[]{"mouthStretchRight"},new[]{"口横広げ"});
   Add("smileL",new[]{"mouthSmileLeft"},new[]{"口角上げ","にやり"});Add("smileR",new[]{"mouthSmileRight"},new[]{"口角上げ","にやり"});
   Add("frownL",new[]{"mouthFrownLeft"},new[]{"口角下げ","への字"});Add("frownR",new[]{"mouthFrownRight"},new[]{"口角下げ","への字"});
   Add("shiftL",new[]{"mouthLeft"},new[]{"口_左","口左"});Add("shiftR",new[]{"mouthRight"},new[]{"口_右","口右"});Add("bow",null,new[]{"ω"});
   Add("blinkL",new[]{"eyeBlinkLeft"},new[]{"ウィンク２","ウィンク2","ウィンク"});Add("blinkR",new[]{"eyeBlinkRight"},new[]{"ウィンク２右","ウィンク2右","ウィンク右"});
   Add("browLI",new[]{"browInnerUp"},new[]{"上"});Add("browRI",new[]{"browInnerUp"},new[]{"上"});
   Add("browLO",new[]{"browOuterUpLeft"},new[]{"上"});Add("browRO",new[]{"browOuterUpRight"},new[]{"上"});
   Add("browLD",new[]{"browDownLeft"},new[]{"下"});Add("browRD",new[]{"browDownRight"},new[]{"下"});
   Add("browSad",null,new[]{"困る"});Add("browAngry",null,new[]{"怒り"});
   foreach(string side in new[]{"L","R"}){
    string label=side=="L"?"Left":"Right";
    Add("eye"+side+"Pos",new[]{"eyeLook"+(side=="L"?"In":"Out")+label},new[]{"目線右","視線右"});
    Add("eye"+side+"Neg",new[]{"eyeLook"+(side=="L"?"Out":"In")+label},new[]{"目線左","視線左"});
    Add("eye"+side+"Up",new[]{"eyeLookUp"+label},new[]{"目線上","視線上"});
    Add("eye"+side+"Down",new[]{"eyeLookDown"+label},new[]{"目線下","視線下"});
   }
   foreach(var binding in profile?.bindings??new FaceBinding[0]){
    if(binding==null||string.IsNullOrEmpty(binding.channel)||string.IsNullOrEmpty(binding.shape)||binding.priority<0||binding.priority>2)continue;
    if(slots.TryGetValue(binding.channel,out var previous) && previous.info.priority<binding.priority)continue;
    var renderer=meshes.FirstOrDefault(r=>r.sharedMesh && PathOf(r.transform,root)==binding.renderer && Valid(r.sharedMesh,r.sharedMesh.GetBlendShapeIndex(binding.shape)));
    if(renderer)Bind(binding.channel,renderer,renderer.sharedMesh.GetBlendShapeIndex(binding.shape),binding.source,binding.priority);
   }
   if(auto){
    foreach(var pair in AutoChannels){
     if(slots.TryGetValue(pair.Key,out var existing)&&existing.info.priority==0)continue;
     var found=Find(new[]{pair.Value},false);if(found!=null)Bind(pair.Key,found.renderer,found.index,"auto-custom",1);
    }
   }
   foreach(var pair in slots){Report[pair.Key]=pair.Value.info;weights[(pair.Value.renderer,pair.Value.index)]=0;}
   owned=weights.Keys.ToArray();
   Debug.Log("TANAKACAP_EXPRESSION_MAP "+JsonUtility.ToJson(new FaceProfile{bindings=Report.Values.ToArray()}));
   if(!Has("jaw")&&!Has("a")&&!Has("jawFallback"))Debug.LogWarning("Expression not mapped: mouth opening");
   foreach(var key in new[]{"smileL","frownL","shiftL","blinkL","browLI"})if(!Has(key))Debug.LogWarning("Expression not mapped: "+key);
  }
  Slot Find(string[] aliases,bool brow){
   foreach(string alias in aliases??new string[0])foreach(var r in meshes){
    if(!r.sharedMesh)continue;
    // Single-character MMD up/down is ambiguous without the brow set.
    if(brow && r.sharedMesh.GetBlendShapeIndex("困る")<0 && r.sharedMesh.GetBlendShapeIndex("真面目")<0)continue;
    for(int i=0;i<r.sharedMesh.blendShapeCount;i++)if(Normalize(r.sharedMesh.GetBlendShapeName(i))==Normalize(alias)&&Valid(r.sharedMesh,i))return new Slot{renderer=r,index=i};
   }
   return null;
  }
  bool Valid(Mesh mesh,int index){
   if(index<0)return false;if(usable.TryGetValue((mesh,index),out bool known))return known;
   var delta=new Vector3[mesh.vertexCount];var normals=new Vector3[mesh.vertexCount];bool valid=false;
   for(int frame=0;frame<mesh.GetBlendShapeFrameCount(index)&&!valid;frame++){
    mesh.GetBlendShapeFrameVertices(index,frame,delta,normals,null);
    for(int i=0;i<delta.Length;i++)if(delta[i].sqrMagnitude>1e-14f||normals[i].sqrMagnitude>1e-14f){valid=true;break;}
   }
   usable[(mesh,index)]=valid;return valid;
  }
  void Add(string channel,string[] arkit=null,string[] mmd=null,string[] vrc=null){
   var sets=new[]{arkit,mmd,vrc};for(int rank=0;rank<sets.Length;rank++){
    var found=Find(sets[rank],rank==1&&channel.StartsWith("brow")&&sets[rank]!=null&&sets[rank].Any(n=>n=="上"||n=="下"));
    if(found!=null){Bind(channel,found.renderer,found.index,new[]{"ARKit","MMD","VRC-name"}[rank],rank);return;}
   }
  }
  void Bind(string channel,SkinnedMeshRenderer r,int index,string source,int rank){slots[channel]=new Slot{renderer=r,index=index,info=new FaceBinding{channel=channel,renderer=PathOf(r.transform,root),shape=r.sharedMesh.GetBlendShapeName(index),source=source,priority=rank}};}
  public bool Has(string channel){return slots.ContainsKey(channel);}
  public void Begin(){foreach(var key in owned)weights[key]=0;}
  void Put(string key,float value){if(slots.TryGetValue(key,out var slot)){var id=(slot.renderer,slot.index);weights[id]=Mathf.Max(weights[id],Mathf.Clamp01(value)*100);}}
  void Group(string[] keys,float[] values){
   var sums=new Dictionary<(SkinnedMeshRenderer,int),(float,int)>();
   for(int i=0;i<keys.Length;i++)if(slots.TryGetValue(keys[i],out var s)){var id=(s.renderer,s.index);sums.TryGetValue(id,out var sum);sums[id]=(sum.Item1+Mathf.Clamp01(values[i]),sum.Item2+1);}
   foreach(var item in sums)weights[item.Key]=Mathf.Max(weights[item.Key],item.Value.Item1/item.Value.Item2*100);
  }
  public void ApplyMouth(float open,float width,float round,float lc,float rc,float shift,float bow,float emphasis){
   if(Has("jaw")){Put("jaw",open);Put("funnel",open*round);Put("pucker",round*(1-open*.5f));}
   else {
    float i=Has("i")?Mathf.Max(0,width)*.7f:0;
    Put("a",open*(1-(Has("o")?round:0))*(1-i));Put("i",open*(1-round)*i);
    Put("o",open*round);Put("u",(1-open)*round*.7f);Put("jawFallback",Has("a")?0:open);
    Put("funnel",open*round);Put("pucker",round*(1-open*.5f));
   }
   Group(new[]{"wideL","wideR"},new[]{Mathf.Max(0,width),Mathf.Max(0,width)});
   float left=ExpressiveCorner(lc,open),right=ExpressiveCorner(rc,open);
   float gain=Mathf.Lerp(1,2,Mathf.Clamp01(emphasis));
   Group(new[]{"smileL","smileR"},new[]{Corner("smileL",left,true,emphasis,gain),Corner("smileR",right,true,emphasis,gain)});
   Group(new[]{"frownL","frownR"},new[]{Corner("frownL",left,false,emphasis,gain),Corner("frownR",right,false,emphasis,gain)});
   Put("shiftL",Mathf.Max(0,shift));Put("shiftR",Mathf.Max(0,-shift));Put("bow",bow*.65f);
  }
  public void ApplyBrows(float li,float lo,float ri,float ro){
   Group(new[]{"browLI","browLO","browRI","browRO"},new[]{li,lo,ri,ro});
   Group(new[]{"browLD","browRD"},new[]{-(li+lo)*.5f,-(ri+ro)*.5f});
   bool arkit=slots.Values.Any(s=>s.info.channel.StartsWith("brow")&&s.info.priority==0);
   if(!arkit){Put("browSad",Mathf.Max(0,(li-lo+ri-ro)*.25f));Put("browAngry",Mathf.Max(0,(lo-li+ro-ri)*.25f));}
  }
  public void Blink(float left,float right){Group(new[]{"blinkL","blinkR"},new[]{left,right});}
  float Corner(string key,float value,bool up,float emphasis,float gain){
   if(slots.TryGetValue(key,out var slot)&&slot.info.source=="auto-custom"){
    // The historical 30% offset applies only to generated downward keys from this recipe.
    float weight=up?Mathf.Max(0,value):Mathf.Max(0,-value)+.30f*(1-Mathf.Abs(value));
    if(cornerGains!=null&&cornerGains.TryGetValue((slot.renderer,slot.info.shape),out float bakedGain))weight*=Mathf.Lerp(1/bakedGain,1,emphasis);
    return weight;
   }
   return Mathf.Max(0,up?value:-value)*gain;
  }
  public Vector2 Eye(string side,Vector2 angles,bool allowShapes=true){
   string k="eye"+side;var residual=angles;
   if(!allowShapes){Put(k+"Pos",0);Put(k+"Neg",0);Put(k+"Up",0);Put(k+"Down",0);return residual;}
   foreach(string suffix in new[]{"Pos","Neg","Up","Down"})if(slots.TryGetValue(k+suffix,out var reset))weights[(reset.renderer,reset.index)]=0;
   if(Has(k+"Pos")&&Has(k+"Neg")){Put(k+"Pos",angles.x/20);Put(k+"Neg",-angles.x/20);residual.x=0;}
   if(Has(k+"Up")&&Has(k+"Down")){Put(k+"Down",angles.y/12);Put(k+"Up",-angles.y/12);residual.y=0;}
   return residual;
  }
  public void Commit(){foreach(var item in weights)item.Key.Item1.SetBlendShapeWeight(item.Key.Item2,item.Value);}
  public static float ExpressiveCorner(float corner,float opening){
   corner=Mathf.Clamp(corner,-1,1);corner*=Mathf.Abs(corner);
   return corner<=0?corner:corner*(1-.9f*Mathf.SmoothStep(0,1,Mathf.Clamp01(opening/.65f)));
  }
  public void CheckMouthMotion(){
   var saved=owned.Select(k=>k.Item1.GetBlendShapeWeight(k.Item2)).ToArray();
   var baseline=new Dictionary<SkinnedMeshRenderer,Vector3[]>();
   Begin();Commit();foreach(var mesh in meshes){var baked=new Mesh();mesh.BakeMesh(baked);baseline[mesh]=baked.vertices;UnityEngine.Object.Destroy(baked);}
   ApplyMouth(.8f,.3f,.2f,.6f,-.6f,.5f,.2f,0);Commit();float maximum=0;
   foreach(var mesh in meshes){var baked=new Mesh();mesh.BakeMesh(baked);var points=baked.vertices;for(int i=0;i<points.Length;i++)maximum=Mathf.Max(maximum,mesh.transform.TransformVector(points[i]-baseline[mesh][i]).magnitude);UnityEngine.Object.Destroy(baked);}
   for(int i=0;i<owned.Length;i++)owned[i].Item1.SetBlendShapeWeight(owned[i].Item2,saved[i]);
   if(maximum<1e-5f)throw new Exception("Mapped mouth controls did not deform the avatar");
   Debug.Log("TANAKACAP_MAPPED_MOUTH_VERIFIED displacement="+maximum);
  }
 }
}
