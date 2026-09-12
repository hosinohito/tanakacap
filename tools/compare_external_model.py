"""Raw 3D inference worker for an isolated, upstream-compatible CUDA environment.

No automatic asset downloads, retargeting, confidence fabrication or global installs.
SAM/HaMeR need licensed assets and a validated independent environment first.
"""
import argparse,json,sys,time,os
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
    if args.stride<1 or args.start_frame<0:raise ValueError('Invalid sampling interval')
    if sys.platform=='win32':os.environ.setdefault('PYOPENGL_PLATFORM','win32')
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
            if args.dinov3_repo is None or not (args.dinov3_repo/'hubconf.py').is_file():raise ValueError('SAM requires --dinov3-repo with official local source')
            report['dinov3_python_sha256']={str(p.relative_to(args.dinov3_repo)):sha256(p) for p in sorted(args.dinov3_repo.rglob('*.py'))}
            report['config_sha256']=sha256(args.checkpoint.parent/'model_config.yaml')
            import sam_3d_body.build_models as sam_builder
            state_loader=sam_builder.load_state_dict
            def audited_state_loader(module,state_dict,*a,**kw):
                expected=set(module.state_dict());actual=set(state_dict)
                missing=sorted(expected-actual);unexpected=sorted(actual-expected)
                report['checkpoint_missing_keys']=missing;report['checkpoint_unexpected_keys']=unexpected
                allowed={'backbone.encoder.mask_token','head_pose.hand_pose_comps_ori','head_pose_hand.hand_pose_comps_ori'}
                unsupported=[k for k in missing if not k.startswith(('head_pose.mhr.','head_pose_hand.mhr.')) and k not in allowed]
                if unsupported or unexpected:raise RuntimeError('Unexplained SAM checkpoint mismatch: '+str(unsupported+unexpected))
                return state_loader(module,state_dict,*a,**kw)
            hub_load=torch.hub.load
            def local_backbone(repo,name,*a,**kw):
                if repo!='facebookresearch/dinov3' or kw.get('pretrained') is not False:raise ValueError('Unexpected backbone download request')
                kw['source']='local'
                return hub_load(str(args.dinov3_repo.resolve()),name,*a,**kw)
            try:
                torch.hub.load=local_backbone
                sam_builder.load_state_dict=audited_state_loader
                model,cfg=load_sam_3d_body(str(args.checkpoint),device='cuda',mhr_path=str(args.mhr))
            finally:
                torch.hub.load=hub_load
                sam_builder.load_state_dict=state_loader
            report['cuda_backbone_calls']=0
            def check_cuda(module,inputs,output):
                if not torch.is_tensor(output) or output.device.type!='cuda':raise RuntimeError('SAM backbone output must be CUDA')
                report['cuda_backbone_calls']+=1
            model.backbone.register_forward_hook(check_cuda)
            estimator=SAM3DBodyEstimator(model,cfg)
            report['mhr_sha256']=sha256(args.mhr)
        else:
            from hamer.models import HAMER
            from hamer.configs import get_config
            from hamer.datasets.vitdet_dataset import ViTDetDataset
            from hamer.utils import recursive_to
            config_path=args.checkpoint.parent.parent/'model_config.yaml'
            cfg=get_config(str(config_path),update_cachedir=False);cfg.defrost()
            if cfg.MODEL.BACKBONE.TYPE=='vit' and 'BBOX_SHAPE' not in cfg.MODEL:cfg.MODEL.BBOX_SHAPE=[192,256]
            cfg.MODEL.BACKBONE.pop('PRETRAINED_WEIGHTS',None)
            if args.mano_dir is None or args.mean_params is None:raise ValueError('HaMeR requires --mano-dir and --mean-params')
            cfg.MANO.MODEL_PATH=str(args.mano_dir.resolve());cfg.MANO.MEAN_PARAMS=str(args.mean_params.resolve());cfg.freeze()
            report.update(config_sha256=sha256(config_path),mano_sha256=sha256(args.mano_dir/'MANO_RIGHT.pkl'),mean_params_sha256=sha256(args.mean_params))
            # The official checkpoint includes Lightning metadata; this is an explicit
            # trusted local checkpoint load, not a global torch.load override.
            model=HAMER.load_from_checkpoint(str(args.checkpoint),strict=False,cfg=cfg,init_renderer=False,weights_only=False,map_location='cpu').to('cuda').eval()
        torch.cuda.reset_peak_memory_stats();durations=[];processed=0;predicted_hands=0;prediction_count=0
        with cache.open(encoding='utf-8') as source,(args.output/'raw.jsonl').open('w',encoding='utf-8') as out:
            for clock,image in images(args.take,timeline,args.limit):
                common=json.loads(next(source))
                if (clock['frame'],clock['time'])!=(common['frame'],common['time']):raise ValueError('Frame alignment mismatch')
                if clock['frame']<args.start_frame or (clock['frame']-args.start_frame)%args.stride:continue
                processed+=1
                result={**clock,'predictions':[]};roi=common['roi']
                if roi is not None:
                    torch.cuda.synchronize();start=time.perf_counter()
                    with torch.inference_mode():
                        if args.model=='sam3d':
                            x,y,w,h=roi
                            predictions=estimator.process_one_image(image[:,:,::-1].copy(),bboxes=np.array([[x,y,x+w,y+h]],dtype=np.float32))
                            for p in predictions:
                                if not np.isfinite(p['pred_keypoints_3d']).all():raise RuntimeError('Nonfinite SAM joints')
                                result['predictions'].append({k:p[k] for k in ('pred_keypoints_2d','pred_keypoints_3d','pred_cam_t','focal_length')})
                        else:
                            boxes,sides=hand_boxes(common['points_xy'],common['scores'])
                            if len(boxes):
                                right=np.array([side=='right' for side in sides],dtype=np.float32)
                                dataset=ViTDetDataset(cfg,image,boxes,right,rescale_factor=2.)
                                loader=torch.utils.data.DataLoader(dataset,batch_size=2,shuffle=False,num_workers=0)
                                for batch in loader:
                                    batch=recursive_to(batch,'cuda');pred=model(batch)
                                    if pred['pred_keypoints_3d'].device.type!='cuda':raise RuntimeError('HaMeR output must remain CUDA')
                                    if not torch.isfinite(pred['pred_keypoints_3d']).all():raise RuntimeError('Nonfinite HaMeR joints')
                                    for i,person in enumerate(batch['personid'].detach().cpu().numpy()):
                                        side=sides[int(person)];xyz=pred['pred_keypoints_3d'][i].detach().cpu().numpy().copy()
                                        if xyz.shape!=(21,3):raise ValueError('Unexpected HaMeR joint layout')
                                        uv=pred['pred_keypoints_2d'][i].detach().cpu().numpy().copy()
                                        if side=='left':xyz[:,0]*=-1;uv[:,0]*=-1
                                        uv=uv*float(batch['box_size'][i])+batch['box_center'][i].detach().cpu().numpy()
                                        predicted_hands+=1
                                        result['predictions'].append({'side':side,'hand_xyz_camera_axes':xyz,'projected_xy':uv,'box':boxes[int(person)],'right_model_reflection_applied':side=='left'})
                    torch.cuda.synchronize();durations.append((time.perf_counter()-start)*1000)
                    result['inference_ms']=durations[-1]
                prediction_count+=len(result['predictions'])
                line(out,result)
                if clock['frame']%100==0:print(args.model,clock['frame'],flush=True)
        if processed==0 or prediction_count==0:raise RuntimeError('No candidate predictions; not a successful inference test')
        report.update(status='complete',prediction_count=prediction_count,predicted_hands=predicted_hands,frames=processed,start_frame=args.start_frame,stride=args.stride,cuda_device=str(next(model.parameters()).device),inference_ms_p50_p95=np.percentile(durations,[50,95]).tolist() if durations else [],peak_allocated_bytes=torch.cuda.max_memory_allocated())
        dump(args.output/'report.json',report)
    except BaseException as exc:
        report.update(status='failed',error=str(exc));dump(args.output/'report.json',report);raise


def main():
    p=argparse.ArgumentParser();p.add_argument('model',choices=['sam3d','hamer'])
    for name in ('repo','checkpoint','take','common','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--mhr',type=Path);p.add_argument('--dinov3-repo',type=Path);p.add_argument('--limit',type=int)
    p.add_argument('--mano-dir',type=Path);p.add_argument('--mean-params',type=Path)
    p.add_argument('--start-frame',type=int,default=0);p.add_argument('--stride',type=int,default=1)
    run(p.parse_args())
if __name__=='__main__':main()
