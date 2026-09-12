import json
import pytest
from tools.audit_sam_profile import analyze, union_us


def test_union_does_not_double_count_nested_or_overlapping_activity():
    assert union_us([{"ts": 8, "dur": 5}, {"ts": 0, "dur": 10}, {"ts": 2, "dur": 3}, {"ts": 20, "dur": 2}]) == 15
    assert union_us([]) == 0


def test_gpu_annotation_is_not_kernel_time(tmp_path):
    def event(cat, name, ts, dur):
        return dict(ph="X", cat=cat, name=name, ts=ts, dur=dur)
    path=tmp_path/"trace.json"
    path.write_text(json.dumps({"traceEvents": [
        event("user_annotation", "SAM_FULL_FRAME", 0, 1000),
        event("gpu_user_annotation", "SAM_FULL_FRAME", 0, 999),
        event("user_annotation", "SAM_MHR", 100, 400),
        event("kernel", "compute", 200, 100),
        event("gpu_memcpy", "copy", 280, 50),
        event("cuda_runtime", "cudaStreamSynchronize", 400, 50),
        event("cuda_runtime", "cudaStreamSynchronize", 600, 100),
        event("cpu_op", "aten::nonzero", 150, 100),
    ]}))
    result=analyze(path)
    assert result["cpu_frame_ms"] == 1
    assert result["kernel_union_ms"] == .1
    assert result["gpu_kernel_copy_memset_union_ms"] == .13
    assert result["mhr_synchronization_calls"] == 1
    assert result["synchronization_calls"] == 2
    assert result["mhr_nonzero_calls"] == 1


def test_reject_trace_without_cpu_frame(tmp_path):
    path=tmp_path/"empty.json";path.write_text('{"traceEvents": []}')
    with pytest.raises(ValueError): analyze(path)
