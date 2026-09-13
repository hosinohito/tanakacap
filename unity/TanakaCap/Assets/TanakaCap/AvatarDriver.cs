using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.IO;
using System.Collections;
using UnityEngine;

namespace TanakaCap
{
    [Serializable] public class TrackingPacket
    {
        public int version;
        public long sequence;
        public double inputReadTime,inputSentTime;
        public bool tracked, headTracked, faceTracked, leftArmTracked, rightArmTracked, body3d, torsoTracked;
        public float headPitch, headYaw, headRoll, mouth, mouthWidth,mouthRound,mouthSmile,leftBlink, rightBlink, torsoRoll, torsoPitch, torsoYaw;
        public bool mouthContourTracked;
        public float mouthLeftCorner,mouthRightCorner,mouthBow,mouthShift;
        public bool browTracked;
        public float browLeftInner,browLeftOuter,browRightInner,browRightOuter;
        public bool gazeTracked;
        public float gazeYaw,gazePitch;
        public bool faceDistanceTracked;
        public float faceDistanceRatio;
        public float leftCrossBody,rightCrossBody;
        public Vector3 leftElbow, leftWrist, rightElbow, rightWrist;
        public bool leftHandTracked, rightHandTracked;
        public bool leftArmHeld,rightArmHeld;
        public bool leftOutOfView,rightOutOfView;
        public bool leftUpperArmTracked,rightUpperArmTracked;
        public bool leftWristInFront,rightWristInFront,leftUpperInFront,rightUpperInFront;
        public bool[] leftFingerTracked, rightFingerTracked;
        public float[] leftFingerFlex, rightFingerFlex;
        public Vector3 leftHandForward, leftHandNormal, rightHandForward, rightHandNormal;
    }

    public partial class AvatarDriver : MonoBehaviour
    {
        [Serializable] class BoneDiagnostics
        {
            public float gazeYawApplied,gazePitchApplied;
            public float headPitchApplied;
            public float faceDistanceRatioApplied;
            public float seatedLeanDegrees;
            public bool seatedLeanLimited;
            public Vector3 avatarDisplacement;
            public Vector3 leftHandForward,leftHandNormal,rightHandForward,rightHandNormal;
            public float[] leftFingerAngles,rightFingerAngles;
            public bool lossHoldVerified;
            public bool mouthWidthVerified;
            public float mouthWidthWeight;
            public float torsoRotationError;
            public Vector3 chestRestLocalUpInRoot;
            public float leftWristSwing,rightWristSwing,leftWristTwist,rightWristTwist,leftForearmTwist,rightForearmTwist;
            public Vector3 leftElbowRelative,rightElbowRelative,leftWristRelative,rightWristRelative;
        }
        public Animator animator;
        public int port = 39540;
        public bool showStatus = false;
        // HAOLAN 1.6: vrc.blink_* barely move. These author-provided shapes close each eye.
        public string leftBlinkShape = "ウィンク２";
        public string rightBlinkShape = "ウィンク２右";
        UdpClient receiver;
        TrackingPacket current;
        long lastSequence = -1;
        float lastReceived = -100;
        public const float ForearmTwistLimit=160f;
        string error;
        Transform head, chest, spine;
        Quaternion headRest, chestRest, spineRest, headRootRest, chestRootRest, spineRootRest;
        Vector3 torsoNeutral;
        Vector3 faceCenterLocal;
        Arm left, right;
        SkinnedMeshRenderer[] meshes;
        bool demo;
        bool motionDemo;
        bool obsMode;
        bool gazeEnabled=true;
        bool gazeIrisMode=true;
        float gazeGain=4f;
        float mouthShiftDistance=.004f;
        bool legacyGazeResponse;
        SkinnedMeshRenderer gazeMesh;
        Transform leftEye,rightEye;
        Quaternion leftEyeRest,rightEyeRest;
        Vector2 gazeAngles;
        bool faceDistanceEnabled=true;
        Vector3 rootRestPosition,depthDirection;
        float initialFaceDepth,faceDistanceRatio=1;
        bool seatedDistance=true,distanceEstablished,seatedLeanLimited;
        float seatedLeanDegrees;
        Vector3 seatedHeadOffset,lastTorso;
        bool framedDistance=true;
        float initialHeadCameraY;
        public void CameraFramingChanged(Vector3 cameraDelta){
            if(!Camera.main)return;
            initialHeadCameraY-=Vector3.Dot(cameraDelta,Camera.main.transform.up);
            initialFaceDepth-=Vector3.Dot(cameraDelta,depthDirection);
        }
        float mouth, mouthWidth,mouthRound,mouthSmile,blinkLeft, blinkRight;
        float mouthLeftCorner,mouthRightCorner,mouthBow,mouthShift;
        public float MouthCornerEmphasis { get; set; } = 0;
        public float MouthCornerGamma { get; set; } = 1;
        public float MouthOpenSmileSuppression { get; set; } = 0;
        readonly Dictionary<(SkinnedMeshRenderer,string),float> cornerGains=new Dictionary<(SkinnedMeshRenderer,string),float>();
        bool detailedMouth;
        BrowExpressions browExpressions; // Standalone authored-brow regression probe.
        public FaceProfile faceProfile;
        FaceExpressions expressions;
        bool autoExpressions;
        bool adaptiveHeadFollow;
        bool adaptiveBrowFollow=true;
        FacialExaggeration exaggeration=new FacialExaggeration();

        public static float FollowBrow(float current,float target,float dt,bool adaptive=true)
        {
            target=Mathf.Clamp(target,-1,1);
            if(!adaptive)return target;
            float weight=Mathf.SmoothStep(0,1,Mathf.Clamp01(Mathf.Abs(target-current)/.3f));
            float amount=1-Mathf.Exp(-Mathf.Max(0,dt)*Mathf.Lerp(6,45,weight));
            return Mathf.Lerp(current,target,amount);
        }

        public static float HeadFollowAmount(float errorDegrees,float dt,bool adaptive)
        {
            float weight=Mathf.SmoothStep(0,1,Mathf.Clamp01(errorDegrees/12f));
            float rate=adaptive?Mathf.Lerp(6f,45f,weight):45f;
            return 1-Mathf.Exp(-Mathf.Max(0,dt)*rate);
        }
        readonly HashSet<Mesh> expressionClones=new HashSet<Mesh>();
        Mesh ExpressionClone(SkinnedMeshRenderer renderer) {
            if(expressionClones.Contains(renderer.sharedMesh))return renderer.sharedMesh;
            var clone=Instantiate(renderer.sharedMesh);expressionClones.Add(clone);renderer.sharedMesh=clone;return clone;
        }
        float browLeftInner,browLeftOuter,browRightInner,browRightOuter;
        float probeDelta;
        float FrameDelta => probeDelta>0?probeDelta:Time.unscaledDeltaTime;

        class Arm
        {
            public Transform upper, lower, hand;
            public Quaternion upperRest, lowerRest, upperRootRest, lowerRootRest;
            public float upperLength, lowerLength;
            public Vector3 pole;
            public Quaternion handRest, handFrameCorrection;
            public bool handBasisValid;
            public Vector3 upperDirection, lowerDirection;
            public Quaternion lowerUntwisted;
            public float twist;
            public float requestedTwist;
            public Quaternion handBeforeSolve;
            public Finger[] fingers;
        }

        class Finger
        {
            public Transform[] bones = new Transform[3];
            public Quaternion[] rest = new Quaternion[3];
            public Vector3[] axes = new Vector3[3];
            public Vector3[] directions = new Vector3[3];
        }

        Finger[] MakeFingers(bool isLeft, Vector3 inward)
        {
            var result = new Finger[5];
            string[] names = {"Thumb", "Index", "Middle", "Ring", "Little"};
            string[] joints = {"Proximal", "Intermediate", "Distal"};
            for(int f=0; f<5; f++)
            {
                var finger = result[f] = new Finger();
                for(int j=0; j<3; j++)
                    finger.bones[j] = animator.GetBoneTransform((HumanBodyBones)Enum.Parse(typeof(HumanBodyBones),(isLeft?"Left":"Right")+names[f]+joints[j]));
                for(int j=0; j<3; j++)
                {
                    var bone=finger.bones[j];
                    if(!bone) continue;
                    var next=j<2?finger.bones[j+1]:null;
                    var previous=j>0?finger.bones[j-1]:null;
                    Vector3 direction=next?next.position-bone.position:previous?bone.position-previous.position:Vector3.zero;
                    finger.directions[j]=bone.InverseTransformDirection(direction.normalized);
                    finger.rest[j]=bone.localRotation;
                    if(f!=0 && direction.sqrMagnitude>1e-10f)
                    {
                        // Zero flex means extended phalanges. Preserve finger
                        // spread at MCP; remove the imported rest-pose curl.
                        Vector3 extended=j==0?Vector3.ProjectOnPlane(direction,inward):bone.position-previous.position;
                        if(extended.sqrMagnitude>1e-10f)
                            finger.rest[j]=Quaternion.Inverse(bone.parent.rotation)*
                                Quaternion.FromToRotation(direction,extended)*bone.rotation;
                    }
                    Vector3 curlToward=inward;
                    if(f==0)
                    {
                        var index=animator.GetBoneTransform(isLeft?HumanBodyBones.LeftIndexProximal:HumanBodyBones.RightIndexProximal);
                        if(index) curlToward=index.position-bone.position;
                    }
                    finger.axes[j]=bone.InverseTransformDirection(Vector3.Cross(direction,curlToward).normalized);
                }
            }
            return result;
        }

        void DriveFingers(Arm arm, bool[] valid, float[] flex)
        {
            if(valid==null || flex==null || arm.fingers==null) return;
            for(int f=0; f<5; f++)
            {
                if(!valid[f]) continue;
                var finger=arm.fingers[f];
                for(int j=0; j<3; j++)
                {
                    var bone=finger.bones[j];
                    if(!bone || finger.axes[j].sqrMagnitude<.5f) continue;
                    float limit=f==0?(j==0?0:j==1?50:65):(j==0?80:j==1?110:90);
                    var target=finger.rest[j]*Quaternion.AngleAxis(Mathf.Clamp(flex[f*3+j],0,limit),finger.axes[j]);
                    bone.localRotation=Quaternion.Slerp(bone.localRotation,target,1-Mathf.Exp(-60*FrameDelta));
                }
            }
        }

        void Start()
        {
            int renderFps = 60;
            var renderArgs = Environment.GetCommandLineArgs();
            // Sync output is packet-driven in AlphaOutput. Keep the event loop responsive
            // without inheriting the user's previous fixed/custom output rate.
            if(Array.IndexOf(renderArgs,"--render-sync")>=0)renderFps=240;
            int renderIndex = Array.IndexOf(renderArgs, "--render-fps");
            if (renderIndex >= 0 && (renderIndex+1 >= renderArgs.Length ||
                !int.TryParse(renderArgs[renderIndex+1], out renderFps) || renderFps<1 || renderFps>240))
                throw new ArgumentException("--render-fps must be 1..240");
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = renderFps;
            head = animator.GetBoneTransform(HumanBodyBones.Head);
            rootRestPosition=transform.position;
            var outputCamera=Camera.main;
            if(outputCamera)
            {
                depthDirection=outputCamera.transform.forward;
                initialFaceDepth=Vector3.Dot(head.position-outputCamera.transform.position,depthDirection);
                initialHeadCameraY=Vector3.Dot(head.position-outputCamera.transform.position,outputCamera.transform.up);
            }
            var eyeL=animator.GetBoneTransform(HumanBodyBones.LeftEye);
            var eyeR=animator.GetBoneTransform(HumanBodyBones.RightEye);
            leftEye=eyeL;rightEye=eyeR;
            if(!leftEye && !string.IsNullOrEmpty(faceProfile?.leftEye))leftEye=transform.Find(faceProfile.leftEye);
            if(!rightEye && !string.IsNullOrEmpty(faceProfile?.rightEye))rightEye=transform.Find(faceProfile.rightEye);
            // HAOLAN has eye bones, but does not map them in its Humanoid avatar.
            foreach(var bone in head.GetComponentsInChildren<Transform>(true))
            {
                if(!leftEye && bone.name=="LeftEye")leftEye=bone;
                if(!rightEye && bone.name=="RightEye")rightEye=bone;
            }
            if(leftEye)leftEyeRest=leftEye.localRotation;
            if(rightEye)rightEyeRest=rightEye.localRotation;
            var faceCenter=eyeL && eyeR?(eyeL.position+eyeR.position)*.5f-transform.forward*.04f:head.position+transform.up*.09f;
            faceCenterLocal=head.InverseTransformPoint(faceCenter);
            chest = animator.GetBoneTransform(HumanBodyBones.Chest);
            if (!chest) chest = animator.GetBoneTransform(HumanBodyBones.Spine);
            headRest = head.localRotation; chestRest = chest.localRotation;
            chestRootRest=Quaternion.Inverse(transform.rotation)*chest.rotation;
            headRootRest = Quaternion.Inverse(transform.rotation)*head.rotation;
            spine = animator.GetBoneTransform(HumanBodyBones.Spine);
            if (spine == chest) spine = null;
            if (spine) {spineRest = spine.localRotation;spineRootRest=Quaternion.Inverse(transform.rotation)*spine.rotation;}
            seatedHeadOffset=transform.InverseTransformVector(head.position-(spine?spine:chest).position);
            left = MakeArm(HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand);
            right = MakeArm(HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand);
            meshes = GetComponentsInChildren<SkinnedMeshRenderer>(true);
            int expressionIndex=Array.IndexOf(renderArgs,"--expression-mode");
            string expressionMode=expressionIndex<0?"existing":expressionIndex+1<renderArgs.Length?renderArgs[expressionIndex+1]:"";
            if(expressionMode!="existing" && expressionMode!="auto-custom")throw new ArgumentException("--expression-mode must be existing or auto-custom");
            bool demoShapes=Array.IndexOf(renderArgs,"--use-demo-shape-keys")>=0;
            exaggeration=FacialExaggeration.Parse(renderArgs,demoShapes);
            autoExpressions=expressionMode=="auto-custom" || demoShapes;
            mouthShiftDistance=Array.IndexOf(Environment.GetCommandLineArgs(),"--experimental-mouth-shift-8mm")>=0?.008f:.004f;
            if(autoExpressions){GenerateAutoMouthShapes();GenerateAutoGazeShapes();}
            if(autoExpressions)BrowShapeSplit.Generate(meshes,leftEye,rightEye,ExpressionClone);
            expressions=new FaceExpressions(transform,meshes,faceProfile,autoExpressions,cornerGains);
            if(Array.IndexOf(renderArgs,"--check-brow-sides")>=0)expressions.CheckBrowSides();
            Debug.Log("TANAKACAP_EXPRESSION_MODE "+expressionMode);
            Debug.Log("TANAKACAP_EXAGGERATION brow="+exaggeration.Brow+" eye="+exaggeration.Eye+" eyelid="+exaggeration.Eyelid+" mouth="+exaggeration.Mouth);
            browExpressions=new BrowExpressions(meshes);
            var args = Environment.GetCommandLineArgs();
            adaptiveHeadFollow=Array.IndexOf(args,"--adaptive-head-follow")>=0;
            adaptiveBrowFollow=Array.IndexOf(args,"--no-adaptive-brow-follow")<0;
            MouthCornerGamma=ReadExpressionOption(args,"--mouth-corner-gamma",autoExpressions?2:1,.25f,4);
            MouthOpenSmileSuppression=ReadExpressionOption(args,"--mouth-open-smile-suppression",autoExpressions?.9f:0,0,1);
            Debug.Log("TANAKACAP_CORNER_OPTIONS gamma="+MouthCornerGamma+" suppression="+MouthOpenSmileSuppression);
            int emphasisArg=Array.IndexOf(args,"--mouth-corner-emphasis");
            if(emphasisArg>=0)
            {
                if(emphasisArg+1>=args.Length || !float.TryParse(args[emphasisArg+1],System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out var emphasis) || float.IsNaN(emphasis) || emphasis<0 || emphasis>1)
                    throw new ArgumentException("--mouth-corner-emphasis must be 0..1");
                MouthCornerEmphasis=emphasis;
            }
            faceDistanceEnabled=Array.IndexOf(args,"--no-face-distance")<0;
            seatedDistance=Array.IndexOf(args,"--face-distance-translate")<0;
            framedDistance=seatedDistance && Array.IndexOf(args,"--face-distance-seated")<0;
            gazeIrisMode=Array.IndexOf(args,"--gaze-bones")<0;
            int gazeGainArg=Array.IndexOf(args,"--gaze-gain");
            legacyGazeResponse=Array.IndexOf(args,"--legacy-gaze-response")>=0;
            if(gazeGainArg>=0 && gazeGainArg+1<args.Length && float.TryParse(args[gazeGainArg+1],System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out var requestedGazeGain) && !float.IsNaN(requestedGazeGain))
                gazeGain=Mathf.Clamp(requestedGazeGain,.5f,6f);
            if(Array.IndexOf(args,"--obs")>=0)SetObsMode(true);
            if(TryStartVideo(args))return;
            int portArg=Array.IndexOf(args,"--port");
            if(portArg>=0 && portArg+1<args.Length && int.TryParse(args[portArg+1],out var testPort) && testPort>0 && testPort<=65535) port=testPort;
            motionDemo=Array.IndexOf(args,"--motion-demo")>=0;
            if(motionDemo)demo=true;
            try { if(!motionDemo)receiver = new UdpClient(new IPEndPoint(IPAddress.Loopback, port)); }
            catch (Exception ex) { error = ex.Message; }
            if (Array.IndexOf(args,"--demo") >= 0) demo = true;
            int snapshot = Array.IndexOf(args,"--snapshot");
            if (snapshot >= 0 && snapshot+1 < args.Length) StartCoroutine(Snapshot(args[snapshot+1]));
        }

        Arm MakeArm(HumanBodyBones a, HumanBodyBones b, HumanBodyBones c)
        {
            var arm = new Arm { upper = animator.GetBoneTransform(a), lower = animator.GetBoneTransform(b), hand = animator.GetBoneTransform(c) };
            arm.upperRest = arm.upper.localRotation; arm.lowerRest = arm.lower.localRotation;
            arm.upperRootRest = Quaternion.Inverse(transform.rotation)*arm.upper.rotation;
            arm.lowerRootRest = Quaternion.Inverse(transform.rotation)*arm.lower.rotation;
            arm.lowerUntwisted = arm.lower.rotation;
            arm.upperLength = Vector3.Distance(arm.upper.position,arm.lower.position);
            arm.lowerLength = Vector3.Distance(arm.lower.position,arm.hand.position);
            arm.pole = new Vector3(a == HumanBodyBones.LeftUpperArm ? -1 : 1,-1,0).normalized;
            bool isLeft = a == HumanBodyBones.LeftUpperArm;
            arm.handRest = arm.hand.localRotation;
            var index = animator.GetBoneTransform(isLeft ? HumanBodyBones.LeftIndexProximal : HumanBodyBones.RightIndexProximal);
            var middle = animator.GetBoneTransform(isLeft ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
            var little = animator.GetBoneTransform(isLeft ? HumanBodyBones.LeftLittleProximal : HumanBodyBones.RightLittleProximal);
            if (index && middle && little)
            {
                Vector3 forward = middle.position-arm.hand.position;
                Vector3 normal = Vector3.Cross(index.position-arm.hand.position,little.position-arm.hand.position);
                if (forward.sqrMagnitude>1e-8f && normal.sqrMagnitude>1e-12f)
                {
                    arm.handFrameCorrection = Quaternion.Inverse(Quaternion.LookRotation(forward,normal))*arm.hand.rotation;
                    arm.handBasisValid = true;
                    arm.fingers = MakeFingers(isLeft,normal.normalized*(isLeft?1:-1));
                }
            }
            arm.upperDirection = arm.upper.InverseTransformDirection(arm.lower.position - arm.upper.position).normalized;
            arm.lowerDirection = arm.lower.InverseTransformDirection(arm.hand.position - arm.lower.position).normalized;
            return arm;
        }

        void Update()
        {
            if(videoMode)return;
            if (Input.GetKeyDown(KeyCode.F3)) SetObsMode(!obsMode);
            if (Input.GetKeyDown(KeyCode.F4)) gazeEnabled=!gazeEnabled;
            if (Input.GetKeyDown(KeyCode.F2)) demo = !demo;
            if (Input.GetKeyDown(KeyCode.C) && current != null && current.torsoTracked && Time.unscaledTime-lastReceived<.3f)
                torsoNeutral = new Vector3(current.torsoPitch,current.torsoYaw,current.torsoRoll);
            if (receiver == null) return;
            // Bounded drain: stale UDP messages cannot accumulate an unbounded render cost.
            for (int n = 0; n < 64 && receiver.Available > 0; n++)
            {
                IPEndPoint sender = null;
                byte[] bytes = receiver.Receive(ref sender);
                if (bytes.Length > 4096) continue;
                try
                {
                    var packet = JsonUtility.FromJson<TrackingPacket>(Encoding.UTF8.GetString(bytes));
                    if (packet == null || packet.version != 1 || !Finite(packet)) continue;
                    // A sender may restart at sequence 0 after the old stream expires.
                    if (packet.sequence <= lastSequence && Time.unscaledTime-lastReceived < 1) continue;
                    lastSequence = packet.sequence;
                    ReceivedPackets++;
                    current = packet;
                    lastReceived = Time.unscaledTime;
                }
                catch (ArgumentException) { }
            }
        }

        static bool Finite(TrackingPacket p)
        {
            if(double.IsNaN(p.inputReadTime)||double.IsInfinity(p.inputReadTime)||double.IsNaN(p.inputSentTime)||double.IsInfinity(p.inputSentTime))return false;
            if(float.IsNaN(p.faceDistanceRatio)||float.IsInfinity(p.faceDistanceRatio))return false;
            if(float.IsNaN(p.gazeYaw)||float.IsInfinity(p.gazeYaw)||float.IsNaN(p.gazePitch)||float.IsInfinity(p.gazePitch))return false;
            float[] values = {p.headPitch,p.headYaw,p.headRoll,p.mouth,p.mouthWidth,p.mouthRound,p.mouthSmile,p.mouthLeftCorner,p.mouthRightCorner,p.mouthBow,p.leftBlink,p.rightBlink,p.torsoRoll,p.torsoPitch,p.torsoYaw,
                p.browLeftInner,p.browLeftOuter,p.browRightInner,p.browRightOuter,
                p.mouthShift,p.leftCrossBody,p.rightCrossBody,
                p.leftElbow.x,p.leftElbow.y,p.leftElbow.z,p.leftWrist.x,p.leftWrist.y,p.leftWrist.z,
                p.rightElbow.x,p.rightElbow.y,p.rightElbow.z,p.rightWrist.x,p.rightWrist.y,p.rightWrist.z,
                p.leftHandForward.x,p.leftHandForward.y,p.leftHandForward.z,p.leftHandNormal.x,p.leftHandNormal.y,p.leftHandNormal.z,
                p.rightHandForward.x,p.rightHandForward.y,p.rightHandForward.z,p.rightHandNormal.x,p.rightHandNormal.y,p.rightHandNormal.z};
            foreach (float v in values) if (float.IsNaN(v) || float.IsInfinity(v) || Mathf.Abs(v)>10000) return false;
            return ValidFingers(p.leftFingerTracked,p.leftFingerFlex) && ValidFingers(p.rightFingerTracked,p.rightFingerFlex);
        }

        static bool ValidFingers(bool[] tracked,float[] flex)
        {
            if(tracked==null && flex==null) return true; // older senders
            if(tracked==null || flex==null || tracked.Length!=5 || flex.Length!=15) return false;
            foreach(float v in flex) if(float.IsNaN(v) || float.IsInfinity(v) || v<0 || v>180) return false;
            return true;
        }

        public long ReceivedPackets { get; private set; }
        public long AppliedSequence { get { return current==null ? -1 : current.sequence; } }
        public double InputReadTime { get { return current==null ? 0 : current.inputReadTime; } }
        public double InputSentTime { get { return current==null ? 0 : current.inputSentTime; } }
        public float PacketAgeMilliseconds { get { return current==null ? -1 : (Time.unscaledTime-lastReceived)*1000; } }

        void LateUpdate()
        {
            if(videoMode && probeDelta<=0)return;
            if (!head) return;
            float t = 1-Mathf.Exp(-FrameDelta*16);
            bool live = current != null && current.tracked && Time.unscaledTime-lastReceived < .3f;
            if(!live && !demo){DriveGaze(null,false,FrameDelta);return;} // Only gaze returns to center on loss.
            var p = live ? current : new TrackingPacket();
            if (demo) p = motionDemo ? ProceduralMotion.Sample(Time.time) : new TrackingPacket { tracked=true, faceTracked=true,
                headYaw=25*Mathf.Sin(Time.time), headRoll=10*Mathf.Sin(Time.time*.6f),
                mouth=.5f+.5f*Mathf.Sin(Time.time*3), leftBlink=Mathf.Pow(Mathf.Max(0,Mathf.Sin(Time.time*2)),16),
                rightBlink=Mathf.Pow(Mathf.Max(0,Mathf.Sin(Time.time*2)),16) };
            if(demo && motionDemo)live=true;
            if(framedDistance && faceDistanceEnabled && distanceEstablished && p.faceTracked && p.faceDistanceTracked)transform.position=rootRestPosition;
            var leftParentBefore=left.lower.parent.rotation;
            var rightParentBefore=right.lower.parent.rotation;
            DriveFaceDistance(p,live,FrameDelta);
            bool seated=faceDistanceEnabled && seatedDistance && distanceEstablished;
            Vector3 torso = p.torsoTracked ? new Vector3(p.torsoPitch,p.torsoYaw,p.torsoRoll)-torsoNeutral :
                new Vector3(0,0,p.body3d ? 0 : p.torsoRoll);
            if(p.torsoTracked)lastTorso=torso;
            else if(seated)torso=lastTorso;
            if(seated)torso.x=seatedLeanDegrees;
            torso = new Vector3(Mathf.Clamp(torso.x,-50,50),Mathf.Clamp(torso.y,-80,80),Mathf.Clamp(torso.z,-25,25));
            if(seated)torso.x=seatedLeanDegrees;
            float share = spine ? .65f : 1;
            bool updateTorso=p.torsoTracked || (seated && p.faceTracked && p.faceDistanceTracked);
            var lowerTorso=torso*(1-share);
            if(seated)lowerTorso.x=torso.x;
            if (updateTorso && spine) spine.rotation = Quaternion.Slerp(spine.rotation,transform.rotation*TorsoRotation(lowerTorso,seated)*spineRootRest,t);
            if(updateTorso) chest.rotation = Quaternion.Slerp(chest.rotation,transform.rotation*TorsoRotation(torso,seated)*chestRootRest,t);
            // Carry the cached forearm frame through inherited torso motion.
            // Otherwise interpolation starts from a stale world orientation.
            left.lowerUntwisted=left.lower.parent.rotation*Quaternion.Inverse(leftParentBefore)*left.lowerUntwisted;
            right.lowerUntwisted=right.lower.parent.rotation*Quaternion.Inverse(rightParentBefore)*right.lowerUntwisted;
            bool headActive=p.headTracked || p.faceTracked;
            var headTarget = transform.rotation * (headActive ? Quaternion.Euler(Mathf.Clamp(p.headPitch,-40,40),
                Mathf.Clamp(p.headYaw,-60,60),Mathf.Clamp(p.headRoll,-35,35)) : Quaternion.identity) * headRootRest;
            // Face orientation is camera-relative: do not add torso rotation a second time.
            float faceT=headActive ? HeadFollowAmount(Quaternion.Angle(head.rotation,headTarget),FrameDelta,adaptiveHeadFollow) : t;
            if (headActive) head.rotation = Quaternion.Slerp(head.rotation,headTarget,faceT);
            ApplyFaceFraming(p,live);
            expressions.Begin();
            DriveGaze(p,live,FrameDelta);

            left.handBeforeSolve=left.hand.rotation; right.handBeforeSolve=right.hand.rotation;
            DriveArm(left,p.leftArmTracked && !p.leftArmHeld,p.leftElbow,p.leftWrist,true,t,p.leftWristInFront,p.leftUpperInFront,p.leftCrossBody);
            DriveArm(right,p.rightArmTracked && !p.rightArmHeld,p.rightElbow,p.rightWrist,false,t,p.rightWristInFront,p.rightUpperInFront,p.rightCrossBody);
            DriveHand(left,p.leftArmTracked && !p.leftArmHeld && p.leftHandTracked,p.leftHandForward,p.leftHandNormal,t);
            DriveHand(right,p.rightArmTracked && !p.rightArmHeld && p.rightHandTracked,p.rightHandForward,p.rightHandNormal,t);
            DriveFingers(left,p.leftFingerTracked,p.leftFingerFlex);
            DriveFingers(right,p.rightFingerTracked,p.rightFingerFlex);
            if(p.faceTracked) mouth = Mathf.Lerp(mouth,Mathf.Clamp01(p.mouth),faceT);
            if(p.faceTracked) mouthWidth = Mathf.Lerp(mouthWidth,Mathf.Clamp(p.mouthWidth,-1,1),faceT);
            if(p.faceTracked) mouthRound = Mathf.Lerp(mouthRound,Mathf.Clamp01(p.mouthRound),faceT);
            if(p.faceTracked) mouthSmile = Mathf.Lerp(mouthSmile,Mathf.Clamp01(p.mouthSmile),faceT);
            if(p.faceTracked && p.mouthContourTracked)
            {
                detailedMouth=true;
                mouthLeftCorner=Mathf.Lerp(mouthLeftCorner,Mathf.Clamp(p.mouthLeftCorner,-1,1),faceT);
                mouthRightCorner=Mathf.Lerp(mouthRightCorner,Mathf.Clamp(p.mouthRightCorner,-1,1),faceT);
                mouthBow=Mathf.Lerp(mouthBow,Mathf.Clamp01(p.mouthBow),faceT);
                mouthShift=Mathf.Lerp(mouthShift,Mathf.Clamp(p.mouthShift,-1,1),faceT);
            }
            if(p.faceTracked) blinkLeft = Mathf.Lerp(blinkLeft,Mathf.Clamp01(p.leftBlink),faceT);
            if(p.faceTracked && p.browTracked){
                browLeftInner=FollowBrow(browLeftInner,p.browLeftInner,FrameDelta,adaptiveBrowFollow);
                browLeftOuter=FollowBrow(browLeftOuter,p.browLeftOuter,FrameDelta,adaptiveBrowFollow);
                browRightInner=FollowBrow(browRightInner,p.browRightInner,FrameDelta,adaptiveBrowFollow);
                browRightOuter=FollowBrow(browRightOuter,p.browRightOuter,FrameDelta,adaptiveBrowFollow);
            }
            expressions.ApplyBrows(exaggeration.BrowValue(browLeftInner),exaggeration.BrowValue(browLeftOuter),exaggeration.BrowValue(browRightInner),exaggeration.BrowValue(browRightOuter));
            if(p.faceTracked) blinkRight = Mathf.Lerp(blinkRight,Mathf.Clamp01(p.rightBlink),faceT);
            expressions.CornerGamma=MouthCornerGamma;expressions.OpenSmileSuppression=MouthOpenSmileSuppression;
            expressions.ApplyMouth(exaggeration.MouthValue(mouth),exaggeration.MouthValue(mouthWidth),exaggeration.MouthValue(mouthRound),exaggeration.MouthValue(detailedMouth?mouthLeftCorner:mouthSmile),
                exaggeration.MouthValue(detailedMouth?mouthRightCorner:mouthSmile),exaggeration.MouthValue(mouthShift),exaggeration.MouthValue(mouthBow),Mathf.Max(MouthCornerEmphasis,exaggeration.Mouth));
            expressions.Blink(exaggeration.LidValue(blinkLeft),exaggeration.LidValue(blinkRight));
            expressions.Commit();
        }

        static float ReadExpressionOption(string[] args,string key,float fallback,float minimum,float maximum)
        {
            int index=Array.IndexOf(args,key);if(index<0)return fallback;
            if(index+1>=args.Length || !float.TryParse(args[index+1],System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out float value)
                || float.IsNaN(value) || float.IsInfinity(value) || value<minimum || value>maximum)
                throw new ArgumentException(key+" must be "+minimum+".."+maximum);
            return value;
        }

        // HAOLAN's resting mouth needs a downward offset. Fade it at either
        // expression endpoint so full smiles/frowns and asymmetry remain usable.
        public static float CornerDownWeight(float corner)
        {
            corner=Mathf.Clamp(corner,-1,1);
            return (Mathf.Max(0,-corner)+.30f*(1-Mathf.Abs(corner)))*100;
        }

        public static float ExpressiveCorner(float corner,float opening)
        {
            // Signed gamma: retain full expressions while reducing small deviations.
            corner=Mathf.Clamp(corner,-1,1);
            corner=corner*Mathf.Abs(corner);
            return corner<=0?corner:corner*(1-.9f*Mathf.SmoothStep(0,1,Mathf.Clamp01(opening/.65f)));
        }

        void DriveFaceDistance(TrackingPacket packet,bool live,float dt)
        {
            if(!faceDistanceEnabled || !live || packet==null || !packet.faceTracked || !packet.faceDistanceTracked || initialFaceDepth<=0)return;
            float requested=seatedDistance?Mathf.Clamp(packet.faceDistanceRatio,.34f,2.86f):Mathf.Clamp(packet.faceDistanceRatio,.75f,1.5f);
            faceDistanceRatio=Mathf.Lerp(faceDistanceRatio,requested,1-Mathf.Exp(-Mathf.Max(0,dt)*22));
            distanceEstablished=true;
            if(seatedDistance)
            {
                seatedLeanDegrees=SolveSeatedLean(framedDistance?1+(faceDistanceRatio-1)*.35f:faceDistanceRatio,out seatedLeanLimited);
                if(framedDistance)seatedLeanDegrees=Mathf.Clamp(seatedLeanDegrees,-15,35);
                return;
            }
            // Translate the entire hierarchy; retain mesh scale and local joint geometry.
            transform.position=rootRestPosition+depthDirection*(initialFaceDepth*(faceDistanceRatio-1));
        }

        void ApplyFaceFraming(TrackingPacket packet,bool live)
        {
            if(!framedDistance || !faceDistanceEnabled || !distanceEstablished || !live || !packet.faceTracked || !packet.faceDistanceTracked || !Camera.main)return;
            var camera=Camera.main.transform;
            float wantedDepth=initialFaceDepth*Mathf.Clamp(faceDistanceRatio,.5f,2f);
            float actualDepth=Vector3.Dot(head.position-camera.position,depthDirection);
            transform.position+=depthDirection*(wantedDepth-actualDepth);
            float wantedY=initialHeadCameraY*wantedDepth/initialFaceDepth;
            transform.position+=camera.up*(wantedY-Vector3.Dot(head.position-camera.position,camera.up));
        }

        static Quaternion TorsoRotation(Vector3 angles,bool seated)
        {
            // Apply yaw/roll first, then lean about the camera-aligned root X.
            // Euler(x,y,z) instead yaws the leaning direction toward the side.
            return seated?Quaternion.AngleAxis(angles.x,Vector3.right)*Quaternion.Euler(0,angles.y,angles.z):Quaternion.Euler(angles);
        }

        float SolveSeatedLean(float ratio,out bool limited)
        {
            // Head motion on an arc about the lower spine. Head orientation is
            // still driven in camera space below, avoiding a second head pitch.
            float wanted=initialFaceDepth*(ratio-1);
            float lo=-25,hi=65;
            Func<float,float> depth=a=>Vector3.Dot(transform.TransformVector(
                Quaternion.Euler(a,0,0)*seatedHeadOffset-seatedHeadOffset),depthDirection);
            limited=wanted<depth(hi) || wanted>depth(lo);
            for(int i=0;i<24;i++)
            {
                float mid=(lo+hi)*.5f;
                if(depth(mid)>wanted)lo=mid;else hi=mid;
            }
            return (lo+hi)*.5f;
        }

        void CheckSeatedPose()
        {
            var bones=GetComponentsInChildren<Transform>(true);
            var rotations=Array.ConvertAll(bones,b=>b.localRotation);
            var saved=current;float received=lastReceived,delta=probeDelta;
            float savedRatio=faceDistanceRatio,savedLean=seatedLeanDegrees;
            bool enabled=faceDistanceEnabled,mode=seatedDistance,established=distanceEstablished,limit=seatedLeanLimited;
            var torso=lastTorso;var root=transform.position;
            bool savedFramed=framedDistance;framedDistance=false;
            var leftCache=left.lowerUntwisted;var rightCache=right.lowerUntwisted;
            var hips=animator.GetBoneTransform(HumanBodyBones.Hips);
            var hipPosition=hips.position;var hipRotation=hips.rotation;
            probeDelta=1f/60;faceDistanceEnabled=true;seatedDistance=true;
            current=new TrackingPacket{tracked=true,faceTracked=true,body3d=true,torsoTracked=true,faceDistanceTracked=true,faceDistanceRatio=1};
            for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
            var headBase=head.position;
            current.faceDistanceRatio=.8f;
            for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
            float approach=-Vector3.Dot(head.position-headBase,depthDirection);
            if(approach<.05f || head.position.y>=headBase.y || transform.position!=root || Vector3.Distance(hips.position,hipPosition)>.00001f || Quaternion.Angle(hips.rotation,hipRotation)>.01f)
                throw new Exception("Seated pose failed actual head arc or fixed pelvis");
            if(Quaternion.Angle(head.rotation,transform.rotation*headRootRest)>.1f)throw new Exception("Seated lean doubled head pitch");
            var held=head.position;current=new TrackingPacket{tracked=true,body3d=true};
            for(int i=0;i<30;i++){lastReceived=Time.unscaledTime;LateUpdate();}
            if(Vector3.Distance(head.position,held)>.00001f)throw new Exception("Seated pose moved during loss");
            foreach(float yaw in new[]{-45f,45f})
            {
                current=new TrackingPacket{tracked=true,faceTracked=true,body3d=true,torsoTracked=true,torsoYaw=yaw,
                    faceDistanceTracked=true,faceDistanceRatio=1,leftArmTracked=true,rightArmTracked=true,leftArmHeld=true,rightArmHeld=true};
                for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
                var neutralHead=head.position;
                var localUpper=left.upper.localRotation;var localLower=left.lower.localRotation;
                var relativeElbow=chest.InverseTransformPoint(left.lower.position);
                current.faceDistanceRatio=.8f;
                for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
                float lateral=Mathf.Abs(transform.InverseTransformVector(head.position-neutralHead).x);
                if(lateral>.005f)throw new Exception("Seated yaw redirects approach laterally: "+lateral);
                if(Quaternion.Angle(localUpper,left.upper.localRotation)>.05f || Quaternion.Angle(localLower,left.lower.localRotation)>.05f ||
                    Vector3.Distance(relativeElbow,chest.InverseTransformPoint(left.lower.position))>.001f)
                    throw new Exception("Held elbow did not follow chest with local pose intact");
                var cacheBefore=Quaternion.Inverse(right.lower.parent.rotation)*right.lowerUntwisted;
                current.rightArmTracked=false;current.faceDistanceRatio=1;
                for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
                if(Quaternion.Angle(cacheBefore,Quaternion.Inverse(right.lower.parent.rotation)*right.lowerUntwisted)>.05f)
                    throw new Exception("Unobserved forearm cache stayed in world frame");
                Debug.Log("SEATED_COUPLING_OK yaw="+yaw+" lateral="+lateral+" held_elbow/local_cache");
            }
            for(int i=0;i<bones.Length;i++)bones[i].localRotation=rotations[i];
            current=saved;lastReceived=received;probeDelta=delta;faceDistanceRatio=savedRatio;seatedLeanDegrees=savedLean;
            faceDistanceEnabled=enabled;seatedDistance=mode;distanceEstablished=established;seatedLeanLimited=limit;lastTorso=torso;
            left.lowerUntwisted=leftCache;right.lowerUntwisted=rightCache;
            framedDistance=savedFramed;
            Debug.Log("SEATED_POSE_OK fixed_pelvis/head_arc/head_orientation/loss approach="+approach);
        }

        void CheckFramedPose()
        {
            var bones=GetComponentsInChildren<Transform>(true);
            var rotations=Array.ConvertAll(bones,b=>b.localRotation);
            var saved=current;float received=lastReceived,delta=probeDelta;
            float ratio=faceDistanceRatio,lean=seatedLeanDegrees;var root=transform.position;
            var torso=lastTorso;var lc=left.lowerUntwisted;var rc=right.lowerUntwisted;
            bool enabled=faceDistanceEnabled,mode=seatedDistance,framed=framedDistance,established=distanceEstablished,limited=seatedLeanLimited;
            faceDistanceEnabled=true;seatedDistance=true;framedDistance=true;probeDelta=1f/60;
            current=new TrackingPacket{tracked=true,faceTracked=true,body3d=true,torsoTracked=true,faceDistanceTracked=true,faceDistanceRatio=1};
            for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
            float baseY=Camera.main.WorldToViewportPoint(head.position).y;
            foreach(float target in new[]{.8f,.55f,1.25f})
            {
                current.faceDistanceRatio=target;
                for(int i=0;i<120;i++){lastReceived=Time.unscaledTime;LateUpdate();}
                float y=Camera.main.WorldToViewportPoint(head.position).y;
                float depth=Vector3.Dot(head.position-Camera.main.transform.position,depthDirection);
                if(Mathf.Abs(y-baseY)>.001f || Mathf.Abs(depth/initialFaceDepth-target)>.002f || Mathf.Abs(seatedLeanDegrees)>35.01f)
                    throw new Exception("Framed approach failed stable face height/depth/modest lean");
                var held=transform.position;var pos=head.position;
                current.faceDistanceTracked=false;
                for(int i=0;i<30;i++){lastReceived=Time.unscaledTime;LateUpdate();}
                if(Vector3.Distance(held,transform.position)>.00001f || Vector3.Distance(pos,head.position)>.0001f)throw new Exception("Framed approach drifted during distance loss");
                current.faceDistanceTracked=true;
            }
            for(int i=0;i<bones.Length;i++)bones[i].localRotation=rotations[i];
            transform.position=root;current=saved;lastReceived=received;probeDelta=delta;faceDistanceRatio=ratio;seatedLeanDegrees=lean;
            faceDistanceEnabled=enabled;seatedDistance=mode;framedDistance=framed;distanceEstablished=established;seatedLeanLimited=limited;
            lastTorso=torso;left.lowerUntwisted=lc;right.lowerUntwisted=rc;
            Debug.Log("FRAMED_POSE_OK stable_screen_height/depth/loss/modest_lean");
        }

        void CheckFaceDistance()
        {
            var savedPosition=transform.position;float savedRatio=faceDistanceRatio;
            bool savedEnabled=faceDistanceEnabled;faceDistanceEnabled=true;
            bool savedSeated=seatedDistance,savedEstablished=distanceEstablished;
            float savedLean=seatedLeanDegrees;bool savedLimited=seatedLeanLimited;
            seatedDistance=false;
            var scale=transform.localScale;
            foreach(float ratio in new[]{.8f,1.25f})
            {
                var p=new TrackingPacket{faceTracked=true,faceDistanceTracked=true,faceDistanceRatio=ratio};
                for(int i=0;i<60;i++)DriveFaceDistance(p,true,1f/60);
                float offset=Vector3.Dot(transform.position-rootRestPosition,depthDirection);
                if(Mathf.Abs(offset-initialFaceDepth*(ratio-1))>.001f)throw new Exception("Face distance translation mismatch");
                if(transform.localScale!=scale)throw new Exception("Face distance changed avatar scale");
                var held=transform.position;
                DriveFaceDistance(null,false,1);DriveFaceDistance(new TrackingPacket{faceTracked=true},true,1);
                if(transform.position!=held)throw new Exception("Face distance moved during loss");
            }
            faceDistanceEnabled=false;
            var disabled=transform.position;
            DriveFaceDistance(new TrackingPacket{faceTracked=true,faceDistanceTracked=true,faceDistanceRatio=.75f},true,1);
            if(transform.position!=disabled)throw new Exception("Disabled face distance moved");
            seatedDistance=true;faceDistanceEnabled=true;transform.position=savedPosition;
            foreach(float ratio in new[]{.8f,1.2f})
            {
                for(int i=0;i<60;i++)DriveFaceDistance(new TrackingPacket{faceTracked=true,faceDistanceTracked=true,faceDistanceRatio=ratio},true,1f/60);
                if(transform.position!=savedPosition || (ratio<1?seatedLeanDegrees<=0:seatedLeanDegrees>=0))throw new Exception("Seated lean direction/pivot mismatch");
            }
            SolveSeatedLean(.01f,out bool bounded);
            if(!bounded)throw new Exception("Missing seated angle limit diagnostic");
            seatedDistance=savedSeated;distanceEstablished=savedEstablished;seatedLeanDegrees=savedLean;seatedLeanLimited=savedLimited;
            transform.position=savedPosition;faceDistanceRatio=savedRatio;faceDistanceEnabled=savedEnabled;
            Debug.Log("FACE_DISTANCE_OK approach/retreat/loss/disabled/scale");
        }

        Vector2 CameraGazeTarget()
        {
            if(!Camera.main || !head)return Vector2.zero;
            var frame=head.rotation*Quaternion.Inverse(headRootRest);
            var center=head.TransformPoint(faceCenterLocal);
            var local=Quaternion.Inverse(frame)*(Camera.main.transform.position-center).normalized;
            return new Vector2(Mathf.Clamp(Mathf.Atan2(local.x,local.z)*Mathf.Rad2Deg,-20,20),
                Mathf.Clamp(-Mathf.Atan2(local.y,Mathf.Sqrt(local.x*local.x+local.z*local.z))*Mathf.Rad2Deg,-12,12));
        }

        void DriveGaze(TrackingPacket packet,bool live,float dt)
        {
            bool valid=gazeEnabled && live && packet!=null && packet.faceTracked && packet.gazeTracked;
            var target=valid?FacialExaggeration.GazeTarget(new Vector2(packet.gazeYaw,packet.gazePitch),gazeGain*exaggeration.EyeGain,legacyGazeResponse):(gazeEnabled?CameraGazeTarget():Vector2.zero);
            gazeAngles=Vector2.Lerp(gazeAngles,target,1-Mathf.Exp(-Mathf.Max(0,dt)*(valid?22f:2f)));
            if(gazeAngles.sqrMagnitude<.0001f)gazeAngles=Vector2.zero;
            for(int eyeIndex=0;eyeIndex<2;eyeIndex++)
            {
                var eye=eyeIndex==0?leftEye:rightEye;
                string side=eyeIndex==0?"L":"R";
                var angles=expressions.Eye(side,gazeAngles,allowShapes:gazeIrisMode);
                if(!eye)continue;
                var rest=eye==leftEye?leftEyeRest:rightEyeRest;
                var frame=head.rotation*Quaternion.Inverse(headRootRest);
                var turn=Quaternion.AngleAxis(angles.x,frame*Vector3.up)*Quaternion.AngleAxis(angles.y,frame*Vector3.right);
                eye.rotation=turn*eye.parent.rotation*rest;
            }
            expressions.Commit(); // Also permits isolated gaze checks outside LateUpdate.
        }

        void GenerateAutoGazeShapes()
        {
            // HAOLAN's eye skin weights are ~3.5%. Use the author's iris region,
            // intersected with actual eye-bone influence; never edit original weights.
            foreach(var renderer in meshes)
            {
                var mesh=renderer.sharedMesh;int index=mesh.GetBlendShapeIndex("瞳小");
                if(index<0 || !leftEye || !rightEye)continue;
                if(!mesh.isReadable){Debug.LogWarning("Auto iris generation skipped: mesh Read/Write disabled on "+renderer.name);continue;}
                int l=Array.IndexOf(renderer.bones,leftEye),r=Array.IndexOf(renderer.bones,rightEye);
                if(l<0 || r<0)continue;
                var iris=new Vector3[mesh.vertexCount];mesh.GetBlendShapeFrameVertices(index,0,iris,null,null);
                var weights=mesh.boneWeights;var support=new float[weights.Length];float maximum=0;
                for(int i=0;i<weights.Length;i++)
                {
                    var w=weights[i];
                    float value=(w.boneIndex0==l||w.boneIndex0==r?w.weight0:0)+(w.boneIndex1==l||w.boneIndex1==r?w.weight1:0)+
                        (w.boneIndex2==l||w.boneIndex2==r?w.weight2:0)+(w.boneIndex3==l||w.boneIndex3==r?w.weight3:0);
                    if(iris[i].sqrMagnitude>1e-12f){support[i]=value;maximum=Mathf.Max(maximum,value);}
                }
                if(maximum<=0)continue;
                mesh=ExpressionClone(renderer); // Iris-only avatars also require an isolated clone.
                var directions=new[]{Vector3.right*.004f,Vector3.left*.004f,Vector3.down*.0025f,Vector3.up*.0025f};
                var names=new[]{"TC_GazeRight","TC_GazeLeft","TC_GazeDown","TC_GazeUp"};
                for(int d=0;d<4;d++)
                {
                    if(mesh.GetBlendShapeIndex(names[d])>=0)continue;
                    var delta=new Vector3[mesh.vertexCount];
                    var direction=renderer.transform.InverseTransformVector(transform.TransformVector(directions[d]));
                    for(int i=0;i<delta.Length;i++)delta[i]=direction*(support[i]/maximum);
                    mesh.AddBlendShapeFrame(names[d],100,delta,null,null);
                }
                renderer.sharedMesh=null;renderer.sharedMesh=mesh;gazeMesh=renderer;
                Debug.Log("TANAKACAP_GAZE_IRIS_SHAPES_READY maxEyeWeight="+maximum);
                return;
            }
        }

        void CheckGaze()
        {
            if(!leftEye || !rightEye)throw new Exception("HAOLAN eye bones missing");
            var saved=gazeAngles;bool enabled=gazeEnabled;gazeEnabled=true;
            gazeAngles=Vector2.zero;DriveGaze(null,false,0);
            var eyeMeshes=new System.Collections.Generic.List<SkinnedMeshRenderer>();
            var neutralMeshes=new System.Collections.Generic.List<Vector3[]>();
            foreach(var renderer in meshes)
            {
                bool usesEyes=false;
                foreach(var bone in renderer.bones)
                    if(bone && (bone==leftEye || bone==rightEye || bone.IsChildOf(leftEye) || bone.IsChildOf(rightEye)))usesEyes=true;
                if(!usesEyes)continue;
                for(int b=0;b<renderer.bones.Length;b++)if(renderer.bones[b] && renderer.bones[b].name.Contains("Eye"))
                {
                    float weight=0;int count=0;
                    foreach(var w in renderer.sharedMesh.boneWeights)
                    {
                        float value=(w.boneIndex0==b?w.weight0:0)+(w.boneIndex1==b?w.weight1:0)+(w.boneIndex2==b?w.weight2:0)+(w.boneIndex3==b?w.weight3:0);
                        if(value>0){weight+=value;count++;}
                    }
                    Debug.Log("TANAKACAP_EYE_WEIGHTS "+renderer.name+" "+renderer.bones[b].name+" count="+count+" total="+weight+" position="+renderer.bones[b].position.ToString("F5"));
                }
                var baked=new Mesh();renderer.BakeMesh(baked);eyeMeshes.Add(renderer);neutralMeshes.Add(baked.vertices);Destroy(baked);
            }
            foreach(float sign in new[]{-1f,1f})
            {
                var p=new TrackingPacket{faceTracked=true,gazeTracked=true,gazeYaw=15*sign,gazePitch=8*sign};
                for(int i=0;i<60;i++)DriveGaze(p,true,1f/60);
                float maxMovement=0;
                for(int m=0;m<eyeMeshes.Count;m++)
                {
                    var baked=new Mesh();eyeMeshes[m].BakeMesh(baked);var vertices=baked.vertices;
                    for(int v=0;v<vertices.Length;v++)maxMovement=Mathf.Max(maxMovement,eyeMeshes[m].transform.TransformVector(vertices[v]-neutralMeshes[m][v]).magnitude);
                    var mesh=eyeMeshes[m].sharedMesh;int irisIndex=mesh.GetBlendShapeIndex("瞳小");
                    if(gazeIrisMode && eyeMeshes[m]==gazeMesh)
                    {
                        var movement=new Vector3[mesh.vertexCount];mesh.GetBlendShapeFrameVertices(mesh.GetBlendShapeIndex("TC_GazeRight"),0,movement,null,null);
                        var frame=head.rotation*Quaternion.Inverse(headRootRest);int checkedVertices=0;
                        for(int v=0;v<vertices.Length;v++)
                        {
                            var delta=Quaternion.Inverse(frame)*eyeMeshes[m].transform.TransformVector(vertices[v]-neutralMeshes[m][v]);
                            if(movement[v].sqrMagnitude<1e-14f)
                            {if(delta.magnitude>1e-6f)throw new Exception("Gaze moved a non-iris vertex");}
                            else
                            {
                                if(delta.x*sign<.0024f || delta.y*sign>-.0012f || Mathf.Abs(delta.z)>.0002f)
                                    throw new Exception("Iris translation direction/range mismatch");
                                checkedVertices++;
                            }
                        }
                        if(checkedVertices<100)throw new Exception("Iris translation has too little support");
                        Debug.Log("TANAKACAP_IRIS_DIRECTION_ISOLATION_OK sign="+sign+" vertices="+checkedVertices);
                    }
                    if(irisIndex>=0)
                    {
                        var shape=new Vector3[mesh.vertexCount];mesh.GetBlendShapeFrameVertices(irisIndex,0,shape,null,null);
                        float moved=0;int count=0;float pixels=0;
                        for(int v=0;v<vertices.Length;v++)if(shape[v].sqrMagnitude>1e-12f)
                        {
                            var a=eyeMeshes[m].transform.TransformPoint(neutralMeshes[m][v]);var b=eyeMeshes[m].transform.TransformPoint(vertices[v]);
                            moved=Mathf.Max(moved,(b-a).magnitude);pixels=Mathf.Max(pixels,Vector2.Distance(Camera.main.WorldToScreenPoint(a),Camera.main.WorldToScreenPoint(b)));count++;
                        }
                        Debug.Log("TANAKACAP_IRIS_AUDIT sign="+sign+" vertices="+count+" maxMeters="+moved+" maxPixels="+pixels);
                        foreach(var eye in new[]{leftEye,rightEye})
                        {
                            Vector3 center=Vector3.zero,delta=Vector3.zero;int selected=0;
                            int eyeIndex=Array.IndexOf(eyeMeshes[m].bones,eye);var skin=mesh.boneWeights;
                            for(int v=0;v<vertices.Length;v++)if(shape[v].sqrMagnitude>1e-12f)
                            {
                                var a=eyeMeshes[m].transform.TransformPoint(neutralMeshes[m][v]);var b=eyeMeshes[m].transform.TransformPoint(vertices[v]);
                                var w=skin[v];
                                if(!((w.boneIndex0==eyeIndex && w.weight0>0)||(w.boneIndex1==eyeIndex && w.weight1>0)||(w.boneIndex2==eyeIndex && w.weight2>0)||(w.boneIndex3==eyeIndex && w.weight3>0)))continue;
                                center+=a;delta+=Camera.main.WorldToScreenPoint(b)-Camera.main.WorldToScreenPoint(a);selected++;
                            }
                            if(selected>0)Debug.Log("TANAKACAP_IRIS_CENTER "+eye.name+" sign="+sign+" pixels="+(delta/selected).ToString("F4")+" pivotToCenter="+(Quaternion.Inverse(head.rotation*Quaternion.Inverse(headRootRest))*(center/selected-eye.position)).ToString("F5"));
                        }
                    }
                    Destroy(baked);
                }
                if(maxMovement<.0001f)throw new Exception("Gaze bones did not deform the avatar mesh");
                Debug.Log("TANAKACAP_GAZE_MESH_OK sign="+sign+" max="+maxMovement);
                foreach(var eye in new[]{leftEye,rightEye})
                {
                    var rest=eye==leftEye?leftEyeRest:rightEyeRest;
                    var delta=eye.rotation*Quaternion.Inverse(eye.parent.rotation*rest);
                    var frame=head.rotation*Quaternion.Inverse(headRootRest);
                    var direction=Quaternion.Inverse(frame)*(delta*(frame*Vector3.forward));
                    if((!gazeIrisMode || !gazeMesh) && (direction.x*sign<.20f || direction.y*sign>-.10f))throw new Exception("Gaze bone direction mismatch");
                }
                var targetCamera=CameraGazeTarget();var before=gazeAngles-targetCamera;DriveGaze(null,false,1f/60);
                if((gazeAngles-targetCamera).magnitude<before.magnitude*.95f || (gazeAngles-targetCamera).magnitude>=before.magnitude)
                    throw new Exception("Lost gaze snapped instead of slowly returning");
                for(int i=0;i<180;i++)DriveGaze(null,false,1f/60);
                if((gazeAngles-targetCamera).magnitude>before.magnitude*.003f)throw new Exception("Lost gaze failed to converge to camera in three seconds");
            }
            var savedHead=head.rotation;
            foreach(float yaw in new[]{-10f,10f})
            {
                head.rotation=Quaternion.LookRotation(Camera.main.transform.position-head.position,Vector3.up)*Quaternion.Euler(0,yaw,0)*headRootRest;
                for(int i=0;i<240;i++)DriveGaze(null,false,1f/60);
                var frame=head.rotation*Quaternion.Inverse(headRootRest);
                float x=gazeAngles.x*Mathf.Deg2Rad,y=gazeAngles.y*Mathf.Deg2Rad;
                var direction=frame*new Vector3(Mathf.Sin(x)*Mathf.Cos(y),-Mathf.Sin(y),Mathf.Cos(x)*Mathf.Cos(y));
                var wanted=(Camera.main.transform.position-head.TransformPoint(faceCenterLocal)).normalized;
                if(Vector3.Angle(direction,wanted)>.1f)throw new Exception("Lost gaze is not aimed at camera after head turn");
            }
            head.rotation=savedHead;
            Debug.Log("CAMERA_GAZE_OK head_turn/world_direction/slow_return");
            gazeAngles=new Vector2(15,8);gazeEnabled=false;
            for(int i=0;i<180;i++)DriveGaze(new TrackingPacket{faceTracked=true,gazeTracked=true,gazeYaw=20},true,1f/60);
            if(gazeAngles.magnitude>.05f)throw new Exception("Disabled gaze still tracked");
            gazeEnabled=enabled;gazeAngles=saved;DriveGaze(null,false,0);
            Debug.Log("TANAKACAP_GAZE_DIRECTIONS_LOSS_DISABLE_OK");
        }

        void DriveArm(Arm arm, bool valid, Vector3 elbow, Vector3 wrist, bool isLeft, float t, bool wristInFront=false, bool upperInFront=false,float crossBody=0)
        {
            if(!valid) return;
            // Position is already filtered at capture cadence. Keep only a short
            // render interpolation; face/torso and wrist constraints stay separate.
            if(valid) t=1-Mathf.Exp(-FrameDelta*36);
            // Directions now include learned depth. Bone lengths come from the avatar.
            Vector3 a = valid ? elbow : new Vector3(isLeft ? -.22f : .22f,-.8f,.1f);
            Vector3 b = valid ? wrist-elbow : new Vector3(0,-.7f,.3f);
            if (a.sqrMagnitude < .002f || b.sqrMagnitude < .002f) return;
            var bodyForward=transform.InverseTransformDirection(chest.rotation*Quaternion.Inverse(chestRootRest)*Vector3.forward).normalized;
            var target=a.normalized*arm.upperLength+b.normalized*arm.lowerLength;
            var center=transform.InverseTransformVector(head.TransformPoint(faceCenterLocal)-arm.upper.position);
            var clearTarget=ClearFace(target,center,.18f);
            bool faceCollision=(target-clearTarget).sqrMagnitude>.0000001f;
            bool outwardBehind=!wristInFront && crossBody<=0 && (isLeft?-1:1)*wrist.x>.035f &&
                target.y<.12f && Vector3.Dot(target,bodyForward)<-.025f;
            SolveArm(a,b,arm.upperLength,arm.lowerLength,ref arm.pole,out var upperDirection,out var lowerDirection,wristInFront,upperInFront,crossBody,bodyForward,faceCollision?(Vector3?)clearTarget:null,outwardBehind);
            Quaternion upperBase = transform.rotation*arm.upperRootRest;
            Quaternion upperTarget = Quaternion.FromToRotation(upperBase*arm.upperDirection,transform.TransformDirection(upperDirection))*upperBase;
            arm.upper.rotation = Quaternion.Slerp(arm.upper.rotation,upperTarget,t);
            Quaternion lowerBase = transform.rotation*arm.lowerRootRest;
            Quaternion lowerTarget = Quaternion.FromToRotation(lowerBase*arm.lowerDirection,transform.TransformDirection(lowerDirection))*lowerBase;
            // A fixed authored reference avoids moving the rotation limit's
            // center when the elbow plane flips or its hemisphere history changes.
            arm.lowerUntwisted = Quaternion.Slerp(arm.lowerUntwisted,lowerTarget,t);
            arm.lower.rotation = Quaternion.AngleAxis(arm.twist,arm.lowerUntwisted*arm.lowerDirection)*arm.lowerUntwisted;
            // Interpolation from an old backward pose must not violate a newly
            // confirmed front constraint. Project to the solved feasible pose.
            if(faceCollision || outwardBehind || (wristInFront && transform.InverseTransformVector(arm.hand.position-arm.upper.position).z<0) ||
                (upperInFront && transform.InverseTransformVector(arm.lower.position-arm.upper.position).z<0) ||
                (crossBody>0 && (Vector3.Dot(transform.InverseTransformVector(arm.lower.position-arm.upper.position),bodyForward)<.06f*crossBody ||
                 Vector3.Dot(transform.InverseTransformVector(arm.hand.position-arm.upper.position),bodyForward)<.06f*crossBody)))
            {
                arm.upper.rotation=upperTarget;
                arm.lowerUntwisted=lowerTarget;
                arm.lower.rotation=Quaternion.AngleAxis(arm.twist,lowerTarget*arm.lowerDirection)*lowerTarget;
            }
        }

        public static Vector3 ClearFace(Vector3 target,Vector3 center,float radius)
        {
            var delta=target-center;
            if(delta.sqrMagnitude>=radius*radius)return target;
            target.z=center.z+Mathf.Sqrt(Mathf.Max(0,radius*radius-delta.x*delta.x-delta.y*delta.y))+.005f;
            return target;
        }

        public static void SolveArm(Vector3 a, Vector3 b, float l1, float l2, ref Vector3 pole, out Vector3 upper, out Vector3 lower, bool wristInFront=false, bool upperInFront=false,float crossBody=0,Vector3 bodyForward=default(Vector3),Vector3? targetOverride=null,bool outwardBehind=false)
        {
            if(upperInFront) a.z=Mathf.Abs(a.z);
            Vector3 target = a.normalized*l1+b.normalized*l2;
            if(targetOverride.HasValue)target=targetOverride.Value;
            if(wristInFront) target.z=Mathf.Max(.015f,target.z);
            crossBody=Mathf.Clamp01(crossBody);
            if(bodyForward.sqrMagnitude<.01f)bodyForward=Vector3.forward;
            bodyForward.Normalize();
            if(crossBody>0)target+=bodyForward*Mathf.Max(0,.10f*crossBody-Vector3.Dot(target,bodyForward));
            Vector3 axis = target.sqrMagnitude>.000001f ? target.normalized : a.normalized;
            float minimum = Mathf.Sqrt(l1*l1+l2*l2+2*l1*l2*Mathf.Cos(155*Mathf.Deg2Rad));
            float maximum = Mathf.Sqrt(l1*l1+l2*l2+2*l1*l2*Mathf.Cos(5*Mathf.Deg2Rad));
            float distance = Mathf.Clamp(target.magnitude,minimum,maximum);
            Vector3 candidate = Vector3.ProjectOnPlane(a.normalized,axis);
            if (candidate.sqrMagnitude > .0025f) pole = candidate.normalized;
            Vector3 bend = Vector3.ProjectOnPlane(pole,axis);
            if (bend.sqrMagnitude<.0001f) bend = Vector3.Cross(axis,Vector3.forward);
            if (bend.sqrMagnitude<.0001f) bend = Vector3.Cross(axis,Vector3.up);
            bend.Normalize();
            float cosine = Mathf.Clamp((l1*l1+distance*distance-l2*l2)/(2*l1*distance),-1,1);
            if(crossBody>0)
            {
                // Choose the nearest point on the elbow circle clearing the
                // torso plane. Preserve lengths and endpoint, never reflect a.z.
                float radius=l1*Mathf.Sqrt(Mathf.Max(0,1-cosine*cosine));
                Vector3 gradient=Vector3.ProjectOnPlane(bodyForward,axis);
                float extent=radius*gradient.magnitude;
                if(extent>.00001f)
                {
                    gradient.Normalize();
                    float required=Mathf.Clamp((.08f*crossBody-l1*cosine*Vector3.Dot(axis,bodyForward))/extent,-1,1);
                    if(Vector3.Dot(bend,gradient)<required)
                    {
                        var tangent=bend-gradient*Vector3.Dot(bend,gradient);
                        if(tangent.sqrMagnitude<.00001f)tangent=Vector3.Cross(axis,gradient);
                        bend=gradient*required+tangent.normalized*Mathf.Sqrt(Mathf.Max(0,1-required*required));
                    }
                }
            }
            if(outwardBehind)
            {
                // Low outward hand behind the torso: choose a posterior elbow
                // on the same fixed-length circle, instead of a reverse bend.
                float radius=l1*Mathf.Sqrt(Mathf.Max(0,1-cosine*cosine));
                var normal=-bodyForward;
                var gradient=Vector3.ProjectOnPlane(normal,axis);
                float extent=radius*gradient.magnitude;
                if(extent>.00001f)
                {
                    gradient.Normalize();
                    float minimumDepth=-Vector3.Dot(axis*distance,bodyForward)+.02f;
                    float required=Mathf.Clamp((minimumDepth-l1*cosine*Vector3.Dot(axis,normal))/extent,-1,1);
                    if(Vector3.Dot(bend,gradient)<required)
                    {
                        var tangent=bend-gradient*Vector3.Dot(bend,gradient);
                        if(tangent.sqrMagnitude<.00001f)tangent=Vector3.Cross(axis,gradient);
                        bend=gradient*required+tangent.normalized*Mathf.Sqrt(Mathf.Max(0,1-required*required));
                    }
                }
            }
            upper = axis*cosine+bend*Mathf.Sqrt(Mathf.Max(0,1-cosine*cosine));
            if(upperInFront && upper.z<0)
            {
                bend=Vector3.ProjectOnPlane(Vector3.forward,axis).normalized;
                upper=axis*cosine+bend*Mathf.Sqrt(Mathf.Max(0,1-cosine*cosine));
            }
            lower = (axis*distance-upper*l1).normalized;
        }

        void DriveHand(Arm arm, bool valid, Vector3 forward, Vector3 normal, float t)
        {
            if (!valid || !arm.handBasisValid || forward.sqrMagnitude<.01f || normal.sqrMagnitude<.01f || Vector3.Cross(forward,normal).sqrMagnitude<.001f)
            {
                return;
            }
            Vector3 axis=arm.lowerUntwisted*arm.lowerDirection;
            Quaternion neutralFrame=arm.lowerUntwisted*arm.handRest*Quaternion.Inverse(arm.handFrameCorrection);
            Vector3 baseNormal=Vector3.ProjectOnPlane(neutralFrame*Vector3.up,axis);
            // Undo the hand bend before extracting forearm roll. Projecting a
            // bent palm's normal directly onto the forearm confounds both axes.
            var undoBend=Quaternion.FromToRotation(transform.TransformDirection(forward),neutralFrame*Vector3.forward);
            Vector3 wantedNormal=Vector3.ProjectOnPlane(undoBend*transform.TransformDirection(normal),axis);
            float desiredTwist=0;
            if(baseNormal.sqrMagnitude>.001f && wantedNormal.sqrMagnitude>.001f)
            {
                float raw=Vector3.SignedAngle(baseNormal,wantedNormal,axis);
                // No accumulated revolutions: unwrap relative to the displayed,
                // bounded joint, not a hidden unconstrained integrator.
                arm.requestedTwist=UnwrapTwist(arm.twist,arm.twist,raw);
                desiredTwist=SelectForearmTwist(arm.twist,raw);
            }
            else desiredTwist=arm.twist;
            arm.twist=Mathf.MoveTowards(arm.twist,desiredTwist,900*FrameDelta);
            // Rotation about the forearm axis leaves elbow and wrist positions fixed.
            arm.lower.rotation=Quaternion.AngleAxis(arm.twist,axis)*arm.lowerUntwisted;
            neutralFrame=arm.lower.rotation*arm.handRest*Quaternion.Inverse(arm.handFrameCorrection);
            Quaternion target=ConstrainHandFrame(neutralFrame,transform.TransformDirection(forward),transform.TransformDirection(normal))*arm.handFrameCorrection;
            Quaternion smooth = Quaternion.Slerp(arm.handBeforeSolve,target,1-Mathf.Exp(-60*FrameDelta));
            arm.hand.rotation = Quaternion.RotateTowards(arm.handBeforeSolve,smooth,1080*FrameDelta);
            // The parent can move while the hand is smoothing: enforce local limits
            // after interpolation too, rather than only constraining its target.
            var actualFrame=arm.hand.rotation*Quaternion.Inverse(arm.handFrameCorrection);
            arm.hand.rotation=ConstrainHandFrame(neutralFrame,actualFrame*Vector3.forward,actualFrame*Vector3.up)*arm.handFrameCorrection;
        }

        public static float UnwrapTwist(float continuous,float previousRaw,float raw)
        {
            return continuous+Mathf.DeltaAngle(previousRaw,raw);
        }

        public static Quaternion ConstrainHandFrame(Quaternion neutral,Vector3 forward,Vector3 normal)
        {
            Vector3 limited=Vector3.RotateTowards(neutral*Vector3.forward,forward.normalized,90*Mathf.Deg2Rad,0);
            Quaternion swing=Quaternion.FromToRotation(neutral*Vector3.forward,limited)*neutral;
            Vector3 wanted=Vector3.ProjectOnPlane(normal,limited);
            float twist=wanted.sqrMagnitude>.001f ? Mathf.Clamp(Vector3.SignedAngle(swing*Vector3.up,wanted,limited),-40,40) : 0;
            return Quaternion.AngleAxis(twist,limited)*swing;
        }

        public static float SelectForearmTwist(float displayed,float raw)
        {
            // Choose the short angular path BEFORE applying limits. Do not
            // switch to the opposite branch when wrapped raw crosses +/-140.
            // An unreachable continuation stops at the limit instead of taking
            // a 200-degree reverse detour through the joint's allowed interval.
            return Mathf.Clamp(UnwrapTwist(displayed,displayed,raw),-ForearmTwistLimit,ForearmTwistLimit);
        }


        void GenerateAutoMouthShapes()
        {
            foreach(var renderer in meshes)
            {
                var original=renderer.sharedMesh;
                if(original.GetBlendShapeIndex("口角上げ")<0)continue;
                if(!original.isReadable){Debug.LogWarning("Auto mouth generation skipped: mesh Read/Write disabled on "+renderer.name);continue;}
                // Runtime-only clone: never modify the imported avatar asset.
                var mesh=ExpressionClone(renderer);
                var vertices=mesh.vertices;
                {
                    var shift=new Vector3[vertices.Length];
                    var authored=new Vector3[vertices.Length];
                    int source=original.GetBlendShapeIndex("口_上");
                    if(source>=0)original.GetBlendShapeFrameVertices(source,original.GetBlendShapeFrameCount(source)-1,authored,null,null);
                    float maximum=0,weightSum=0,centerY=0;
                    for(int i=0;i<authored.Length;i++)
                    {
                        float weight=Mathf.Abs(transform.InverseTransformVector(renderer.transform.TransformVector(authored[i])).y);
                        maximum=Mathf.Max(maximum,weight);
                        float y=transform.InverseTransformPoint(renderer.transform.TransformPoint(vertices[i])).y;
                        centerY+=y*weight*weight;weightSum+=weight*weight;
                    }
                    centerY/=Mathf.Max(weightSum,1e-10f);
                    int moved=0;
                    for(int i=0;i<shift.Length;i++)
                    {
                        // Only the author's mouth-translation support may move.
                        // A narrow vertical taper keeps the chin silhouette fixed.
                        float y=transform.InverseTransformPoint(renderer.transform.TransformPoint(vertices[i])).y;
                        float vertical=Mathf.Abs(transform.InverseTransformVector(renderer.transform.TransformVector(authored[i])).y);
                        float support=vertical/Mathf.Max(maximum,1e-8f)*MouthLipMask(y-centerY);
                        shift[i]=renderer.transform.InverseTransformVector(transform.TransformVector(Vector3.left*mouthShiftDistance))*support;
                        if(shift[i].sqrMagnitude>1e-12f)moved++;
                        if(Mathf.Abs(y-centerY)>=.014f && shift[i].sqrMagnitude>1e-12f)throw new Exception("Mouth shift escaped lip band");
                    }
                    var opposite=new Vector3[shift.Length];
                    for(int i=0;i<shift.Length;i++)opposite[i]=-shift[i];
                    if(moved==0){Debug.LogWarning("Auto mouth shift unavailable: no isolated lip support on "+renderer.name);}
                    else {
                    if(mesh.GetBlendShapeIndex("TC_MouthShiftLeft")<0)mesh.AddBlendShapeFrame("TC_MouthShiftLeft",100,shift,null,null);
                    if(mesh.GetBlendShapeIndex("TC_MouthShiftRight")<0)mesh.AddBlendShapeFrame("TC_MouthShiftRight",100,opposite,null,null);
                    renderer.sharedMesh=null;renderer.sharedMesh=mesh;
                    Debug.Log("TANAKACAP_MOUTH_ISOLATED: "+renderer.name+" vertices="+moved+" centerY="+centerY+" band=14mm");
                    if(Array.IndexOf(Environment.GetCommandLineArgs(),"--motion-check")>=0 || Array.IndexOf(Environment.GetCommandLineArgs(),"--check-mouth-shift-isolation")>=0)
                        CheckMouthShiftIsolation(renderer,vertices,authored,centerY);
                    }
                }
                foreach(bool up in new[]{true,false})foreach(bool isLeft in new[]{true,false})
                {
                    string existingCorner="TC_"+(isLeft?"Left":"Right")+"Corner"+(up?"Up":"Down");
                    if(mesh.GetBlendShapeIndex(existingCorner)>=0)continue;
                    int source=original.GetBlendShapeIndex(up?"口角上げ":"口角下げ");
                    if(source<0)continue;
                    var delta=new Vector3[vertices.Length];var normals=new Vector3[vertices.Length];var tangents=new Vector3[vertices.Length];
                    original.GetBlendShapeFrameVertices(source,original.GetBlendShapeFrameCount(source)-1,delta,normals,tangents);
                    float vertical=0;
                    foreach(var d in delta) vertical=Mathf.Max(vertical,Mathf.Abs(transform.InverseTransformVector(renderer.transform.TransformVector(d)).y));
                    // Author morphs can be very subtle. Normalize small corner
                    // motion up to 6mm at full control, with a bounded gain.
                    float cornerGain=vertical>1e-6f?Mathf.Clamp(.006f/vertical,1,3):1;
                    for(int i=0;i<vertices.Length;i++)
                    {
                        float x=transform.InverseTransformPoint(renderer.transform.TransformPoint(vertices[i])).x;
                        // Anatomical left is root -X for this +Z-facing avatar.
                        float leftWeight=Mathf.Clamp01(.5f-x/.02f);
                        float weight=isLeft?leftWeight:1-leftWeight;
                        delta[i]*=weight*cornerGain;normals[i]*=weight*cornerGain;tangents[i]*=weight*cornerGain;
                    }
                    string cornerName="TC_"+(isLeft?"Left":"Right")+"Corner"+(up?"Up":"Down");
                    mesh.AddBlendShapeFrame(cornerName,100,delta,normals,tangents);
                    cornerGains[(renderer,cornerName)]=cornerGain;
                }
            }
        }

        void SetCornerShape(SkinnedMeshRenderer renderer,string name,float weight)
        {
            // Shapes retain the old baked gain: 1 reproduces the previous output,
            // 0 removes only that gain, preserving gamma/calibration/open-mouth suppression.
            if(cornerGains.TryGetValue((renderer,name),out float gain))
                weight*=Mathf.Lerp(1/gain,1,Mathf.Clamp01(MouthCornerEmphasis));
            SetShape(renderer,name,weight);
        }

        static void SetShape(SkinnedMeshRenderer renderer, string name, float weight)
        {
            int index = renderer.sharedMesh.GetBlendShapeIndex(name);
            if (index >= 0) renderer.SetBlendShapeWeight(index,weight);
        }

        public static float MouthLipMask(float y)
        {
            return 1-Mathf.SmoothStep(0,1,Mathf.Clamp01((Mathf.Abs(y)-.006f)/.008f));
        }

        void CheckMouthShiftIsolation(SkinnedMeshRenderer renderer,Vector3[] rest,Vector3[] authored,float centerY)
        {
            int leftIndex=renderer.sharedMesh.GetBlendShapeIndex("TC_MouthShiftLeft");
            int rightIndex=renderer.sharedMesh.GetBlendShapeIndex("TC_MouthShiftRight");
            float savedLeft=renderer.GetBlendShapeWeight(leftIndex),savedRight=renderer.GetBlendShapeWeight(rightIndex);
            var baseline=new Mesh();var changed=new Mesh();
            renderer.SetBlendShapeWeight(leftIndex,0);renderer.SetBlendShapeWeight(rightIndex,0);renderer.BakeMesh(baseline);var points=baseline.vertices;
            foreach(float sign in new[]{-1f,1f})
            {
                renderer.SetBlendShapeWeight(leftIndex,sign>0?100:0);renderer.SetBlendShapeWeight(rightIndex,sign<0?100:0);
                renderer.BakeMesh(changed);var target=changed.vertices;float maximum=0;
                for(int i=0;i<points.Length;i++)
                {
                    float movement=renderer.transform.TransformVector(target[i]-points[i]).magnitude;
                    float y=transform.InverseTransformPoint(renderer.transform.TransformPoint(rest[i])).y;
                    if((Mathf.Abs(y-centerY)>=.014f || authored[i].sqrMagnitude<1e-15f) && movement>1e-6f)
                        throw new Exception("Baked mouth shift moved chin/neck or unauthored vertex");
                    maximum=Mathf.Max(maximum,movement);
                }
                if(Mathf.Abs(maximum-mouthShiftDistance)>.0002f)throw new Exception("Isolated mouth shift did not reach requested limit: "+sign+" / "+maximum+" expected="+mouthShiftDistance);
                Debug.Log("TANAKACAP_BAKED_LIP_ONLY_OK: sign="+sign+" max="+maximum);
            }
            renderer.SetBlendShapeWeight(leftIndex,savedLeft);renderer.SetBlendShapeWeight(rightIndex,savedRight);Destroy(baseline);Destroy(changed);
        }

        static float WristSwing(Arm arm)
        {
            var neutral=arm.lower.rotation*arm.handRest*Quaternion.Inverse(arm.handFrameCorrection);
            var actual=arm.hand.rotation*Quaternion.Inverse(arm.handFrameCorrection);
            return Vector3.Angle(neutral*Vector3.forward,actual*Vector3.forward);
        }

        static float WristTwist(Arm arm)
        {
            var neutral=arm.lower.rotation*arm.handRest*Quaternion.Inverse(arm.handFrameCorrection);
            var actual=arm.hand.rotation*Quaternion.Inverse(arm.handFrameCorrection);
            var swing=Quaternion.FromToRotation(neutral*Vector3.forward,actual*Vector3.forward)*neutral;
            return Quaternion.Angle(swing,actual);
        }

        void OnGUI()
        {
            if (!showStatus || obsMode) return;
            string state = demo ? "DEMO - not camera tracking" :
                current != null && Time.unscaledTime-lastReceived<.3f ? (current.tracked ? "Tracking" : "Holding last pose (no person)") : (current==null?"Waiting for capture":"Holding last pose (stream stopped)");
            if(current!=null && (current.leftOutOfView || current.rightOutOfView))
                state+=" / Hand outside frame: "+(current.leftOutOfView?"L ":"")+(current.rightOutOfView?"R":"");
            GUI.Box(new Rect(12,12,450,154),"tanakacap development lab");
            GUI.Label(new Rect(24,38,430,22),error ?? state);
            GUI.Label(new Rect(24,62,430,22),"F1: status  F2: demo  F3: OBS  F6: hair/cloth  C: neutral torso  " + (current != null && current.body3d ? "3D body" : "2D body"));
            GUI.Label(new Rect(24,86,430,22),"F4: gaze "+(!gazeEnabled?"OFF":current!=null && current.gazeTracked && Time.unscaledTime-lastReceived<.3f?"tracking":"returning")+" / "+(gazeIrisMode && gazeMesh?"iris":"bones")+" / "+gazeAngles.ToString("F1"));
            GUI.Label(new Rect(24,134,430,22),"F7: edge AA "+(EdgeAntialiasing.Active?"ON":"OFF"));
            bool distanceLive=current!=null && current.tracked && current.faceTracked && current.faceDistanceTracked && Time.unscaledTime-lastReceived<.3f;
            string distanceState=!faceDistanceEnabled?"OFF":!distanceLive?(distanceEstablished?"HOLD (lost)":"waiting for face"):seatedDistance && seatedLeanLimited?"ANGLE LIMIT":"tracking";
            GUI.Label(new Rect(24,110,430,22),"Distance: "+distanceState+" / "+(seatedDistance?(framedDistance?"framed ":"seated ")+seatedLeanDegrees.ToString("F1")+" deg":"translate")+" / ratio "+faceDistanceRatio.ToString("F2"));
        }

        public void SetObsMode(bool enabled)
        {
            obsMode=enabled;
        }
        void OnDestroy() { receiver?.Close();foreach(var mesh in expressionClones)if(mesh)Destroy(mesh); }

        static float[] FingerAngles(Arm arm)
        {
            var result=new float[15];
            if(arm.fingers==null) return result;
            for(int f=0;f<5;f++) for(int j=0;j<3;j++)
                if(arm.fingers[f].bones[j]) result[f*3+j]=Quaternion.Angle(arm.fingers[f].rest[j],arm.fingers[f].bones[j].localRotation);
            return result;
        }

        bool CheckLossHold()
        {
            var bones=GetComponentsInChildren<Transform>(true);
            var rotations=Array.ConvertAll(bones,b=>b.localRotation);
            var saved=current; float received=lastReceived;
            var savedGaze=gazeAngles;
            var savedPosition=transform.position;
            float savedMouth=mouth,savedWidth=mouthWidth,savedRound=mouthRound,savedSmile=mouthSmile,savedLeft=blinkLeft,savedRight=blinkRight;
            var savedDetail=new[]{mouthLeftCorner,mouthRightCorner,mouthBow};
            // Independent part loss, whole-person loss, and stream timeout.
            for(int mode=0;mode<3;mode++)
            {
                current=mode==2?saved:new TrackingPacket {tracked=mode==0,body3d=true};
                lastReceived=mode==2?-100:Time.unscaledTime;
                for(int i=0;i<30;i++) LateUpdate();
                if(transform.position!=savedPosition)throw new Exception("Avatar position changed during loss");
                for(int i=0;i<bones.Length;i++)
                    if(bones[i]!=leftEye && bones[i]!=rightEye && Quaternion.Angle(rotations[i],bones[i].localRotation)>.05f)
                        throw new Exception("Pose changed during loss: "+bones[i].name+" mode="+mode);
                if(mouth!=savedMouth || mouthWidth!=savedWidth || mouthRound!=savedRound || mouthSmile!=savedSmile || blinkLeft!=savedLeft || blinkRight!=savedRight)
                    throw new Exception("Expression changed during loss");
                var detail=new[]{mouthLeftCorner,mouthRightCorner,mouthBow};
                for(int j=0;j<detail.Length;j++)if(detail[j]!=savedDetail[j])throw new Exception("Detailed face changed during loss");
            }
            current=saved; lastReceived=received;
            gazeAngles=savedGaze;DriveGaze(null,false,0);
            return true;
        }

        [Serializable] class MotionPath
        {
            public string side,scenario;
            public float totalRotation,maxStep,maxSwing,maxTwist;
            public float[] forearmAngles;
        }
        [Serializable] class MotionReport { public MotionPath[] paths; public bool frontPoseVerified; }

        void CheckMotionPaths(string path)
        {
            if(!(HeadFollowAmount(1,1f/60,true)<HeadFollowAmount(6,1f/60,true)) ||
               Mathf.Abs(HeadFollowAmount(12,1f/60,true)-HeadFollowAmount(12,1f/60,false))>1e-6f ||
               HeadFollowAmount(1,0,true)!=0)
                throw new Exception("Adaptive head follow gain regression");
            float remaining=1;
            for(int i=0;i<120;i++) remaining*=1-HeadFollowAmount(remaining,1f/60,true);
            if(remaining>.001f)throw new Exception("Adaptive head follow small motion cannot converge");
            Debug.Log("TANAKACAP_ADAPTIVE_HEAD_CHECK_OK");
            browExpressions.CheckMotion();
            CheckGaze();
            CheckFaceDistance();
            CheckSeatedPose();
            CheckFramedPose();
            var reports=new System.Collections.Generic.List<MotionPath>();
            probeDelta=1f/60;
            foreach(bool isLeft in new[]{true,false}) foreach(bool wrap in new[]{false,true})
            {
                var arm=isLeft?left:right;
                current=new TrackingPacket {tracked=true,body3d=true}; lastReceived=Time.unscaledTime;
                var elbow=new Vector3(isLeft?-.5f:.5f,-.8f,.1f);
                var wrist=elbow+new Vector3(0,.7f,.9f);
                if(isLeft) {current.leftArmTracked=true;current.leftElbow=elbow;current.leftWrist=wrist;}
                else {current.rightArmTracked=true;current.rightElbow=elbow;current.rightWrist=wrist;}
                for(int i=0;i<90;i++) LateUpdate();
                var neutral=arm.lowerUntwisted*arm.handRest*Quaternion.Inverse(arm.handFrameCorrection);
                var axis=arm.lowerUntwisted*arm.lowerDirection;
                var steps=new System.Collections.Generic.List<float>();
                var report=new MotionPath {side=isLeft?"left":"right",scenario=wrap?"wrap_170_to_230":"turn_minus80_plus80_return"};
                Quaternion previous=arm.hand.rotation;
                for(int i=-90;i<=160;i++)
                {
                    float degrees=wrap?170+Mathf.Max(0,i)*.375f:-80+(i<0?0:i<=80?i*2:(160-i)*2);
                    var rotation=Quaternion.AngleAxis(degrees,axis)*neutral;
                    var f=transform.InverseTransformDirection(rotation*Vector3.forward);
                    var n=transform.InverseTransformDirection(rotation*Vector3.up);
                    if(isLeft) {current.leftHandTracked=true;current.leftHandForward=f;current.leftHandNormal=n;}
                    else {current.rightHandTracked=true;current.rightHandForward=f;current.rightHandNormal=n;}
                    LateUpdate();
                    if(i>=0)
                    {
                        float step=Quaternion.Angle(previous,arm.hand.rotation);
                        report.totalRotation+=step;report.maxStep=Mathf.Max(report.maxStep,step);
                        report.maxSwing=Mathf.Max(report.maxSwing,WristSwing(arm));
                        report.maxTwist=Mathf.Max(report.maxTwist,WristTwist(arm));
                        steps.Add(arm.twist);
                    }
                    previous=arm.hand.rotation;
                }
                report.forearmAngles=steps.ToArray(); reports.Add(report);
                if(report.maxStep>10 || report.maxSwing>90.1f || report.maxTwist>40.1f ||
                    (wrap?report.totalRotation>75:report.totalRotation>350))
                    throw new Exception("Unexpected hand rotation path: "+JsonUtility.ToJson(report));
            }
            foreach(bool isLeft in new[]{true,false})
            {
                var arm=isLeft?left:right;
                current=new TrackingPacket {tracked=true,body3d=true};lastReceived=Time.unscaledTime;
                var elbow=new Vector3(isLeft?-.5f:.5f,-.5f,-.6f);
                var wrist=elbow+new Vector3(0,.5f,-.8f);
                if(isLeft) {current.leftArmTracked=true;current.leftElbow=elbow;current.leftWrist=wrist;}
                else {current.rightArmTracked=true;current.rightElbow=elbow;current.rightWrist=wrist;}
                for(int i=0;i<60;i++) LateUpdate();
                if(isLeft) {current.leftWristInFront=true;current.leftUpperInFront=true;}
                else {current.rightWristInFront=true;current.rightUpperInFront=true;}
                for(int i=0;i<30;i++)
                {
                    LateUpdate();
                    if(transform.InverseTransformVector(arm.hand.position-arm.upper.position).z<-.001f ||
                        transform.InverseTransformVector(arm.lower.position-arm.upper.position).z<-.001f)
                        throw new Exception("Displayed arm violated front constraint after interpolation");
                }
            }
            foreach(var arm in new[]{left,right})
            {
                for(int i=0;i<30;i++) DriveFingers(arm,new[]{false,true,true,true,true},new float[15]);
                for(int f=1;f<5;f++) for(int j=1;j<3;j++)
                {
                    var finger=arm.fingers[f];
                    Vector3 a=finger.bones[j].position-finger.bones[j-1].position;
                    Vector3 b=finger.bones[j].TransformDirection(finger.directions[j]);
                    if(Vector3.Angle(a,b)>1) throw new Exception("Zero flex did not extend finger "+f+"/"+j+": "+Vector3.Angle(a,b));
                }
            }
            Debug.Log("TANAKACAP_EXTENDED_FINGERS_OK");
            foreach(bool isLeft in new[]{true,false})
            {
                var arm=isLeft?left:right;
                var lowerLocal=arm.lower.localRotation;var handLocal=arm.hand.localRotation;
                var upperLocal=arm.upper.localRotation;
                var fingers=FingerAngles(arm);
                var direction=new Vector3(isLeft?-.3f:.3f,.7f,.5f).normalized;
                current=new TrackingPacket {tracked=true,body3d=true};lastReceived=Time.unscaledTime;
                if(isLeft){current.leftUpperArmTracked=true;current.leftElbow=direction;current.leftOutOfView=true;}
                else {current.rightUpperArmTracked=true;current.rightElbow=direction;current.rightOutOfView=true;}
                for(int i=0;i<60;i++)LateUpdate();
                if(Quaternion.Angle(upperLocal,arm.upper.localRotation)>.01f ||
                   Quaternion.Angle(lowerLocal,arm.lower.localRotation)>.01f || Quaternion.Angle(handLocal,arm.hand.localRotation)>.01f)
                    throw new Exception("Offscreen rollback failed to hold entire arm");
                var after=FingerAngles(arm);
                for(int i=0;i<fingers.Length;i++) if(Mathf.Abs(fingers[i]-after[i])>.01f)
                    throw new Exception("Upper-only tracking changed fingers");
            }
            Debug.Log("TANAKACAP_OFFSCREEN_FULL_ARM_HOLD_OK");
            current=new TrackingPacket {tracked=true,faceTracked=true,body3d=true,mouth=.6f,mouthRound=.8f,mouthSmile=.7f,
                torsoTracked=true,torsoPitch=45,torsoYaw=70};lastReceived=Time.unscaledTime;
            for(int i=0;i<90;i++)LateUpdate();
            expressions.CheckMouthMotion();
            if(Quaternion.Angle(chest.rotation,transform.rotation*Quaternion.Euler(new Vector3(45,70,0)-torsoNeutral)*chestRootRest)>.1f)
                throw new Exception("Relaxed torso range did not reach target");
            CheckLossHold();
            Debug.Log("TANAKACAP_MOUTH_SHAPES_TORSO_RANGE_OK");
            foreach(bool isLeft in new[]{true,false})
            {
                var arm=isLeft?left:right;float sign=isLeft?-1:1;
                var bodyRotation=Quaternion.Inverse(transform.rotation)*chest.rotation*Quaternion.Inverse(chestRootRest);
                var forward=bodyRotation*Vector3.forward;
                var elbow=bodyRotation*new Vector3(sign*.1f,-.22f,-.1f);
                var wrist=elbow+bodyRotation*new Vector3(-sign*.25f,.08f,.08f);
                for(int i=0;i<90;i++)DriveArm(arm,true,elbow,wrist,isLeft,1,false,false,1);
                var actualElbow=transform.InverseTransformVector(arm.lower.position-arm.upper.position);
                var actualWrist=transform.InverseTransformVector(arm.hand.position-arm.upper.position);
                if(Vector3.Dot(actualElbow,forward)<.059f || Vector3.Dot(actualWrist,forward)<.059f)
                    throw new Exception("Actual avatar cross-body forearm remained inside torso plane");
            }
            Debug.Log("TANAKACAP_ACTUAL_CROSS_BODY_CLEARANCE_OK");
            foreach(bool isLeft in new[]{true,false})
            {
                var arm=isLeft?left:right;
                var center=transform.InverseTransformVector(head.TransformPoint(faceCenterLocal)-arm.upper.position);
                var pole=Vector3.down;
                SolveArm(Vector3.down,Vector3.up,arm.upperLength,arm.lowerLength,ref pole,out var a,out var b,false,false,0,Vector3.forward,center);
                for(int i=0;i<90;i++)DriveArm(arm,true,a*arm.upperLength,a*arm.upperLength+b*arm.lowerLength,isLeft,1);
                var actual=transform.InverseTransformVector(arm.hand.position-arm.upper.position);
                if((actual-center).magnitude<.175f || actual.z<center.z)
                    throw new Exception("Actual hand remained in head volume");
            }
            Debug.Log("TANAKACAP_ACTUAL_FACE_CLEARANCE_OK");
            chest.rotation=transform.rotation*chestRootRest;
            foreach(bool isLeft in new[]{true,false})
            {
                var arm=isLeft?left:right;float sign=isLeft?-1:1;
                var a=new Vector3(sign*.12f,-.18f,.1f);var b=new Vector3(sign*.14f,.04f,-.2f);
                for(int i=0;i<90;i++)DriveArm(arm,true,a,a+b,isLeft,1);
                var elbow=transform.InverseTransformVector(arm.lower.position-arm.upper.position);
                var wrist=transform.InverseTransformVector(arm.hand.position-arm.upper.position);
                if(elbow.z>wrist.z-.015f)throw new Exception("Actual outward-back arm still reverse-bends");
            }
            Debug.Log("TANAKACAP_ACTUAL_OUTWARD_BACK_OK");
            current=new TrackingPacket {tracked=true,faceTracked=true,body3d=true,torsoTracked=true,
                headRoll=20,torsoRoll=20,mouthContourTracked=true,mouthLeftCorner=.8f,mouthRightCorner=-.6f,
                mouthBow=.5f,mouthShift=.75f,leftBlink=1};lastReceived=Time.unscaledTime;
            for(int i=0;i<90;i++)LateUpdate();
            var headDelta=head.rotation*Quaternion.Inverse(transform.rotation*headRootRest);
            var chestDelta=chest.rotation*Quaternion.Inverse(transform.rotation*chestRootRest);
            if(Quaternion.Angle(headDelta,chestDelta)>.1f)throw new Exception("Head and torso roll disagree");
            foreach(var renderer in meshes)
            {
                if(renderer.sharedMesh.GetBlendShapeIndex("TC_LeftCornerUp")<0)continue;
                var names=new[]{"TC_LeftCornerUp","TC_RightCornerDown","ω","TC_MouthShiftLeft"};
                var weights=new[]{64f,55.2f,32.5f,75f};
                for(int j=0;j<2;j++)
                    if(cornerGains.TryGetValue((renderer,names[j]),out float gain))
                        weights[j]*=Mathf.Lerp(1/gain,1,Mathf.Clamp01(MouthCornerEmphasis));
                for(int j=0;j<names.Length;j++)
                {
                    int index=renderer.sharedMesh.GetBlendShapeIndex(names[j]);
                    if(index<0 || Mathf.Abs(renderer.GetBlendShapeWeight(index)-weights[j])>.1f)
                        throw new Exception("Contour transfer failed: "+names[j]);
                }
                float savedEmphasis=MouthCornerEmphasis;
                int cornerIndex=renderer.sharedMesh.GetBlendShapeIndex(names[0]);
                var measured=new float[3];
                for(int j=0;j<3;j++)
                {
                    MouthCornerEmphasis=j*.5f;SetCornerShape(renderer,names[0],64);
                    measured[j]=renderer.GetBlendShapeWeight(cornerIndex);
                }
                MouthCornerEmphasis=savedEmphasis;
                SetCornerShape(renderer,names[0],64);
                if(Mathf.Abs(measured[2]-64)>.001f || measured[0]>measured[2] || Mathf.Abs(measured[1]-(measured[0]+measured[2])*.5f)>.001f)
                    throw new Exception("Continuous corner emphasis failed");
                Debug.Log("TANAKACAP_CORNER_EMPHASIS_OK 0/0.5/1="+string.Join(",",measured));
                foreach(var name in new[]{leftBlinkShape,rightBlinkShape,"TC_LeftCornerUp","TC_RightCornerUp","TC_LeftCornerDown","TC_RightCornerDown"})
                {
                    var mesh=renderer.sharedMesh;int index=mesh.GetBlendShapeIndex(name);
                    var delta=new Vector3[mesh.vertexCount];mesh.GetBlendShapeFrameVertices(index,mesh.GetBlendShapeFrameCount(index)-1,delta,null,null);
                    var vertices=mesh.vertices;float weight=0,x=0;
                    for(int j=0;j<delta.Length;j++)
                    {
                        float w=delta[j].magnitude;weight+=w;
                        x+=w*transform.InverseTransformPoint(renderer.transform.TransformPoint(vertices[j])).x;
                    }
                    bool isLeft=name==leftBlinkShape || name.StartsWith("TC_Left");
                    if(weight<1e-5f || (isLeft?x/weight>=0:x/weight<=0))throw new Exception("Wrong anatomical side: "+name);
                    if(name.StartsWith("TC_"))
                    {
                        float verticalSum=0,maxVertical=0;
                        foreach(var d in delta)
                        {
                            float dy=transform.InverseTransformVector(renderer.transform.TransformVector(d)).y;
                            verticalSum+=dy;maxVertical=Mathf.Max(maxVertical,Mathf.Abs(dy));
                        }
                        if((name.EndsWith("Up")?verticalSum<=0:verticalSum>=0)||maxVertical<.0005f)
                            throw new Exception("Corner vertical deformation failed: "+name);
                        Debug.Log("TANAKACAP_CORNER_DEFORMATION_OK "+name+" maxY="+maxVertical);
                    }
                }
            }
            CheckLossHold();
            Debug.Log("TANAKACAP_FACE_SIDE_CONTOUR_OK");
            foreach(bool isLeft in new[]{true,false})foreach(float sign in new[]{-1f,1f})
            {
                var arm=isLeft?left:right;
                current=new TrackingPacket {tracked=true,body3d=true};lastReceived=Time.unscaledTime;
                var elbow=new Vector3(isLeft?-.5f:.5f,-.8f,.1f);
                var wrist=elbow+new Vector3(0,.7f,.9f);
                if(isLeft){current.leftArmTracked=true;current.leftElbow=elbow;current.leftWrist=wrist;}
                else{current.rightArmTracked=true;current.rightElbow=elbow;current.rightWrist=wrist;}
                arm.twist=0;
                for(int i=0;i<90;i++)LateUpdate();
                var neutral=arm.lowerUntwisted*arm.handRest*Quaternion.Inverse(arm.handFrameCorrection);
                var axis=arm.lowerUntwisted*arm.lowerDirection;
                float pathLength=0,maxStep=0,backError=0;
                for(int i=-60;i<=180;i++)
                {
                    float degrees=sign*(i<0?0:i<=90?i*2:(180-i)*2);
                    var target=Quaternion.AngleAxis(degrees,axis)*neutral;
                    var f=transform.InverseTransformDirection(target*Vector3.forward);
                    var n=transform.InverseTransformDirection(target*Vector3.up);
                    if(isLeft){current.leftHandTracked=true;current.leftHandForward=f;current.leftHandNormal=n;}
                    else{current.rightHandTracked=true;current.rightHandForward=f;current.rightHandNormal=n;}
                    var previous=arm.hand.rotation;
                    LateUpdate();
                    if(i>=0){float step=Quaternion.Angle(previous,arm.hand.rotation);pathLength+=step;maxStep=Mathf.Max(maxStep,step);}
                    if(i==90 || i==180)
                    {
                        for(int settle=0;settle<20;settle++)LateUpdate();
                        float error=Quaternion.Angle(arm.hand.rotation*Quaternion.Inverse(arm.handFrameCorrection),target);
                        if(i==90)backError=error;
                        if(error>2)throw new Exception("Palm/back target unreachable: "+isLeft+" sign="+sign+" error="+error);
                    }
                }
                if(maxStep>5 || pathLength>365 || pathLength<345)throw new Exception("Palm/back detour: "+pathLength+" step="+maxStep);
                Debug.Log("TANAKACAP_PALM_BACK_REACH_OK side="+(isLeft?"left":"right")+" sign="+sign+" backError="+backError+" path="+pathLength+" maxStep="+maxStep);
            }
            foreach(bool rightForward in new[]{true,false})
            {
                current=new TrackingPacket {tracked=true,body3d=true,torsoTracked=true,torsoYaw=rightForward?-45:45};
                lastReceived=Time.unscaledTime;
                for(int i=0;i<120;i++)LateUpdate();
                float rightDepth=transform.InverseTransformPoint(right.upper.position).z;
                float leftDepth=transform.InverseTransformPoint(left.upper.position).z;
                if(rightForward?rightDepth<=leftDepth:leftDepth<=rightDepth)throw new Exception("Shoulder yaw rendered wrong side forward");
            }
            Debug.Log("TANAKACAP_SHOULDER_FORWARD_SIDE_OK");
            probeDelta=0;
            File.WriteAllText(path+".motion.json",JsonUtility.ToJson(new MotionReport {paths=reports.ToArray(),frontPoseVerified=true},true));
            Debug.Log("TANAKACAP_MOTION_PATH_OK");
        }

        [Serializable] class ReplayRow { public TrackingPacket packet; public float dt; }
        [Serializable] class AuditRow
        {
            public int frame;
            public float requestedYaw,actualYaw,shoulderYaw;
            public float leftPalmError,rightPalmError,leftRoll,rightRoll;
            public float leftRequestedRoll,rightRequestedRoll;
            public bool torsoTracked,leftHandTracked,rightHandTracked;
        }
        void AuditRecording(string source,string output)
        {
            int frame=0;
            using(var writer=new StreamWriter(output))
            foreach(var line in File.ReadLines(source))
            {
                var row=JsonUtility.FromJson<ReplayRow>(line);
                current=row.packet;lastReceived=Time.unscaledTime;
                // Replay each capture interval as render substeps, preserving
                // time-based interpolation without depending on audit wall time.
                int steps=Mathf.Max(1,Mathf.CeilToInt(row.dt*60));
                probeDelta=Mathf.Clamp(row.dt,.001f,.3f)/steps;
                for(int i=0;i<steps;i++) LateUpdate();
                var chestDelta=Quaternion.Inverse(transform.rotation)*chest.rotation*Quaternion.Inverse(chestRootRest);
                var shoulderLine=transform.InverseTransformVector(right.upper.position-left.upper.position);
                writer.WriteLine(JsonUtility.ToJson(new AuditRow {
                    frame=frame++,requestedYaw=current.torsoYaw,actualYaw=Mathf.DeltaAngle(0,chestDelta.eulerAngles.y),
                    shoulderYaw=Mathf.Atan2(-shoulderLine.z,shoulderLine.x)*Mathf.Rad2Deg,
                    torsoTracked=current.torsoTracked,leftHandTracked=current.leftHandTracked,rightHandTracked=current.rightHandTracked,
                    leftPalmError=PalmError(left,current.leftHandForward,current.leftHandNormal),
                    rightPalmError=PalmError(right,current.rightHandForward,current.rightHandNormal),
                    leftRoll=left.twist,rightRoll=right.twist,
                    leftRequestedRoll=left.requestedTwist,rightRequestedRoll=right.requestedTwist}));
            }
            probeDelta=0;
        }
        float PalmError(Arm arm,Vector3 forward,Vector3 normal)
        {
            if(Vector3.Cross(forward,normal).sqrMagnitude<.001f)return 0;
            var target=transform.rotation*Quaternion.LookRotation(forward,normal)*arm.handFrameCorrection;
            return Quaternion.Angle(target,arm.hand.rotation);
        }

        bool CheckMouthWidth()
        {
            foreach(var renderer in meshes)
            {
                int index=renderer.sharedMesh.GetBlendShapeIndex("口横広げ");
                if(index<0)continue;
                float saved=renderer.GetBlendShapeWeight(index);
                var mesh=new Mesh();
                renderer.SetBlendShapeWeight(index,0);renderer.BakeMesh(mesh);var neutral=mesh.vertices;
                renderer.SetBlendShapeWeight(index,100);renderer.BakeMesh(mesh);var wide=mesh.vertices;
                renderer.SetBlendShapeWeight(index,-50);renderer.BakeMesh(mesh);var narrow=mesh.vertices;
                renderer.SetBlendShapeWeight(index,saved);Destroy(mesh);
                int largest=0;
                for(int i=1;i<wide.Length;i++) if((wide[i]-neutral[i]).sqrMagnitude>(wide[largest]-neutral[largest]).sqrMagnitude)largest=i;
                var a=wide[largest]-neutral[largest];var b=narrow[largest]-neutral[largest];
                if(a.sqrMagnitude<1e-10f || Vector3.Dot(a,b)>=0 || b.magnitude<a.magnitude*.4f)
                    throw new Exception("Mouth width did not deform in both directions");
                return true;
            }
            throw new Exception("Mouth width shape missing in haolan test avatar");
        }

        IEnumerator Snapshot(string path)
        {
            float deadline=Time.realtimeSinceStartup+10;
            while(!demo && current==null && Time.realtimeSinceStartup<deadline) yield return null;
            for (int i = 0; i < 90; i++) yield return null;
            // Camera render also works when the automated player is batchmode.
            var camera = Camera.main;
            var target = new RenderTexture(1280,720,24);
            var previous = RenderTexture.active;
            camera.targetTexture = target;
            camera.Render();
            RenderTexture.active = target;
            var image = new Texture2D(1280,720,TextureFormat.RGB24,false);
            image.ReadPixels(new Rect(0,0,1280,720),0,0);
            image.Apply();
            File.WriteAllBytes(path,image.EncodeToPNG());
            if(demo){
                // A procedural demo intentionally moves without observations; loss-hold assertions do not apply.
                camera.targetTexture=null;RenderTexture.active=previous;Destroy(image);target.Release();Destroy(target);
                camera.GetComponent<AlphaOutput>().CheckOutput(path,obsMode && !Application.isBatchMode);
                Debug.Log("TANAKACAP_DEMO_SNAPSHOT_OK "+path);Application.Quit();yield break;
            }
            File.WriteAllText(path+".tracking.json",JsonUtility.ToJson(current ?? new TrackingPacket(),true));
            var leftFrame = left.hand.rotation*Quaternion.Inverse(left.handFrameCorrection);
            var rightFrame = right.hand.rotation*Quaternion.Inverse(right.handFrameCorrection);
            File.WriteAllText(path+".bones.json",JsonUtility.ToJson(new BoneDiagnostics {
                gazeYawApplied=gazeAngles.x,gazePitchApplied=gazeAngles.y,
                headPitchApplied=Mathf.DeltaAngle(0,(Quaternion.Inverse(transform.rotation)*head.rotation*Quaternion.Inverse(headRootRest)).eulerAngles.x),
                faceDistanceRatioApplied=faceDistanceRatio,avatarDisplacement=transform.position-rootRestPosition,
                seatedLeanDegrees=seatedLeanDegrees,seatedLeanLimited=seatedLeanLimited,
                leftHandForward=transform.InverseTransformDirection(leftFrame*Vector3.forward),
                leftHandNormal=transform.InverseTransformDirection(leftFrame*Vector3.up),
                rightHandForward=transform.InverseTransformDirection(rightFrame*Vector3.forward),
                rightHandNormal=transform.InverseTransformDirection(rightFrame*Vector3.up),
                torsoRotationError=current!=null && current.torsoTracked?Quaternion.Angle(chest.rotation,
                    transform.rotation*Quaternion.Euler(new Vector3(current.torsoPitch,current.torsoYaw,current.torsoRoll)-torsoNeutral)*chestRootRest):0,
                chestRestLocalUpInRoot=chestRootRest*Vector3.up,
                leftFingerAngles=FingerAngles(left),rightFingerAngles=FingerAngles(right),lossHoldVerified=CheckLossHold(),
                mouthWidthVerified=CheckMouthWidth(),mouthWidthWeight=mouthWidth*(mouthWidth<0?50:100),
                leftWristSwing=WristSwing(left),rightWristSwing=WristSwing(right),
                leftWristTwist=WristTwist(left),rightWristTwist=WristTwist(right),
                leftForearmTwist=left.twist,rightForearmTwist=right.twist,
                leftElbowRelative=transform.InverseTransformVector(left.lower.position-left.upper.position),
                rightElbowRelative=transform.InverseTransformVector(right.lower.position-right.upper.position),
                leftWristRelative=transform.InverseTransformVector(left.hand.position-left.upper.position),
                rightWristRelative=transform.InverseTransformVector(right.hand.position-right.upper.position)},true));
            camera.targetTexture = null;
            RenderTexture.active = previous;
            Destroy(image); target.Release(); Destroy(target);
            camera.GetComponent<AlphaOutput>().CheckOutput(path,obsMode && !Application.isBatchMode);
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--motion-check")>=0) CheckMotionPaths(path);
            var auditArgs=Environment.GetCommandLineArgs();
            int auditIndex=Array.IndexOf(auditArgs,"--replay-file");
            if(auditIndex>=0 && auditIndex+1<auditArgs.Length) AuditRecording(auditArgs[auditIndex+1],path+".audit.jsonl");
            Debug.Log("TANAKACAP_SNAPSHOT_OK " + path);
            Application.Quit();
        }
    }
}
