using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
namespace TanakaCap {
 public sealed class UiStatusFeedback:MonoBehaviour {
  [Serializable] class Status { public string kind="player"; public float renderHz,receiveHz,loopHz; public PartStatus[] parts; }
  UdpClient client; IPEndPoint endpoint; AlphaOutput output; AvatarDriver driver;
  float previous;long renders,received,loops;long totalLoops;
  void Start(){
   var args=Environment.GetCommandLineArgs();int index=Array.IndexOf(args,"--ui-status-port");
   if(index<0){enabled=false;return;}
   if(index+1>=args.Length||!int.TryParse(args[index+1],out int port)||port<1||port>65535)throw new ArgumentException("Invalid UI status port");
   client=new UdpClient();endpoint=new IPEndPoint(IPAddress.Loopback,port);output=GetComponent<AlphaOutput>();previous=Time.realtimeSinceStartup;
  }
  void Update(){
   totalLoops++;if(!driver)driver=FindObjectOfType<AvatarDriver>();
   float now=Time.realtimeSinceStartup,elapsed=now-previous;if(elapsed<.5f)return;
   long current=driver?driver.ReceivedPackets:0;
   var message=new Status{parts=driver?driver.PartStatuses:null,renderHz=(output.RenderedFrames-renders)/elapsed,receiveHz=(current-received)/elapsed,loopHz=(totalLoops-loops)/elapsed};
   byte[] bytes=Encoding.UTF8.GetBytes(JsonUtility.ToJson(message));
   try{client.Send(bytes,bytes.Length,endpoint);}catch(SocketException){}
   previous=now;renders=output.RenderedFrames;received=current;loops=totalLoops;
  }
  void OnDestroy(){client?.Close();}
 }
}
