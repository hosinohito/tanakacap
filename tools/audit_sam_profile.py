"""Summarize real CUDA activity separately from annotation spans and CPU waits."""
import argparse
import bisect
import json
from collections import Counter
from pathlib import Path


def union_us(events):
    end = None
    total = 0.0
    for start, stop in sorted((e["ts"], e["ts"] + e["dur"]) for e in events):
        total += max(0.0, stop - max(start, end if end is not None else start))
        end = max(stop, end if end is not None else stop)
    return total


def analyze(path):
    events = [e for e in json.loads(path.read_text())["traceEvents"] if e.get("ph") == "X"]
    cpu_ranges = [e for e in events if e.get("cat") == "user_annotation" and e.get("name", "").startswith("SAM_")]
    full = [e for e in cpu_ranges if e["name"] == "SAM_FULL_FRAME"]
    if len(full) != 1:
        raise ValueError("One full-frame CPU annotation required")
    kernels = [e for e in events if e.get("cat") == "kernel"]
    gpu = [e for e in events if e.get("cat") in ("kernel", "gpu_memcpy", "gpu_memset")]
    runtime = [e for e in events if e.get("cat") in ("cuda_runtime", "cuda_driver")]
    sync = [e for e in runtime if "Synchronize" in e["name"]]
    mhr = sorted((e["ts"], e["ts"] + e["dur"]) for e in cpu_ranges if e["name"] == "SAM_MHR")
    starts = [a for a, b in mhr]
    def inside_mhr(event):
        i = bisect.bisect_right(starts, event["ts"]) - 1
        return i >= 0 and event["ts"] + event["dur"] <= mhr[i][1]
    return dict(trace=str(path), cpu_frame_ms=full[0]["dur"]/1000,
        cpu_ranges={name:dict(count=sum(e["name"] == name for e in cpu_ranges), inclusive_ms=sum(e["dur"] for e in cpu_ranges if e["name"] == name)/1000) for name in sorted({e["name"] for e in cpu_ranges})},
        kernel_count=len(kernels), kernel_union_ms=union_us(kernels)/1000,
        gpu_kernel_copy_memset_union_ms=union_us(gpu)/1000,
        synchronization_calls=len(sync), synchronization_cpu_ms=sum(e["dur"] for e in sync)/1000,
        mhr_synchronization_calls=sum(inside_mhr(e) for e in sync),
        mhr_synchronization_cpu_ms=sum(e["dur"] for e in sync if inside_mhr(e))/1000,
        mhr_nonzero_calls=sum(e.get("cat") == "cpu_op" and e["name"] == "aten::nonzero" and inside_mhr(e) for e in events),
        runtime_call_counts=dict(Counter(e["name"] for e in runtime)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument("folder",type=Path);args=parser.parse_args()
    records=[analyze(p) for p in sorted(args.folder.glob("*/trace-*.json"))]
    if not records: raise ValueError("No traces found")
    result={"scope":"Instrumented frames only. GPU activity is interval union, not annotation duration. CPU inclusive ranges overlap and must not be summed. Synchronization is waiting as well as runtime overhead, not CPU arithmetic. No production FPS claim.", "records":records}
    (args.folder/"trace-audit.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    for record in records: print(json.dumps(record))


if __name__ == "__main__": main()
