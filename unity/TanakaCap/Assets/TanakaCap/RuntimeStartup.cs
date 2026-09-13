using System;
using System.IO;
using UnityEngine;
namespace TanakaCap {
 public static class RuntimeStartup {
  static readonly object gate=new object();
  static string errorLogPath;
  public static string ErrorLogPath=>errorLogPath;
  [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
  static void Initialize(){
   errorLogPath=Path.Combine(Directory.GetParent(Application.dataPath).FullName,"logs","player-errors.log");
   Application.logMessageReceivedThreaded-=WriteError;
   Application.logMessageReceivedThreaded+=WriteError;
   // Enforce a limit before loading an avatar; its driver might never start.
   QualitySettings.vSyncCount=0;
   Application.targetFrameRate=InitialFrameRate(Environment.GetCommandLineArgs());
  }
  public static int InitialFrameRate(string[] args){
   int i=Array.IndexOf(args,"--render-fps");
   return i>=0&&i+1<args.Length&&int.TryParse(args[i+1],out int fps)&&fps>=1&&fps<=240?fps:60;
  }
  static void WriteError(string message,string stack,LogType type){
   if(type!=LogType.Error&&type!=LogType.Exception&&type!=LogType.Assert)return;
   lock(gate)try {
    string path=ErrorLogPath;Directory.CreateDirectory(Path.GetDirectoryName(path));
    if(File.Exists(path)&&new FileInfo(path).Length>1024*1024){string previous=path+".previous";if(File.Exists(previous))File.Delete(previous);File.Move(path,previous);}
    File.AppendAllText(path,DateTime.UtcNow.ToString("O")+" "+type+"\n"+message+"\n"+stack+"\n");
   }catch { /* Do not recurse into Unity logging if the log directory is unwritable. */ }
  }
 }
}
