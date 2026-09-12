using System;
using UnityEngine;

namespace TanakaCap
{
    // Original single-pass edge filter. No temporal history or external runtime.
    [RequireComponent(typeof(Camera))]
    public sealed class EdgeAntialiasing : MonoBehaviour
    {
        public Shader shader;
        public static bool Active = true;
        Material material;
        void OnRenderImage(RenderTexture source, RenderTexture destination)
        {
            if (!Active || !shader || !shader.isSupported) { Graphics.Blit(source,destination); return; }
            if (!material) material=new Material(shader){hideFlags=HideFlags.HideAndDontSave};
            Graphics.Blit(source,destination,material);
        }
        void OnDestroy(){if(material)Destroy(material);}
    }
}
