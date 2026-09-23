"""Paired original/mirrored recording inference; restore hand identities before controls."""
import argparse, copy, json, sys
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tanakacap.comparison import load_take,images,line,dump,frame_mask
from tanakacap.inference import SimCCModel
from tanakacap.hand_orientation import palm_basis,PalmFilter,add_hands
from tanakacap.fingers import FingerTracker
from tanakacap.models import sha256

# COCO-WholeBody: left 91..111 <-> right 112..132, same joint order.
HAND_SWAP=np.r_[np.arange(112,133),np.arange(91,112)]
def restore_hands(xy,scores,z,zscores,width):
    x=xy.copy();s=scores.copy();d=z.copy();ds=zscores.copy()
    x[91:133]=xy[HAND_SWAP];x[91:133,0]=width-1-x[91:133,0]
    s[91:133]=scores[HAND_SWAP];d[91:133]=z[HAND_SWAP];ds[91:133]=zscores[HAND_SWAP]
    return x,s,d,ds

def reflect_roi(roi,width):
    x,y,w,h=roi
    return [width-1-x-w,y,w,h]

def check_restore():
    roi=[123.25,50.5,400.5,550.25]
    np.testing.assert_allclose(reflect_roi(reflect_roi(roi,1280),1280),roi)
    reflected=reflect_roi(roi,1280)
    assert reflected[0]+reflected[2]/2==1279-(roi[0]+roi[2]/2)
    xy=np.arange(266,dtype=float).reshape(133,2);s=np.arange(133,dtype=float)
    result=restore_hands(*restore_hands(xy,s,s,s,1280),1280)
    for actual,expected in zip(result,(xy,s,s,s)):
        np.testing.assert_array_equal(actual[91:133],expected[91:133])
    out=restore_hands(xy,s,s,s,1280)
    assert out[0][91,0]==1279-xy[112,0] and out[2][91]==112


def run(args):
    check_restore();meta,timeline=load_take(args.take)
    baseline=[json.loads(x) for x in args.records.read_text().splitlines()]
    assert len(baseline)==len(timeline)
    assert all(a["frame"]==b["frame"] and a["time"]==b["time"] for a,b in zip(baseline,timeline))
    settings=json.loads((ROOT/"tracking-settings.json").read_text())
    args.output.mkdir(parents=True,exist_ok=False)
    names=("original","mirrored","mirror-z-only","mirror-xy-only")
    block=settings["observation_block"];stride=settings["observation_stride"]
    palms={n:PalmFilter(block,stride) for n in names};fingers={n:FingerTracker(block,stride) for n in names}
    streams={}; replays={}
    for n in names:
        folder=args.output/n;folder.mkdir();streams[n]=(folder/"frames.jsonl").open("w")
        replays[n]=(folder/"replay.jsonl").open("w")
    model=SimCCModel("rtmw3d-x-384",None,"graph-fp16",preprocess_mode=settings["preprocess_mode"])
    report=dict(status="running",source=str(args.take),video_sha256=meta["video_sha256"],
        records_sha256=sha256(args.records),model=model.identity,settings=settings,
        scope="Same frames, recorded ROI and face-derived scale. Mirrored image and reflected ROI; hands unmirrored and swapped, Z not negated. Face/arms fixed. Z/XY hybrid conditions are diagnostic only. No raw images saved or displayed; no accuracy ground truth.")
    dump(args.output/"report.json",report)
    try:
        previous=None
        for clock,image in images(args.take,timeline,args.limit):
            i=clock["frame"];row=baseline[i];roi=row["roi"];w=image.shape[1]
            base=row["sent_packet"];scale=row.get("body_diagnostics",{}).get("geometry",{}).get("model_scale")
            observations={}
            if roi is not None and scale is not None:
                xy,s,_=model.predict(image,roi);original=(xy.copy(),s.copy(),model.depth.copy(),model.depth_scores.copy())
                reflected=reflect_roi(roi,w)
                mx,ms,_=model.predict(cv2.flip(image,1),reflected)
                mirrored=restore_hands(mx,ms,model.depth,model.depth_scores,w)
                observations=dict(original=original,mirrored=mirrored)
                for name,use_z in [("mirror-z-only",True),("mirror-xy-only",False)]:
                    hx,hs,hz,hd=[a.copy() for a in original]
                    if use_z:hz[91:]=mirrored[2][91:];hd[91:]=mirrored[3][91:]
                    else:hx[91:]=mirrored[0][91:] # Keep original scores to isolate geometry.
                    observations[name]=(hx,hs,hz,hd)
            for name in names:
                packet=copy.deepcopy(base);detail={}
                if name in observations:
                    xy,s,z,ds=observations[name];scores=frame_mask(xy,s,image.shape[1::-1])
                    xyz=np.column_stack((-xy[:,0]*scale,-xy[:,1]*scale,-z))
                    detail=dict(xy=xy[91:],z=z[91:],scores=scores[91:],depth_scores=ds[91:],scale=scale,normal={})
                    for side,k in [("left",91),("right",112)]:
                        b=palm_basis(xyz,scores,ds,k);detail["normal"][side]=None if b is None else b[1]
                    add_hands(packet,xyz,scores,ds);palms[name].update(packet,clock["time"])
                    fingers[name].update(packet,xyz,scores,ds,clock["time"])
                    detail["reasons"]=fingers[name].diagnostics
                else:
                    for side in ("left","right"):
                        packet[side+"HandTracked"]=False;packet[side+"FingerTracked"]=[False]*5
                line(streams[name],dict(frame=i,time=clock["time"],**detail,packet=packet))
                line(replays[name],dict(packet=packet,dt=1/30 if previous is None else clock["time"]-previous))
            previous=clock["time"]
            if (i+1)%150==0:print("paired frames",i+1,flush=True)
        report.update(status="complete",frames=i+1,execution=model.finish())
    except BaseException as e:
        report.update(status="failed",error=repr(e));raise
    finally:
        for stream in [*streams.values(),*replays.values()]:stream.close()
        dump(args.output/"report.json",report)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--take",type=Path,required=True);p.add_argument("--records",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--limit",type=int)
    run(p.parse_args())
