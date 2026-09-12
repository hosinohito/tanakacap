"""Profile CPU work, CUDA calls and kernels after comparison videos finish.

Diagnostics only: no changes to the full comparison or live controller.
Profiler timings include instrumentation overhead and are not live FPS.
"""
import argparse,gc,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'assets-source/sam-3d-body-code'))


def run_profile(variant,output):
    os.environ.setdefault('PYOPENGL_PLATFORM','win32')
    import torch
    from sam_3d_body import SAM3DBodyEstimator
    from sam_3d_body.models.heads.mhr_head import MHRHead
    import sam_3d_body.sam_3d_body_estimator as estimator_module
    from compare_external_model import run
    from capture_lab.comparison import dump
    from capture_lab.models import sha256
    original=SAM3DBodyEstimator.process_one_image;original_init=SAM3DBodyEstimator.__init__;original_mhr=MHRHead.mhr_forward;original_batch=estimator_module.prepare_batch
    steps=[];calls=0
    def init(estimator,*a,**kw):
        original_init(estimator,*a,**kw)
        backbone=estimator.model.backbone;forward=backbone.forward
        def marked(*x,**k):
            with torch.profiler.record_function('SAM_BACKBONE'):return forward(*x,**k)
        backbone.forward=marked
    def mhr(head,*a,**kw):
        with torch.profiler.record_function('SAM_MHR'):return original_mhr(head,*a,**kw)
    def batch(*a,**kw):
        with torch.profiler.record_function('SAM_PREPARE_BATCH'):return original_batch(*a,**kw)
    def process(estimator,*a,**kw):
        nonlocal calls
        index=calls;calls+=1
        if index not in (3,5):return original(estimator,*a,**kw)
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=False,with_stack=False,profile_memory=False) as prof:
            with torch.profiler.record_function('SAM_FULL_FRAME'):
                result=original(estimator,*a,**kw)
                torch.cuda.synchronize()
        trace=output/f'trace-{index}.json';prof.export_chrome_trace(str(trace))
        events=[]
        for event in prof.key_averages():
            events.append({'name':event.key,'count':event.count,'self_cpu_ms':event.self_cpu_time_total/1000,'total_cpu_ms':event.cpu_time_total/1000,'self_device_ms':getattr(event,'self_device_time_total',0)/1000,'total_device_ms':getattr(event,'device_time_total',0)/1000})
        data=json.loads(trace.read_text(encoding='utf-8'))['traceEvents']
        kernels=[e for e in data if e.get('cat')=='kernel' and e.get('ph')=='X']
        runtime=[e for e in data if e.get('cat') in ('cuda_runtime','cuda_driver') and e.get('ph')=='X']
        sync=[e for e in runtime if 'Synchronize' in e.get('name','')]
        # CUDA user annotations share CPU range names but include launch gaps.
        # Keep the CPU ranges explicitly rather than overwriting them by name.
        ranges={e['name']:e for e in events if e['name'].startswith('SAM_') and e['total_cpu_ms']>0}
        step={'call':index,'frame':2100+index,'ranges':ranges,'cuda_kernel_events':len(kernels),'cuda_kernel_sum_ms':sum(e['dur'] for e in kernels)/1000,'cuda_runtime_calls':len(runtime),'cuda_runtime_sum_ms':sum(e['dur'] for e in runtime)/1000,'cuda_sync_calls':len(sync),'cuda_sync_sum_ms':sum(e['dur'] for e in sync)/1000,'top_self_cpu':sorted(events,key=lambda e:e['self_cpu_ms'],reverse=True)[:20],'top_self_device':sorted(events,key=lambda e:e['self_device_ms'],reverse=True)[:20]}
        steps.append(step)
        print(variant,'profile frame',2100+index,'CUDA kernels',len(kernels),'kernel ms',step['cuda_kernel_sum_ms'],'sync ms',step['cuda_sync_sum_ms'],flush=True)
        return result
    args=SimpleNamespace(model='sam3d',repo=ROOT/'assets-source/sam-3d-body-code',checkpoint=ROOT/f'assets-source/sam-3d-body-{variant}/model.ckpt',mhr=ROOT/'assets-source/sam-3d-body-dinov3/assets/mhr_model.pt',dinov3_repo=ROOT/'assets-source/dinov3',take=ROOT/'results/comparison-takes/20260911T235327-031115Z',common=ROOT/'results/comparisons/first-take',output=output,torch_threads=1,keep_cuda_cache=True,start_frame=2100,limit=2112,stride=1)
    with patch.object(SAM3DBodyEstimator,'__init__',init),patch.object(SAM3DBodyEstimator,'process_one_image',process),patch.object(MHRHead,'mhr_forward',mhr),patch.object(estimator_module,'prepare_batch',batch):run(args)
    raw=[json.loads(line) for line in (output/'raw.jsonl').read_text().splitlines()]
    plain=[r['inference_ms'] for i,r in enumerate(raw) if i>=3 and i not in (3,5)]
    dump(output/'profile-summary.json',{'status':'complete','variant':variant,'worker_sha256':sha256(ROOT/'tools/compare_external_model.py'),'profiler_sha256':sha256(Path(__file__)),'scope':'Isolated candidate after videos. Two instrumented frames after three warmup observations. CUDA kernel sums exclude launch gaps; overlapping work can double count. Synchronization time includes waiting for GPU, not CPU arithmetic. Profiler adds overhead; do not interpret these totals as production FPS.','unprofiled_post_warmup_inference_ms':plain,'steps':steps})
    gc.collect();torch.cuda.empty_cache()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--variant',choices=['dinov3','vith','all'],default='all');p.add_argument('--wait-for-videos',action='store_true');a=p.parse_args()
    if a.wait_for_videos:
        deadline=time.monotonic()+10800
        while True:
            try:r=json.loads((ROOT/'results/avatar-videos/body-three-models/report.json').read_text());ready=r.get('status')=='complete'
            except (OSError,json.JSONDecodeError):ready=False
            if ready:break
            if time.monotonic()>deadline:raise TimeoutError('Videos not complete; isolated profile not started')
            time.sleep(5)
    for variant in (['dinov3','vith'] if a.variant=='all' else [a.variant]):run_profile(variant,a.output/variant)

if __name__=='__main__':main()
