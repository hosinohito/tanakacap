using System;
using System.IO;
using System.Globalization;
using System.Runtime.InteropServices;
using UnityEngine;
using UnityEngine.Profiling;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;
using System.Collections.Generic;

namespace TanakaCap
{
    // Explicit diagnostic only. Bounded one-second arrays, no image readback.
    [DefaultExecutionOrder(1100)]
    public sealed class PerformanceProbe : MonoBehaviour
    {
        StreamWriter writer;
        double start, previous, window;
        double duration;
        int count, frames;
        double renderSum, renderMax, secondaryMax, ageSum;
        int ageCount;
        long packets,lastTimedSequence=-1;
        int latencyCount;
        readonly double[] readLatency=new double[2048],sendLatency=new double[2048];
        [DllImport("Kernel32.dll")] static extern bool QueryPerformanceCounter(out long count);
        [DllImport("Kernel32.dll")] static extern bool QueryPerformanceFrequency(out long frequency);
        long clockFrequency;
        ProfilerRecorder gpuRecorder;
        double gpuSum,gpuMax;
        int gpuCount;
        readonly double[] intervals=new double[2048];
        AvatarDriver driver;
        SecondaryMotion secondary;
        AlphaOutput output;
        [Serializable] class Sample
        {
            public double seconds,windowSeconds,fps,frameP50Ms,frameP95Ms,frameMaxMs;
            public double latestInputReadToRenderSubmitP50Ms,latestInputReadToRenderSubmitP95Ms,sendToRenderSubmitP50Ms;
            public int timedPackets,gpuSamples;
            public double gpuFrameMeanMs,gpuFrameMaxMs;
            public double renderSubmitMeanMs,renderSubmitMaxMs,secondaryMaxMs,packetAgeMeanMs;
            public long receivedPackets,appliedSequence,managedBytes,allocatedBytes,reservedBytes;
            public bool edgeAA;
            public int width,height;
        }
        void Start()
        {
            var args=Environment.GetCommandLineArgs();
            int i=Array.IndexOf(args,"--performance-log");
            if(i<0){enabled=false;return;}
            if(i+1>=args.Length)throw new ArgumentException("--performance-log requires a path");
            int j=Array.IndexOf(args,"--performance-seconds");
            if(j>=0 && (j+1>=args.Length || !double.TryParse(args[j+1],NumberStyles.Float,CultureInfo.InvariantCulture,out duration) || duration<=0))
                throw new ArgumentException("Invalid --performance-seconds");
            if(!QueryPerformanceFrequency(out clockFrequency) || clockFrequency<=0)throw new Exception("QPC unavailable");
            writer=new StreamWriter(args[i+1],false);
            output=GetComponent<AlphaOutput>();
            if(Array.IndexOf(args,"--performance-gpu")>=0)
            {
                var available=new List<ProfilerRecorderHandle>();
                ProfilerRecorderHandle.GetAvailable(available);
                foreach(var handle in available)
                {
                    var description=ProfilerRecorderHandle.GetDescription(handle);
                    if(description.Name=="GPU Frame Time")
                    {gpuRecorder=ProfilerRecorder.StartNew(description.Category,description.Name);break;}
                }
                Debug.Log("TANAKACAP_GPU_RECORDER valid="+gpuRecorder.Valid);
            }
            start=previous=window=Time.realtimeSinceStartupAsDouble;
        }
        void LateUpdate()
        {
            if(writer==null)return;
            double now=Time.realtimeSinceStartupAsDouble;
            if(count<intervals.Length)intervals[count++]=(now-previous)*1000;
            previous=now;frames++;
            if(!driver)driver=FindObjectOfType<AvatarDriver>();
            if(!secondary && driver)secondary=driver.GetComponent<SecondaryMotion>();
            if(gpuRecorder.Valid && gpuRecorder.LastValue>0)
            {double ms=gpuRecorder.LastValue/1000000.0;gpuSum+=ms;gpuMax=Math.Max(gpuMax,ms);gpuCount++;}
            double submit=output.RenderSubmitMilliseconds;
            renderSum+=submit;renderMax=Math.Max(renderMax,submit);
            if(secondary)secondaryMax=Math.Max(secondaryMax,secondary.LastStepMilliseconds);
            if(driver && driver.PacketAgeMilliseconds>=0){ageSum+=driver.PacketAgeMilliseconds;ageCount++;}
            if(driver && driver.AppliedSequence!=lastTimedSequence && driver.InputReadTime>0 && driver.InputSentTime>=driver.InputReadTime)
            {
                QueryPerformanceCounter(out long ticks);
                double read=(ticks/(double)clockFrequency-driver.InputReadTime)*1000;
                double sent=(ticks/(double)clockFrequency-driver.InputSentTime)*1000;
                if(read>=0 && read<10000 && sent>=0 && latencyCount<readLatency.Length)
                {readLatency[latencyCount]=read;sendLatency[latencyCount++]=sent;}
                lastTimedSequence=driver.AppliedSequence;
            }
            if(now-window>=1)Flush(now);
            if(duration>0 && now-start>=duration)Application.Quit();
        }
        void Flush(double now)
        {
            if(frames==0)return;
            Array.Sort(intervals,0,count);
            Array.Sort(readLatency,0,latencyCount);Array.Sort(sendLatency,0,latencyCount);
            long received=driver?driver.ReceivedPackets:0;
            var sample=new Sample{
                gpuSamples=gpuCount,gpuFrameMeanMs=gpuCount==0?-1:gpuSum/gpuCount,gpuFrameMaxMs=gpuCount==0?-1:gpuMax,
                timedPackets=latencyCount,
                latestInputReadToRenderSubmitP50Ms=latencyCount==0?-1:readLatency[(latencyCount-1)/2],
                latestInputReadToRenderSubmitP95Ms=latencyCount==0?-1:readLatency[(int)((latencyCount-1)*.95)],
                sendToRenderSubmitP50Ms=latencyCount==0?-1:sendLatency[(latencyCount-1)/2],
                seconds=now-start,windowSeconds=now-window,fps=frames/(now-window),
                frameP50Ms=intervals[(count-1)/2],frameP95Ms=intervals[(int)((count-1)*.95)],frameMaxMs=intervals[count-1],
                renderSubmitMeanMs=renderSum/frames,renderSubmitMaxMs=renderMax,secondaryMaxMs=secondaryMax,
                packetAgeMeanMs=ageCount==0?-1:ageSum/ageCount,receivedPackets=received-packets,
                appliedSequence=driver?driver.AppliedSequence:-1,edgeAA=EdgeAntialiasing.Active,
                managedBytes=GC.GetTotalMemory(false),allocatedBytes=Profiler.GetTotalAllocatedMemoryLong(),
                reservedBytes=Profiler.GetTotalReservedMemoryLong(),width=output.OutputWidth,height=output.OutputHeight
            };
            writer.WriteLine(JsonUtility.ToJson(sample));writer.Flush();
            gpuCount=0;gpuSum=gpuMax=0;
            packets=received;window=now;count=frames=ageCount=latencyCount=0;renderSum=renderMax=secondaryMax=ageSum=0;
        }
        void OnDestroy()
        {
            if(gpuRecorder.Valid)gpuRecorder.Dispose();
            if(writer==null)return;
            Flush(Time.realtimeSinceStartupAsDouble);writer.Dispose();writer=null;
        }
    }
}
