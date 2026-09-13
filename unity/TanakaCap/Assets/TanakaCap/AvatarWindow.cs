using System;
using System.Runtime.InteropServices;
using System.Text;
using UnityEngine;
namespace TanakaCap {
 public sealed class AvatarWindow:MonoBehaviour {
  [DllImport("user32.dll",EntryPoint="GetWindowLongPtrW")] static extern IntPtr GetStyle(IntPtr h,int index);
  [DllImport("user32.dll",EntryPoint="SetWindowLongPtrW")] static extern IntPtr SetStyle(IntPtr h,int index,IntPtr value);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
  [DllImport("user32.dll")] static extern bool ReleaseCapture();
  [DllImport("user32.dll",EntryPoint="SendMessageW")] static extern IntPtr SendMessage(IntPtr h,uint message,IntPtr wp,IntPtr lp);
  delegate bool WindowVisitor(IntPtr window,IntPtr parameter);
  [DllImport("user32.dll")] static extern bool EnumWindows(WindowVisitor visitor,IntPtr parameter);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr window,out uint process);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr window,StringBuilder name,int capacity);
  [DllImport("user32.dll")] static extern bool IsWindow(IntPtr window);
  [StructLayout(LayoutKind.Sequential)] struct Rect {public int left,top,right,bottom;}
  [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr window,out Rect rect);
  IntPtr handle;
  float nextCheck;
  const long FrameBits=0x00C00000L|0x00040000L; // caption, border and resizing frame
  void ConfigureWindow(){
   if(handle==IntPtr.Zero||!IsWindow(handle)){
    handle=IntPtr.Zero;
    uint process=(uint)System.Diagnostics.Process.GetCurrentProcess().Id;
    EnumWindows((window,unused)=>{
     GetWindowThreadProcessId(window,out uint owner);
     if(owner!=process)return true;
     var name=new StringBuilder(128);GetClassName(window,name,name.Capacity);
     if(name.ToString()!="UnityWndClass")return true;
     handle=window;return false;
    },IntPtr.Zero);
   }
   if(handle==IntPtr.Zero)return;
   var output=GetComponent<AlphaOutput>();if(!output)return;
   long style=GetStyle(handle,-16).ToInt64();
   if(!GetClientRect(handle,out var rect))return;
   if((style&FrameBits)==0&&rect.right-rect.left==output.OutputWidth&&rect.bottom-rect.top==output.OutputHeight)return;
   // Unity's asynchronous SetResolution can restore decorations after startup.
   // Apply and verify the actual client size after removing every non-client frame.
   SetStyle(handle,-16,new IntPtr(style&~FrameBits));
   SetWindowPos(handle,IntPtr.Zero,0,0,output.OutputWidth,output.OutputHeight,0x0036);
  }
  void Update(){
   if(Application.platform!=RuntimePlatform.WindowsPlayer||Application.isBatchMode)return;
   if(Time.unscaledTime>=nextCheck){nextCheck=Time.unscaledTime+.5f;ConfigureWindow();}
   if(handle==IntPtr.Zero)return;
   var framing=GetComponent<AvatarFraming>();
   if(Input.GetMouseButtonDown(0)&&(!framing||!framing.OverControls())){ReleaseCapture();SendMessage(handle,0x00A1,new IntPtr(2),IntPtr.Zero);}
  }
 }
}
