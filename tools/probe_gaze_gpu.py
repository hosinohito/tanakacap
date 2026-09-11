"""Synthetic GPU execution/latency probe; makes no claim about gaze accuracy."""
import sys,json,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.gaze import IrisGaze

output=Path('results/gaze-contour'); output.mkdir(exist_ok=True,parents=True)
model=IrisGaze(output)
tensor=np.random.default_rng(12).random((1,3,64,64),dtype=np.float32)
times=[]
for i in range(103):
    start=time.perf_counter()
    result,contour=model.session.run(['output_iris','output_eyes_contours_and_brows'],{'input_1':tensor})
    model.calls+=1
    if i>=3: times.append((time.perf_counter()-start)*1000)
    assert result.shape==(1,15) and np.isfinite(result).all()
    assert contour.shape==(1,213) and np.isfinite(contour).all()
report=model.finish()
report.update(synthetic=True,accuracy_verified=False,call_ms_p50=float(np.median(times)),call_ms_p95=float(np.percentile(times,95)))
(output/'gpu.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
