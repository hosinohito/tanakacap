// Local Editor-only video capture of the real SDK and independent solver.
using System;
using System.IO;
using System.Diagnostics;
using UnityEngine;
using UnityEditor;
[DefaultExecutionOrder(21000)]
public class PhysReferenceVideo : MonoBehaviour {
 public Transform original,independent; public string outputDirectory;
 class View {
  public Camera[] cameras;public RenderTexture[] targets;public Texture2D[] textures;
  public byte[] pixels;public Process encoder;public Stream stream;public string path;
 }
 View[] views;int frames;bool finished;
 void Start(){try{Initialize();}catch(Exception e){UnityEngine.Debug.LogException(e);EditorApplication.Exit(2);}}
 void Initialize(){
  Directory.CreateDirectory(outputDirectory);
  int layer=8;foreach(var root in new[]{original,independent}){
   foreach(var t in root.GetComponentsInChildren<Transform>(true))t.gameObject.layer=layer;
   foreach(var renderer in root.GetComponentsInChildren<SkinnedMeshRenderer>(true))renderer.updateWhenOffscreen=true;
   layer++;
  }
  var light=new GameObject("Comparison Light").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1;light.transform.rotation=Quaternion.Euler(35,-145,0);
  RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.65f,.65f,.65f);
  QualitySettings.vSyncCount=0;
  var a=original.GetComponent<Animator>();float top=a.GetBoneTransform(HumanBodyBones.Head).position.y+.24f;
  foreach(var r in original.GetComponentsInChildren<SkinnedMeshRenderer>(true))if(r.name=="Kemomimi"){
   var mesh=new Mesh();r.BakeMesh(mesh);foreach(var v in mesh.vertices)top=Mathf.Max(top,r.transform.TransformPoint(v).y+.05f);Destroy(mesh);}
  float lower=a.GetBoneTransform(HumanBodyBones.Hips).position.y-.4f;
  float upper=a.GetBoneTransform(HumanBodyBones.Chest).position.y-.02f;
  views=new[]{Create("front",lower,top,0),Create("hair-closeup",upper,top,25)};
 }
 View Create(string name,float bottom,float top,float yaw){
  const int w=960,h=1080;var view=new View{cameras=new Camera[2],targets=new RenderTexture[2],textures=new Texture2D[2],pixels=new byte[w*2*h*3]};
  for(int i=0;i<2;i++){
   var c=new GameObject(name+i).AddComponent<Camera>();c.enabled=false;c.cullingMask=1<<(8+i);
   c.clearFlags=CameraClearFlags.SolidColor;c.backgroundColor=new Color(.12f,.15f,.19f);c.nearClipPlane=.01f;c.farClipPlane=30;
   c.orthographic=true;c.orthographicSize=(top-bottom)*.5f;c.aspect=w/(float)h;
   var center=new Vector3(0,(top+bottom)*.5f,0);c.transform.position=center+Quaternion.Euler(0,yaw,0)*new Vector3(0,0,3);c.transform.LookAt(center);
   var rt=new RenderTexture(w,h,24,RenderTextureFormat.ARGB32){antiAliasing=4};rt.Create();c.targetTexture=rt;
   view.cameras[i]=c;view.targets[i]=rt;view.textures[i]=new Texture2D(w,h,TextureFormat.RGB24,false);
  }
  view.path=Path.Combine(outputDirectory,name+"-raw.mp4");
  var ff=Path.GetFullPath("../../../tools/bin/ffmpeg.exe");
  var info=new ProcessStartInfo(ff,"-hide_banner -loglevel error -y -f rawvideo -pixel_format rgb24 -video_size 1920x1080 -framerate 60 -i pipe:0 -vf vflip -an -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -movflags +faststart \""+view.path+"\""){
   UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true};
  view.encoder=Process.Start(info);view.stream=view.encoder.StandardInput.BaseStream;return view;
 }
 public void Capture(int frame){
  if(views==null)throw new Exception("Video capture not initialized");
  var old=RenderTexture.active;const int rowBytes=960*3;
  foreach(var v in views){
   for(int i=0;i<2;i++){
    v.cameras[i].Render();RenderTexture.active=v.targets[i];v.textures[i].ReadPixels(new Rect(0,0,960,1080),0,0,false);v.textures[i].Apply(false);
    byte[] raw=v.textures[i].GetRawTextureData();
    for(int y=0;y<1080;y++)Buffer.BlockCopy(raw,y*rowBytes,v.pixels,(y*2+i)*rowBytes,rowBytes);
   }
   v.stream.Write(v.pixels,0,v.pixels.Length);
  }
  RenderTexture.active=old;frames++;
 }
 public void Finish(){
  if(finished)return;finished=true;
  foreach(var v in views){v.stream.Dispose();if(!v.encoder.WaitForExit(60000)||v.encoder.ExitCode!=0)throw new Exception("Video encoder failed");}
  File.WriteAllText(Path.Combine(outputDirectory,"capture.json"),"{\"frames\":"+frames+",\"fps\":60,\"sdk\":\"3.10.5\",\"independentDamping\":1.5}");
  UnityEngine.Debug.Log("TANAKACAP_PHYS_VIDEO_COMPLETE frames="+frames);
 }
 void OnDestroy(){if(!finished&&views!=null)foreach(var v in views){try{v.stream?.Dispose();if(v.encoder!=null&&!v.encoder.HasExited)v.encoder.Kill();}catch{}}}
}
