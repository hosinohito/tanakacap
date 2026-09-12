"""Deterministic local derivatives; original weights are never overwritten."""
from pathlib import Path
import onnx
from .models import sha256


def split_detector(path):
    path=Path(path)
    folder=path.parent / ('split-v1-'+sha256(path)[:16])
    fixed, tail = folder/'fixed.onnx', folder/'nms.onnx'
    if fixed.exists() and tail.exists(): return fixed, tail
    model=onnx.shape_inference.infer_shapes(onnx.load(path))
    cuts=[i for i,n in enumerate(model.graph.node) if n.op_type=='NonMaxSuppression']
    if len(cuts)!=1: raise ValueError('Expected one detector NMS')
    cut=cuts[0]
    outputs={o for n in model.graph.node[:cut] for o in n.output}
    boundary=sorted({i for n in model.graph.node[cut:] for i in n.input if i in outputs})
    extractor=onnx.utils.Extractor(model)
    core=extractor.extract_model([i.name for i in model.graph.input],boundary)
    end=extractor.extract_model(boundary,[o.name for o in model.graph.output])
    for value in core.graph.output:
        if any(not d.HasField('dim_value') or d.dim_value<=0 for d in value.type.tensor_type.shape.dim):
            raise ValueError('Detector graph boundary is not fixed size')
    folder.mkdir(parents=True,exist_ok=True)
    for model,target in [(core,fixed),(end,tail)]:
        onnx.checker.check_model(model)
        temporary=target.with_suffix('.tmp')
        onnx.save(model,temporary);temporary.replace(target)
    return fixed,tail
