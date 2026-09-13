using System;
using System.IO;
using System.Linq;
using System.Globalization;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEditor;
namespace TanakaCap.Editor {
 // Reads avatar-authored serialized data; no SDK DLL or solver code is bundled.
 public static class SecondaryMotionExporter {
  abstract class Reader {
   public string id;public abstract float Number(string name,float fallback=0);
   public abstract string Text(string name);public abstract string[] References(string name);
   public abstract string Resolve(string reference);public abstract Reader Lookup(string reference);
   public abstract string Owner();public abstract SecondaryCurve Curve(string name);
   public virtual Vector3 Vector(string name){string s=Text(name);return new Vector3(Axis(s,"x"),Axis(s,"y"),Axis(s,"z"));}
   public virtual Quaternion Rotation(string name){string s=Text(name);return new Quaternion(Axis(s,"x"),Axis(s,"y"),Axis(s,"z"),Axis(s,"w",1));}
   public string Root(){var refs=References("rootTransform");return refs.Length==0||refs[0]=="0"?Owner():Resolve(refs[0]);}
  }
  static float Parse(string s,float fallback=0){if(s==".inf"||s=="Infinity")return float.PositiveInfinity;if(s=="-.inf")return float.NegativeInfinity;return float.TryParse(s,NumberStyles.Float,CultureInfo.InvariantCulture,out var v)?v:fallback;}
  static float Axis(string s,string axis,float fallback=0){var m=Regex.Match(s??"",@"\b"+axis+@":\s*([^,}]+)");return m.Success?Parse(m.Groups[1].Value,fallback):fallback;}
  class Live : Reader {
   SerializedObject so;Transform avatar;Dictionary<string,Live> objects;
   public Live(Component c,Transform root,Dictionary<string,Live> map){so=new SerializedObject(c);avatar=root;objects=map;id=c.GetInstanceID().ToString();}
   public override float Number(string n,float d=0){var p=so.FindProperty(n);if(p==null)return d;if(p.propertyType==SerializedPropertyType.Boolean)return p.boolValue?1:0;if(p.propertyType==SerializedPropertyType.Float)return p.floatValue;return p.intValue;}
   public override string Text(string n)=>"";
   public override Vector3 Vector(string n)=>so.FindProperty(n)?.vector3Value??Vector3.zero;
   public override Quaternion Rotation(string n)=>so.FindProperty(n)?.quaternionValue??Quaternion.identity;
   string Ref(UnityEngine.Object o){if(!o)return "0";if(o is Transform t)return "path:"+Path(t);return o.GetInstanceID().ToString();}
   string Path(Transform t){if(t!=avatar&&!t.IsChildOf(avatar))throw new Exception("PhysBone reference outside avatar: "+t.name);return AnimationUtility.CalculateTransformPath(t,avatar);}
   public override string[] References(string n){var p=so.FindProperty(n);if(p==null)return new string[0];if(p.isArray){var a=new string[p.arraySize];for(int i=0;i<a.Length;i++)a[i]=Ref(p.GetArrayElementAtIndex(i).objectReferenceValue);return a;}return new[]{Ref(p.objectReferenceValue)};}
   public override string Resolve(string r){if(!r.StartsWith("path:"))throw new Exception("Invalid transform reference "+r);return r.Substring(5);}
   public override Reader Lookup(string r)=>objects.TryGetValue(r,out var v)?v:null;
   public override string Owner()=>Path(((Component)so.targetObject).transform);
   public override SecondaryCurve Curve(string n){var c=so.FindProperty(n)?.animationCurveValue;return c==null?new SecondaryCurve():new SecondaryCurve{preWrap=(int)c.preWrapMode,postWrap=(int)c.postWrapMode,keys=c.keys.Select(k=>new SecondaryCurve.Key{time=k.time,value=k.value,inSlope=k.inTangent,outSlope=k.outTangent,inWeight=k.inWeight,outWeight=k.outWeight,weightedMode=(int)k.weightedMode}).ToArray()};}
  }
  class Yaml : Reader {
   public string body,type;public Dictionary<string,Yaml> objects;
   public override string Text(string n){var m=Regex.Match(body,@"^  "+Regex.Escape(n)+@":\s*([^\r\n]*)",RegexOptions.Multiline);return m.Success?m.Groups[1].Value:"";}
   public override float Number(string n,float d=0)=>Parse(Text(n),d);
   public override string[] References(string n){var m=Regex.Match(body,@"^  "+Regex.Escape(n)+@":([^\n]*\n(?:  -[^\n]*\n)*)",RegexOptions.Multiline);return Regex.Matches(m.Value,@"fileID: (-?\d+)").Cast<Match>().Select(x=>x.Groups[1].Value).ToArray();}
   string Ref(string n)=>References(n).FirstOrDefault()??"0";
   string FullPath(string reference,int depth=0){if(reference=="0")return "";if(depth>256||!objects.TryGetValue(reference,out var t)||t.type!="4")throw new Exception("Unsupported prefab transform reference "+reference);var go=objects[t.Ref("m_GameObject")];return FullPath(t.Ref("m_Father"),depth+1)+"/"+go.Text("m_Name");}
   public override string Resolve(string r){var full=FullPath(r);int slash=full.IndexOf('/',1);return slash<0?"":full.Substring(slash+1);}
   public override Reader Lookup(string r)=>objects.TryGetValue(r,out var v)?v:null;
   public override string Owner(){var go=Ref("m_GameObject");return Resolve(objects.Values.First(x=>x.type=="4"&&x.Ref("m_GameObject")==go).id);}
   public override SecondaryCurve Curve(string n){
    var m=Regex.Match(body,@"^  "+Regex.Escape(n)+@":\n(.*?)(?=^  [A-Za-z_]|\z)",RegexOptions.Multiline|RegexOptions.Singleline);
    var keys=new List<SecondaryCurve.Key>();
    foreach(Match k in Regex.Matches(m.Value,@"    - serializedVersion:[^\n]*\n(.*?)(?=    - serializedVersion:|    m_PreInfinity:|\z)",RegexOptions.Singleline)){
     Func<string,float> f=name=>Parse(Regex.Match(k.Value,@"      "+name+@": ([^\n]+)").Groups[1].Value);
     keys.Add(new SecondaryCurve.Key{time=f("time"),value=f("value"),inSlope=f("inSlope"),outSlope=f("outSlope"),inWeight=f("inWeight"),outWeight=f("outWeight"),weightedMode=(int)f("weightedMode")});
    }
    return new SecondaryCurve{keys=keys.ToArray(),preWrap=(int)Parse(Regex.Match(m.Value,@"m_PreInfinity: (\d+)").Groups[1].Value,8),postWrap=(int)Parse(Regex.Match(m.Value,@"m_PostInfinity: (\d+)").Groups[1].Value,8)};
   }
  }
  static List<Reader> Read(GameObject source,List<string> warnings){
   var all=source.GetComponentsInChildren<Component>(true).Where(c=>c && (c.GetType().Name=="VRCPhysBone"||c.GetType().Name=="VRCPhysBoneCollider")).ToArray();
   if(all.Length>0){var map=new Dictionary<string,Live>();foreach(var c in all){var r=new Live(c,source.transform,map);map.Add(r.id,r);}return all.Where(c=>c.GetType().Name=="VRCPhysBone").Select(c=>(Reader)map[c.GetInstanceID().ToString()]).ToList();}
   string path=AssetDatabase.GetAssetPath(source);
   if(string.IsNullOrEmpty(path)){
    var prefab=PrefabUtility.GetCorrespondingObjectFromSource(source);path=AssetDatabase.GetAssetPath(prefab);
    if(PrefabUtility.HasPrefabInstanceAnyOverrides(source,false))throw new Exception("Missing PhysBone scripts with prefab overrides: restore SDK scripts before export.");
   }
   if(!path.EndsWith(".prefab",StringComparison.OrdinalIgnoreCase))throw new Exception("Cannot read missing PhysBone settings: export a saved text prefab or restore SDK components.");
   string text=File.ReadAllText(path).Replace("\r\n","\n");
   if(Regex.IsMatch(text,@"^PrefabInstance:",RegexOptions.Multiline))throw new Exception("Missing PhysBone fallback does not support nested/variant prefabs; restore SDK scripts first.");
   var docs=new Dictionary<string,Yaml>();
   foreach(Match m in Regex.Matches(text,@"--- !u!(\d+) &(-?\d+)\n(.*?)(?=\n--- !u!|\z)",RegexOptions.Singleline)){var r=new Yaml{type=m.Groups[1].Value,id=m.Groups[2].Value,body=m.Groups[3].Value,objects=docs};docs.Add(r.id,r);}
   warnings.Add("PhysBone settings read from text prefab because SDK scripts are missing; raw legacy serialized settings, no SDK binary dependency. Prefab variants/overrides are refused in this fallback.");
   return docs.Values.Where(x=>x.type=="114"&&x.Text("m_Script").Contains("fileID: 1661641543,")&&x.Text("m_Script").Contains("2a2c05204084d904aa4945ccff20d8e5")).Cast<Reader>().ToList();
  }
  public static SecondaryPhysicsData Collect(GameObject source,GameObject copy,List<string> warnings){
   var readers=Read(source,warnings).Where(r=>r.Number("m_Enabled",1)!=0).OrderBy(r=>r.Root().Count(ch=>ch=='/')+(r.Root().Length==0?0:1)).ToList();var chains=new List<SecondaryChain>();var colliders=new List<SecondaryCollider>();var bones=new List<SecondaryBone>();
   var activeRoots=new HashSet<string>(readers.Select(r=>r.Root()));
   var colliderIds=new Dictionary<string,int>();var roots=new HashSet<string>();var owned=new HashSet<string>();
   var animator=copy.GetComponent<Animator>();var human=new HashSet<Transform>();for(int i=0;i<(int)HumanBodyBones.LastBone;i++){var b=animator.GetBoneTransform((HumanBodyBones)i);if(b)human.Add(b);}
   foreach(var r in readers){
    if(r.Number("m_Enabled",1)==0)continue;
    var root=r.Root();var t=string.IsNullOrEmpty(root)?copy.transform:copy.transform.Find(root);if(!t)throw new Exception("PhysBone root missing: "+root);
    if(!roots.Add(root)){warnings.Add("Duplicate PhysBone root omitted (first component wins): "+root+" source="+r.id);continue;}
    var c=new SecondaryChain{root=root,sourceId=r.id,sourceMode=r is Live?"serialized-component":"text-prefab",
     version=(int)r.Number("version"),integrationType=(int)r.Number("integrationType"),multiChildType=(int)r.Number("multiChildType"),immobileType=(int)r.Number("immobileType"),limitType=(int)r.Number("limitType"),
     endpointPosition=r.Vector("endpointPosition"),limitRotation=r.Vector("limitRotation"),isAnimated=r.Number("isAnimated")!=0,resetWhenDisabled=r.Number("resetWhenDisabled")!=0,
     ignored=r.References("ignoreTransforms").Where(x=>x!="0").Select(r.Resolve).ToArray()};
    foreach(var f in typeof(SecondaryChain).GetFields())if(f.FieldType==typeof(float))f.SetValue(c,r.Number(f.Name));else if(f.FieldType==typeof(SecondaryCurve))f.SetValue(c,r.Curve(f.Name));
    if(c.version<0||c.version>1||c.integrationType<0||c.integrationType>1||c.limitType<0||c.limitType>3||c.multiChildType<0||c.multiChildType>2)throw new Exception("Unsupported PhysBone enum/version: "+root);
    var refs=new List<int>();foreach(string id in r.References("colliders")){
     if(id=="0"){warnings.Add("Null PhysBone collider reference: "+root);continue;}
     if(!colliderIds.TryGetValue(id,out int ci)){
      var cr=r.Lookup(id);if(cr==null)throw new Exception("Missing PhysBone collider "+id);
      var cc=new SecondaryCollider{path=cr.Root(),sourceId=id,shapeType=(int)cr.Number("shapeType"),insideBounds=cr.Number("insideBounds")!=0,bonesAsSpheres=cr.Number("bonesAsSpheres")!=0,radius=cr.Number("radius"),height=cr.Number("height"),position=cr.Vector("position"),rotation=cr.Rotation("rotation")};
      if(cc.shapeType<0||cc.shapeType>2)throw new Exception("Unsupported collider shape "+cc.shapeType);
      ci=colliders.Count;colliders.Add(cc);colliderIds.Add(id,ci);
     }refs.Add(ci);
    }c.colliders=refs.Distinct().ToArray();int chainIndex=chains.Count;chains.Add(c);
    var selected=CollectSegments(t,copy.transform,c,activeRoots,human,warnings);
    int maxDepth=selected.Count==0?1:Math.Max(1,selected.Max(x=>x.Item3)+1);
    foreach(var item in selected){string bp=AnimationUtility.CalculateTransformPath(item.Item1,copy.transform);if(!owned.Add(bp))throw new Exception("Overlapping PhysBone chains: "+bp);bones.Add(new SecondaryBone{path=bp,tail=item.Item2,chain=chainIndex,depth=item.Item3/(float)maxDepth});}
    if(c.isAnimated)warnings.Add("Animated PhysBone: base transforms supported, original Animator controllers are not exported: "+root);
    if(r.Number("stretchMotion")!=0||r.Number("maxStretch")!=0||r.Number("maxSquish")!=0)warnings.Add("Stretch/squish not simulated (bone lengths preserved): "+root);
   }
   warnings.Add("Independent PhysBone-parameter conversion: "+chains.Count+" chains / "+bones.Count+" segments / "+colliders.Count+" explicit colliders. Force mapping, curve depth and collision response approximate; not the VRChat solver. No global/player collisions, grab/pose or animator parameters.");
   if(chains.Count==0)warnings.Add("No readable PhysBone chains; secondary motion unavailable.");
   return new SecondaryPhysicsData{chains=chains.ToArray(),bones=bones.ToArray(),colliders=colliders.ToArray()};
  }
  internal static List<Tuple<Transform,Vector3,int>> CollectSegments(Transform root,Transform avatar,SecondaryChain c,HashSet<string> activeRoots,HashSet<Transform> human,List<string> warnings){
    var selected=new List<Tuple<Transform,Vector3,int>>();
    Action<Transform,int> visit=null;visit=(b,depth)=>{
     string bp=AnimationUtility.CalculateTransformPath(b,avatar);
     if(c.ignored.Any(p=>bp==p||bp.StartsWith(p+"/",StringComparison.Ordinal)))return;
     if(b!=root&&activeRoots.Contains(bp)){warnings.Add("Nested PhysBone boundary: "+c.root+" stops at "+bp+"; the child PhysBone owns this subtree. Parent tail still references the child position. Original components are unchanged.");return;}
     if(human.Contains(b))throw new Exception("PhysBone controls Humanoid bone: "+bp);
     var children=b.Cast<Transform>().Where(x=>!c.ignored.Contains(AnimationUtility.CalculateTransformPath(x,avatar))).ToArray();
     Vector3 tail=c.endpointPosition;
     if(children.Length==1 || children.Length>1&&c.multiChildType==1)tail=children[0].localPosition;
     else if(children.Length>1&&c.multiChildType==2){tail=Vector3.zero;foreach(var child in children)tail+=child.localPosition;tail/=children.Length;}
     else if(children.Length>1)tail=Vector3.zero;
     if(ShouldSimulate(b,tail,bp,warnings))selected.Add(Tuple.Create(b,tail,depth));
     foreach(var child in children)visit(child,depth+1);
    };visit(root,0);
    return selected;
  }
  internal static bool ShouldSimulate(Transform bone,Vector3 tail,string path,List<string> warnings){
   if(tail.sqrMagnitude<=1e-10f)return false;
   var constraints=bone.GetComponents<Component>().Where(c=>c is UnityEngine.Animations.IConstraint).ToArray();
   if(constraints.Length==0)return true;
   // Native constraints run after LateUpdate. Keep them intact instead of
   // scheduling a second rotation writer which they would overwrite.
   warnings.Add("Constraint takes priority over secondary motion at "+path+" ("+string.Join(", ",constraints.Select(c=>c.GetType().Name))+"). Constraint preserved; PhysBone simulation omitted on this bone only. Unconstrained descendants are still collected. This can reduce the original sway.");
   return false;
  }
 }
}
