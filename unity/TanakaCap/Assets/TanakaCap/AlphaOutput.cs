using System;
using System.IO;
using UnityEngine;
using Klak.Spout;

namespace TanakaCap
{
    // A separate camera keeps preview/UI out of the RGBA texture sent to OBS.
    [DefaultExecutionOrder(1000)]
    public sealed class AlphaOutput : MonoBehaviour
    {
        public SpoutResources resources;
        public Shader edgeShader;
        public int OutputWidth { get; private set; }=1280;
        public int OutputHeight { get; private set; }=720;
        public double RenderSubmitMilliseconds { get; private set; }
        Camera outputCamera;
        RenderTexture texture;
        SpoutSender sender;
        bool quitting;
        bool readyToQuit;
        [NonSerialized] public int exitCode;

        void Start()
        {
            EdgeAntialiasing.Active=Array.IndexOf(Environment.GetCommandLineArgs(),"--no-edge-aa")<0;
            var previewAA=gameObject.AddComponent<EdgeAntialiasing>();
            previewAA.shader=edgeShader;
            var startupArgs=Environment.GetCommandLineArgs();
            int heightIndex=Array.IndexOf(startupArgs,"--output-height");
            if(heightIndex>=0)
            {
                if(heightIndex+1>=startupArgs.Length || !int.TryParse(startupArgs[heightIndex+1],out int height) || (height!=720 && height!=1080))
                    throw new ArgumentException("--output-height must be 720 or 1080");
                OutputHeight=height;OutputWidth=height*16/9;
            }
            texture=new RenderTexture(OutputWidth,OutputHeight,24,RenderTextureFormat.ARGB32);
            texture.name="TanakaCap RGBA";
            texture.antiAliasing=4;
            texture.Create();
            outputCamera=new GameObject("Transparent Output").AddComponent<Camera>();
            outputCamera.CopyFrom(GetComponent<Camera>());
            outputCamera.transform.SetParent(transform,false);
            outputCamera.transform.localPosition=Vector3.zero;
            outputCamera.transform.localRotation=Quaternion.identity;
            outputCamera.ResetWorldToCameraMatrix();
            outputCamera.clearFlags=CameraClearFlags.SolidColor;
            outputCamera.backgroundColor=Color.clear;
            outputCamera.allowHDR=false;
            outputCamera.allowMSAA=true;
            outputCamera.targetTexture=texture;
            outputCamera.enabled=false;
            outputCamera.gameObject.AddComponent<EdgeAntialiasing>().shader=edgeShader;
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--performance-log")>=0)gameObject.AddComponent<PerformanceProbe>();
            sender=outputCamera.gameObject.AddComponent<SpoutSender>();
            sender.SetResources(resources);
            sender.spoutName="TanakaCap";
            sender.captureMethod=CaptureMethod.Texture;
            sender.sourceTexture=texture;
            sender.keepAlpha=true;
            Debug.Log("TANAKACAP_ALPHA_OUTPUT_READY "+OutputWidth+"x"+OutputHeight+" RGBA Spout=TanakaCap edgeAA="+EdgeAntialiasing.Active);
            Application.wantsToQuit+=WantsToQuit;
            var args=Environment.GetCommandLineArgs();
            int check=Array.IndexOf(args,"--aa-check");
            if(check>=0 && check+1<args.Length)StartCoroutine(CheckAA(args[check+1]));

        }

        void LateUpdate()
        {
            // Explicit offscreen rendering also runs when the preview is hidden.
            if(Input.GetKeyDown(KeyCode.F7))EdgeAntialiasing.Active=!EdgeAntialiasing.Active;
            if(outputCamera && texture && !quitting)
            {
                var start=System.Diagnostics.Stopwatch.GetTimestamp();
                outputCamera.Render();
                RenderSubmitMilliseconds=(System.Diagnostics.Stopwatch.GetTimestamp()-start)*1000.0/System.Diagnostics.Stopwatch.Frequency;
            }
        }

        // Readback is diagnostic-only; normal output stays on the GPU.
        public void CheckOutput(string path,bool requireSender)
        {
            outputCamera.Render();
            var previous=RenderTexture.active;
            var image=new Texture2D(texture.width,texture.height,TextureFormat.RGBA32,false);
            try
            {
                RenderTexture.active=texture;
                image.ReadPixels(new Rect(0,0,texture.width,texture.height),0,0);
                image.Apply();
                int transparent=0,opaque=0,partial=0;
                foreach(var p in image.GetPixels32())
                    if(p.a==0)transparent++;else if(p.a==255)opaque++;else partial++;
                File.WriteAllBytes(path+".alpha.png",image.EncodeToPNG());
                if(transparent<10000 || opaque<10000)
                    throw new Exception("Output must contain both transparent background and opaque avatar: "+transparent+" / "+opaque);
                if(requireSender && Array.IndexOf(SpoutManager.GetSourceNames(),"TanakaCap")<0)
                    throw new Exception("Spout sender was not registered");
                Debug.Log("TANAKACAP_ALPHA_OK transparent="+transparent+" opaque="+opaque+" partial="+partial+" senderChecked="+requireSender);
            }
            finally { RenderTexture.active=previous;Destroy(image); }
        }

        System.Collections.IEnumerator CheckAA(string path)
        {
            yield return new WaitForSeconds(3);
            bool saved=EdgeAntialiasing.Active;
            try
            {
                EdgeAntialiasing.Active=false;CheckOutput(path+".off",false);
                EdgeAntialiasing.Active=true;CheckOutput(path+".on",false);
                Debug.Log("TANAKACAP_AA_CHECK_OK");
            }
            finally {EdgeAntialiasing.Active=saved;}
            Application.Quit();
        }

        bool WantsToQuit()
        {
            if(readyToQuit)return true;
            if(!quitting){quitting=true;StartCoroutine(StopBeforeQuit());}
            return false;
        }

        System.Collections.IEnumerator StopBeforeQuit()
        {
            ReleaseOutput();
            // Let native render-thread close events finish before device teardown.
            yield return null;
            yield return null;
            readyToQuit=true;
            Application.Quit(exitCode);
        }

        void ReleaseOutput()
        {
            RenderTexture.active=null;
            if(sender)sender.enabled=false;
            if(outputCamera){outputCamera.enabled=false;outputCamera.targetTexture=null;Destroy(outputCamera.gameObject);}
            if(texture){if(RenderTexture.active==texture)RenderTexture.active=null;texture.Release();Destroy(texture);}
            sender=null;outputCamera=null;texture=null;
        }

        void OnDestroy(){Application.wantsToQuit-=WantsToQuit;ReleaseOutput();}
    }
}
