using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;
namespace TanakaCap {
 // Window controls are not drawn into the explicit OBS render texture.
 public sealed class AvatarFraming:MonoBehaviour {
  public const float MinimumZoom=-1.4f,MaximumZoom=1f;
  [Serializable] public class Settings { public float height,zoom,fov=35; }
  Camera cameraComponent;Vector3 rest;Settings settings=new Settings();string path;bool expanded=true;Font uiFont;
  float appliedHeight,appliedZoom,appliedFov,restFov;Vector3 lastMouse;
  void Start(){
   cameraComponent=GetComponent<Camera>();rest=transform.position;
   restFov=cameraComponent.fieldOfView;settings.fov=restFov;
   if(!GetComponent<AvatarWindow>())gameObject.AddComponent<AvatarWindow>();
   uiFont=Font.CreateDynamicFontFromOSFont(new[]{"Yu Gothic UI","Meiryo","Arial"},14);
   var args=Environment.GetCommandLineArgs();int index=Array.IndexOf(args,"--avatar");
   string avatar=index>=0&&index+1<args.Length?Path.GetFullPath(args[index+1]):"default";
   string key;using(var sha=SHA256.Create())key=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(avatar.ToLowerInvariant()))).Replace("-","");
   path=Path.Combine(Application.persistentDataPath,"framing-"+key+".json");
   int check=Array.IndexOf(args,"--framing-check");
   if(check>=0&&check+1<args.Length){
    path=Path.GetFullPath(args[check+1]);
    if(File.Exists(path))throw new Exception("Framing check requires a new output path");
    settings.height=.2f;settings.zoom=.15f;settings.fov=45;Apply();Save();
    var loaded=JsonUtility.FromJson<Settings>(File.ReadAllText(path));
    if(loaded.height!=.2f||loaded.zoom!=.15f||loaded.fov!=45||cameraComponent.fieldOfView!=45||(transform.position-(rest+transform.up*.2f-transform.forward*.15f)).magnitude>1e-5f)throw new Exception("Framing save/movement failed");
    ResetFraming();if(File.Exists(path)||(transform.position-rest).magnitude>1e-5f||cameraComponent.fieldOfView!=restFov)throw new Exception("Framing reset failed");
    Debug.Log("TANAKACAP_FRAMING_CHECK_OK");enabled=false;return;
   }
   // Offline comparisons always start at the shared original composition.
   if(Array.IndexOf(args,"--render-replay")>=0){enabled=false;return;}
   if(File.Exists(path))try{settings=JsonUtility.FromJson<Settings>(File.ReadAllText(path))??new Settings();}catch(Exception e){Debug.LogWarning("Framing settings: "+e.Message);}
   if(float.IsNaN(settings.height)||float.IsInfinity(settings.height)||float.IsNaN(settings.zoom)||float.IsInfinity(settings.zoom))settings=new Settings();
   if(settings.fov<=0||float.IsNaN(settings.fov)||float.IsInfinity(settings.fov))settings.fov=restFov;
   Apply();
  }
  void Apply(){
   settings.height=Mathf.Clamp(settings.height,-.6f,.6f);settings.zoom=Mathf.Clamp(settings.zoom,MinimumZoom,MaximumZoom);
   settings.fov=Mathf.Clamp(settings.fov,15,80);cameraComponent.fieldOfView=settings.fov;
   var next=rest+transform.up*settings.height-transform.forward*settings.zoom;
   var delta=next-transform.position;
   foreach(var driver in FindObjectsOfType<AvatarDriver>())driver.CameraFramingChanged(delta);
   transform.position=next;appliedHeight=settings.height;appliedZoom=settings.zoom;appliedFov=settings.fov;
   var output=GetComponent<AlphaOutput>();if(output)output.FramingChanged();
  }
  public bool OverControls(){
   var mouse=new Vector2(Input.mousePosition.x,Screen.height-Input.mousePosition.y);
   return enabled&&expanded&&new Rect(Screen.width-282,12,270,232).Contains(mouse);
  }
  void Update(){
   if(Input.GetKeyDown(KeyCode.Escape))expanded=!expanded;
   if(!OverControls()){
    bool changed=false;
    if(Input.GetMouseButton(1)&&!Input.GetMouseButtonDown(1)){
     settings.height-=(Input.mousePosition.y-lastMouse.y)/Mathf.Max(Screen.height,1)*1.2f;changed=true;
    }
    float scroll=Input.mouseScrollDelta.y;
    if(scroll!=0){
     if(Input.GetKey(KeyCode.LeftControl)||Input.GetKey(KeyCode.RightControl))settings.fov-=scroll*2;
     else settings.zoom-=scroll*.05f;
     changed=true;
    }
    if(changed)Apply();
   }
   lastMouse=Input.mousePosition;
  }
  void Save(){Directory.CreateDirectory(Path.GetDirectoryName(path));File.WriteAllText(path,JsonUtility.ToJson(settings));}
  void ResetFraming(){settings=new Settings{fov=restFov};Apply();if(File.Exists(path))File.Delete(path);}
  void OnGUI(){
   var oldFont=GUI.skin.font;if(uiFont)GUI.skin.font=uiFont;
   if(!expanded){GUI.skin.font=oldFont;return;}
   GUI.Box(new Rect(Screen.width-282,12,270,232),"");
   GUI.Label(new Rect(Screen.width-270,22,250,22),"上下");
   settings.height=GUI.HorizontalSlider(new Rect(Screen.width-270,52,242,20),settings.height,-.6f,.6f);
   GUI.Label(new Rect(Screen.width-270,74,250,22),"寄り・引き");
   settings.zoom=GUI.HorizontalSlider(new Rect(Screen.width-270,104,242,20),settings.zoom,MinimumZoom,MaximumZoom);
   GUI.Label(new Rect(Screen.width-270,126,250,22),"FOV  "+settings.fov.ToString("F1")+"°");
   settings.fov=GUI.HorizontalSlider(new Rect(Screen.width-270,156,242,20),settings.fov,15,80);
   if(settings.height!=appliedHeight||settings.zoom!=appliedZoom||settings.fov!=appliedFov)Apply();
   if(GUI.Button(new Rect(Screen.width-270,198,110,30),"保存"))Save();
   if(GUI.Button(new Rect(Screen.width-150,198,110,30),"リセット"))ResetFraming();
   GUI.skin.font=oldFont;
  }
 }
}
