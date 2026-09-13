using System;
using System.Globalization;
using UnityEngine;
namespace TanakaCap {
 public sealed class FacialExaggeration {
  public float Brow,Eye,Eyelid,Mouth;
  public static FacialExaggeration Parse(string[] args,bool demo){
   var result=new FacialExaggeration();
   result.Brow=Read(args,"--brow-exaggeration");result.Eye=Read(args,"--eye-exaggeration");
   result.Eyelid=Read(args,"--eyelid-exaggeration");result.Mouth=Read(args,"--mouth-exaggeration");
   bool baseline=Array.IndexOf(args,"--comparison-neutral-exaggeration")>=0;
   if(baseline&&Array.IndexOf(args,"--render-replay")<0)throw new ArgumentException("Comparison baseline is only available for offline replay");
   if(demo)result.Brow=result.Eye=result.Eyelid=result.Mouth=baseline?0:1;
   return result;
  }
  static float Read(string[] args,string key){
   int i=Array.IndexOf(args,key);if(i<0)return 0;
   if(i+1>=args.Length||!float.TryParse(args[i+1],NumberStyles.Float,CultureInfo.InvariantCulture,out float value)||float.IsNaN(value)||value<0||value>1)
    throw new ArgumentException(key+" must be 0..1");
   return value;
  }
  public static float Signed(float value,float amount,float maximum){return Mathf.Clamp(value*Mathf.Lerp(1,maximum,amount),-1,1);}
  public float BrowValue(float value){return Signed(value,Brow,1.75f);}
  public float EyeGain=>Mathf.Lerp(1,1.5f,Eye);
  // Inputs encode the same eye-width displacement as yaw=-80*x, pitch=60*y.
  // Normalize BOTH axes by that displacement before applying display sensitivity.
  // A soft bounded response preserves motion beyond the old hard clipping point.
  public static Vector2 GazeTarget(Vector2 input,float gain,bool legacy=false){
   if(legacy)return new Vector2(Mathf.Clamp(input.x*gain,-20,20),Mathf.Clamp(input.y*gain,-12,12));
   float x=input.x*gain/20f,y=input.y*gain/15f;
   return new Vector2(20*x/Mathf.Sqrt(1+x*x),12*y/Mathf.Sqrt(1+y*y));
  }
  public float LidValue(float value){return Mathf.Clamp01(Signed(value,Eyelid,1.8f));}
  public float MouthValue(float value){return Signed(value,Mouth,1.7f);}
 }
}
