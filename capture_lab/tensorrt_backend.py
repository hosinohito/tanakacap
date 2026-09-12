"""Optional standard TensorRT EP; original ONNX and CUDA path stay intact."""
import functools
import hashlib
import json
import subprocess
from pathlib import Path

import onnxruntime as ort

MODES = ('trt-fp32', 'trt-fp16')


@functools.lru_cache(maxsize=1)
def environment():
    # The NVIDIA Python package loads its DLLs before ORT opens its provider.
    try:
        import tensorrt as trt
    except ImportError as error:
        raise RuntimeError('TensorRT is optional. Install requirements-tensorrt.txt or select graph.') from error
    if trt.__version__ != '10.16.1.11':
        raise RuntimeError(f'Untested TensorRT version: {trt.__version__}; expected 10.16.1.11')
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,driver_version', '--format=csv,noheader'],
                                  text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
    return dict(tensorrt=trt.__version__, onnxruntime=ort.__version__, gpu=gpu)


def providers(mode, path):
    if path is None: raise ValueError('TensorRT requires the model path for its cache key')
    env = environment()
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    key = hashlib.sha256(json.dumps(dict(**env, model=digest, mode=mode), sort_keys=True).encode()).hexdigest()
    cache = Path(__file__).resolve().parents[1]/'models/trt-cache'/key
    cache.mkdir(parents=True, exist_ok=True)
    (cache/'identity.json').write_text(json.dumps(dict(**env, model=digest, mode=mode), indent=2), encoding='utf-8')
    return [('TensorrtExecutionProvider', dict(device_id=0, trt_fp16_enable=mode=='trt-fp16',
             trt_engine_cache_enable=True, trt_engine_cache_path=str(cache),
             trt_timing_cache_enable=True, trt_timing_cache_path=str(cache),
             trt_max_workspace_size=2*1024**3)),
            ('CUDAExecutionProvider', dict(device_id=0, enable_cuda_graph='0'))]


def require_provider(session, mode):
    expected = 'TensorrtExecutionProvider' if mode in MODES else 'CUDAExecutionProvider'
    session.disable_fallback()
    if session.get_providers()[0] != expected:
        raise RuntimeError(f'{expected} initialization failed; refusing silent fallback')
