using System;
namespace TanakaCap {
 [Serializable] public class AvatarPackageManifest {
  public int formatVersion=1;
  public string unityVersion,platform="StandaloneWindows64",profile="haolan-1.6",prefab="avatar",displayName,bundleSha256;
  public string[] warnings;
 }
}
