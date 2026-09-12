Shader "Hidden/TanakaCap/PreviewComposite"
{
    Properties { _MainTex ("RGBA", 2D) = "black" {} }
    SubShader
    {
        Cull Off ZWrite Off ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            float4 _Background;
            float _OutputAspect, _ViewAspect;
            float4 frag(v2f_img i) : SV_Target
            {
                float2 uv=i.uv-.5;
                if(_ViewAspect>_OutputAspect)uv.x*=_ViewAspect/_OutputAspect;
                else uv.y*=_OutputAspect/_ViewAspect;
                uv+=.5;
                if(any(uv<0) || any(uv>1))return float4(_Background.rgb,1);
                float4 c=tex2D(_MainTex,uv);
                return float4(c.rgb+_Background.rgb*(1-c.a),1);
            }
            ENDCG
        }
    }
}
