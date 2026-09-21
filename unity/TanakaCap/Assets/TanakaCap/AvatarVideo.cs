using System;
using System.IO;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace TanakaCap
{
    // Explicit offline mode only: replay timestamps drive the existing controller.
    public partial class AvatarDriver
    {
        bool videoMode;
        [Serializable] class VideoArmPose
        {
            public Vector3 leftElbow,leftWrist,rightElbow,rightWrist;
            public float leftTwist,rightTwist,leftRequestedTwist,rightRequestedTwist,leftElbowTwist,rightElbowTwist;
            public Quaternion leftUpperRotation,leftLowerRotation,rightUpperRotation,rightLowerRotation;
        }
        [Serializable] class VideoReport
        {
            public string status="complete",source,output;
            public int frames,width=1280,height=720,fps=30,packets;
            public double duration;
            public string armCorrection;
            public Vector3 headProxyRadii;
            public int headCorrections,crossBodyCues,wristFrontClamps,outwardElbowCues;
            public VideoArmPose[] armPoses;
            public bool wristHeadOnly;
            public string armRotation;
            public float twistLimit;
            public int handHeadCorrections;
            public float maximumHandHeadShift,maximumHandHeadResidual;
        }
        bool TryStartVideo(string[] args)
        {
            int input=Array.IndexOf(args,"--render-replay");
            if(input<0)return false;
            videoMode=true;
            var secondary=GetComponent<SecondaryMotion>();if(secondary)secondary.externalClock=true;
            int output=Array.IndexOf(args,"--video-output"),encoder=Array.IndexOf(args,"--ffmpeg");
            if(input+1>=args.Length || output<0 || output+1>=args.Length || encoder<0 || encoder+1>=args.Length)
                throw new ArgumentException("Video mode requires replay, output and ffmpeg paths");
            StartCoroutine(RenderVideo(args[input+1],args[output+1],args[encoder+1]));
            return true;
        }
        IEnumerator RenderVideo(string input,string output,string encoder)
        {
            yield return null; // Finish camera/component initialization first.
            var job=RenderVideoFrames(input,output,encoder);
            while(true)
            {
                bool more=false;Exception failure=null;
                try { more=job.MoveNext(); } catch(Exception ex) { failure=ex; }
                if(failure!=null)
                {
                    Debug.LogException(failure);File.WriteAllText(output+".error.txt",failure.ToString());Application.Quit(1);yield break;
                }
                if(!more) {Application.Quit(0);yield break;}
                yield return job.Current;
            }
        }
        void VideoStep(double interval)
        {
            while(interval>1e-8)
            {
                probeDelta=(float)Math.Min(interval,1.0/60);
                lastReceived=Time.unscaledTime;
                var secondary=GetComponent<SecondaryMotion>();if(secondary)secondary.Restore();
                LateUpdate();
                if(secondary)secondary.Step(probeDelta);
                interval-=probeDelta;
            }
            probeDelta=0;
        }
        static string VideoQuote(string path)
        {
            if(path.Contains("\""))throw new ArgumentException("Invalid path");
            return "\""+path+"\"";
        }
        IEnumerator RenderVideoFrames(string input,string output,string encoder)
        {
            if(File.Exists(output))throw new IOException("Video output already exists");
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output)));
            var rows=new List<ReplayRow>();var times=new List<double>();double end=0;
            foreach(var line in File.ReadLines(input))
            {
                var row=JsonUtility.FromJson<ReplayRow>(line);
                if(row==null || row.packet==null || !Finite(row.packet) || row.dt<=0 || float.IsNaN(row.dt) || float.IsInfinity(row.dt))
                    throw new InvalidDataException("Invalid replay row");
                if(rows.Count>0)end+=row.dt;
                times.Add(end);rows.Add(row);
            }
            if(rows.Count==0)throw new InvalidDataException("Empty replay");
            // Last sample is displayed for one output frame.
            int frames=(int)Math.Ceiling((end+1.0/30)*30);
            var camera=Camera.main;var oldTarget=camera.targetTexture;var oldActive=RenderTexture.active;
            var target=new RenderTexture(1280,720,24,RenderTextureFormat.ARGB32);
            target.antiAliasing=4;target.Create();
            var pixels=new Texture2D(1280,720,TextureFormat.RGB24,false);
            var errors=new StringBuilder();
            var armPoses=new List<VideoArmPose>();
            var start=new System.Diagnostics.ProcessStartInfo {
                FileName=encoder,
                Arguments="-hide_banner -loglevel error -n -f rawvideo -pixel_format rgb24 -video_size 1280x720 -framerate 30 -i pipe:0 -vf vflip -an -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -movflags +faststart "+VideoQuote(output),
                UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardError=true
            };
            using(var process=new System.Diagnostics.Process { StartInfo=start })
            {
                process.ErrorDataReceived+=(sender,eventArgs)=>{if(eventArgs.Data!=null)lock(errors)errors.AppendLine(eventArgs.Data);};
                try
                {
                    process.Start();process.BeginErrorReadLine();camera.targetTexture=target;
                    current=rows[0].packet;int index=0;double simulation=0;
                    for(int frame=0;frame<frames;frame++)
                    {
                        double time=frame/30.0;
                        while(index+1<rows.Count && times[index+1]<=time)
                        {
                            VideoStep(times[index+1]-simulation);simulation=times[index+1];current=rows[++index].packet;
                        }
                        VideoStep(time-simulation);simulation=time;
                        // Unity refreshes skinned meshes once per engine frame.
                        // Manual Camera.Render calls inside one frame reuse stale skinning.
                        yield return null;
                        armPoses.Add(new VideoArmPose {leftElbow=left.lower.position,leftWrist=left.hand.position,
                            rightElbow=right.lower.position,rightWrist=right.hand.position,
                            leftTwist=left.twist,rightTwist=right.twist,leftRequestedTwist=left.requestedTwist,rightRequestedTwist=right.requestedTwist,
                            leftElbowTwist=ElbowAxialTwist(left),rightElbowTwist=ElbowAxialTwist(right),
                            leftUpperRotation=left.upper.localRotation,leftLowerRotation=left.lower.localRotation,
                            rightUpperRotation=right.upper.localRotation,rightLowerRotation=right.lower.localRotation});
                        camera.Render();RenderTexture.active=target;
                        pixels.ReadPixels(new Rect(0,0,1280,720),0,0,false);
                        var bytes=pixels.GetRawTextureData();
                        process.StandardInput.BaseStream.Write(bytes,0,bytes.Length);
                        if(frame%300==0)Debug.Log("TANAKACAP_VIDEO "+frame+"/"+frames);
                    }
                    process.StandardInput.Close();
                    if(!process.WaitForExit(60000))throw new TimeoutException("Encoder did not finish");
                    process.WaitForExit();
                    if(process.ExitCode!=0)throw new IOException("Encoder failed: "+errors);
                    File.WriteAllText(output+".json",JsonUtility.ToJson(new VideoReport {source=input,output=output,frames=frames,packets=rows.Count,duration=frames/30.0,
                        armCorrection=armCorrectionTrial,headProxyRadii=headClearance.radii,headCorrections=headCorrectionCount,
                        crossBodyCues=crossCorrectionCount,wristFrontClamps=wristCorrectionCount,outwardElbowCues=outwardCorrectionCount,
                        armRotation=legacyArmRotation?"legacy":"hinge",twistLimit=float.IsInfinity(armTwistLimit)?-1:armTwistLimit,
                        wristHeadOnly=wristHeadOnly,handHeadCorrections=handHeadCorrections,maximumHandHeadShift=maximumHandHeadShift,
                        maximumHandHeadResidual=maximumHandHeadResidual,armPoses=armPoses.ToArray()},true));
                    Debug.Log("TANAKACAP_VIDEO_OK "+output);
                }
                finally
                {
                    camera.targetTexture=oldTarget;RenderTexture.active=oldActive;probeDelta=0;
                    Destroy(pixels);target.Release();Destroy(target);
                    try {if(!process.HasExited)process.Kill();}catch(InvalidOperationException){}
                }
            }
        }
    }
}
