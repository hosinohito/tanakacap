using System;
using System.IO;
using UnityEngine;
using Klak.Spout;

namespace TanakaCap
{
    // A separate camera keeps preview/UI out of the RGBA texture sent to OBS.
    public sealed class AlphaOutput : MonoBehaviour
    {
        public SpoutResources resources;
        Camera outputCamera;
        RenderTexture texture;
        SpoutSender sender;
        bool quitting;
        bool readyToQuit;

        void Start()
        {
            texture=new RenderTexture(1280,720,24,RenderTextureFormat.ARGB32);
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
            sender=outputCamera.gameObject.AddComponent<SpoutSender>();
            sender.SetResources(resources);
            sender.spoutName="TanakaCap";
            sender.captureMethod=CaptureMethod.Texture;
            sender.sourceTexture=texture;
            sender.keepAlpha=true;
            Debug.Log("TANAKACAP_ALPHA_OUTPUT_READY 1280x720 RGBA Spout=TanakaCap");
            Application.wantsToQuit+=WantsToQuit;
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
            Application.Quit();
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
