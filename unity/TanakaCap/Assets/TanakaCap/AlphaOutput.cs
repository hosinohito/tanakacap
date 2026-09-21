using System;
using System.IO;
using System.Runtime.InteropServices;
using UnityEngine;
using Klak.Spout;

namespace TanakaCap
{
    // A separate camera keeps preview/UI out of the RGBA texture sent to OBS.
    [DefaultExecutionOrder(1000)]
    public sealed class AlphaOutput : MonoBehaviour
    {
        [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr window,int command);
        System.Collections.IEnumerator HidePreviewWindow(){
            for(int i=0;i<60;i++){
                var process=System.Diagnostics.Process.GetCurrentProcess();process.Refresh();var window=process.MainWindowHandle;process.Dispose();
                if(window!=IntPtr.Zero){ShowWindow(window,0);yield break;}
                yield return null;
            }
        }
        public SpoutResources resources;
        public Shader edgeShader;
        public Shader previewShader;
        public void FramingChanged(){lastPacket=-1;}
        public int OutputWidth { get; private set; }=1920;
        public int OutputHeight { get; private set; }=1080;
        public bool PreviewVisible { get; private set; }=true;
        public bool SharedPreview { get; private set; }=true;
        Camera previewCamera;
        Material previewMaterial;
        int previewMask;
        public double RenderSubmitMilliseconds { get; private set; }
        public long RenderedFrames {get;private set;}
        bool inferenceSync;AvatarDriver syncDriver;long lastPacket=-1;float lastOutput=-1;
        Camera outputCamera;
        RenderTexture texture;
        SpoutSender sender;
        bool quitting;
        bool readyToQuit;
        [NonSerialized] public int exitCode;

        void Start()
        {
            EdgeAntialiasing.Active=Array.IndexOf(Environment.GetCommandLineArgs(),"--no-edge-aa")<0;
            var startupArgs=Environment.GetCommandLineArgs();
            inferenceSync=Array.IndexOf(startupArgs,"--render-sync")>=0;
            if(Array.IndexOf(startupArgs,"--ui-status-port")>=0)gameObject.AddComponent<UiStatusFeedback>();
            SharedPreview=Array.IndexOf(startupArgs,"--legacy-preview")<0;
            PreviewVisible=Array.IndexOf(startupArgs,"--no-preview")<0;
            if(!PreviewVisible && Application.platform==RuntimePlatform.WindowsPlayer)StartCoroutine(HidePreviewWindow());
            int heightIndex=Array.IndexOf(startupArgs,"--output-height");
            if(heightIndex>=0)
            {
                if(heightIndex+1>=startupArgs.Length || !int.TryParse(startupArgs[heightIndex+1],out int height) || height<64 || height>4096)
                    throw new ArgumentException("--output-height must be 64..4096");
                OutputHeight=height;OutputWidth=height*16/9;
            }
            int widthIndex=Array.IndexOf(startupArgs,"--output-width");
            if(widthIndex>=0)
            {
                if(widthIndex+1>=startupArgs.Length || !int.TryParse(startupArgs[widthIndex+1],out int width) || width<64 || width>4096)
                    throw new ArgumentException("--output-width must be 64..4096");
                OutputWidth=width;
            }
            if(OutputWidth>4096 || OutputWidth>SystemInfo.maxTextureSize || OutputHeight>SystemInfo.maxTextureSize)
                throw new ArgumentException("Output dimensions exceed supported texture size");
            if(!Application.isBatchMode)Screen.SetResolution(OutputWidth,OutputHeight,FullScreenMode.Windowed);
            previewCamera=GetComponent<Camera>();
            previewCamera.backgroundColor=Color.black;
            int backgroundArg=Array.IndexOf(startupArgs,"--preview-background");
            if(backgroundArg>=0){
                if(backgroundArg+1>=startupArgs.Length)throw new ArgumentException("Preview background is missing");
                switch(startupArgs[backgroundArg+1]){
                    case "green":previewCamera.backgroundColor=Color.green;break;
                    case "blue":previewCamera.backgroundColor=Color.blue;break;
                    case "magenta":previewCamera.backgroundColor=Color.magenta;break;
                    case "none":break;
                    default:throw new ArgumentException("Unknown preview background");
                }
            }
            if(!GetComponent<AvatarFraming>())gameObject.AddComponent<AvatarFraming>();
            previewMask=previewCamera.cullingMask;
            if(SharedPreview)
            {
                if(!previewShader || !previewShader.isSupported)throw new Exception("Preview shader unavailable");
                previewMaterial=new Material(previewShader){hideFlags=HideFlags.HideAndDontSave};
            }
            else gameObject.AddComponent<EdgeAntialiasing>().shader=edgeShader;
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
            outputCamera.aspect=(float)OutputWidth/OutputHeight;
            outputCamera.enabled=false;
            previewCamera.cullingMask=SharedPreview || !PreviewVisible ? 0 : previewMask;
            outputCamera.gameObject.AddComponent<EdgeAntialiasing>().shader=edgeShader;
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--performance-log")>=0)gameObject.AddComponent<PerformanceProbe>();
            sender=outputCamera.gameObject.AddComponent<SpoutSender>();
            sender.SetResources(resources);
            sender.spoutName="TanakaCap";
            sender.captureMethod=CaptureMethod.Texture;
            sender.sourceTexture=texture;
            sender.keepAlpha=true;
            Debug.Log("TANAKACAP_ALPHA_OUTPUT_READY "+OutputWidth+"x"+OutputHeight+" RGBA Spout=TanakaCap edgeAA="+EdgeAntialiasing.Active);
            Debug.Log("TANAKACAP_PREVIEW shared="+SharedPreview+" visible="+PreviewVisible);
            Application.wantsToQuit+=WantsToQuit;
            var args=Environment.GetCommandLineArgs();
            int check=Array.IndexOf(args,"--aa-check");
            if(check>=0 && check+1<args.Length)StartCoroutine(CheckAA(args[check+1]));

        }

        void LateUpdate()
        {
            // Explicit offscreen rendering also runs when the preview is hidden.
            if(Input.GetKeyDown(KeyCode.F7))EdgeAntialiasing.Active=!EdgeAntialiasing.Active;
            if(Input.GetKeyDown(KeyCode.F8))
            {
                PreviewVisible=!PreviewVisible;
                previewCamera.cullingMask=SharedPreview || !PreviewVisible ? 0 : previewMask;
            }
            if(outputCamera && texture && !quitting)
            {
                outputCamera.fieldOfView=previewCamera.fieldOfView;
                if(inferenceSync){
                    if(!syncDriver)syncDriver=FindObjectOfType<AvatarDriver>();
                    long sequence=syncDriver?syncDriver.TrackingFrameRevision:0;
                    bool motion=Array.IndexOf(Environment.GetCommandLineArgs(),"--motion-demo")>=0;
                    if(!motion && sequence==lastPacket && Time.unscaledTime-lastOutput<.1f)return;
                    lastPacket=sequence;
                }
                var start=System.Diagnostics.Stopwatch.GetTimestamp();
                outputCamera.Render();
                RenderedFrames++;lastOutput=Time.unscaledTime;
                RenderSubmitMilliseconds=(System.Diagnostics.Stopwatch.GetTimestamp()-start)*1000.0/System.Diagnostics.Stopwatch.Frequency;
            }
        }

        void OnRenderImage(RenderTexture source,RenderTexture destination)
        {
            if(!SharedPreview || !PreviewVisible || !texture || !previewMaterial)
            { Graphics.Blit(source,destination);return; }
            // The output was already rendered/antialiased this frame. Only composite
            // its premultiplied RGBA over the preview background, with letterboxing.
            previewMaterial.SetColor("_Background",previewCamera.backgroundColor);
            previewMaterial.SetFloat("_OutputAspect",(float)OutputWidth/OutputHeight);
            previewMaterial.SetFloat("_ViewAspect",(float)source.width/source.height);
            Graphics.Blit(texture,destination,previewMaterial);
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

        void OnDestroy(){Application.wantsToQuit-=WantsToQuit;ReleaseOutput();if(previewMaterial)Destroy(previewMaterial);}
    }
}
