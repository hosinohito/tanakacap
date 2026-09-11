"""Raw 3D inference worker for an isolated, upstream-compatible CUDA environment.

No automatic asset downloads, retargeting, confidence fabrication or global installs.
SAM/HaMeR need licensed assets and a validated independent environment first.
"""
import argparse,json,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.comparison import load_take,images,line,dump
from capture_lab.models import sha256


def hand_boxes(xy,scores):
    boxes=[];sides=[]
    for side,offset in [('left',91),('right',112)]:
        hand=np.asarray(xy,float)[offset:offset+21];score=np.asarray(scores,float)[offset:offset+21]
        valid=np.isfinite(hand).all(axis=1)&(score>.5)
        if valid.sum()<4:continue
        lo=hand[valid].min(axis=0);hi=hand[valid].max(axis=0)
        if (hi-lo).min()<5:continue
        boxes.append([*lo,*hi]);sides.append(side)
    return np.asarray(boxes,dtype=np.float32).reshape(-1,4),sides


def run(args):
    for path in (args.repo,args.checkpoint,args.take,args.common):
        if not path.exists():raise FileNotFoundError(path)
    if args.model=='sam3d' and (args.mhr is None or not args.mhr.is_file()):raise ValueError('SAM requires --mhr assets/mhr_model.pt')
    sys.path.insert(0,str(args.repo.resolve()))
    import torch
    if not torch.cuda.is_available():raise RuntimeError('CUDA required; no CPU fallback')
    meta,timeline=load_take(args.take)
    cache=args.common/'common.jsonl';parent=json.loads((args.common/'report.json').read_text(encoding='utf-8'))
    if parent['status']!='complete' or parent['source_video_sha256']!=meta['video_sha256'] or parent['source_timeline_sha256']!=meta['timeline_sha256']:raise ValueError('Common input provenance mismatch')
    args.output.mkdir(parents=True,exist_ok=False)
    report={'status':'running','model':args.model,'checkpoint_sha256':sha256(args.checkpoint),'video_sha256':meta['video_sha256'],'controls_sha256':parent['controls']['sha256'],'upstream_python_sha256':{str(p.relative_to(args.repo)):sha256(p) for p in sorted(args.repo.rglob('*.py'))},'torch':torch.__version__,'gpu':torch.cuda.get_device_name(0),'scope':'Raw 3D candidate only. No common-retarget quality claim until units, joints and confidence policy are verified on actual assets.'}
    dump(args.output/'report.json',report)
    try:
        if args.model=='sam3d':
            from sam_3d_body import load_sam_3d_body,SAM3DBodyEstimator
            model,cfg=load_sam_3d_body(str(args.checkpoint),device='cuda',mhr_path=str(args.mhr))
            estimator=SAM3DBodyEstimator(model,cfg)
            report['mhr_sha256']=sha256(args.mhr)
        else:
            from hamer.models import load_hamer
            from hamer.datasets.vitdet_dataset import ViTDetDataset
            from hamer.utils import recursive_to
            model,cfg=load_hamer(str(args.checkpoint));model=model.to('cuda').eval()
        torch.cuda.reset_peak_memory_stats();durations=[]
        with cache.open(encoding='utf-8') as source,(args.output/'raw.jsonl').open('w',encoding='utf-8') as out:
            for clock,image in images(args.take,timeline,args.limit):
                common=json.loads(next(source))
                if (clock['frame'],clock['time'])!=(common['frame'],common['time']):raise ValueError('Frame alignment mismatch')
                result={**clock,'predictions':[]};roi=common['roi']
                if roi is not None:
                    torch.cuda.synchronize();start=time.perf_counter()
                    with torch.inference_mode():
                        if args.model=='sam3d':
                            x,y,w,h=roi
                            predictions=estimator.process_one_image(image[:,:,::-1].copy(),bboxes=np.array([[x,y,x+w,y+h]],dtype=np.float32))
                            for p in predictions:
                                result['predictions'].append({k:p[k] for k in ('pred_keypoints_2d','pred_keypoints_3d','pred_cam_t','focal_length')})
                        else:
                            boxes,sides=hand_boxes(common['points_xy'],common['scores'])
                            if len(boxes):
                                right=np.array([side=='right' for side in sides],dtype=np.float32)
                                dataset=ViTDetDataset(cfg,image,boxes,right,rescale_factor=2.)
                                loader=torch.utils.data.DataLoader(dataset,batch_size=2,shuffle=False,num_workers=0)
                                for batch in loader:
                                    batch=recursive_to(batch,'cuda');pred=model(batch)
                                    for i,person in enumerate(batch['personid'].detach().cpu().numpy()):
                                        side=sides[int(person)];xyz=pred['pred_keypoints_3d'][i].detach().cpu().numpy().copy()
                                        if side=='left':xyz[:,0]*=-1
                                        result['predictions'].append({'side':side,'hand_xyz_camera_axes':xyz,'box':boxes[int(person)],'right_model_reflection_applied':side=='left'})
                    torch.cuda.synchronize();durations.append((time.perf_counter()-start)*1000)
                    result['inference_ms']=durations[-1]
                line(out,result)
                if clock['frame']%100==0:print(args.model,clock['frame'],flush=True)
        report.update(status='complete',frames=min(len(timeline),args.limit or len(timeline)),cuda_device=str(next(model.parameters()).device),inference_ms_p50_p95=np.percentile(durations,[50,95]).tolist() if durations else [],peak_allocated_bytes=torch.cuda.max_memory_allocated())
        dump(args.output/'report.json',report)
    except BaseException as exc:
        report.update(status='failed',error=str(exc));dump(args.output/'report.json',report);raise


def main():
    p=argparse.ArgumentParser();p.add_argument('model',choices=['sam3d','hamer'])
    for name in ('repo','checkpoint','take','common','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--mhr',type=Path);p.add_argument('--limit',type=int)
    run(p.parse_args())
if __name__=='__main__':main()
