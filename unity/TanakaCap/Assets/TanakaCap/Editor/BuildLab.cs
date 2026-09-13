using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;

namespace TanakaCap.Editor
{
    public static class BuildLab
    {
        [MenuItem("TanakaCap/Create haolan lab scene")]
        public static void Prepare()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/HAOLAN/Phys_Haolan.prefab");
            if (!prefab) throw new Exception("BOOTH haolan prefab has not been imported");
            var avatar = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            PrefabUtility.UnpackPrefabInstance(avatar, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            avatar.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            var report = new List<string> { "Local development scene. Source prefab is unchanged.",
                "VRChat SDK behaviours are omitted from this diagnostic scene. No PhysBone compatibility claim." };
            int missing = 0;
            foreach (var t in avatar.GetComponentsInChildren<Transform>(true))
            {
                int count = GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject);
                if (count > 0) report.Add("Omitted missing components: " + t.name + " : " + count);
                missing += count;
                GameObjectUtility.RemoveMonoBehavioursWithMissingScript(t.gameObject);
            }
            var animator = avatar.GetComponent<Animator>();
            if (!animator || !animator.isHuman) throw new Exception("Humanoid Avatar is required");
            animator.runtimeAnimatorController = null;
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            var driver = avatar.AddComponent<AvatarDriver>();
            driver.animator = animator;
            foreach (var bone in new[] {HumanBodyBones.LeftUpperArm,HumanBodyBones.RightUpperArm,HumanBodyBones.LeftHand,HumanBodyBones.RightHand})
                report.Add("Bone " + bone + ": " + animator.GetBoneTransform(bone).position.ToString("F4"));
            foreach (var renderer in avatar.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                report.Add("Mesh: " + renderer.name);
                if(renderer.name=="Body")
                {
                    var mesh=renderer.sharedMesh;var baked=new Mesh();renderer.BakeMesh(baked);
                    var raw=mesh.vertices;var bakedVertices=baked.vertices;
                    foreach(var label in new[]{"口角上げ","口_上","口_下","vrc.v_aa"})
                    {
                        int idx=mesh.GetBlendShapeIndex(label);if(idx<0)continue;
                        var delta=new Vector3[raw.Length];mesh.GetBlendShapeFrameVertices(idx,0,delta,null,null);
                        var rawBounds=new Bounds();var bakedBounds=new Bounds();int count=0;
                        for(int i=0;i<raw.Length;i++)if(delta[i].sqrMagnitude>1e-10f)
                        {
                            var a=avatar.transform.InverseTransformPoint(renderer.transform.TransformPoint(raw[i]));
                            var b=avatar.transform.InverseTransformPoint(renderer.transform.TransformPoint(bakedVertices[i]));
                            if(count++==0){rawBounds=new Bounds(a,Vector3.zero);bakedBounds=new Bounds(b,Vector3.zero);}else{rawBounds.Encapsulate(a);bakedBounds.Encapsulate(b);}
                        }
                        report.Add("MOUTH_AUDIT "+label+" count="+count+" raw="+rawBounds.ToString("F5")+" baked="+bakedBounds.ToString("F5"));
                    }
                    UnityEngine.Object.DestroyImmediate(baked);
                }
                for (int i = 0; i < renderer.sharedMesh.blendShapeCount; i++)
                {
                    report.Add("  Shape " + i + ": " + renderer.sharedMesh.GetBlendShapeName(i));
                    string shape = renderer.sharedMesh.GetBlendShapeName(i);
                    if (shape.Contains("blink") || shape == "まばたき" || shape.StartsWith("ウィンク"))
                    {
                        var vertices = new Vector3[renderer.sharedMesh.vertexCount];
                        renderer.sharedMesh.GetBlendShapeFrameVertices(i,0,vertices,null,null);
                        var sourceVertices = renderer.sharedMesh.vertices;
                        float weightedX=0, weight=0;
                        for(int v=0;v<vertices.Length;v++) { float d=vertices[v].magnitude; weight+=d; weightedX+=d*sourceVertices[v].x; }
                        report.Add("    MaxDelta="+vertices.Max(v=>v.magnitude)+" FrameWeight="+renderer.sharedMesh.GetBlendShapeFrameWeight(i,0)+" AffectedLocalX="+(weightedX/Mathf.Max(weight,.000001f)));
                    }
                }
                foreach (var mat in renderer.sharedMaterials)
                {
                    report.Add("  Material: " + (mat ? mat.name + " / " + mat.shader.name : "MISSING"));
                    if (!mat || !mat.shader || mat.shader.name == "Hidden/InternalErrorShader")
                        throw new Exception("Missing shader/material on " + renderer.name);
                }
            }
            report.Add("Missing components omitted in instance: " + missing);
            var camera = new GameObject("Output Camera").AddComponent<Camera>();
            camera.tag = "MainCamera";
            var head = animator.GetBoneTransform(HumanBodyBones.Head);
            var hips=animator.GetBoneTransform(HumanBodyBones.Hips);
            var chest=animator.GetBoneTransform(HumanBodyBones.Chest);
            float bottom=Mathf.Lerp(hips.position.y,chest?chest.position.y:head.position.y,.45f)-.02f;
            float top=head.position.y+.20f;
            foreach(var renderer in avatar.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                if(renderer.name!="Kemomimi")continue;
                var baked=new Mesh();renderer.BakeMesh(baked);
                foreach(var v in baked.vertices)top=Mathf.Max(top,renderer.transform.TransformPoint(v).y+.035f);
                UnityEngine.Object.DestroyImmediate(baked);
            }
            float y=(bottom+top)*.5f;
            float distance=(top-bottom)*.5f/Mathf.Tan(35*.5f*Mathf.Deg2Rad);
            camera.transform.position = new Vector3(0, y, distance);
            camera.transform.LookAt(new Vector3(0, y, 0));
            camera.fieldOfView = 35;
            report.Add("Upper-body framing: bottom="+bottom+" top="+top+" distance="+distance);
            camera.nearClipPlane = .01f;
            camera.farClipPlane = 30;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.06f, .07f, .09f);
            var output=camera.gameObject.AddComponent<AlphaOutput>();
            output.edgeShader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/TanakaCap/EdgeAntialiasing.shader");
            output.previewShader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/TanakaCap/PreviewComposite.shader");
            if(!output.previewShader || !output.previewShader.isSupported)throw new Exception("Preview shader unavailable");
            if(!output.edgeShader || !output.edgeShader.isSupported)throw new Exception("Edge AA shader unavailable");
            output.resources=AssetDatabase.LoadAssetAtPath<Klak.Spout.SpoutResources>("Packages/jp.keijiro.klak.spout/Editor/SpoutResources.asset");
            if(!output.resources)throw new Exception("Spout resources missing");
            var light = new GameObject("Key Light").AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1;
            light.transform.rotation = Quaternion.Euler(35, -145, 0);
            RenderSettings.ambientLight = new Color(.65f, .65f, .65f);
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = 60;
            PlayerSettings.enableFrameTimingStats=true; // GPU recorder activated only by explicit diagnostics.
            PlayerSettings.companyName = "tanakacap";
            PlayerSettings.productName = "tanakacap lab";
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.runInBackground = true;
            Directory.CreateDirectory("Assets/TanakaCap/Scenes");
            EditorSceneManager.SaveScene(scene, "Assets/TanakaCap/Scenes/HaolanLab.unity");
            Directory.CreateDirectory("../../results/unity");
            File.WriteAllLines("../../results/unity/avatar-inspection.txt", report);
            AssetDatabase.SaveAssets();
            Debug.Log("TANAKACAP_PREPARE_OK: " + missing + " unsupported components reported");
        }

        public static void Build()
        {
            FaceExpressionChecks.Run();
            CheckArmSolver();
            Prepare();
            Directory.CreateDirectory("../../builds/lab/avatars");
            string package="../../builds/lab/avatars/haolan.tcap";
            // This generated output is replaceable; original BOOTH assets remain untouched.
            string pending=package+"."+DateTime.UtcNow.Ticks+".new";
            var original=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/HAOLAN/Phys_Haolan.prefab");
            var sourceHash=AssetDatabase.GetAssetDependencyHash(AssetDatabase.GetAssetPath(original));
            AvatarExporter.Export(original,pending);
            if(sourceHash!=AssetDatabase.GetAssetDependencyHash(AssetDatabase.GetAssetPath(original)))throw new Exception("Source avatar dependencies changed during export");
            if(File.Exists(package))File.Move(package,package+"."+DateTime.UtcNow.Ticks+".bak");
            File.Move(pending,package);
            File.Copy(pending+".report.json",package+".report.json",true);
            File.Delete(pending+".report.json");
            Debug.Log("TANAKACAP_SOURCE_UNCHANGED "+sourceHash);
            var embedded=UnityEngine.Object.FindObjectOfType<AvatarDriver>();
            if(!embedded)throw new Exception("Lab avatar missing before externalization");
            UnityEngine.Object.DestroyImmediate(embedded.gameObject);
            new GameObject("Avatar Loader").AddComponent<AvatarPackageLoader>();
            EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(),"Assets/TanakaCap/Scenes/HaolanLab.unity");
            File.Copy("../../docs/PROCEDURAL_MOTION_LICENSE.txt","../../builds/lab/PROCEDURAL_MOTION_LICENSE.txt",true);
            AssetDatabase.ExportPackage(new[]{"Assets/TanakaCap/LICENSE.txt","Assets/TanakaCap/AvatarPackage.cs","Assets/TanakaCap/FaceExpressions.cs","Assets/TanakaCap/Editor/FaceProfileExporter.cs","Assets/TanakaCap/Editor/AvatarExporter.cs","Assets/TanakaCap/Editor/SecondaryMotionExporter.cs"},"../../builds/lab/TanakaCapExporter.unitypackage",ExportPackageOptions.Default);
            Directory.CreateDirectory("../../builds/lab");
            var result = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { "Assets/TanakaCap/Scenes/HaolanLab.unity" },
                locationPathName = "../../builds/lab/TanakaCap.exe",
                target = BuildTarget.StandaloneWindows64, options = BuildOptions.None });
            if (result.summary.result != BuildResult.Succeeded) throw new Exception("Player build failed");
            File.Copy("../../docs/THIRD_PARTY.md","../../builds/lab/THIRD_PARTY.md",true);
            File.Copy("../../assets-source/haolan-license-ja.pdf","../../builds/lab/haolan-license-ja.pdf",true);
            Debug.Log("TANAKACAP_BUILD_OK");
        }

        static void CheckArmSolver()
        {
            float angle=179;
            angle=AvatarDriver.UnwrapTwist(angle,179,-179);
            if(Mathf.Abs(angle-181)>.001f) throw new Exception("Twist wrap took long path");
            if(Mathf.Clamp(angle,-100,100)!=100) throw new Exception("Twist limit switched sides");
            float displayed=0;
            for(int cycle=0;cycle<5;cycle++)
                for(int degrees=0;degrees<=360;degrees+=2)
                    displayed=AvatarDriver.SelectForearmTwist(displayed,Mathf.DeltaAngle(0,degrees));
            displayed=AvatarDriver.SelectForearmTwist(displayed,0);
            if(Mathf.Abs(displayed)>.01f) throw new Exception("Forearm retained accumulated revolutions");
            float limit=AvatarDriver.ForearmTwistLimit;
            if(AvatarDriver.SelectForearmTwist(limit,-179)!=limit || AvatarDriver.SelectForearmTwist(-limit,179)!=-limit)
                throw new Exception("Bounded forearm selection reversed at 180 degrees");
            if(AvatarDriver.SelectForearmTwist(limit,-120)!=limit || AvatarDriver.SelectForearmTwist(-limit,120)!=-limit)
                throw new Exception("Forearm reversed into a long detour across wrap");
            foreach(float sign in new[]{-1f,1f})
            {
                float joint=sign*limit;
                for(int degrees=(int)limit;degrees<=240;degrees++)
                {
                    joint=AvatarDriver.SelectForearmTwist(joint,Mathf.DeltaAngle(0,sign*degrees));
                    if(joint!=sign*limit)throw new Exception("Limit continuation reversed around wrap");
                }
                joint=AvatarDriver.SelectForearmTwist(joint,0);
                if(Mathf.Abs(joint)>.01f)throw new Exception("Returning to neutral failed");
            }
            Vector3 frontPole=Vector3.back;
            AvatarDriver.SolveArm(new Vector3(-.2f,-.3f,-.5f),new Vector3(.1f,.4f,-1),.3f,.2f,
                ref frontPole,out var frontA,out var frontB,true,true);
            if(frontA.z<-.001f || (frontA*.3f+frontB*.2f).z<-.001f)
                throw new Exception("Front arm constraint was lost in avatar IK");
            Debug.Log("TANAKACAP_FRONT_AND_TWIST_PATH_OK");
            foreach(var forward in new[]{Vector3.forward,Vector3.back,Vector3.left,Vector3.up})
            {
                var q=AvatarDriver.ConstrainHandFrame(Quaternion.identity,forward,Vector3.down);
                if(float.IsNaN(q.x) || Vector3.Angle(Vector3.forward,q*Vector3.forward)>90.1f)
                    throw new Exception("Wrist swing constraint failed");
                var swing=Quaternion.FromToRotation(Vector3.forward,q*Vector3.forward);
                if(Quaternion.Angle(swing,q)>40.1f) throw new Exception("Wrist twist constraint failed");
            }
            Debug.Log("TANAKACAP_WRIST_LIMITS_OK");
            var lateral=AvatarDriver.ConstrainHandFrame(Quaternion.identity,Vector3.left,Vector3.up);
            if(Vector3.Angle(lateral*Vector3.forward,Vector3.left)>.1f)
                throw new Exception("Lateral pointing incorrectly bends toward camera");
            Debug.Log("TANAKACAP_LATERAL_POINTING_OK");
            foreach(var pair in new[] {
                new[]{Vector3.left,Vector3.left},new[]{Vector3.down,Vector3.up},
                new[]{new Vector3(-1,-1,.5f),new Vector3(.2f,1,2)},
                new[]{Vector3.forward,Vector3.back}})
            {
                Vector3 pole=Vector3.down;
                AvatarDriver.SolveArm(pair[0],pair[1],.3f,.25f,ref pole,out var a,out var b);
                float bendAngle=Vector3.Angle(a,b);
                if(float.IsNaN(bendAngle) || bendAngle<4.9f || bendAngle>155.1f || Mathf.Abs(a.magnitude-1)>.001f || Mathf.Abs(b.magnitude-1)>.001f)
                    throw new Exception("Arm solver violated bend limits: "+bendAngle);
            }
            Debug.Log("TANAKACAP_ARM_SOLVER_OK: straight/folded/depth/degenerate cases");
            foreach(float mirror in new[]{-1f,1f})
            foreach(float yaw in new[]{-45f,0f,45f})
            {
                var body=Quaternion.Euler(0,yaw,0);
                var observedA=body*new Vector3(mirror*.08f,-.18f,-.18f).normalized;
                var observedB=body*new Vector3(mirror*.08f,.1f,.12f).normalized;
                Vector3 pole=Vector3.down;
                AvatarDriver.SolveArm(observedA,observedB,.3f,.25f,ref pole,out var a,out var b);
                if((Quaternion.Inverse(body)*a).z>=0 || Vector3.Angle(a,observedA)>.1f ||
                   (a*.3f+b*.25f-observedA*.3f-observedB*.25f).magnitude>.0001f)
                    throw new Exception("Posterior elbow / outward hand branch or endpoint lost");
            }
            if(Mathf.Abs(AvatarDriver.CornerDownWeight(0)-30)>.001f ||
                AvatarDriver.CornerDownWeight(1)!=0 || AvatarDriver.CornerDownWeight(-1)!=100)
                throw new Exception("Neutral corner offset lost expression range");
            Debug.Log("TANAKACAP_POSTERIOR_ELBOW_AND_NEUTRAL_MOUTH_OK");
            foreach(float mirror in new[]{-1f,1f})foreach(float yaw in new[]{-45f,0f,45f})
            {
                var body=Quaternion.Euler(0,yaw,0);var forward=body*Vector3.forward;
                var a=body*new Vector3(mirror*.1f,-.22f,-.1f);
                var b=body*new Vector3(-mirror*.25f,.08f,.08f);
                Vector3 pole=Vector3.down;
                AvatarDriver.SolveArm(a,b,.3f,.25f,ref pole,out var upper,out var lower,false,false,1,forward);
                var elbow=upper*.3f;var wrist=elbow+lower*.25f;
                if(Vector3.Dot(elbow,forward)<.079f || Vector3.Dot(wrist,forward)<.099f ||
                    Mathf.Abs(upper.magnitude-1)>.001f || Mathf.Abs(lower.magnitude-1)>.001f)
                    throw new Exception("Cross-body forearm did not clear torso with fixed lengths");
            }
            if(Mathf.Abs(AvatarDriver.ExpressiveCorner(-.8f,1)+.64f)>.0001f || AvatarDriver.ExpressiveCorner(1,1)>.101f ||
                AvatarDriver.ExpressiveCorner(1,0)!=1)
                throw new Exception("Open-mouth smile suppression changed frown or closed smile");
            Debug.Log("TANAKACAP_CROSS_BODY_CLEARANCE_AND_OPEN_MOUTH_OK");
            foreach(float input in new[]{-.2f,-.5f,-1f,0,.2f,.5f,1f})
                if(Mathf.Abs(AvatarDriver.ExpressiveCorner(input,0)-input*Mathf.Abs(input))>.00001f)
                    throw new Exception("Signed corner gamma endpoints/sign/small-input suppression failed");
            foreach(float x in new[]{-.1f,0,.1f})
            {
                var center=new Vector3(0,.2f,.1f);
                var target=center+new Vector3(x,0,-.04f);
                var clear=AvatarDriver.ClearFace(target,center,.18f);
                if((clear-center).magnitude<.18f || clear.z<=center.z || clear.x!=target.x || clear.y!=target.y)
                    throw new Exception("Face clearance did not preserve XY on camera side");
                if(AvatarDriver.ClearFace(clear,center,.18f)!=clear)
                    throw new Exception("Face clearance drifted outside collision volume");
            }
            Debug.Log("TANAKACAP_FACE_CLEARANCE_OK");
            foreach(float sign in new[]{-1f,1f})foreach(float yaw in new[]{-35f,0,35f})
            {
                var rot=Quaternion.Euler(0,yaw,0);var normal=rot*Vector3.forward;
                var a=rot*new Vector3(sign*.12f,-.18f,.10f);
                var b=rot*new Vector3(sign*.14f,.04f,-.20f);
                var pole=Vector3.down;
                AvatarDriver.SolveArm(a,b,.3f,.25f,ref pole,out var upper,out var lower,false,false,0,normal,null,true);
                var wrist=upper*.3f+lower*.25f;
                if(Vector3.Dot(upper*.3f,normal)>Vector3.Dot(wrist,normal)-.019f ||
                    (wrist-a.normalized*.3f-b.normalized*.25f).magnitude>.0001f)
                    throw new Exception("Outward posterior hand lost elbow branch or endpoint");
            }
            if(AvatarDriver.MouthLipMask(.014f)>1e-5f || AvatarDriver.MouthLipMask(-.02f)!=0 || AvatarDriver.MouthLipMask(0)!=1)
                throw new Exception("Mouth shift can move chin/neck outside lip band");
            Debug.Log("TANAKACAP_OUTWARD_POSTERIOR_AND_LIP_MASK_OK");
        }
    }
}
