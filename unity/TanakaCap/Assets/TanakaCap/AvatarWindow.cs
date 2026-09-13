using System;
using System.Runtime.InteropServices;
using UnityEngine;
namespace TanakaCap {
 public sealed class AvatarWindow:MonoBehaviour {
  [DllImport("user32.dll",EntryPoint="GetWindowLongPtrW")] static extern IntPtr GetStyle(IntPtr h,int index);
  [DllImport("user32.dll",EntryPoint="SetWindowLongPtrW")] static extern IntPtr SetStyle(IntPtr h,int index,IntPtr value);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
  [DllImport("user32.dll")] static extern bool ReleaseCapture();
  [DllImport("user32.dll",EntryPoint="SendMessageW")] static extern IntPtr SendMessage(IntPtr h,uint message,IntPtr wp,IntPtr lp);
  IntPtr handle;
  void Update(){
   if(Application.platform!=RuntimePlatform.WindowsPlayer||Application.isBatchMode)return;
   if(handle==IntPtr.Zero){
    using(var p=System.Diagnostics.Process.GetCurrentProcess()){p.Refresh();handle=p.MainWindowHandle;}
    if(handle==IntPtr.Zero)return;
    long style=GetStyle(handle,-16).ToInt64();SetStyle(handle,-16,new IntPtr(style&~0x00C00000L));
    SetWindowPos(handle,IntPtr.Zero,0,0,0,0,0x0027); // frame changed; retain position, size and Z order
   }
   var framing=GetComponent<AvatarFraming>();
   if(Input.GetMouseButtonDown(0)&&(!framing||!framing.OverControls())){ReleaseCapture();SendMessage(handle,0x00A1,new IntPtr(2),IntPtr.Zero);}
  }
 }
}
