Shader "Hidden/TanakaCap/EdgeAntialiasing"
{
    Properties { _MainTex ("Image", 2D) = "white" {} }
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
            float4 _MainTex_TexelSize;
            // Consider both black and white composites: transparent edges must
            // remain detectable even when the visible hair is nearly black.
            float2 contrast(float4 c)
            {
                float l=dot(c.rgb,float3(.299,.587,.114));
                return float2(l,l+1-c.a);
            }
            float4 frag(v2f_img i) : SV_Target
            {
                float2 d=abs(_MainTex_TexelSize.xy);
                float4 c=tex2D(_MainTex,i.uv);
                float2 n=contrast(tex2D(_MainTex,i.uv+float2(0,d.y)));
                float2 s=contrast(tex2D(_MainTex,i.uv-float2(0,d.y)));
                float2 e=contrast(tex2D(_MainTex,i.uv+float2(d.x,0)));
                float2 w=contrast(tex2D(_MainTex,i.uv-float2(d.x,0)));
                float2 range=max(max(n,s),max(e,w))-min(min(n,s),min(e,w));
                bool white=range.y>range.x;
                float r=white?range.y:range.x;
                if(r<.045)return c;
                float gx=white?e.y-w.y:e.x-w.x;
                float gy=white?n.y-s.y:n.x-s.x;
                float2 tangent=float2(-gy,gx);
                float length2=dot(tangent,tangent);
                if(length2<.0001)return c;
                tangent*=rsqrt(length2);
                // Only diagonal edges need this supplement to MSAA. Keep
                // straight features and broad uniform areas unchanged.
                float diagonal=2*abs(tangent.x*tangent.y);
                float2 offset=tangent*d*.75;
                float4 along=(tex2D(_MainTex,i.uv+offset)+tex2D(_MainTex,i.uv-offset))*.5;
                float strength=.5*diagonal*saturate((r-.045)/.15);
                // Identical linear weights for premultiplied RGB and coverage:
                // no division by alpha, no opaque-alpha replacement or halos.
                return lerp(c,along,strength);
            }
            ENDCG
        }
    }
}
